export const categoryThemes = {
  식물: {
    bg: 'bg-white',
    border: 'border-green-200',
    button: 'bg-green-100 hover:bg-green-200',
    title: 'text-black',
    icon: '🌿',
    colors: ['#d1fae5', '#6ee7b7', '#34d399', '#10b981', '#059669']
  },
  동물: {
    bg: 'bg-white',
    border: 'border-amber-200',
    button: 'bg-amber-100 hover:bg-amber-200',
    title: 'text-black',
    icon: '🦌',
    colors: ['#fef3c7', '#fde68a', '#fbbf24', '#f59e0b', '#d97706']
  },
  곤충: {
    bg: 'bg-white',
    border: 'border-yellow-200',
    button: 'bg-yellow-100 hover:bg-yellow-200',
    title: 'text-black',
    icon: '🐝',
    colors: ['#fef9c3', '#fef08a', '#fde047', '#facc15', '#eab308']
  },
  해양생물: {
    bg: 'bg-white',
    border: 'border-blue-200',
    button: 'bg-blue-100 hover:bg-blue-200',
    title: 'text-black',
    icon: '🐠',
    colors: ['#dbeafe', '#93c5fd', '#60a5fa', '#3b82f6', '#2563eb']
  }
};

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

let dynamicSpeciesCount = {};

export const updateSpeciesCount = (countData, category) => {
  if (!dynamicSpeciesCount[category]) {
    dynamicSpeciesCount[category] = {};
  }
  dynamicSpeciesCount[category] = { ...dynamicSpeciesCount[category], ...countData };
  debugLogCache = {};
};

export const resetSpeciesCount = (category) => {
  dynamicSpeciesCount[category] = {};
};

export const getSpeciesCount = (category) => {
  return dynamicSpeciesCount[category] || {};
};

let colorStatsCache = {};
let debugLogCache = {};

export const getColorIntensity = (category, countryCode) => {
  const colors = categoryThemes[category]?.colors || categoryThemes['동물'].colors;
  const NO_DATA = { color: null, hasData: false };
  const LOADING = { color: colors[2], hasData: true, loading: true };
  const dynamicData = dynamicSpeciesCount[category];
  const upperCode = countryCode?.toUpperCase();

  if (!dynamicData || Object.keys(dynamicData).length === 0) {
    return LOADING;
  }

  const count = dynamicData[upperCode] || dynamicData[countryCode];

  if (count === undefined || count === null) {
    return { color: colors[1], hasData: true, notInCache: true };
  }

  if (count === 0) {
    return NO_DATA;
  }

  const validCounts = Object.values(dynamicData).filter(c => c > 0);

  if (validCounts.length === 0) {
    return NO_DATA;
  }

  const sortedUniqueCounts = [...new Set(validCounts)].sort((a, b) => a - b);
  const totalUniqueValues = sortedUniqueCounts.length;
  const minCount = sortedUniqueCounts[0];
  const maxCount = sortedUniqueCounts[totalUniqueValues - 1];

  const cacheKey = `${category}_${totalUniqueValues}`;
  if (!colorStatsCache[cacheKey]) {
    colorStatsCache[cacheKey] = true;
  }

  if (minCount === maxCount) {
    return { color: colors[2], hasData: true };
  }

  let colorIndex;
  const logMin = Math.log(minCount + 1);
  const logMax = Math.log(maxCount + 1);
  const logValue = Math.log(count + 1);
  const normalizedValue = (logValue - logMin) / (logMax - logMin);

  if (normalizedValue < 0.2) {
    colorIndex = 0;
  } else if (normalizedValue < 0.4) {
    colorIndex = 1;
  } else if (normalizedValue < 0.6) {
    colorIndex = 2;
  } else if (normalizedValue < 0.8) {
    colorIndex = 3;
  } else {
    colorIndex = 4;
  }

  return { color: colors[colorIndex], hasData: true };
};

export const resetColorStats = () => {
  colorStatsCache = {};
  debugLogCache = {};
};
