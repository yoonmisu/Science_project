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

// 카테고리별 국가 멸종위기종 수 데이터 (ISO Alpha-2 코드 사용)
// 수치가 높을수록 멸종위기종이 많음
export const endangeredSpeciesCount = {
  동물: {
    'US': 95,  // 미국
    'CN': 120, // 중국
    'BR': 130, // 브라질
    'ID': 115, // 인도네시아
    'IN': 105, // 인도
    'AU': 90,  // 호주
    'MX': 100, // 멕시코
    'RU': 75,  // 러시아
    'JP': 65,  // 일본
    'KR': 45,  // 한국
    'CA': 70,  // 캐나다
    'DE': 40,  // 독일
    'FR': 50,  // 프랑스
    'GB': 35,  // 영국
    'AR': 80,  // 아르헨티나
    'ZA': 85,  // 남아공
    'KE': 95,  // 케냐
    'PH': 110, // 필리핀
    'MY': 105, // 말레이시아
    'TH': 90   // 태국
  },
  식물: {
    'BR': 140, // 브라질
    'CN': 110, // 중국
    'MX': 100, // 멕시코
    'ID': 115, // 인도네시아
    'AU': 105, // 호주
    'IN': 95,  // 인도
    'US': 85,  // 미국
    'ZA': 90,  // 남아공
    'MY': 100, // 말레이시아
    'PH': 95,  // 필리핀
    'JP': 55,  // 일본
    'KR': 40,  // 한국
    'RU': 60,  // 러시아
    'CA': 45,  // 캐나다
    'AR': 75,  // 아르헨티나
    'KE': 80,  // 케냐
    'TH': 85,  // 태국
    'DE': 35,  // 독일
    'FR': 40,  // 프랑스
    'GB': 30   // 영국
  },
  곤충: {
    'BR': 125, // 브라질
    'ID': 110, // 인도네시아
    'MX': 95,  // 멕시코
    'CN': 90,  // 중국
    'IN': 85,  // 인도
    'AU': 80,  // 호주
    'US': 75,  // 미국
    'MY': 95,  // 말레이시아
    'PH': 90,  // 필리핀
    'TH': 85,  // 태국
    'ZA': 70,  // 남아공
    'KE': 75,  // 케냐
    'JP': 50,  // 일본
    'KR': 35,  // 한국
    'RU': 45,  // 러시아
    'CA': 40,  // 캐나다
    'AR': 65,  // 아르헨티나
    'DE': 30,  // 독일
    'FR': 35,  // 프랑스
    'GB': 25   // 영국
  },
  해양생물: {
    'ID': 120, // 인도네시아
    'PH': 115, // 필리핀
    'AU': 110, // 호주
    'US': 100, // 미국
    'MY': 105, // 말레이시아
    'JP': 90,  // 일본
    'CN': 95,  // 중국
    'BR': 100, // 브라질
    'MX': 90,  // 멕시코
    'IN': 85,  // 인도
    'TH': 95,  // 태국
    'ZA': 75,  // 남아공
    'KE': 70,  // 케냐
    'KR': 60,  // 한국
    'RU': 65,  // 러시아
    'CA': 70,  // 캐나다
    'AR': 75,  // 아르헨티나
    'DE': 40,  // 독일
    'FR': 50,  // 프랑스
    'GB': 55   // 영국
  }
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
  console.log(`📊 [updateSpeciesCount] ${category} 업데이트:`, dynamicSpeciesCount[category]);
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

// 색상 강도 계산 함수 (데이터가 있는 국가들끼리만 비교)
export const getColorIntensity = (category, countryCode) => {
  const colors = categoryThemes[category]?.colors || categoryThemes['동물'].colors;
  const minColor = '#f0f0f0';  // 데이터 없는 경우: 연한 회색

  // 동적 데이터만 사용 (실시간 API) - 정적 데이터 fallback 제거
  const dynamicData = dynamicSpeciesCount[category];
  if (dynamicData && Object.keys(dynamicData).length > 0) {
    const count = dynamicData[countryCode] || 0;

    // 데이터가 없는 경우: 최소 디자인 (연한 회색)
    if (count === 0) return minColor;

    // 데이터가 있는 국가들만 필터링
    const validCounts = Object.values(dynamicData).filter(c => c > 0);

    if (validCounts.length === 0) return minColor;

    // 데이터가 있는 국가들 중에서 최소/최대값 계산
    const minCount = Math.min(...validCounts);
    const maxCount = Math.max(...validCounts);

    // 단일 값인 경우 중간 색상
    if (minCount === maxCount) return colors[2];

    // 데이터가 있는 국가들끼리만 비교하여 5등분
    const range = maxCount - minCount;
    const step = range / 5;
    const normalizedCount = count - minCount;

    // 5개 그룹으로 균등 분할
    if (normalizedCount <= step) return colors[0];        // 0-20%
    if (normalizedCount <= step * 2) return colors[1];    // 20-40%
    if (normalizedCount <= step * 3) return colors[2];    // 40-60%
    if (normalizedCount <= step * 4) return colors[3];    // 60-80%
    return colors[4];                                      // 80-100%
  }

  // 동적 데이터가 없으면 기본 회색 반환 (정적 데이터 fallback 제거)
  return minColor;
};
