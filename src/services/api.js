/**
 * Verde API Service
 *
 * GUIDE API와 통신하는 서비스 레이어
 *
 * 설정 방법:
 * 1. .env 파일에 다음 환경변수를 설정하세요:
 *    VITE_API_BASE_URL=http://127.0.0.1:8000
 *    VITE_API_KEY=your_api_key_here (선택사항)
 *
 * 2. API 엔드포인트는 아래 BASE_URL 변수에서 수정 가능합니다
 */

// API 기본 설정
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const API_KEY = import.meta.env.VITE_API_KEY || ''; // API Key가 필요한 경우

/**
 * 국가 코드 매핑 (지도 코드 -> API 코드)
 * 전 세계 주요 국가 지원
 */
const COUNTRY_MAPPING = {
  // 아시아
  'korea': 'korea',
  'japan': 'japan',
  'china': 'china',
  'india': 'india',

  // 북미
  'usa': 'usa',
  'canada': 'canada',
  'mexico': 'mexico',

  // 유럽
  'russia': 'russia',
  'uk': 'uk',
  'germany': 'germany',
  'france': 'france',

  // 남미
  'brazil': 'brazil',
  'argentina': 'argentina',

  // 아프리카
  'southafrica': 'southafrica',
  'kenya': 'kenya',

  // 오세아니아
  'australia': 'australia',
  'newzealand': 'newzealand'
};

/**
 * API 요청 헬퍼 함수
 * @param {string} endpoint - API 엔드포인트
 * @param {Object} options - fetch 옵션
 * @returns {Promise<Object>} API 응답
 */
const apiRequest = async (endpoint, options = {}) => {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // API Key가 있는 경우 헤더에 추가
  if (API_KEY) {
    headers['Authorization'] = `Bearer ${API_KEY}`;
  }

  const fullUrl = `${BASE_URL}${endpoint}`;
  console.log('🌐 API 요청 시작:', fullUrl);
  console.log('📋 요청 헤더:', headers);

  try {
    const response = await fetch(fullUrl, {
      ...options,
      headers,
    });

    console.log('📥 응답 상태:', response.status, response.statusText);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ API 오류 응답:', errorText);
      throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const jsonData = await response.json();
    console.log('✅ JSON 파싱 성공:', jsonData);
    return jsonData;
  } catch (error) {
    console.error('❌ API Request Failed:', error);
    console.error('❌ 에러 상세:', {
      message: error.message,
      stack: error.stack,
      endpoint: endpoint,
      fullUrl: fullUrl
    });
    throw error;
  }
};

/**
 * 국가별 생물 종 데이터 조회
 *
 * @param {string} countryCode - 국가 코드 (예: 'korea', 'japan')
 * @param {string} category - 카테고리 (예: '동물', '식물', '곤충', '해양생물')
 * @param {number} page - 페이지 번호 (기본값: 1)
 * @param {number} limit - 페이지당 항목 수 (기본값: 3)
 * @param {string|null} speciesName - 종 이름 필터 (검색 모드일 때, 기본값: null)
 * @returns {Promise<Object>} { data: [], total, page, totalPages }
 */
export const fetchSpeciesByCountry = async (countryCode, category, page = 1, limit = 3, speciesName = null) => {
  try {
    console.log(`🔍 API 호출: ${countryCode} - ${category} (페이지 ${page})${speciesName ? ` [검색: ${speciesName}]` : ''}`);

    // ISO Alpha-2 코드를 직접 사용 (예: 'kr', 'jp', 'us')
    // IUCN API는 ISO 코드를 대문자로 요구 (백엔드에서 처리)
    const params = new URLSearchParams({
      country: countryCode, // ISO 코드 직접 전달
      category: category,
      page: page.toString(),
      limit: limit.toString(),
    });

    // 검색 모드일 때 species_name 파라미터 추가
    if (speciesName) {
      params.append('species_name', speciesName);
    }

    const response = await apiRequest(`/api/v1/species?${params}`);

    console.log(`✅ 데이터 수신 완료: ${response.data.length}개 종`);

    return {
      data: response.data.map(species => ({
        id: species.id,
        name: species.common_name || species.scientific_name, // Wikipedia common_name 사용
        image: species.image_url || species.image || '🌱', // image_url 필드 사용
        color: species.color || 'green',
        scientificName: species.scientific_name,
        description: species.description,
        riskLevel: species.risk_level, // 위험 등급
        country: species.country,
      })),
      total: response.total,
      page: response.page,
      totalPages: response.totalPages,
    };
  } catch (error) {
    console.error('❌ fetchSpeciesByCountry 오류:', error);
    throw error;
  }
};

/**
 * 좌표 기반 생물 종 조회 (전 세계 지원)
 *
 * ⚠️ 사용되지 않음: 실제로는 국가 코드 기반 조회(fetchSpeciesByCountry)만 사용됩니다.
 * 좌표 정보는 UI 표시용으로만 사용되며, API 호출에는 사용되지 않습니다.
 *
 * @deprecated 이 함수는 더 이상 사용되지 않습니다. fetchSpeciesByCountry를 사용하세요.
 * @param {number} lat - 위도 (-90 ~ 90)
 * @param {number} lng - 경도 (-180 ~ 180)
 * @param {string} category - 카테고리
 * @param {number} page - 페이지 번호
 * @param {number} limit - 페이지당 항목 수
 * @returns {Promise<Object>} { data: [], total, page, totalPages, country }
 */
export const fetchSpeciesByLocation = async (lat, lng, category, page = 1, limit = 3) => {
  console.warn('⚠️ fetchSpeciesByLocation은 더 이상 사용되지 않습니다. fetchSpeciesByCountry를 사용하세요.');

  try {
    console.log(`🌍 좌표 기반 API 호출: (${lat}, ${lng}) - ${category}`);

    const params = new URLSearchParams({
      lat: lat.toString(),
      lng: lng.toString(),
      category: category,
      page: page.toString(),
      limit: limit.toString(),
    });

    const response = await apiRequest(`/api/v1/species/by-location?${params}`);

    console.log(`✅ 좌표 기반 데이터 수신 완료: ${response.data.length}개 종`);

    return {
      data: response.data.map(species => ({
        id: species.id,
        name: species.name,
        image: species.image || '🌱',
        color: species.color || 'green',
        scientificName: species.scientific_name,
        description: species.description,
        country: species.country,
      })),
      total: response.total,
      page: response.page,
      totalPages: response.totalPages,
    };
  } catch (error) {
    console.error('❌ fetchSpeciesByLocation 오류:', error);
    throw error;
  }
};

/**
 * 특정 종의 상세 정보 조회
 *
 * @param {number} speciesId - 종 ID
 * @param {string} lang - 언어 코드 (ko, en, ja, zh 등) - navigator.language에서 추출
 * @returns {Promise<Object>} 종 상세 정보
 */
export const fetchSpeciesDetail = async (speciesId, lang = 'en') => {
  try {
    console.log(`🔍 종 상세 정보 조회: ID ${speciesId} (언어: ${lang})`);

    const params = new URLSearchParams({ lang });
    const response = await apiRequest(`/api/v1/species/${speciesId}?${params}`);

    console.log(`✅ 상세 정보 수신 완료: ${response.name}`);

    // 에러 응답 처리 (백엔드에서 error 필드를 포함한 경우)
    if (response.error) {
      console.warn(`⚠️ 상세 정보 조회 실패: ${response.error_message}`);
    }

    return {
      id: response.id,
      name: response.name,
      scientificName: response.scientific_name,
      commonName: response.common_name,
      category: response.category,
      country: response.country,
      image: response.image || '',
      color: response.color || 'green',
      description: response.description || '',
      status: response.status,
      population: response.population,
      habitat: response.habitat,
      threats: response.threats || [],
      error: response.error || false,
      errorMessage: response.error_message || null,
    };
  } catch (error) {
    console.error('❌ fetchSpeciesDetail 오류:', error);
    throw error;
  }
};

/**
 * 멸종위기종 목록 조회
 *
 * @param {string} countryCode - 국가 코드
 * @param {string} category - 카테고리 (선택사항)
 * @param {number} page - 페이지 번호
 * @param {number} limit - 페이지당 항목 수
 * @returns {Promise<Object>} 멸종위기종 목록
 */
export const fetchEndangeredSpecies = async (countryCode, category = null, page = 1, limit = 20) => {
  try {
    console.log(`🔍 멸종위기종 조회: ${countryCode}`);

    const mappedCountry = COUNTRY_MAPPING[countryCode] || countryCode;

    const params = new URLSearchParams({
      country: mappedCountry,
      page: page.toString(),
      limit: limit.toString(),
    });

    if (category) {
      params.append('category', category);
    }

    const response = await apiRequest(`/api/v1/species/endangered?${params}`);

    console.log(`✅ 멸종위기종 ${response.data.length}개 수신`);

    return {
      data: response.data.map(species => ({
        id: species.id,
        name: species.name,
        image: species.image || '🌱',
        status: species.status,
        population: species.population,
        threats: species.threats || [],
      })),
      total: response.total,
      page: response.page,
      totalPages: response.totalPages,
    };
  } catch (error) {
    console.error('❌ fetchEndangeredSpecies 오류:', error);
    throw error;
  }
};

/**
 * 오늘의 랜덤 생물 조회
 *
 * @returns {Promise<Object>} 오늘의 랜덤 생물 정보
 */
export const fetchDailyRandomSpecies = async () => {
  try {
    console.log('🎲 오늘의 랜덤 생물 조회 중...');

    const response = await apiRequest('/api/v1/species/random-daily');

    console.log(`✅ 오늘의 랜덤 생물: ${response.scientific_name}`);

    return {
      scientificName: response.scientific_name,
      date: response.date,
      message: response.message,
    };
  } catch (error) {
    console.error('❌ fetchDailyRandomSpecies 오류:', error);
    return null;
  }
};

/**
 * 주간 인기 생물 조회
 *
 * @returns {Promise<Object>} 주간 최다 검색 생물 정보
 */
export const fetchWeeklyTopSpecies = async () => {
  try {
    console.log('🔥 주간 인기 생물 조회 중...');

    const response = await apiRequest('/api/v1/species/weekly-top');

    console.log(`✅ 주간 인기 생물: ${response.species_name} (${response.search_count}회)`);

    return {
      speciesName: response.species_name,
      searchCount: response.search_count,
      periodDays: response.period_days,
      message: response.message,
    };
  } catch (error) {
    console.error('❌ fetchWeeklyTopSpecies 오류:', error);
    return null;
  }
};

/**
 * 인기 멸종위기종 조회
 *
 * ⚠️ 미구현 기능: 백엔드에 /api/v1/species/popular-endangered 엔드포인트 추가 필요
 *
 * @param {number} limit - 조회할 항목 수
 * @returns {Promise<Object>} 인기 멸종위기종 목록
 */
export const fetchPopularEndangered = async (limit = 10) => {
  try {
    console.log('📊 인기 멸종위기종 조회 중...');

    const response = await apiRequest(`/api/v1/species/popular-endangered?limit=${limit}`);

    console.log(`✅ 인기 멸종위기종 ${response.data.length}개 수신`);

    return {
      data: response.data.map(species => ({
        id: species.id,
        name: species.name,
        country: species.country,
        category: species.category,
        mentions: species.mentions || 0,
        status: species.status,
      })),
    };
  } catch (error) {
    console.error('❌ fetchPopularEndangered 오류:', error);
    throw error;
  }
};

/**
 * 생물 검색
 *
 * @param {string} query - 검색어
 * @param {string} country - 국가 필터 (선택사항)
 * @param {string} category - 카테고리 필터 (선택사항)
 * @param {number} page - 페이지 번호
 * @param {number} limit - 페이지당 항목 수
 * @returns {Promise<Object>} 검색 결과
 */
export const searchSpecies = async (query, country = null, category = null, page = 1, limit = 20) => {
  try {
    console.log(`🔍 생물 검색: "${query}"`);

    const params = new URLSearchParams({
      q: query,
      page: page.toString(),
      limit: limit.toString(),
    });

    if (country) {
      params.append('country', COUNTRY_MAPPING[country] || country);
    }

    if (category) {
      params.append('category', category);
    }

    // ⚠️ 미구현: 현재는 searchSpeciesByName()을 사용 중
    // 향후 상세 검색 기능 추가 시 백엔드 구현 필요
    const response = await apiRequest(`/api/v1/species/search?${params}`);

    console.log(`✅ 검색 결과 ${response.data.length}개 수신`);

    return {
      data: response.data.map(species => ({
        id: species.id,
        name: species.name,
        image: species.image || '🌱',
        category: species.category,
        country: species.country,
      })),
      total: response.total,
      page: response.page,
      totalPages: response.totalPages,
      query: response.query,
    };
  } catch (error) {
    console.error('❌ searchSpecies 오류:', error);
    throw error;
  }
};

/**
 * 종 이름으로 검색하여 해당 종이 서식하는 국가 목록 조회
 *
 * @param {string} query - 종 이름 검색어
 * @param {string} category - 카테고리 (선택사항)
 * @returns {Promise<Object>} { query, countries: [], total }
 */
export const searchSpeciesByName = async (query, category = null) => {
  try {
    console.log(`🔍 종 검색: "${query}" (카테고리: ${category})`);

    const params = new URLSearchParams({
      query: query,
    });

    if (category) {
      params.append('category', category);
    }

    const response = await apiRequest(`/api/v1/species/search?${params}`);

    console.log(`✅ 검색 결과: ${response.countries.length}개 국가 (카테고리: ${response.category})`);

    return {
      query: response.query,
      countries: response.countries,
      total: response.total,
      category: response.category, // 매칭된 카테고리 추가
      matchedSpecies: response.matched_species, // 검색된 종 이름 (한글/영어)
      matchedScientificName: response.matched_scientific_name, // 검색된 종 학명 (정확한 필터링용)
    };
  } catch (error) {
    console.error('❌ searchSpeciesByName 오류:', error);
    throw error;
  }
};

/**
 * 실시간 검색어 랭킹 조회
 *
 * @param {number} limit - 조회할 검색어 개수 (기본 7개)
 * @param {number} hours - 조회 기간 시간 (기본 24시간)
 * @returns {Promise<Object>} { data: [{rank, query, count}], period_hours, total }
 */
export const fetchTrendingSearches = async (limit = 7, hours = 24) => {
  try {
    console.log(`📊 실시간 검색어 조회 중... (최근 ${hours}시간, ${limit}개)`);

    const params = new URLSearchParams({
      limit: limit.toString(),
      hours: hours.toString(),
    });

    const response = await apiRequest(`/api/v1/species/trending?${params}`);

    console.log(`✅ 실시간 검색어 ${response.data.length}개 수신`);

    return {
      data: response.data,
      periodHours: response.period_hours,
      total: response.total,
    };
  } catch (error) {
    console.error('❌ fetchTrendingSearches 오류:', error);
    return {
      data: [],
      periodHours: hours,
      total: 0,
    };
  }
};

/**
 * 모든 국가의 종 개수 조회 (지도 시각화용)
 *
 * @param {string} category - 카테고리 (예: '동물', '식물')
 * @returns {Promise<Object>} { 'KR': 10, 'US': 15, ... }
 */
export const fetchAllCountriesSpeciesCount = async (category = '동물') => {
  try {
    console.log(`📊 모든 국가의 종 개수 조회 (카테고리: ${category})`);

    const params = new URLSearchParams({
      category: category,
    });

    const response = await apiRequest(`/api/v1/species/stats/countries?${params}`);

    console.log(`✅ 국가별 종 개수 수신:`, response);

    return response;
  } catch (error) {
    console.error('❌ fetchAllCountriesSpeciesCount 오류:', error);
    return {};
  }
};

/**
 * API 연결 상태 확인
 *
 * @returns {Promise<boolean>} API 연결 성공 여부
 */
export const checkApiHealth = async () => {
  try {
    const response = await apiRequest('/');
    return response && response.message;
  } catch (error) {
    console.error('❌ API 연결 실패:', error);
    return false;
  }
};
