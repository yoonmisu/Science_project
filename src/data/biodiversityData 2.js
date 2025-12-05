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
