# Verde 백엔드 - 프론트엔드 연동 가이드

## 🚀 빠른 시작

### 1. API 베이스 URL

```javascript
// config.js 또는 .env
const API_CONFIG = {
  development: 'http://localhost:8000/api/v1',
  production: 'https://api.verde.com/api/v1',
  websocket: {
    development: 'ws://localhost:8000/ws',
    production: 'wss://api.verde.com/ws'
  }
};

export const API_BASE_URL = API_CONFIG[process.env.NODE_ENV] || API_CONFIG.development;
export const WS_URL = API_CONFIG.websocket[process.env.NODE_ENV] || API_CONFIG.websocket.development;
```

### 2. API 클라이언트 유틸리티

```javascript
// utils/api.js
class VerdeAPIClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error?.message || '요청 실패');
      }

      return {
        data: data.data,
        metadata: data.metadata,
        headers: response.headers
      };
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  }

  // GET 요청
  get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;
    return this.request(url, { method: 'GET' });
  }

  // POST 요청
  post(endpoint, body) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  // PUT 요청
  put(endpoint, body) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  // DELETE 요청
  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

// 싱글톤 인스턴스
export const api = new VerdeAPIClient(API_BASE_URL);
```

## 📱 React 컴포넌트 예제

### 1. 앱 초기화 및 전역 데이터 로드

```jsx
// App.jsx
import { useEffect, useState } from 'react';
import { api } from './utils/api';

function App() {
  const [appData, setAppData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // 앱 초기 데이터 로드
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const response = await api.get('/frontend/init/app-data');
      setAppData(response.data);
    } catch (err) {
      setError(err.message);
      console.error('Failed to load initial data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <Spinner />
        <p>Verde를 불러오는 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-screen">
        <h2>⚠️ 데이터를 불러올 수 없습니다</h2>
        <p>{error}</p>
        <button onClick={loadInitialData}>다시 시도</button>
      </div>
    );
  }

  return (
    <div className="app">
      <Header />
      <FeaturedToday species={appData.featured_today} />
      <TrendingSearches searches={appData.trending_searches} />
      <Statistics stats={appData.statistics} />
      <InteractiveMap legend={appData.heatmap_legend} />
      <Footer />
    </div>
  );
}

export default App;
```

### 2. 오늘의 추천 생물종

```jsx
// components/FeaturedToday.jsx
import { motion } from 'framer-motion';
import { useState } from 'react';
import SpeciesModal from './SpeciesModal';

function FeaturedToday({ species }) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  if (!species) return null;

  return (
    <motion.section
      className="featured-today"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="container">
        <h2>🌟 오늘의 생물</h2>

        <div className="featured-card" onClick={() => setIsModalOpen(true)}>
          <div className="featured-image">
            <img
              src={species.image_url}
              alt={species.name}
              loading="lazy"
            />
            {species.conservation_status && (
              <span className={`badge badge-${species.conservation_status}`}>
                {species.conservation_status}
              </span>
            )}
          </div>

          <div className="featured-content">
            <h3>{species.name}</h3>
            <p className="scientific-name">{species.scientific_name}</p>
            <p className="description">{species.description}</p>

            <div className="meta">
              <span className="category">{species.category}</span>
              <span className="region">{species.region}</span>
            </div>
          </div>
        </div>
      </div>

      <SpeciesModal
        speciesId={species.id}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </motion.section>
  );
}

export default FeaturedToday;
```

### 3. 실시간 인기 검색어

```jsx
// components/TrendingSearches.jsx
import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useVerdeWebSocket } from '../hooks/useVerdeWebSocket';

function TrendingSearches({ initialSearches }) {
  const [trending, setTrending] = useState(initialSearches);

  // WebSocket으로 실시간 업데이트
  const { message } = useVerdeWebSocket(['trending']);

  useEffect(() => {
    if (message?.type === 'trending_update') {
      setTrending(message.data);
    }
  }, [message]);

  const handleSearchClick = (query) => {
    // 검색 페이지로 이동
    window.location.href = `/search?q=${encodeURIComponent(query)}`;
  };

  return (
    <section className="trending-searches">
      <div className="container">
        <div className="section-header">
          <h2>🔥 실시간 인기 검색어</h2>
          <span className="live-badge">LIVE</span>
        </div>

        <AnimatePresence>
          <div className="trending-list">
            {trending.map((item, index) => (
              <motion.div
                key={item.query}
                className="trending-item"
                onClick={() => handleSearchClick(item.query)}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ delay: index * 0.05 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <span className={`rank rank-${index + 1}`}>{index + 1}</span>
                <span className="query">{item.query}</span>
                <span className="score">{Math.round(item.score)}</span>
              </motion.div>
            ))}
          </div>
        </AnimatePresence>
      </div>
    </section>
  );
}

export default TrendingSearches;
```

### 4. 검색 바 및 자동완성

```jsx
// components/SearchBar.jsx
import { useState, useEffect, useRef } from 'react';
import { debounce } from 'lodash';
import { api } from '../utils/api';
import { motion, AnimatePresence } from 'framer-motion';

function SearchBar({ onSearch }) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);

  // 디바운스된 검색 함수
  const fetchSuggestions = useRef(
    debounce(async (q) => {
      if (q.length < 1) {
        setSuggestions([]);
        return;
      }

      setLoading(true);
      try {
        const response = await api.get('/frontend/search/autocomplete', {
          q: q,
          limit: 10
        });
        setSuggestions(response.data.suggestions);
        setShowSuggestions(true);
      } catch (error) {
        console.error('Autocomplete error:', error);
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 300)
  ).current;

  useEffect(() => {
    fetchSuggestions(query);
  }, [query]);

  // 외부 클릭 감지
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target) &&
        !inputRef.current.contains(event.target)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 키보드 네비게이션
  const handleKeyDown = (e) => {
    if (!showSuggestions || suggestions.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev =>
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;

      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;

      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0) {
          handleSuggestionClick(suggestions[selectedIndex]);
        } else {
          handleSearch();
        }
        break;

      case 'Escape':
        setShowSuggestions(false);
        setSelectedIndex(-1);
        break;
    }
  };

  const handleSearch = () => {
    if (query.trim()) {
      onSearch(query);
      setShowSuggestions(false);
      inputRef.current?.blur();
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion.name);
    setShowSuggestions(false);
    onSearch(suggestion.name);
  };

  const highlightMatch = (text, query) => {
    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, i) =>
      part.toLowerCase() === query.toLowerCase() ? (
        <mark key={i}>{part}</mark>
      ) : (
        part
      )
    );
  };

  return (
    <div className="search-bar-container">
      <div className="search-bar">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => query && setShowSuggestions(true)}
          placeholder="생물종 검색 (예: 호랑이, 판다, 벚나무)"
          className="search-input"
        />

        <button
          className="search-button"
          onClick={handleSearch}
          disabled={!query.trim()}
        >
          🔍 검색
        </button>

        {loading && (
          <div className="search-loading">
            <Spinner size="small" />
          </div>
        )}
      </div>

      <AnimatePresence>
        {showSuggestions && suggestions.length > 0 && (
          <motion.div
            ref={suggestionsRef}
            className="suggestions-dropdown"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {suggestions.map((suggestion, index) => (
              <div
                key={suggestion.id}
                className={`suggestion-item ${selectedIndex === index ? 'selected' : ''}`}
                onClick={() => handleSuggestionClick(suggestion)}
                onMouseEnter={() => setSelectedIndex(index)}
              >
                {suggestion.thumbnail && (
                  <img
                    src={suggestion.thumbnail}
                    alt={suggestion.name}
                    className="suggestion-thumbnail"
                    loading="lazy"
                  />
                )}

                <div className="suggestion-content">
                  <div className="suggestion-name">
                    {highlightMatch(suggestion.name, query)}
                  </div>
                  <div className="suggestion-scientific-name">
                    {suggestion.scientific_name}
                  </div>
                </div>

                <div className="suggestion-meta">
                  <span className={`badge badge-${suggestion.category}`}>
                    {suggestion.category}
                  </span>
                  {suggestion.conservation_status && (
                    <span className={`badge badge-${suggestion.conservation_status}`}>
                      {suggestion.conservation_status}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default SearchBar;
```

### 5. 지도 컴포넌트 (Leaflet)

```jsx
// components/InteractiveMap.jsx
import { useEffect, useState, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { api } from '../utils/api';

function InteractiveMap({ legend: legendData }) {
  const [heatmapData, setHeatmapData] = useState(null);
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [loading, setLoading] = useState(true);
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);

  useEffect(() => {
    loadMapData();
  }, []);

  useEffect(() => {
    if (heatmapData && !mapInstanceRef.current) {
      initializeMap();
    }
  }, [heatmapData]);

  const loadMapData = async () => {
    try {
      const response = await api.get('/frontend/map/countries/simple');
      setHeatmapData(response.data);
    } catch (error) {
      console.error('Failed to load map data:', error);
    } finally {
      setLoading(false);
    }
  };

  const initializeMap = () => {
    // 지도 초기화
    const map = L.map(mapRef.current).setView([37.5665, 126.9780], 4);

    // 타일 레이어
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18,
    }).addTo(map);

    // GeoJSON 로드 및 히트맵 적용
    fetch('/data/countries.geojson')  // 별도로 GeoJSON 파일 준비 필요
      .then(res => res.json())
      .then(geojson => {
        L.geoJSON(geojson, {
          style: (feature) => {
            const countryCode = feature.properties.iso_a2;
            const countryData = heatmapData.countries.find(
              c => c.code === countryCode
            );

            return {
              fillColor: countryData?.color || '#E8F5E9',
              fillOpacity: countryData?.intensity || 0.3,
              weight: 1,
              color: '#2E7D32',
              dashArray: '3',
            };
          },
          onEachFeature: (feature, layer) => {
            const countryCode = feature.properties.iso_a2;
            const countryData = heatmapData.countries.find(
              c => c.code === countryCode
            );

            if (countryData) {
              // 툴팁
              layer.bindTooltip(`
                <strong>${countryData.name}</strong><br/>
                멸종위기종: ${countryData.count}종<br/>
                위험도: ${countryData.label}
              `, {
                permanent: false,
                direction: 'auto'
              });

              // 클릭 이벤트
              layer.on('click', () => {
                setSelectedCountry(countryData);
                map.fitBounds(layer.getBounds());
              });

              // 호버 효과
              layer.on('mouseover', () => {
                layer.setStyle({
                  weight: 3,
                  dashArray: '',
                  fillOpacity: 0.7
                });
              });

              layer.on('mouseout', () => {
                layer.setStyle({
                  weight: 1,
                  dashArray: '3',
                  fillOpacity: countryData.intensity
                });
              });
            }
          }
        }).addTo(map);
      });

    // 범례 추가
    const legend = L.control({ position: 'bottomright' });
    legend.onAdd = function() {
      const div = L.DomUtil.create('div', 'map-legend');
      div.innerHTML = `
        <h4>멸종위기종 분포</h4>
        ${legendData.levels.map(level => `
          <div class="legend-item">
            <span
              class="legend-color"
              style="background: ${level.color}"
            ></span>
            <span class="legend-label">
              ${level.label} (${level.min}-${level.max}종)
            </span>
          </div>
        `).join('')}
        <div class="legend-footer">
          ${legendData.description}
        </div>
      `;
      return div;
    };
    legend.addTo(map);

    mapInstanceRef.current = map;
  };

  if (loading) {
    return (
      <div className="map-loading">
        <Spinner />
        <p>지도를 불러오는 중...</p>
      </div>
    );
  }

  return (
    <section className="interactive-map-section">
      <div className="container">
        <h2>🗺️ 전 세계 멸종위기종 분포</h2>

        <div className="map-container">
          <div
            ref={mapRef}
            className="map"
            style={{ height: '600px', width: '100%' }}
          />
        </div>

        {selectedCountry && (
          <div className="country-detail-panel">
            <button
              className="close-btn"
              onClick={() => setSelectedCountry(null)}
            >
              ✕
            </button>

            <h3>{selectedCountry.name}</h3>
            <div className="country-stats">
              <div className="stat">
                <span className="stat-label">멸종위기종</span>
                <span className="stat-value">{selectedCountry.count}종</span>
              </div>
              <div className="stat">
                <span className="stat-label">위험도</span>
                <span className={`stat-value badge-${selectedCountry.label}`}>
                  {selectedCountry.label}
                </span>
              </div>
            </div>

            <button
              className="btn-primary"
              onClick={() => {
                window.location.href = `/regions/${selectedCountry.code}`;
              }}
            >
              상세 정보 보기 →
            </button>
          </div>
        )}
      </div>
    </section>
  );
}

export default InteractiveMap;
```

### 6. 무한 스크롤 생물종 목록

```jsx
// components/SpeciesList.jsx
import { useState, useEffect } from 'react';
import InfiniteScroll from 'react-infinite-scroll-component';
import { api } from '../utils/api';
import SpeciesCard from './SpeciesCard';

function SpeciesList({ category, conservationStatus }) {
  const [species, setSpecies] = useState([]);
  const [cursor, setCursor] = useState(null);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // 필터 변경 시 리셋
    setSpecies([]);
    setCursor(null);
    setHasMore(true);
    loadMore(true);
  }, [category, conservationStatus]);

  const loadMore = async (reset = false) => {
    if (loading) return;

    setLoading(true);
    setError(null);

    try {
      const params = {
        limit: 20,
        ...(cursor && !reset ? { cursor } : {}),
        ...(category ? { category } : {}),
        ...(conservationStatus ? { status: conservationStatus } : {})
      };

      const response = await api.get('/frontend/species/infinite', params);

      if (reset) {
        setSpecies(response.data.items);
      } else {
        setSpecies(prev => [...prev, ...response.data.items]);
      }

      setCursor(response.data.next_cursor);
      setHasMore(response.data.has_next);
    } catch (err) {
      setError(err.message);
      console.error('Failed to load species:', err);
    } finally {
      setLoading(false);
    }
  };

  if (error && species.length === 0) {
    return (
      <div className="error-message">
        <p>⚠️ {error}</p>
        <button onClick={() => loadMore(true)}>다시 시도</button>
      </div>
    );
  }

  return (
    <div className="species-list-container">
      <InfiniteScroll
        dataLength={species.length}
        next={loadMore}
        hasMore={hasMore}
        loader={
          <div className="loading-more">
            <Spinner />
            <p>더 불러오는 중...</p>
          </div>
        }
        endMessage={
          <div className="end-message">
            <p>✅ 모든 생물종을 불러왔습니다</p>
            <p className="count">총 {species.length}종</p>
          </div>
        }
      >
        <div className="species-grid">
          {species.map((s, index) => (
            <SpeciesCard
              key={s.id}
              species={s}
              index={index}
            />
          ))}
        </div>
      </InfiniteScroll>
    </div>
  );
}

export default SpeciesList;
```

### 7. 생물종 카드

```jsx
// components/SpeciesCard.jsx
import { motion } from 'framer-motion';
import { useState } from 'react';
import SpeciesModal from './SpeciesModal';

function SpeciesCard({ species, index }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);

  const getCategoryIcon = (category) => {
    const icons = {
      '동물': '🦁',
      '식물': '🌿',
      '곤충': '🦋',
      '해양생물': '🐠'
    };
    return icons[category] || '🌱';
  };

  const getStatusColor = (status) => {
    const colors = {
      '멸종위기': '#D32F2F',
      '취약': '#F57C00',
      '준위협': '#FBC02D',
      '관심대상': '#388E3C',
      '안전': '#1976D2'
    };
    return colors[status] || '#757575';
  };

  return (
    <>
      <motion.div
        className="species-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: index * 0.05 }}
        whileHover={{ y: -8, boxShadow: '0 12px 24px rgba(0,0,0,0.15)' }}
        onClick={() => setIsModalOpen(true)}
      >
        <div className="card-image">
          {!imageLoaded && (
            <div className="image-skeleton">
              <Spinner size="small" />
            </div>
          )}
          <img
            src={species.image_url || '/placeholder-species.jpg'}
            alt={species.name}
            loading="lazy"
            onLoad={() => setImageLoaded(true)}
            style={{ display: imageLoaded ? 'block' : 'none' }}
          />

          {species.conservation_status && (
            <span
              className="status-badge"
              style={{ backgroundColor: getStatusColor(species.conservation_status) }}
            >
              {species.conservation_status}
            </span>
          )}
        </div>

        <div className="card-content">
          <div className="card-header">
            <span className="category-icon">
              {getCategoryIcon(species.category)}
            </span>
            <h3 className="species-name">{species.name}</h3>
          </div>

          <p className="scientific-name">{species.scientific_name}</p>

          {species.description && (
            <p className="description">
              {species.description.length > 100
                ? `${species.description.slice(0, 100)}...`
                : species.description}
            </p>
          )}

          <div className="card-footer">
            <span className="region">📍 {species.region}</span>
            {species.search_count > 0 && (
              <span className="search-count">
                🔍 {species.search_count.toLocaleString()}
              </span>
            )}
          </div>
        </div>
      </motion.div>

      <SpeciesModal
        speciesId={species.id}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );
}

export default SpeciesCard;
```

### 8. 생물종 상세 모달

```jsx
// components/SpeciesModal.jsx
import { useState, useEffect } from 'react';
import Modal from 'react-modal';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../utils/api';

Modal.setAppElement('#root');

function SpeciesModal({ speciesId, isOpen, onClose }) {
  const [species, setSpecies] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (isOpen && speciesId) {
      fetchSpeciesDetails();
    }

    return () => {
      setSpecies(null);
      setActiveTab('overview');
    };
  }, [isOpen, speciesId]);

  const fetchSpeciesDetails = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.get(`/species/${speciesId}`);
      setSpecies(response.data);
    } catch (err) {
      setError(err.message);
      console.error('Failed to load species details:', err);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'overview', label: '📝 개요', icon: '📝' },
    { id: 'characteristics', label: '✨ 특징', icon: '✨' },
    { id: 'habitat', label: '🏠 서식지', icon: '🏠' },
    { id: 'conservation', label: '🛡️ 보전', icon: '🛡️' },
  ];

  const renderContent = () => {
    if (!species) return null;

    switch (activeTab) {
      case 'overview':
        return (
          <motion.div
            key="overview"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="modal-content-section"
          >
            <h2>{species.name}</h2>
            <p className="scientific-name">{species.scientific_name}</p>

            {species.description && (
              <div className="description-block">
                <p>{species.description}</p>
              </div>
            )}

            <div className="quick-facts">
              <div className="fact">
                <span className="fact-label">카테고리</span>
                <span className="fact-value">{species.category}</span>
              </div>
              <div className="fact">
                <span className="fact-label">지역</span>
                <span className="fact-value">{species.region}</span>
              </div>
              <div className="fact">
                <span className="fact-label">국가</span>
                <span className="fact-value">{species.country}</span>
              </div>
              {species.conservation_status && (
                <div className="fact">
                  <span className="fact-label">보전 상태</span>
                  <span className={`fact-value badge-${species.conservation_status}`}>
                    {species.conservation_status}
                  </span>
                </div>
              )}
            </div>
          </motion.div>
        );

      case 'characteristics':
        return (
          <motion.div
            key="characteristics"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="modal-content-section"
          >
            <h3>주요 특징</h3>
            {species.characteristics ? (
              <div className="characteristics-grid">
                {Object.entries(species.characteristics).map(([key, value]) => (
                  <div key={key} className="characteristic-item">
                    <strong>{key}:</strong> {value}
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-data">특징 정보가 없습니다</p>
            )}
          </motion.div>
        );

      case 'habitat':
        return (
          <motion.div
            key="habitat"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="modal-content-section"
          >
            <h3>서식지 정보</h3>
            <p>지역: {species.region}</p>
            <p>국가: {species.country}</p>
          </motion.div>
        );

      case 'conservation':
        return (
          <motion.div
            key="conservation"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="modal-content-section"
          >
            <h3>보전 상태</h3>
            {species.conservation_status ? (
              <div className="conservation-info">
                <div className={`status-badge-large badge-${species.conservation_status}`}>
                  {species.conservation_status}
                </div>
                <p className="conservation-description">
                  {getConservationDescription(species.conservation_status)}
                </p>
              </div>
            ) : (
              <p className="no-data">보전 상태 정보가 없습니다</p>
            )}
          </motion.div>
        );

      default:
        return null;
    }
  };

  const getConservationDescription = (status) => {
    const descriptions = {
      '멸종위기': '매우 높은 수준의 보호가 필요한 상태입니다.',
      '취약': '보호 조치가 필요한 취약한 상태입니다.',
      '준위협': '주의가 필요한 상태입니다.',
      '관심대상': '현재는 안정적이나 지속적인 관찰이 필요합니다.',
      '안전': '안정적인 개체수를 유지하고 있습니다.'
    };
    return descriptions[status] || '';
  };

  return (
    <Modal
      isOpen={isOpen}
      onRequestClose={onClose}
      className="species-modal"
      overlayClassName="species-modal-overlay"
      closeTimeoutMS={200}
    >
      <div className="modal-container">
        <button className="modal-close-btn" onClick={onClose}>
          ✕
        </button>

        {loading ? (
          <div className="modal-loading">
            <Spinner />
            <p>생물종 정보를 불러오는 중...</p>
          </div>
        ) : error ? (
          <div className="modal-error">
            <p>⚠️ {error}</p>
            <button onClick={fetchSpeciesDetails}>다시 시도</button>
          </div>
        ) : species ? (
          <>
            <div className="modal-header">
              {species.image_url && (
                <div className="modal-image">
                  <img src={species.image_url} alt={species.name} />
                </div>
              )}
            </div>

            <div className="modal-tabs">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  <span className="tab-icon">{tab.icon}</span>
                  <span className="tab-label">{tab.label}</span>
                </button>
              ))}
            </div>

            <div className="modal-body">
              <AnimatePresence mode="wait">
                {renderContent()}
              </AnimatePresence>
            </div>

            <div className="modal-footer">
              <div className="stats">
                <span>👁️ {species.search_count?.toLocaleString() || 0} 조회</span>
              </div>
              <button className="btn-primary" onClick={onClose}>
                닫기
              </button>
            </div>
          </>
        ) : null}
      </div>
    </Modal>
  );
}

export default SpeciesModal;
```

## 🔌 Custom Hooks

### 1. WebSocket Hook

```javascript
// hooks/useVerdeWebSocket.js
import { useState, useEffect, useCallback, useRef } from 'react';
import { WS_URL } from '../config';

export function useVerdeWebSocket(channels = []) {
  const [isConnected, setIsConnected] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        setError(null);

        // 채널 구독
        if (channels.length > 0) {
          ws.send(JSON.stringify({
            action: 'subscribe',
            channels: channels
          }));
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setMessage(data);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setError('WebSocket 연결 오류');
      };

      ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        setIsConnected(false);

        // 자동 재연결 (5초 후)
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('🔄 Reconnecting...');
          connect();
        }, 5000);
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError(err.message);
    }
  }, [channels]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const subscribe = useCallback((newChannels) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'subscribe',
        channels: newChannels
      }));
    }
  }, []);

  const unsubscribe = useCallback((channelsToRemove) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'unsubscribe',
        channels: channelsToRemove
      }));
    }
  }, []);

  const ping = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'ping' }));
    }
  }, []);

  return {
    isConnected,
    message,
    error,
    subscribe,
    unsubscribe,
    ping
  };
}
```

### 2. API Hook

```javascript
// hooks/useAPI.js
import { useState, useEffect } from 'react';
import { api } from '../utils/api';

export function useAPI(endpoint, params = {}, options = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const { skip = false, refetchOnMount = true } = options;

  const fetch = async () => {
    if (skip) return;

    setLoading(true);
    setError(null);

    try {
      const response = await api.get(endpoint, params);
      setData(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (refetchOnMount) {
      fetch();
    }
  }, [endpoint, JSON.stringify(params)]);

  const refetch = () => fetch();

  return { data, loading, error, refetch };
}
```

## 📱 스타일링 예제

### Verde 테마 CSS

```css
/* styles/theme.css */

/* Verde 브랜드 색상 */
:root {
  /* 녹색 팔레트 */
  --verde-very-light: #E8F5E9;
  --verde-light: #81C784;
  --verde-medium: #4CAF50;
  --verde-dark: #2E7D32;

  /* 텍스트 */
  --text-primary: #212121;
  --text-secondary: #757575;
  --text-disabled: #BDBDBD;

  /* 배경 */
  --background-primary: #FFFFFF;
  --background-secondary: #F5F5F5;
  --background-tertiary: #EEEEEE;

  /* 보전 상태 색상 */
  --status-critical: #D32F2F;
  --status-endangered: #F57C00;
  --status-vulnerable: #FBC02D;
  --status-concern: #388E3C;
  --status-safe: #1976D2;

  /* 그림자 */
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.12);
  --shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.15);

  /* 반경 */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;

  /* 간격 */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
}

/* 기본 리셋 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: var(--text-primary);
  background-color: var(--background-secondary);
  line-height: 1.6;
}

/* 컨테이너 */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-md);
}

/* 버튼 */
.btn-primary {
  background-color: var(--verde-medium);
  color: white;
  border: none;
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-md);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  background-color: var(--verde-dark);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.btn-primary:active {
  transform: translateY(0);
}

/* 배지 */
.badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.badge-멸종위기 {
  background-color: var(--status-critical);
  color: white;
}

.badge-취약 {
  background-color: var(--status-endangered);
  color: white;
}

.badge-준위협 {
  background-color: var(--status-vulnerable);
  color: #333;
}

.badge-관심대상 {
  background-color: var(--status-concern);
  color: white;
}

.badge-안전 {
  background-color: var(--status-safe);
  color: white;
}

/* 카드 */
.card {
  background: var(--background-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: all 0.3s;
}

.card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-4px);
}

/* 히트맵 색상 */
.heatmap-very-light {
  background-color: var(--verde-very-light);
  color: var(--text-primary);
}

.heatmap-light {
  background-color: var(--verde-light);
  color: white;
}

.heatmap-medium {
  background-color: var(--verde-medium);
  color: white;
}

.heatmap-dark {
  background-color: var(--verde-dark);
  color: white;
}

/* 스피너 */
@keyframes spin {
  to { transform: rotate(360deg); }
}

.spinner {
  border: 3px solid var(--background-tertiary);
  border-top-color: var(--verde-medium);
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 0.8s linear infinite;
}

.spinner.small {
  width: 20px;
  height: 20px;
  border-width: 2px;
}

/* 반응형 */
@media (max-width: 768px) {
  .container {
    padding: 0 var(--spacing-sm);
  }

  .species-grid {
    grid-template-columns: 1fr;
  }
}
```

## 🚀 배포 가이드

### 환경 변수 설정

```bash
# .env.production
VITE_API_URL=https://api.verde.com/api/v1
VITE_WS_URL=wss://api.verde.com/ws
```

### Vercel 배포

```json
// vercel.json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

### Netlify 배포

```toml
# netlify.toml
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

## 📚 추가 리소스

- **API 문서:** http://localhost:8000/docs
- **WebSocket 테스트:** http://localhost:8000/ws/stats
- **헬스 체크:** http://localhost:8000/health
- **백엔드 가이드:** `FRONTEND_API_GUIDE.md`
