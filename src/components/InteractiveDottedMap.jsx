import React, { useEffect, useRef, useState, useMemo } from 'react';
import * as d3 from 'd3';
import { getColorIntensity } from '../data/biodiversityData';

// GeoJSON 캐시 (앱 전역)
let cachedGeoJSON = null;
let geoJSONPromise = null;

// ISO Alpha-3 to Alpha-2 변환 맵 (전 세계 주요 국가)
const alpha3ToAlpha2 = {
  // 아시아
  'kor': 'kr', 'jpn': 'jp', 'chn': 'cn', 'prk': 'kp', 'twn': 'tw',
  'ind': 'in', 'pak': 'pk', 'bgd': 'bd', 'vnm': 'vn', 'phl': 'ph',
  'tha': 'th', 'mmr': 'mm', 'mys': 'my', 'idn': 'id', 'sgp': 'sg',
  'lka': 'lk', 'npl': 'np', 'afg': 'af', 'irn': 'ir', 'irq': 'iq',
  'sau': 'sa', 'yem': 'ye', 'syr': 'sy', 'jor': 'jo', 'lbn': 'lb',
  'isr': 'il', 'pse': 'ps', 'kwt': 'kw', 'omn': 'om', 'qat': 'qa',
  'bhr': 'bh', 'are': 'ae', 'khm': 'kh', 'lao': 'la', 'mng': 'mn',

  // 유럽
  'rus': 'ru', 'gbr': 'gb', 'deu': 'de', 'fra': 'fr', 'ita': 'it',
  'esp': 'es', 'pol': 'pl', 'rou': 'ro', 'nld': 'nl', 'bel': 'be',
  'grc': 'gr', 'cze': 'cz', 'prt': 'pt', 'swe': 'se', 'hun': 'hu',
  'aut': 'at', 'che': 'ch', 'bgr': 'bg', 'dnk': 'dk', 'fin': 'fi',
  'svk': 'sk', 'nor': 'no', 'irl': 'ie', 'hrv': 'hr', 'bih': 'ba',
  'srb': 'rs', 'alb': 'al', 'ltu': 'lt', 'lva': 'lv', 'est': 'ee',
  'svn': 'si', 'mkd': 'mk', 'blr': 'by', 'ukr': 'ua', 'mda': 'md',
  'tur': 'tr', 'geo': 'ge', 'arm': 'am', 'aze': 'az', 'isl': 'is',

  // 아메리카
  'usa': 'us', 'can': 'ca', 'mex': 'mx', 'bra': 'br', 'arg': 'ar',
  'col': 'co', 'per': 'pe', 'ven': 've', 'chl': 'cl', 'ecu': 'ec',
  'bol': 'bo', 'pry': 'py', 'ury': 'uy', 'guy': 'gy', 'sur': 'sr',
  'gtm': 'gt', 'hnd': 'hn', 'slv': 'sv', 'nic': 'ni', 'cri': 'cr',
  'pan': 'pa', 'cub': 'cu', 'dom': 'do', 'hti': 'ht', 'jam': 'jm',

  // 아프리카
  'zaf': 'za', 'nga': 'ng', 'egy': 'eg', 'eth': 'et', 'ken': 'ke',
  'tza': 'tz', 'uga': 'ug', 'dza': 'dz', 'sdn': 'sd', 'mar': 'ma',
  'ago': 'ao', 'moz': 'mz', 'gha': 'gh', 'mdg': 'mg', 'cmr': 'cm',
  'civ': 'ci', 'ner': 'ne', 'bfa': 'bf', 'mli': 'ml', 'mwi': 'mw',
  'zmb': 'zm', 'som': 'so', 'sen': 'sn', 'tcd': 'td', 'zwe': 'zw',
  'gin': 'gn', 'rwa': 'rw', 'ben': 'bj', 'tun': 'tn', 'ssd': 'ss',
  'lby': 'ly', 'cog': 'cg', 'cod': 'cd', 'lbr': 'lr', 'mrt': 'mr',

  // 오세아니아
  'aus': 'au', 'nzl': 'nz', 'png': 'pg', 'fji': 'fj', 'slb': 'sb',
  'vut': 'vu', 'wsm': 'ws', 'ton': 'to', 'plw': 'pw'
};

// 국기 이모지 변환 함수 (ISO Alpha-2 코드 -> 국기 이모지)
const getFlagEmoji = (countryCode) => {
  if (!countryCode) {
    return null; // null 반환으로 아이콘 표시하지 않음
  }

  let code = countryCode.toLowerCase().trim();

  // 빈 문자열이면 null 반환
  if (code === '') {
    return null;
  }

  // Alpha-3 코드를 Alpha-2로 변환
  if (code.length === 3 && alpha3ToAlpha2[code]) {
    code = alpha3ToAlpha2[code];
  }

  // 2자가 아니면 null 반환 (아이콘 표시 안 함)
  if (code.length !== 2) {
    return null;
  }

  // 알파벳만 허용, 그 외는 null 반환
  if (!/^[a-z]{2}$/.test(code)) {
    return null;
  }

  // ISO Alpha-2 코드를 유니코드 국기 이모지로 변환
  // 예: 'us' -> U+1F1FA U+1F1F8 -> 🇺🇸
  const upperCode = code.toUpperCase();
  const codePoints = upperCode
    .split('')
    .map(char => {
      const charCode = char.charCodeAt(0);
      // Regional Indicator Symbol Letter A = U+1F1E6 (127462)
      // A-Z (65-90)를 Regional Indicator Symbol (🇦-🇿)로 변환
      const regionIndicator = 127462 + (charCode - 65);
      return regionIndicator;
    });

  const flagEmoji = String.fromCodePoint(...codePoints);

  return flagEmoji;
};

// ISO Alpha-2 국가 코드 매핑 (전 세계 모든 국가)
const countryNameToISO = {
  // 주요 국가
  'South Korea': 'kr', 'Korea': 'kr', 'Japan': 'jp',
  'United States of America': 'us', 'United States': 'us',
  'China': 'cn', 'Russia': 'ru', 'Russian Federation': 'ru',
  'United Kingdom': 'gb', 'Germany': 'de', 'France': 'fr',
  'Italy': 'it', 'Spain': 'es', 'Canada': 'ca',
  'Brazil': 'br', 'India': 'in', 'Australia': 'au',
  'Mexico': 'mx', 'Indonesia': 'id', 'Netherlands': 'nl',
  'Saudi Arabia': 'sa', 'Turkey': 'tr', 'Switzerland': 'ch',
  'Poland': 'pl', 'Belgium': 'be', 'Sweden': 'se',
  'Austria': 'at', 'Portugal': 'pt', 'Greece': 'gr',
  'Czech Republic': 'cz', 'Czechia': 'cz', 'Romania': 'ro', 'Vietnam': 'vn',
  'Philippines': 'ph', 'Pakistan': 'pk', 'Bangladesh': 'bd',
  'Nigeria': 'ng', 'Egypt': 'eg', 'Iran': 'ir',
  'Thailand': 'th', 'South Africa': 'za', 'Colombia': 'co',
  'Argentina': 'ar', 'Ukraine': 'ua', 'Algeria': 'dz',
  'Iraq': 'iq', 'Morocco': 'ma', 'Peru': 'pe',
  'Malaysia': 'my', 'Angola': 'ao', 'Ghana': 'gh',
  'Yemen': 'ye', 'Nepal': 'np', 'Venezuela': 've',
  'Madagascar': 'mg', 'Cameroon': 'cm', 'North Korea': 'kp',
  'Taiwan': 'tw', 'Niger': 'ne', 'Sri Lanka': 'lk',
  'Burkina Faso': 'bf', 'Mali': 'ml', 'Chile': 'cl',
  'Malawi': 'mw', 'Zambia': 'zm', 'Ecuador': 'ec',
  'Guatemala': 'gt', 'Senegal': 'sn', 'Cambodia': 'kh',
  'Zimbabwe': 'zw', 'Guinea': 'gn', 'Rwanda': 'rw',
  'Benin': 'bj', 'Tunisia': 'tn', 'Bolivia': 'bo',
  'Haiti': 'ht', 'Cuba': 'cu', 'Dominican Republic': 'do', 'Dom. Rep.': 'do',
  'Jordan': 'jo', 'Azerbaijan': 'az', 'Hungary': 'hu',
  'Belarus': 'by', 'Tajikistan': 'tj', 'Papua New Guinea': 'pg',
  'Serbia': 'rs', 'Israel': 'il', 'Palestine': 'ps',
  'Hong Kong': 'hk', 'Laos': 'la', 'Paraguay': 'py',
  'El Salvador': 'sv', 'Sierra Leone': 'sl', 'Bulgaria': 'bg',
  'Libya': 'ly', 'Lebanon': 'lb', 'Nicaragua': 'ni',
  'Kyrgyzstan': 'kg', 'Turkmenistan': 'tm', 'Singapore': 'sg',
  'Slovakia': 'sk', 'Oman': 'om', 'Costa Rica': 'cr',
  'New Zealand': 'nz', 'Ireland': 'ie', 'Mauritania': 'mr',
  'Panama': 'pa', 'Kuwait': 'kw', 'Croatia': 'hr',
  'Georgia': 'ge', 'Eritrea': 'er', 'Uruguay': 'uy',
  'Mongolia': 'mn', 'Bosnia and Herzegovina': 'ba', 'Bosnia and Herz.': 'ba', 'Jamaica': 'jm',
  'Armenia': 'am', 'Qatar': 'qa', 'Albania': 'al',
  'Puerto Rico': 'pr', 'Lithuania': 'lt', 'Namibia': 'na',
  'Gambia': 'gm', 'Botswana': 'bw', 'Gabon': 'ga',
  'Lesotho': 'ls', 'North Macedonia': 'mk', 'Macedonia': 'mk', 'Slovenia': 'si',
  'Guinea-Bissau': 'gw', 'Latvia': 'lv', 'Bahrain': 'bh',
  'Equatorial Guinea': 'gq', 'Eq. Guinea': 'gq', 'Trinidad and Tobago': 'tt',
  'Estonia': 'ee', 'Mauritius': 'mu', 'Cyprus': 'cy',
  'Eswatini': 'sz', 'eSwatini': 'sz', 'Swaziland': 'sz', 'Djibouti': 'dj', 'Fiji': 'fj',
  'Reunion': 're', 'Réunion': 're', 'Comoros': 'km', 'Guyana': 'gy',
  'Bhutan': 'bt', 'Solomon Islands': 'sb', 'Macao': 'mo', 'Macau': 'mo',
  'Luxembourg': 'lu', 'Montenegro': 'me', 'Western Sahara': 'eh', 'W. Sahara': 'eh',
  'Suriname': 'sr', 'Cabo Verde': 'cv', 'Cape Verde': 'cv', 'Maldives': 'mv',
  'Malta': 'mt', 'Brunei': 'bn', 'Belize': 'bz',
  'Bahamas': 'bs', 'Iceland': 'is', 'Vanuatu': 'vu',
  'French Polynesia': 'pf', 'Fr. Polynesia': 'pf', 'Barbados': 'bb', 'New Caledonia': 'nc',
  'French Guiana': 'gf', 'Mayotte': 'yt', 'Samoa': 'ws',
  'Sao Tome and Principe': 'st', 'São Tomé and Principe': 'st', 'Dominica': 'dm',
  'Micronesia': 'fm', 'Tonga': 'to', 'Kiribati': 'ki',
  'Palau': 'pw', 'Cook Islands': 'ck', 'Nauru': 'nr',
  'Tuvalu': 'tv', 'Saint Lucia': 'lc', 'St. Lucia': 'lc',

  // 추가 국가 (자주 빠지는 것들)
  'Afghanistan': 'af', 'Uzbekistan': 'uz', 'Kazakhstan': 'kz',
  'Chad': 'td', 'Somalia': 'so', 'Myanmar': 'mm', 'Burma': 'mm',
  'Uganda': 'ug', 'Sudan': 'sd', 'South Sudan': 'ss', 'S. Sudan': 'ss',
  'Ethiopia': 'et', 'Kenya': 'ke', 'Tanzania': 'tz',
  'Mozambique': 'mz', 'Syria': 'sy', 'Liberia': 'lr',
  'Togo': 'tg', 'Central African Republic': 'cf', 'Central African Rep.': 'cf',
  'Mauritania': 'mr', 'Norway': 'no', 'Finland': 'fi',
  'Denmark': 'dk', 'Moldova': 'md', 'Kosovo': 'xk',
  'Timor-Leste': 'tl', 'East Timor': 'tl', 'Côte d\'Ivoire': 'ci', 'Ivory Coast': 'ci',
  'Burundi': 'bi', 'Dem. Rep. Congo': 'cd', 'Democratic Republic of the Congo': 'cd',
  'Congo': 'cg', 'Republic of the Congo': 'cg', 'Somaliland': 'so',
  'Falkland Islands': 'fk', 'Falkland Is.': 'fk', 'Greenland': 'gl',
  'Antarctica': 'aq', 'French Southern and Antarctic Lands': 'tf', 'Fr. S. Antarctic Lands': 'tf'
};

const InteractiveDottedMap = ({
  width = 800,
  height = 400,
  dotSpacing = 3,
  dotRadius = 1.5,
  dotColor = '#9CA3AF',        // 회색 계열 (gray-400)
  highlightColor = '#374151',   // 진한 회색 (gray-700)
  category = null,              // 카테고리 (동물, 식물, 곤충, 해양생물)
  filteredCountries = null,     // 필터링된 국가 목록 (null = 전체, array = 특정 국가들만)
  onCountryClick
}) => {
  const svgRef = useRef(null);
  const [hoveredCountry, setHoveredCountry] = useState(null);
  const [flagPosition, setFlagPosition] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [dots, setDots] = useState([]);
  const [projection, setProjection] = useState(null); // 좌표 변환용

  // 색상 ID 생성 함수 (소수 기반 분산)
  const idToColor = (id) => {
    const r = (id * 73) % 256;
    const g = (id * 151) % 256;
    const b = (id * 233) % 256;
    return `rgb(${r},${g},${b})`;
  };

  // 색상 -> ID 역변환 함수
  const colorToId = (r, g, b, colorMap) => {
    const colorKey = `${r},${g},${b}`;
    return colorMap.get(colorKey) || null;
  };

  // GeoJSON 데이터 로드 및 Canvas Pixel Sampling
  useEffect(() => {
    let isMounted = true;

    const loadAndProcessMap = async () => {
      try {
        setIsLoading(true);

        // GeoJSON 캐싱 처리
        let worldData;
        if (cachedGeoJSON) {
          worldData = cachedGeoJSON;
        } else {
          // 이미 로딩 중이면 기존 Promise 재사용
          if (!geoJSONPromise) {
            geoJSONPromise = fetch('https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson')
              .then(res => res.json());
          }
          worldData = await geoJSONPromise;
          cachedGeoJSON = worldData;
        }

        if (!isMounted) return;

        const geoProjection = d3.geoEquirectangular()
          .fitSize([width, height], { type: 'Sphere' });

        const path = d3.geoPath().projection(geoProjection);

        // projection을 state에 저장 (클릭 시 좌표 변환용)
        setProjection(() => geoProjection);

        // === Hidden Canvas 생성 ===
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const context = canvas.getContext('2d');
        context.imageSmoothingEnabled = false;

        const countryMap = new Map();
        const colorToIdMap = new Map();

        // 국가별 고유 색상으로 Canvas에 렌더링
        worldData.features.forEach((feature, index) => {
          const countryId = index + 1;
          const colorStr = idToColor(countryId);
          const countryName = feature.properties.name;

          // ISO 코드 결정: 매핑 우선, 없으면 feature.id 사용
          let isoCode = countryNameToISO[countryName] || feature.id?.toLowerCase() || '';

          // Alpha-3 코드를 Alpha-2로 자동 변환
          if (isoCode.length === 3 && alpha3ToAlpha2[isoCode]) {
            isoCode = alpha3ToAlpha2[isoCode];
          }

          const rgbMatch = colorStr.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
          if (rgbMatch) {
            const r = parseInt(rgbMatch[1]);
            const g = parseInt(rgbMatch[2]);
            const b = parseInt(rgbMatch[3]);
            const colorKey = `${r},${g},${b}`;
            colorToIdMap.set(colorKey, countryId);
          }

          countryMap.set(countryId, {
            name: countryName,
            code: isoCode,
            feature: feature,
            centroid: null
          });

          context.fillStyle = colorStr;
          context.strokeStyle = colorStr;
          context.lineWidth = 1.0;
          context.beginPath();
          path.context(context)(feature);
          context.fill();
          context.stroke();
        });

        // === Pixel Data 추출 ===
        const imageData = context.getImageData(0, 0, width, height);
        const pixels = imageData.data;

        // === 최적화된 5-point 샘플링 함수 ===
        const detectCountryAtPoint = (x, y) => {
          // 5-point sampling (중심 + 십자)
          const sampleOffsets = [
            [0, 0],                           // 중심
            [-1, 0], [1, 0], [0, -1], [0, 1]  // 십자
          ];

          const candidates = new Map();

          for (const [dx, dy] of sampleOffsets) {
            const sx = x + dx;
            const sy = y + dy;

            if (sx < 0 || sx >= width || sy < 0 || sy >= height) continue;

            const pixelIndex = (sy * width + sx) * 4;
            const r = pixels[pixelIndex];
            const g = pixels[pixelIndex + 1];
            const b = pixels[pixelIndex + 2];
            const a = pixels[pixelIndex + 3];

            if (a >= 200) {
              let countryId = colorToId(r, g, b, colorToIdMap);

              // 정확한 매칭 실패 시 근사 매칭
              if (countryId === null) {
                let minDistance = Infinity;
                let bestMatch = null;

                colorToIdMap.forEach((id, colorKey) => {
                  const [cr, cg, cb] = colorKey.split(',').map(Number);
                  const distance = Math.abs(r - cr) + Math.abs(g - cg) + Math.abs(b - cb);

                  if (distance <= 12 && distance < minDistance) {
                    minDistance = distance;
                    bestMatch = id;
                  }
                });

                countryId = bestMatch;
              }

              if (countryId !== null) {
                candidates.set(countryId, (candidates.get(countryId) || 0) + 1);
              }
            }
          }

          // 최다수 국가 반환
          if (candidates.size === 0) return null;

          let maxCount = 0;
          let selectedCountryId = null;
          candidates.forEach((count, id) => {
            if (count > maxCount) {
              maxCount = count;
              selectedCountryId = id;
            }
          });

          return selectedCountryId;
        };

        // === Dot Generation (9-point sampling only) ===
        const generatedDots = [];
        const countryDotGroups = new Map();

        for (let y = 0; y < height; y += dotSpacing) {
          for (let x = 0; x < width; x += dotSpacing) {
            const countryId = detectCountryAtPoint(x, y);

            if (countryId !== null) {
              const country = countryMap.get(countryId);

              if (country) {
                const dot = {
                  x,
                  y,
                  countryId,
                  countryName: country.name,
                  countryCode: country.code,
                  countryClass: country.name.replace(/[^a-zA-Z0-9]/g, '-').toLowerCase()
                };

                generatedDots.push(dot);

                if (!countryDotGroups.has(countryId)) {
                  countryDotGroups.set(countryId, []);
                }
                countryDotGroups.get(countryId).push(dot);
              }
            }
          }
        }

        // === Centroid 계산 ===
        countryDotGroups.forEach((dots, countryId) => {
          const country = countryMap.get(countryId);
          if (country && dots.length > 0) {
            const avgX = dots.reduce((sum, d) => sum + d.x, 0) / dots.length;
            const avgY = dots.reduce((sum, d) => sum + d.y, 0) / dots.length;
            country.centroid = [avgX, avgY];
          }
        });

        if (!isMounted) return;

        setDots(generatedDots);
        setIsLoading(false);
      } catch (error) {
        console.error('지도 로딩 실패:', error);
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadAndProcessMap();

    return () => {
      isMounted = false;
    };
  }, [width, height, dotSpacing]);

  if (isLoading || dots.length === 0) {
    return (
      <div style={{
        width,
        height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f5f5f5',
        borderRadius: '8px'
      }}>
        <div>지도 로딩 중...</div>
      </div>
    );
  }

  return (
    <div style={{ position: 'relative', width, height }}>
      <svg
        ref={svgRef}
        width={width}
        height={height}
        style={{ display: 'block', background: '#ffffff' }}
      >
        {dots.map((dot, i) => {
          // 카테고리별 색상 계산 (ISO Alpha-2 코드를 대문자로 변환)
          const countryCodeUpper = dot.countryCode?.toUpperCase();

          // 필터링 체크: filteredCountries가 있으면 해당 국가만 표시
          const isFiltered = filteredCountries !== null &&
            filteredCountries.length > 0 &&
            !filteredCountries.includes(countryCodeUpper);

          // 필터링된 국가는 회색으로 표시
          let baseDotColor;
          if (isFiltered) {
            baseDotColor = '#e5e7eb'; // 매우 연한 회색 (보이지만 강조되지 않음)
          } else {
            baseDotColor = category && countryCodeUpper
              ? getColorIntensity(category, countryCodeUpper)
              : dotColor;
          }

          return (
            <g key={i}>
              {/* 투명한 클릭 영역 (더 큰 반경) */}
              <circle
                cx={dot.x}
                cy={dot.y}
                r={dotRadius + 2}
                fill="transparent"
                style={{
                  cursor: isFiltered ? 'default' : 'pointer',
                  pointerEvents: 'all'
                }}
                onMouseEnter={() => {
                  if (!isFiltered) {
                    setHoveredCountry(dot.countryCode);
                    setFlagPosition({ x: dot.x, y: dot.y, code: dot.countryCode });
                  }
                }}
                onMouseLeave={() => {
                  setHoveredCountry(null);
                  setFlagPosition(null);
                }}
                onClick={() => {
                  if (!isFiltered && onCountryClick && projection) {
                    // SVG 좌표를 지리 좌표로 변환
                    const [lng, lat] = projection.invert([dot.x, dot.y]);
                    onCountryClick({
                      code: dot.countryCode,
                      name: dot.countryName,
                      lat: lat,
                      lng: lng
                    });
                  }
                }}
              />
              {/* 실제 보이는 도트 */}
              <circle
                cx={dot.x}
                cy={dot.y}
                r={dotRadius}
                fill={hoveredCountry === dot.countryCode ? highlightColor : baseDotColor}
                className={`dot-${dot.countryClass}`}
                style={{
                  opacity: isFiltered ? 0.3 : 1,
                  pointerEvents: 'none'
                }}
              />
            </g>
          );
        })}
      </svg>

      {flagPosition && (() => {
        const flagEmoji = getFlagEmoji(flagPosition.code);
        // flagEmoji가 null이면 아무것도 표시하지 않음
        if (!flagEmoji) return null;

        return (
          <div
            className="flag-emoji-container"
            style={{
              position: 'absolute',
              left: `${flagPosition.x + 15}px`,
              top: `${flagPosition.y - 32}px`,
              transform: 'translate(0, 0)',
              pointerEvents: 'none',
              zIndex: 1000,
              // 글래스모피즘 원형 배경 (더 투명하게)
              width: '64px',
              height: '64px',
              borderRadius: '50%',
              background: 'rgba(255, 255, 255, 0.12)',
              backdropFilter: 'blur(12px)',
              WebkitBackdropFilter: 'blur(12px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s ease',
              overflow: 'hidden'
            }}
          >
            <div
              style={{
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '40px',
                lineHeight: '1',
                userSelect: 'none',
                WebkitUserSelect: 'none',
                MozUserSelect: 'none',
                msUserSelect: 'none',
                WebkitTouchCallout: 'none',
                fontFamily: '"Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji", sans-serif'
              }}
            >
              {flagEmoji}
            </div>
          </div>
        );
      })()}
    </div>
  );
};

export default InteractiveDottedMap;
