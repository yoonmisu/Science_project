import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

// ISO Alpha-2 국가 코드 매핑 (200+ countries)
const countryNameToISO = {
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
  'Czech Republic': 'cz', 'Romania': 'ro', 'Vietnam': 'vn',
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
  'Haiti': 'ht', 'Cuba': 'cu', 'Dominican Republic': 'do',
  'Jordan': 'jo', 'Azerbaijan': 'az', 'Hungary': 'hu',
  'Belarus': 'by', 'Tajikistan': 'tj', 'Papua New Guinea': 'pg',
  'Serbia': 'rs', 'Israel': 'il',
  'Hong Kong': 'hk', 'Laos': 'la', 'Paraguay': 'py',
  'El Salvador': 'sv', 'Sierra Leone': 'sl', 'Bulgaria': 'bg',
  'Libya': 'ly', 'Lebanon': 'lb', 'Nicaragua': 'ni',
  'Kyrgyzstan': 'kg', 'Turkmenistan': 'tm', 'Singapore': 'sg',
  'Slovakia': 'sk', 'Oman': 'om', 'Costa Rica': 'cr',
  'New Zealand': 'nz', 'Ireland': 'ie', 'Mauritania': 'mr',
  'Panama': 'pa', 'Kuwait': 'kw', 'Croatia': 'hr',
  'Georgia': 'ge', 'Eritrea': 'er', 'Uruguay': 'uy',
  'Mongolia': 'mn', 'Bosnia and Herzegovina': 'ba', 'Jamaica': 'jm',
  'Armenia': 'am', 'Qatar': 'qa', 'Albania': 'al',
  'Puerto Rico': 'pr', 'Lithuania': 'lt', 'Namibia': 'na',
  'Gambia': 'gm', 'Botswana': 'bw', 'Gabon': 'ga',
  'Lesotho': 'ls', 'North Macedonia': 'mk', 'Slovenia': 'si',
  'Guinea-Bissau': 'gw', 'Latvia': 'lv', 'Bahrain': 'bh',
  'Equatorial Guinea': 'gq', 'Trinidad and Tobago': 'tt',
  'Estonia': 'ee', 'Mauritius': 'mu', 'Cyprus': 'cy',
  'Eswatini': 'sz', 'Djibouti': 'dj', 'Fiji': 'fj',
  'Reunion': 're', 'Comoros': 'km', 'Guyana': 'gy',
  'Bhutan': 'bt', 'Solomon Islands': 'sb', 'Macao': 'mo',
  'Luxembourg': 'lu', 'Montenegro': 'me', 'Western Sahara': 'eh',
  'Suriname': 'sr', 'Cabo Verde': 'cv', 'Maldives': 'mv',
  'Malta': 'mt', 'Brunei': 'bn', 'Belize': 'bz',
  'Bahamas': 'bs', 'Iceland': 'is', 'Vanuatu': 'vu',
  'French Polynesia': 'pf', 'Barbados': 'bb', 'New Caledonia': 'nc',
  'French Guiana': 'gf', 'Mayotte': 'yt', 'Samoa': 'ws',
  'Sao Tome and Principe': 'st', 'Dominica': 'dm',
  'Micronesia': 'fm', 'Tonga': 'to', 'Kiribati': 'ki',
  'Palau': 'pw', 'Cook Islands': 'ck', 'Nauru': 'nr',
  'Tuvalu': 'tv', 'Saint Lucia': 'lc'
};

const InteractiveDottedMap = ({
  width = 800,
  height = 400,
  dotSpacing = 3,
  dotRadius = 1.5,
  dotColor = '#6B8E6F',
  highlightColor = '#2D5A2F',
  onCountryClick
}) => {
  const svgRef = useRef(null);
  const [hoveredCountry, setHoveredCountry] = useState(null);
  const [flagPosition, setFlagPosition] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [dots, setDots] = useState([]);

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

        const response = await fetch('https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson');
        const worldData = await response.json();

        if (!isMounted) return;

        const projection = d3.geoEquirectangular()
          .fitSize([width, height], { type: 'Sphere' });

        const path = d3.geoPath().projection(projection);

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
          const isoCode = countryNameToISO[countryName] || feature.id?.toLowerCase() || '';

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

        // === 균형잡힌 9-point 다중 샘플링 함수 ===
        const detectCountryAtPoint = (x, y) => {
          // 9-point sampling (십자 + 대각선)
          const sampleOffsets = [
            [0, 0],                           // 중심
            [-1, 0], [1, 0], [0, -1], [0, 1], // 십자
            [-1, -1], [1, -1], [-1, 1], [1, 1] // 대각선
          ];

          const candidates = new Map();
          let validSamples = 0;

          for (const [dx, dy] of sampleOffsets) {
            const sx = x + dx;
            const sy = y + dy;

            if (sx < 0 || sx >= width || sy < 0 || sy >= height) continue;

            const pixelIndex = (sy * width + sx) * 4;
            const r = pixels[pixelIndex];
            const g = pixels[pixelIndex + 1];
            const b = pixels[pixelIndex + 2];
            const a = pixels[pixelIndex + 3];

            // 알파값 균형잡힌 임계값 (완화)
            if (a >= 200) {
              let countryId = colorToId(r, g, b, colorToIdMap);

              // 정확한 매칭 실패 시 근사 매칭
              if (countryId === null) {
                let minDistance = Infinity;
                let bestMatch = null;

                colorToIdMap.forEach((id, colorKey) => {
                  const [cr, cg, cb] = colorKey.split(',').map(Number);
                  const distance = Math.abs(r - cr) + Math.abs(g - cg) + Math.abs(b - cb);

                  // 균형잡힌 허용 오차
                  if (distance <= 12 && distance < minDistance) {
                    minDistance = distance;
                    bestMatch = id;
                  }
                });

                countryId = bestMatch;
              }

              if (countryId !== null) {
                candidates.set(countryId, (candidates.get(countryId) || 0) + 1);
                validSamples++;
              }
            }
          }

          // 최소 2개 이상의 유효한 샘플 (완화)
          if (validSamples < 2) {
            return null;
          }

          // 다수결: 단순 최다수 (완화)
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

        console.log(`✅ ${generatedDots.length}개 도트 생성 완료`);

        setDots(generatedDots);
        setIsLoading(false);
      } catch (error) {
        console.error('❌ 지도 로딩 실패:', error);
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
        style={{ display: 'block', background: '#f9f9f9' }}
      >
        {dots.map((dot, i) => (
          <circle
            key={i}
            cx={dot.x}
            cy={dot.y}
            r={dotRadius}
            fill={hoveredCountry === dot.countryCode ? highlightColor : dotColor}
            className={`dot-${dot.countryClass}`}
            style={{ cursor: 'pointer' }}
            onMouseEnter={() => {
              setHoveredCountry(dot.countryCode);
              setFlagPosition({ x: dot.x, y: dot.y, code: dot.countryCode });
            }}
            onMouseLeave={() => {
              setHoveredCountry(null);
              setFlagPosition(null);
            }}
            onClick={() => {
              if (onCountryClick) {
                onCountryClick({ code: dot.countryCode, name: dot.countryName });
              }
            }}
          />
        ))}
      </svg>

      {flagPosition && (
        <div
          style={{
            position: 'absolute',
            left: flagPosition.x + 15,
            top: flagPosition.y - 40,
            pointerEvents: 'none',
            background: 'white',
            border: '2px solid #ddd',
            borderRadius: '4px',
            padding: '4px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            zIndex: 1000
          }}
        >
          <img
            src={`https://flagcdn.com/32x24/${flagPosition.code}.png`}
            alt={flagPosition.code}
            style={{ display: 'block' }}
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        </div>
      )}
    </div>
  );
};

export default InteractiveDottedMap;
