// IUCN Red List API
// API 문서: https://apiv3.iucnredlist.org/api/v3/docs

const IUCN_API_KEY = import.meta.env.VITE_IUCN_API_KEY || 'YOUR_API_KEY';
const IUCN_BASE_URL = 'https://apiv3.iucnredlist.org/api/v3';

/**
 * 국가별 멸종위기종 목록 조회
 * @param {string} countryCode - ISO-2 country code (e.g., 'KR', 'US')
 * @param {number} page - 페이지 번호 (기본값: 0)
 * @returns {Promise<Object>} 멸종위기종 목록
 */
export const getEndangeredSpeciesByCountry = async (countryCode, page = 0) => {
  try {
    const response = await fetch(
      `${IUCN_BASE_URL}/country/getspecies/${countryCode}?token=${IUCN_API_KEY}`
    );

    if (!response.ok) {
      throw new Error(`IUCN API error: ${response.status}`);
    }

    const data = await response.json();

    // 멸종위기종만 필터링 (CR, EN, VU)
    const endangeredSpecies = data.result?.filter(species =>
      ['CR', 'EN', 'VU'].includes(species.category)
    ) || [];

    return {
      total: endangeredSpecies.length,
      species: endangeredSpecies,
      page,
      hasMore: false
    };
  } catch (error) {
    console.error('IUCN API 오류:', error);
    return {
      total: 0,
      species: [],
      page: 0,
      hasMore: false,
      error: error.message
    };
  }
};

/**
 * 특정 종의 상세 정보 조회
 * @param {string} scientificName - 학명 (e.g., 'Panthera tigris')
 * @returns {Promise<Object>} 종 상세 정보
 */
export const getSpeciesDetails = async (scientificName) => {
  try {
    const response = await fetch(
      `${IUCN_BASE_URL}/species/${encodeURIComponent(scientificName)}?token=${IUCN_API_KEY}`
    );

    if (!response.ok) {
      throw new Error(`IUCN API error: ${response.status}`);
    }

    const data = await response.json();
    return data.result?.[0] || null;
  } catch (error) {
    console.error('IUCN API 종 상세 정보 오류:', error);
    return null;
  }
};

/**
 * 종의 위협 요인 조회
 * @param {string} scientificName - 학명
 * @returns {Promise<Array>} 위협 요인 목록
 */
export const getSpeciesThreats = async (scientificName) => {
  try {
    const response = await fetch(
      `${IUCN_BASE_URL}/threats/species/name/${encodeURIComponent(scientificName)}?token=${IUCN_API_KEY}`
    );

    if (!response.ok) {
      throw new Error(`IUCN API error: ${response.status}`);
    }

    const data = await response.json();
    return data.result || [];
  } catch (error) {
    console.error('IUCN API 위협 요인 오류:', error);
    return [];
  }
};

/**
 * 멸종위기 등급 설명
 */
export const IUCN_CATEGORIES = {
  'EX': { label: '절멸', color: '#000000', description: '마지막 개체가 사망한 종' },
  'EW': { label: '야생절멸', color: '#542344', description: '야생에서는 절멸, 사육 중인 종' },
  'CR': { label: '위급', color: '#d81e05', description: '극도로 높은 절멸 위험' },
  'EN': { label: '위기', color: '#fc7f3f', description: '높은 절멸 위험' },
  'VU': { label: '취약', color: '#f9e814', description: '야생 절멸 위험 증가' },
  'NT': { label: '준위협', color: '#cce226', description: '가까운 미래 위협 가능' },
  'LC': { label: '관심대상', color: '#60c659', description: '낮은 절멸 위험' },
  'DD': { label: '정보부족', color: '#d1d1c6', description: '평가 자료 부족' },
  'NE': { label: '미평가', color: '#ffffff', description: '아직 평가되지 않음' }
};
