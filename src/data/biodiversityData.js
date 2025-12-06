/**
 * Verde 생물 다양성 데이터 설정
 *
 * 참고: countryData는 제거되었습니다.
 * 모든 생물 종 데이터는 백엔드 API에서 동적으로 가져옵니다.
 * API: GET /api/v1/species?country={country}&category={category}
 */

// 카테고리별 테마 설정 (색상 코드 포함)
export const categoryThemes = {
  식물: {
    bg: 'bg-white',
    border: 'border-green-200',
    button: 'bg-green-100 hover:bg-green-200',
    title: 'text-black',
    icon: '🌿',
    colors: ['#d1fae5', '#6ee7b7', '#34d399', '#10b981', '#059669'] // green 계열 (연한 -> 진한)
  },
  동물: {
    bg: 'bg-white',
    border: 'border-amber-200',
    button: 'bg-amber-100 hover:bg-amber-200',
    title: 'text-black',
    icon: '🦌',
    colors: ['#fef3c7', '#fde68a', '#fbbf24', '#f59e0b', '#d97706'] // amber 계열 (연한 -> 진한)
  },
  곤충: {
    bg: 'bg-white',
    border: 'border-yellow-200',
    button: 'bg-yellow-100 hover:bg-yellow-200',
    title: 'text-black',
    icon: '🐝',
    colors: ['#fef9c3', '#fef08a', '#fde047', '#facc15', '#eab308'] // yellow 계열 (연한 -> 진한)
  },
  해양생물: {
    bg: 'bg-white',
    border: 'border-blue-200',
    button: 'bg-blue-100 hover:bg-blue-200',
    title: 'text-black',
    icon: '🐠',
    colors: ['#dbeafe', '#93c5fd', '#60a5fa', '#3b82f6', '#2563eb'] // blue 계열 (연한 -> 진한)
  }
};

// 국가 이름 매핑 (표시용)
export const countryNames = {
  korea: '대한민국',
  japan: '일본',
  china: '중국',
  usa: '미국',
  russia: '러시아',
  canada: '캐나다',
  mexico: '멕시코',
  brazil: '브라질',
  argentina: '아르헨티나',
  uk: '영국',
  germany: '독일',
  france: '프랑스',
  india: '인도',
  australia: '호주',
  newzealand: '뉴질랜드',
  southafrica: '남아프리카공화국',
  kenya: '케냐'
};

// 동적 종 개수 저장소 (실시간 API 데이터 기반)
let dynamicSpeciesCount = {};

/**
 * 국가별 종 개수를 업데이트 (API 데이터 기반)
 * @param {Object} countData - { 'KR': 10, 'US': 15, ... }
 * @param {string} category - 카테고리
 */
export const updateSpeciesCount = (countData, category) => {
  if (!dynamicSpeciesCount[category]) {
    dynamicSpeciesCount[category] = {};
  }
  dynamicSpeciesCount[category] = { ...dynamicSpeciesCount[category], ...countData };
  const countryCount = Object.keys(dynamicSpeciesCount[category]).length;
  console.log(`📊 [updateSpeciesCount] ${category} 업데이트: ${countryCount}개 국가`);
  console.log(`   국가 목록: ${Object.keys(dynamicSpeciesCount[category]).join(', ')}`);
  console.log(`   샘플 데이터:`, Object.entries(dynamicSpeciesCount[category]).slice(0, 5));

  // 디버그 캐시 초기화 (새 데이터가 로드되었으므로)
  debugLogCache = {};
};

/**
 * 모든 국가의 종 개수 초기화
 * @param {string} category - 카테고리
 */
export const resetSpeciesCount = (category) => {
  dynamicSpeciesCount[category] = {};
  console.log(`🔄 [resetSpeciesCount] ${category} 초기화`);
};

/**
 * 현재 종 개수 데이터 조회
 * @param {string} category - 카테고리
 * @returns {Object} - { 'KR': 10, 'US': 15, ... }
 */
export const getSpeciesCount = (category) => {
  return dynamicSpeciesCount[category] || {};
};

// 색상 분포 통계 캐시 (디버깅 및 성능 최적화)
let colorStatsCache = {};

/**
 * 색상 강도 계산 함수 (동적 데이터 기반 5단계 시각화)
 *
 * API에서 받은 실제 종 개수 데이터를 기반으로:
 * 1. 모든 국가의 종 개수를 수집
 * 2. 순위 기반으로 5그룹으로 분할
 * 3. 각 국가에 해당하는 색상 반환
 *
 * 반환값:
 * - { color: string, hasData: true } : 종이 있는 국가 (색상 표시)
 * - { color: null, hasData: false } : 종이 없는 국가 (회색 표시)
 * - { color: null, hasData: true, loading: true } : 데이터 로딩 중 (기본 색상)
 *
 * @param {string} category - 카테고리 (동물, 식물, 곤충, 해양생물)
 * @param {string} countryCode - ISO 국가 코드
 * @returns {{ color: string|null, hasData: boolean, loading?: boolean }}
 */
// 디버그 로그 캐시 (동일 호출 반복 방지)
let debugLogCache = {};

export const getColorIntensity = (category, countryCode) => {
  const colors = categoryThemes[category]?.colors || categoryThemes['동물'].colors;
  const NO_DATA = { color: null, hasData: false };
  const LOADING = { color: colors[2], hasData: true, loading: true }; // 로딩 중: 중간 색상

  // 동적 데이터 가져오기 (API에서 로드된 실시간 데이터)
  const dynamicData = dynamicSpeciesCount[category];

  // 디버그: 첫 5개 국가에 대해서만 로그 (KR, US, JP, CN, BR)
  const debugCountries = ['KR', 'US', 'JP', 'CN', 'BR'];
  const upperCode = countryCode?.toUpperCase();
  const shouldDebug = debugCountries.includes(upperCode);
  const debugKey = `${category}_${upperCode}`;

  // 데이터가 아직 로드되지 않은 경우: 로딩 상태 (기본 색상 표시)
  // 이렇게 하면 데이터 로드 전에도 지도에 색상이 표시됨
  if (!dynamicData || Object.keys(dynamicData).length === 0) {
    if (shouldDebug && !debugLogCache[debugKey + '_loading']) {
      debugLogCache[debugKey + '_loading'] = true;
      console.log(`🔍 [getColorIntensity] ${category}/${upperCode}: 데이터 없음 → LOADING`);
    }
    return LOADING;
  }

  // 대소문자 무시하고 국가 코드 매칭
  const count = dynamicData[upperCode] || dynamicData[countryCode];

  // 해당 국가 데이터가 없는 경우: 캐시에 없는 국가
  // - count가 undefined/null이면 캐시에 없음
  // - IUCN API에서 데이터를 제공하지 않는 국가이므로 중간 색상으로 표시 (클릭하면 API 호출 가능)
  if (count === undefined || count === null) {
    if (shouldDebug && !debugLogCache[debugKey + '_nodata']) {
      debugLogCache[debugKey + '_nodata'] = true;
      console.log(`🔍 [getColorIntensity] ${category}/${upperCode}: count=${count} → 캐시 미포함 (중간색상)`);
      console.log(`   dynamicData keys: ${Object.keys(dynamicData).slice(0, 10).join(', ')}`);
    }
    // 캐시에 없는 국가도 중간 색상으로 표시 (클릭 가능하게 유지)
    return { color: colors[1], hasData: true, notInCache: true };
  }

  // count가 0인 경우: 실제로 종이 없음 (회색 표시)
  if (count === 0) {
    if (shouldDebug && !debugLogCache[debugKey + '_zero']) {
      debugLogCache[debugKey + '_zero'] = true;
      console.log(`🔍 [getColorIntensity] ${category}/${upperCode}: count=0 → NO_DATA (회색)`);
    }
    return NO_DATA;
  }

  // 디버그 캐시 초기화 (데이터가 있으면)
  if (shouldDebug && !debugLogCache[debugKey + '_hasdata']) {
    debugLogCache[debugKey + '_hasdata'] = true;
    console.log(`🔍 [getColorIntensity] ${category}/${upperCode}: count=${count} → 색상 계산 진행`);
  }

  // 유효한 종 개수만 필터링 (1개 이상)
  const validCounts = Object.values(dynamicData).filter(c => c > 0);

  if (validCounts.length === 0) {
    return NO_DATA;
  }

  // 고유값 정렬 (5단계 분할 기준)
  const sortedUniqueCounts = [...new Set(validCounts)].sort((a, b) => a - b);
  const totalUniqueValues = sortedUniqueCounts.length;
  const minCount = sortedUniqueCounts[0];
  const maxCount = sortedUniqueCounts[totalUniqueValues - 1];

  // 통계 캐시 업데이트 (카테고리별 1회만 로그)
  const cacheKey = `${category}_${totalUniqueValues}`;
  if (!colorStatsCache[cacheKey]) {
    colorStatsCache[cacheKey] = true;
    console.log(`🎨 [${category}] 동적 색상 분포:`);
    console.log(`   범위: ${minCount} ~ ${maxCount} (${totalUniqueValues}개 고유값)`);
    console.log(`   고유값: ${sortedUniqueCounts.join(', ')}`);
  }

  // 모든 값이 같은 경우: 중간 색상
  if (minCount === maxCount) {
    return { color: colors[2], hasData: true };
  }

  // === 로그 스케일 기반 5단계 색상 ===
  // 실제 값 기반으로 계산 (순위 기반보다 직관적)
  // 로그 스케일을 사용하여 큰 값의 차이를 압축하고 작은 값의 차이를 확대

  let colorIndex;

  // 로그 스케일 적용 (0 방지를 위해 +1)
  const logMin = Math.log(minCount + 1);
  const logMax = Math.log(maxCount + 1);
  const logValue = Math.log(count + 1);

  // 0~1 사이 정규화 (로그 스케일)
  const normalizedValue = (logValue - logMin) / (logMax - logMin);

  // 5단계로 분류 (균등 분배)
  if (normalizedValue < 0.2) {
    colorIndex = 0;      // 하위 20%: 가장 연한색
  } else if (normalizedValue < 0.4) {
    colorIndex = 1;      // 20-40%
  } else if (normalizedValue < 0.6) {
    colorIndex = 2;      // 40-60%: 중간
  } else if (normalizedValue < 0.8) {
    colorIndex = 3;      // 60-80%
  } else {
    colorIndex = 4;      // 상위 20%: 가장 진한색
  }

  return { color: colors[colorIndex], hasData: true };
};

/**
 * 색상 분포 통계 초기화 (카테고리 변경 시 호출)
 */
export const resetColorStats = () => {
  colorStatsCache = {};
  debugLogCache = {};  // 디버그 로그 캐시도 초기화
  console.log('🔄 [resetColorStats] 색상 캐시 초기화됨');
};
