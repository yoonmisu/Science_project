/**
 * Verde 프로젝트 상수 정의
 * 
 * 하드코딩된 값들을 중앙 집중화하여 관리합니다.
 */

// ===========================================
// 카테고리 상수
// ===========================================
export const CATEGORIES = ['동물', '식물', '곤충', '해양생물'];

export const CATEGORY_ICONS = {
    동물: '🦌',
    식물: '🌿',
    곤충: '🐝',
    해양생물: '🐠'
};

// ===========================================
// API 설정
// ===========================================
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
export const API_TIMEOUT_MS = 30000;

// ===========================================
// UI 설정
// ===========================================
export const TRENDING_REFRESH_INTERVAL_MS = 5 * 60 * 1000; // 5분
export const DEFAULT_PAGE_SIZE = 3;
export const MAX_PAGE_SIZE = 100;

// ===========================================
// 검색 설정
// ===========================================
export const SEARCH_MIN_LENGTH = 1;

// ===========================================
// 지도 설정
// ===========================================
export const MAP_DEFAULT_WIDTH = 800;
export const MAP_DEFAULT_HEIGHT = 400;
export const MAP_DOT_SPACING = 3;
export const MAP_DOT_RADIUS = 1.5;
export const MAP_DOT_COLOR = '#9CA3AF';
export const MAP_HIGHLIGHT_COLOR = '#374151';

// ===========================================
// 위험 등급 색상 (IUCN Red List)
// ===========================================
export const RISK_LEVEL_COLORS = {
    EX: '#000000',   // Extinct
    EW: '#A855F7',   // Extinct in the Wild
    CR: '#EF4444',   // Critically Endangered
    EN: '#F97316',   // Endangered
    VU: '#EAB308',   // Vulnerable
    NT: '#22C55E',   // Near Threatened
    LC: '#3B82F6',   // Least Concern
    DD: '#9CA3AF',   // Data Deficient
    NE: '#D1D5DB'    // Not Evaluated
};

export const RISK_LEVEL_LABELS = {
    EX: '절멸',
    EW: '야생 절멸',
    CR: '위급',
    EN: '위기',
    VU: '취약',
    NT: '준위협',
    LC: '관심 필요',
    DD: '정보 부족',
    NE: '미평가'
};

// ===========================================
// 국가 코드 매핑
// ===========================================
export const COUNTRY_NAMES = {
    KR: '대한민국',
    US: '미국',
    JP: '일본',
    CN: '중국',
    RU: '러시아',
    AU: '호주',
    BR: '브라질',
    IN: '인도',
    ZA: '남아프리카공화국',
    CA: '캐나다',
    MX: '멕시코',
    AR: '아르헨티나',
    GB: '영국',
    FR: '프랑스',
    DE: '독일',
    IT: '이탈리아',
    ID: '인도네시아',
    TH: '태국',
    VN: '베트남',
    MY: '말레이시아',
    PH: '필리핀',
    KE: '케냐',
    TZ: '탄자니아',
    EG: '이집트',
    NG: '나이지리아'
};
