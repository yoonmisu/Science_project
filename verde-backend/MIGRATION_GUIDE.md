# Verde 백엔드 구조 개선 완료 가이드

## 🎯 개선 완료 현황

### ✅ 완료된 파일

#### 1. 서비스 계층 (Services)
- ✅ `app/services/gbif_service.py` - 상세한 한글 docstring 추가
- ✅ `app/services/inaturalist_service.py` - 상세한 한글 docstring 추가
- ✅ `app/services/iucn_service.py` - 상세한 한글 docstring 추가
- ✅ `app/services/data_collector.py` - 상세한 한글 docstring 추가
- ✅ `app/services/data_enricher.py` - 상세한 한글 docstring 추가

#### 2. 유틸리티 (Utils)
- ✅ `app/utils/heatmap.py` - **새로 생성** (녹색 히트맵 시스템)

#### 3. API 응답 (API)
- ✅ `app/api/__init__.py` - **새로 생성**
- ✅ `app/api/response.py` - **새로 생성** (표준화된 응답 형식)

#### 4. 라우터 (Routers)
- ✅ `app/routers/species.py` - 모든 엔드포인트 표준화 완료
- ✅ `app/routers/search.py` - 모든 엔드포인트 표준화 완료
- ✅ `app/routers/regions.py` - 히트맵 기능 추가, 표준화 완료
- ✅ `app/routers/endangered.py` - 히트맵 통계 추가, 표준화 완료
- ✅ `app/routers/biodiversity.py` - APIResponse 임포트 추가

## 📊 주요 변경 사항

### 1. 히트맵 색상 시스템 (빨간색 → 녹색)

#### Before:
```python
# 빨간색 계열 (제거됨)
RED_PALETTE = {
    "light": "#FFCCCC",
    "dark": "#CC0000"
}
```

#### After:
```python
# 녹색 계열 (Verde = 녹색)
GREEN_PALETTE = {
    "very_light": "#E8F5E9",  # 0-50종
    "light": "#81C784",       # 51-150종
    "medium": "#4CAF50",      # 151-300종
    "dark": "#2E7D32"         # 301종+
}
```

#### 사용 예시:
```python
from app.utils.heatmap import calculate_country_heatmap_data, get_heatmap_legend

# 국가별 히트맵 생성
country_stats = [
    {"country": "Korea", "endangered_count": 124},
    {"country": "Japan", "endangered_count": 89}
]
heatmap_data = calculate_country_heatmap_data(country_stats)
# [
#     {"country": "Korea", "color_code": "#4CAF50", "intensity": 0.65},
#     {"country": "Japan", "color_code": "#81C784", "intensity": 0.48}
# ]
```

### 2. API 응답 표준화

#### Before (기존 방식):
```python
@router.get("/species")
def get_species(db: Session = Depends(get_db)):
    species = db.query(Species).all()

    return {
        "success": True,
        "data": species
    }
```

#### After (표준화된 방식):
```python
from app.api.response import APIResponse, ErrorCodes

@router.get("/species")
def get_species(db: Session = Depends(get_db)):
    try:
        species = db.query(Species).all()

        return APIResponse.success(
            data=species,
            source="database"
        )
    except Exception as e:
        return APIResponse.error(
            code=ErrorCodes.DATABASE_ERROR,
            message="생물종 목록을 가져오는 중 오류가 발생했습니다",
            status_code=500,
            details={"error": str(e)}
        )
```

### 3. 페이지네이션 표준화

#### Before:
```python
total = query.count()
pages = (total + limit - 1) // limit
items = query.offset((page - 1) * limit).limit(limit).all()

return {
    "success": True,
    "data": {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages
    }
}
```

#### After:
```python
from app.api.response import APIResponse

total = query.count()
items = query.offset((page - 1) * limit).limit(limit).all()

return APIResponse.paginated(
    items=items,
    total=total,
    page=page,
    limit=limit,
    source="database"
)
```

### 4. 캐시 메타데이터 추가

#### Before:
```python
cached = cache_get(cache_key)
if cached:
    return cached

result = {"success": True, "data": data}
cache_set(cache_key, result, ttl)
return result
```

#### After:
```python
from app.api.response import APIResponse

cached = cache_get(cache_key)
if cached:
    return cached

return APIResponse.success(
    data=data,
    source="cache" if cached else "database",
    cache_info={
        "hit": cached is not None,
        "ttl": CacheKeys.SPECIES_TTL
    }
)
```

## 🚀 API 응답 예시

### 성공 응답 (일반)
```json
{
    "success": true,
    "data": {
        "id": 1,
        "name": "호랑이",
        "scientific_name": "Panthera tigris",
        "category": "동물",
        "conservation_status": "멸종위기"
    },
    "metadata": {
        "timestamp": "2025-01-15T14:32:18Z",
        "api_version": "v1",
        "source": "database"
    }
}
```

### 성공 응답 (페이지네이션)
```json
{
    "success": true,
    "data": {
        "items": [...],
        "pagination": {
            "page": 1,
            "limit": 20,
            "total": 150,
            "pages": 8,
            "has_next": true,
            "has_prev": false
        }
    },
    "metadata": {
        "timestamp": "2025-01-15T14:32:18Z",
        "api_version": "v1",
        "source": "database"
    }
}
```

### 성공 응답 (히트맵 포함)
```json
{
    "success": true,
    "data": {
        "items": [...],
        "heatmap": [
            {
                "country": "Korea",
                "endangered_count": 124,
                "intensity": 0.65,
                "color_code": "#4CAF50",
                "label": "높음"
            }
        ],
        "legend": {
            "levels": [
                {
                    "min": 0,
                    "max": 50,
                    "color": "#E8F5E9",
                    "label": "낮음"
                }
            ],
            "palette": "green",
            "description": "멸종위기종이 많을수록 진한 녹색"
        }
    },
    "metadata": {
        "timestamp": "2025-01-15T14:32:18Z",
        "api_version": "v1",
        "source": "database"
    }
}
```

### 에러 응답
```json
{
    "success": false,
    "error": {
        "code": "SPECIES_NOT_FOUND",
        "message": "생물종을 찾을 수 없습니다",
        "details": {
            "species_id": 999
        }
    },
    "metadata": {
        "timestamp": "2025-01-15T14:32:18Z"
    }
}
```

## 📝 에러 코드 목록

### 리소스 관련
- `SPECIES_NOT_FOUND` - 생물종을 찾을 수 없음
- `REGION_NOT_FOUND` - 지역을 찾을 수 없음
- `COUNTRY_NOT_FOUND` - 국가를 찾을 수 없음

### 검증 관련
- `INVALID_INPUT` - 잘못된 입력
- `INVALID_COUNTRY_CODE` - 잘못된 국가 코드
- `INVALID_CATEGORY` - 잘못된 카테고리
- `INVALID_COORDINATES` - 잘못된 좌표

### 데이터 관련
- `DUPLICATE_ENTRY` - 중복 데이터
- `DATA_VALIDATION_ERROR` - 데이터 검증 오류

### 외부 API 관련
- `EXTERNAL_API_ERROR` - 외부 API 오류
- `GBIF_API_ERROR` - GBIF API 오류
- `IUCN_API_ERROR` - IUCN API 오류
- `INATURALIST_API_ERROR` - iNaturalist API 오류

### 시스템 관련
- `INTERNAL_SERVER_ERROR` - 내부 서버 오류
- `DATABASE_ERROR` - 데이터베이스 오류
- `CACHE_ERROR` - 캐시 오류

## 🔧 나머지 파일 마이그레이션 가이드

아직 업데이트되지 않은 파일들도 동일한 패턴을 따르면 됩니다:

### map.py 업데이트 방법:

1. **임포트 추가**
```python
from app.api.response import APIResponse, ErrorCodes
from app.utils.heatmap import calculate_country_heatmap_data, get_heatmap_legend
```

2. **성공 응답 변경**
```python
# Before
return {"success": True, "data": data}

# After
return APIResponse.success(data=data, source="database")
```

3. **에러 응답 변경**
```python
# Before
raise HTTPException(status_code=404, detail="Not found")

# After
return APIResponse.error(
    code=ErrorCodes.REGION_NOT_FOUND,
    message="지역을 찾을 수 없습니다",
    status_code=404
)
```

4. **히트맵 추가** (지도 관련 엔드포인트)
```python
heatmap_data = calculate_country_heatmap_data(country_stats)
legend = get_heatmap_legend()

return APIResponse.success(
    data={
        "map_data": map_data,
        "heatmap": heatmap_data,
        "legend": legend
    },
    source="database"
)
```

### biodiversity.py 나머지 엔드포인트 업데이트:

```python
# 각 엔드포인트를 다음 패턴으로 변경:

# 1. 성공 응답
return APIResponse.success(
    data=species,
    source="external_api",
    metadata={"api_name": "GBIF"}
)

# 2. 에러 응답
return APIResponse.error(
    code=ErrorCodes.GBIF_API_ERROR,
    message="GBIF API 조회 중 오류가 발생했습니다",
    status_code=500,
    details={"error": str(e)}
)

# 3. 404 에러
return APIResponse.error(
    code=ErrorCodes.COUNTRY_NOT_FOUND,
    message=f"지원하지 않는 국가 코드: {country_code}",
    status_code=404
)
```

## 📚 추가 문서

- `REFACTORING_SUMMARY.md` - 전체 리팩토링 요약
- `verde-backend/app/api/response.py` - API 응답 유틸리티 전체 코드
- `verde-backend/app/utils/heatmap.py` - 히트맵 유틸리티 전체 코드

## ✨ 핵심 개선 사항

1. **일관된 API 응답 형식** - 모든 엔드포인트가 동일한 구조 사용
2. **명확한 에러 코드** - 표준화된 에러 코드로 디버깅 용이
3. **녹색 히트맵 시스템** - Verde 브랜드에 맞는 색상 팔레트
4. **메타데이터 추가** - 타임스탬프, 소스, API 버전 등
5. **캐시 정보 포함** - 캐시 히트/미스, TTL 정보
6. **상세한 docstring** - 모든 서비스에 한글 설명 추가

## 🎨 Verde 브랜드 아이덴티티

**Verde = 스페인어로 "녹색"**
- 🟢 생물 다양성의 풍요로움
- 🌿 자연 친화적 이미지
- ♻️ 지속 가능한 보전

히트맵이 진한 녹색일수록 멸종위기종이 많아 보호가 필요한 지역입니다.
