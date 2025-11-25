# Verde 프론트엔드 API 가이드

## 🚀 개선 완료 사항

### 1. ✅ CORS 설정 최적화

**위치:** `app/main.py`

```python
# 프론트엔드에서 필요한 커스텀 헤더 노출
expose_headers=[
    "X-Total-Count",      # 전체 아이템 수
    "X-Page",             # 현재 페이지
    "X-Per-Page",         # 페이지당 아이템 수
    "X-Total-Pages",      # 전체 페이지 수
    "X-Has-Next",         # 다음 페이지 존재 여부
    "X-Has-Prev",         # 이전 페이지 존재 여부
    "X-Cursor",           # 무한 스크롤용 커서
]
```

### 2. ✅ 자동 페이지네이션 헤더

모든 페이지네이션 API가 자동으로 헤더에 메타데이터를 포함합니다:

```javascript
// 프론트엔드에서 헤더 읽기
fetch('/api/v1/species?page=1&limit=20')
  .then(response => {
    const totalCount = response.headers.get('X-Total-Count');
    const totalPages = response.headers.get('X-Total-Pages');
    const hasNext = response.headers.get('X-Has-Next');

    console.log(`총 ${totalCount}개 중 ${totalPages}페이지`);
    return response.json();
  });
```

### 3. ✅ 프론트엔드 친화적 엔드포인트

**새 라우터:** `app/routers/frontend.py`

#### 📦 초기 로드용 통합 데이터

**GET /api/v1/frontend/init/app-data**

한 번의 요청으로 모든 초기 데이터를 가져옵니다:

```javascript
// React 사용 예시
useEffect(() => {
  fetch('/api/v1/frontend/init/app-data')
    .then(res => res.json())
    .then(data => {
      setFeaturedSpecies(data.data.featured_today);
      setTrendingSearches(data.data.trending_searches);
      setStats(data.data.statistics);
      setHeatmapLegend(data.data.heatmap_legend);
    });
}, []);
```

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "featured_today": {
      "id": 123,
      "name": "호랑이",
      "image_url": "..."
    },
    "trending_searches": [
      {"query": "호랑이", "score": 150.0},
      {"query": "판다", "score": 120.0}
    ],
    "statistics": {
      "total_species": 1234,
      "total_endangered": 456,
      "countries_covered": 5
    },
    "heatmap_legend": {...}
  }
}
```

#### 🔍 검색 자동완성

**GET /api/v1/frontend/search/autocomplete?q={query}**

```javascript
// Debounced 자동완성
const [suggestions, setSuggestions] = useState([]);

const handleSearch = useMemo(
  () => debounce(async (query) => {
    if (query.length < 2) return;

    const res = await fetch(`/api/v1/frontend/search/autocomplete?q=${query}&limit=10`);
    const data = await res.json();

    setSuggestions(data.data.suggestions);
  }, 300),
  []
);

<input
  onChange={(e) => handleSearch(e.target.value)}
  placeholder="생물종 검색..."
/>

{suggestions.map(s => (
  <div key={s.id} className="suggestion-item">
    <img src={s.thumbnail} alt={s.name} />
    <span>{s.name}</span>
    <small>{s.scientific_name}</small>
    <span className="category">{s.category}</span>
  </div>
))}
```

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "query": "호",
    "suggestions": [
      {
        "id": 1,
        "name": "호랑이",
        "scientific_name": "Panthera tigris",
        "category": "동물",
        "thumbnail": "...",
        "match_type": "name",
        "search_count": 150
      }
    ],
    "count": 5
  }
}
```

#### 🗺️ 지도용 경량 데이터

**GET /api/v1/frontend/map/countries/simple**

GeoJSON 없이 히트맵 렌더링에 필요한 최소 데이터만:

```javascript
// Leaflet 또는 Mapbox 사용
const [mapData, setMapData] = useState(null);

useEffect(() => {
  fetch('/api/v1/frontend/map/countries/simple')
    .then(res => res.json())
    .then(data => {
      setMapData(data.data);
      renderHeatmap(data.data.countries, data.data.legend);
    });
}, []);

function renderHeatmap(countries, legend) {
  countries.forEach(country => {
    // 국가별 색상 적용
    countryLayers[country.code].setStyle({
      fillColor: country.color,
      fillOpacity: country.intensity
    });
  });
}
```

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "countries": [
      {
        "code": "KR",
        "name": "Korea",
        "count": 124,
        "intensity": 0.65,
        "color": "#4CAF50",
        "label": "높음"
      }
    ],
    "legend": {
      "levels": [...],
      "palette": "green"
    },
    "last_updated": "2025-01-15T10:30:00Z"
  }
}
```

#### ♾️ 무한 스크롤

**GET /api/v1/frontend/species/infinite?cursor={id}&limit=20**

```javascript
// React Infinite Scroll
import InfiniteScroll from 'react-infinite-scroll-component';

const [species, setSpecies] = useState([]);
const [cursor, setCursor] = useState(null);
const [hasMore, setHasMore] = useState(true);

const loadMore = async () => {
  const url = cursor
    ? `/api/v1/frontend/species/infinite?cursor=${cursor}&limit=20`
    : `/api/v1/frontend/species/infinite?limit=20`;

  const res = await fetch(url);
  const data = await res.json();

  setSpecies(prev => [...prev, ...data.data.items]);
  setCursor(data.data.next_cursor);
  setHasMore(data.data.has_next);
};

<InfiniteScroll
  dataLength={species.length}
  next={loadMore}
  hasMore={hasMore}
  loader={<Spinner />}
>
  {species.map(s => <SpeciesCard key={s.id} data={s} />)}
</InfiniteScroll>
```

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "items": [...],
    "next_cursor": 40,
    "has_next": true,
    "count": 20
  }
}
```

### 4. ✅ WebSocket 실시간 통신

**엔드포인트:** `ws://localhost:8000/ws`

**새 파일:** `app/api/websocket.py`

#### 프론트엔드 연결 예시

```javascript
// WebSocket 연결 및 구독
class VerdeWebSocket {
  constructor(url = 'ws://localhost:8000/ws') {
    this.ws = new WebSocket(url);
    this.setupHandlers();
  }

  setupHandlers() {
    this.ws.onopen = () => {
      console.log('✅ WebSocket connected');

      // 채널 구독
      this.subscribe(['trending', 'species_updates', 'notifications']);
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'connected':
          console.log('연결됨:', data.message);
          break;

        case 'trending_update':
          // 실시간 검색어 순위 업데이트
          this.updateTrendingList(data.data);
          break;

        case 'species_added':
          // 새로운 생물종 추가 알림
          this.showNotification(`새로운 생물종: ${data.data.name}`);
          break;

        case 'stats_update':
          // 통계 업데이트
          this.updateStats(data.data);
          break;

        case 'notification':
          // 일반 알림
          this.showToast(data.data);
          break;
      }
    };

    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('🔌 WebSocket disconnected');
      // 재연결 로직
      setTimeout(() => this.reconnect(), 5000);
    };
  }

  subscribe(channels) {
    this.ws.send(JSON.stringify({
      action: 'subscribe',
      channels: channels
    }));
  }

  unsubscribe(channels) {
    this.ws.send(JSON.stringify({
      action: 'unsubscribe',
      channels: channels
    }));
  }

  ping() {
    this.ws.send(JSON.stringify({ action: 'ping' }));
  }

  updateTrendingList(trending) {
    // UI 업데이트 로직
    const trendingDiv = document.getElementById('trending-searches');
    trendingDiv.innerHTML = trending
      .map((item, index) => `
        <div class="trending-item">
          <span class="rank">${index + 1}</span>
          <span class="query">${item.query}</span>
          <span class="score">${item.score}</span>
        </div>
      `)
      .join('');
  }

  showNotification(message) {
    // 토스트 알림 표시
    toast.success(message);
  }
}

// 사용
const ws = new VerdeWebSocket();
```

#### React Hook 예시

```javascript
// useVerdeWebSocket.js
import { useEffect, useState } from 'react';

export function useVerdeWebSocket(channels = []) {
  const [ws, setWs] = useState(null);
  const [trending, setTrending] = useState([]);
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    const websocket = new WebSocket('ws://localhost:8000/ws');

    websocket.onopen = () => {
      websocket.send(JSON.stringify({
        action: 'subscribe',
        channels: channels
      }));
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'trending_update') {
        setTrending(data.data);
      }

      if (data.type === 'notification') {
        setNotifications(prev => [...prev, data.data]);
      }
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, []);

  return { ws, trending, notifications };
}

// 컴포넌트에서 사용
function Dashboard() {
  const { trending, notifications } = useVerdeWebSocket(['trending', 'notifications']);

  return (
    <div>
      <h2>실시간 검색어</h2>
      {trending.map((item, i) => (
        <div key={i}>{i + 1}. {item.query}</div>
      ))}

      <h2>알림</h2>
      {notifications.map((n, i) => (
        <Toast key={i} message={n.message} />
      ))}
    </div>
  );
}
```

#### 지원 채널

| 채널 | 설명 | 업데이트 주기 |
|------|------|---------------|
| `trending` | 실시간 검색어 순위 | 30초 |
| `species_updates` | 새로운 생물종 추가 알림 | 이벤트 기반 |
| `stats` | 전체 통계 업데이트 | 이벤트 기반 |
| `notifications` | 일반 알림 | 이벤트 기반 |

### 5. 📊 페이지네이션 Best Practices

#### Option 1: 기본 페이지네이션 (작은 데이터셋)

```javascript
// useState로 페이지 관리
const [page, setPage] = useState(1);
const [totalPages, setTotalPages] = useState(1);
const [species, setSpecies] = useState([]);

useEffect(() => {
  fetch(`/api/v1/species?page=${page}&limit=20`)
    .then(res => {
      setTotalPages(parseInt(res.headers.get('X-Total-Pages')));
      return res.json();
    })
    .then(data => setSpecies(data.data.items));
}, [page]);

// 페이지 버튼
<div className="pagination">
  <button onClick={() => setPage(p => Math.max(1, p - 1))}>이전</button>
  <span>{page} / {totalPages}</span>
  <button onClick={() => setPage(p => Math.min(totalPages, p + 1))}>다음</button>
</div>
```

#### Option 2: 무한 스크롤 (대용량 데이터)

```javascript
// 커서 기반 페이지네이션
const [species, setSpecies] = useState([]);
const [cursor, setCursor] = useState(null);
const [loading, setLoading] = useState(false);

const loadMore = async () => {
  if (loading) return;
  setLoading(true);

  const url = cursor
    ? `/api/v1/frontend/species/infinite?cursor=${cursor}&limit=20`
    : `/api/v1/frontend/species/infinite?limit=20`;

  const res = await fetch(url);
  const data = await res.json();

  setSpecies(prev => [...prev, ...data.data.items]);
  setCursor(data.data.next_cursor);
  setLoading(false);
};

// Intersection Observer로 자동 로드
useEffect(() => {
  const observer = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting && cursor) {
      loadMore();
    }
  });

  const sentinel = document.querySelector('#load-more-sentinel');
  if (sentinel) observer.observe(sentinel);

  return () => observer.disconnect();
}, [cursor]);
```

## 🎯 성능 최적화 팁

### 1. 초기 로드 최적화

```javascript
// ❌ 나쁜 예: 여러 번 API 호출
useEffect(() => {
  fetch('/api/v1/species/random').then(...);
  fetch('/api/v1/search/trending').then(...);
  fetch('/api/v1/stats').then(...);
  fetch('/api/v1/regions').then(...);
}, []);

// ✅ 좋은 예: 한 번에 가져오기
useEffect(() => {
  fetch('/api/v1/frontend/init/app-data').then(res => res.json()).then(data => {
    // 모든 데이터가 한 번에
    setFeatured(data.data.featured_today);
    setTrending(data.data.trending_searches);
    setStats(data.data.statistics);
  });
}, []);
```

### 2. 검색 디바운싱

```javascript
import { useMemo } from 'react';
import debounce from 'lodash/debounce';

const debouncedSearch = useMemo(
  () => debounce(async (query) => {
    const res = await fetch(`/api/v1/frontend/search/autocomplete?q=${query}`);
    const data = await res.json();
    setSuggestions(data.data.suggestions);
  }, 300),
  []
);

<input onChange={(e) => debouncedSearch(e.target.value)} />
```

### 3. 캐시 활용

```javascript
// Response 헤더에서 캐시 정보 확인
fetch('/api/v1/species/popular')
  .then(res => {
    const cacheHit = res.headers.get('X-Cache-Hit');
    console.log(cacheHit ? '캐시 히트!' : '캐시 미스');
    return res.json();
  });
```

## 📱 모바일 최적화

### 1. 작은 화면용 limit 조정

```javascript
const isMobile = window.innerWidth < 768;
const limit = isMobile ? 10 : 20;

fetch(`/api/v1/species?limit=${limit}`);
```

### 2. 이미지 썸네일 사용

```javascript
// 자동완성에서는 thumbnail 사용 (작은 이미지)
<img src={species.thumbnail} alt={species.name} />

// 상세 페이지에서는 full image 사용
<img src={species.image_url} alt={species.name} />
```

## 🔧 에러 처리

```javascript
async function fetchWithErrorHandling(url) {
  try {
    const res = await fetch(url);
    const data = await res.json();

    if (!data.success) {
      // 표준화된 에러 응답
      throw new Error(data.error.message);
    }

    return data.data;
  } catch (error) {
    console.error('API Error:', error);
    toast.error(error.message || '데이터를 불러오는 중 오류가 발생했습니다');
    return null;
  }
}
```

## 📚 추가 리소스

- **API 문서:** http://localhost:8000/docs
- **WebSocket 테스트:** http://localhost:8000/ws/stats
- **헬스 체크:** http://localhost:8000/health
