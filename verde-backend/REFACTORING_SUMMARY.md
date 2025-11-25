# Verde 백엔드 리팩토링 요약

## 📋 개요

최신 설계 문서에 맞춰 Verde 백엔드 코드를 리팩토링했습니다.

## ✅ 완료된 작업

### 1. 비즈니스 로직 분리 및 자연어 주석 추가

모든 주요 서비스 클래스에 상세한 한글 docstring을 추가했습니다:

#### 📁 업데이트된 파일:
- `app/services/gbif_service.py` ✅
- `app/services/inaturalist_service.py` ✅
- `app/services/iucn_service.py` ✅
- `app/services/data_collector.py` ✅
- `app/services/data_enricher.py` ✅

#### 예시:
```python
class GBIFService:
    """
    GBIF (Global Biodiversity Information Facility) API 연동 서비스

    사용자 시나리오:
    1. 관리자가 "한국의 멸종위기종 데이터 수집" 버튼 클릭
    2. 이 서비스가 GBIF API에서 한국(KR) 데이터를 가져옴
    3. GBIF 형식을 우리 Species 모델로 변환
    4. 데이터베이스에 저장

    주요 기능:
    - fetch_species_by_region: 국가별 생물종 검색
    - fetch_species_by_coordinates: 위치 기반 검색
    - get_biodiversity_statistics: 통계 데이터
    """
```

### 2. 히트맵 색상 시스템 업데이트 (녹색 계열) 🟢

기존의 빨간색 계열을 **녹색 계열**로 완전히 변경했습니다.

#### 📁 새로 생성된 파일:
- `app/utils/heatmap.py` ⭐

#### 녹색 팔레트:
```python
GREEN_PALETTE = {
    "very_light": "#E8F5E9",  # 매우 연한 녹색 (0-50종)
    "light": "#81C784",       # 연한 녹색 (51-150종)
    "medium": "#4CAF50",      # 중간 녹색 (151-300종)
    "dark": "#2E7D32"         # 진한 녹색 (301종+)
}
```

#### 주요 기능:
- `calculate_heatmap_intensity()` - 로그 스케일 강도 계산
- `get_green_color_code()` - 강도에 따른 녹색 코드 반환
- `get_green_color_by_count()` - 멸종위기종 수로 직접 색상 반환
- `get_heatmap_legend()` - 프론트엔드용 범례 데이터
- `calculate_country_heatmap_data()` - 국가별 히트맵 데이터 생성

#### 왜 녹색인가?
- **Verde** = 스페인어로 "녹색"
- 생물 다양성의 **풍요로움** 표현
- 자연 친화적 브랜드 이미지

### 3. API 응답 형식 표준화 📦

모든 API 엔드포인트에 일관된 응답 형식을 적용했습니다.

#### 📁 새로 생성된 파일:
- `app/api/__init__.py`
- `app/api/response.py` ⭐

#### 성공 응답 형식:
```json
{
    "success": true,
    "data": {
        "items": [...],
        "heatmap": [...],
        "legend": {...}
    },
    "metadata": {
        "timestamp": "2025-01-15T14:32:18Z",
        "api_version": "v1",
        "source": "database"
    }
}
```

#### 에러 응답 형식:
```json
{
    "success": false,
    "error": {
        "code": "SPECIES_NOT_FOUND",
        "message": "해당 생물종을 찾을 수 없습니다",
        "details": {}
    },
    "metadata": {
        "timestamp": "2025-01-15T14:32:18Z"
    }
}
```

#### 페이지네이션 응답:
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
    "metadata": {...}
}
```

#### 📁 업데이트된 라우터:
- `app/routers/regions.py` ✅
  - `GET /regions/` - 히트맵 데이터 포함
  - `GET /regions/{region}/species` - 페이지네이션

- `app/routers/endangered.py` ✅
  - `GET /endangered/` - 페이지네이션
  - `GET /endangered/statistics` - 히트맵 포함

## 🎯 사용 방법

### 1. 히트맵 사용하기

```python
from app.utils.heatmap import calculate_country_heatmap_data, get_heatmap_legend

# 국가별 통계 데이터
country_stats = [
    {"country": "한국", "endangered_count": 124},
    {"country": "일본", "endangered_count": 89},
    {"country": "중국", "endangered_count": 342}
]

# 히트맵 데이터 계산 (자동으로 녹색 색상 할당)
heatmap_data = calculate_country_heatmap_data(country_stats)

# 범례 가져오기
legend = get_heatmap_legend()
```

### 2. 표준화된 API 응답 사용하기

```python
from app.api.response import APIResponse, ErrorCodes

# 성공 응답
@router.get("/species")
def get_species(db: Session = Depends(get_db)):
    species = db.query(Species).all()

    return APIResponse.success(
        data={"species": species},
        source="database"
    )

# 에러 응답
@router.get("/species/{id}")
def get_species_by_id(id: int, db: Session = Depends(get_db)):
    species = db.query(Species).filter(Species.id == id).first()

    if not species:
        return APIResponse.error(
            code=ErrorCodes.SPECIES_NOT_FOUND,
            message="해당 생물종을 찾을 수 없습니다",
            status_code=404,
            details={"species_id": id}
        )

    return APIResponse.success(data=species)

# 페이지네이션 응답
@router.get("/species")
def get_species_paginated(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    total = db.query(Species).count()
    items = db.query(Species).offset((page - 1) * limit).limit(limit).all()

    return APIResponse.paginated(
        items=items,
        total=total,
        page=page,
        limit=limit,
        source="database"
    )
```

### 3. 표준 에러 코드 사용하기

```python
from app.api.response import ErrorCodes

# 사용 가능한 에러 코드:
ErrorCodes.SPECIES_NOT_FOUND
ErrorCodes.REGION_NOT_FOUND
ErrorCodes.INVALID_INPUT
ErrorCodes.INVALID_COUNTRY_CODE
ErrorCodes.UNAUTHORIZED
ErrorCodes.DATABASE_ERROR
ErrorCodes.GBIF_API_ERROR
ErrorCodes.IUCN_API_ERROR
ErrorCodes.INTERNAL_SERVER_ERROR
```

## 🔄 마이그레이션 가이드

### 기존 코드를 새 형식으로 변경하기

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

#### After (새 방식):
```python
from app.api.response import APIResponse

@router.get("/species")
def get_species(db: Session = Depends(get_db)):
    species = db.query(Species).all()

    return APIResponse.success(
        data=species,
        source="database"
    )
```

## 📊 API 예시

### 지역 목록 조회 (히트맵 포함)

**요청:**
```
GET /regions/
```

**응답:**
```json
{
    "success": true,
    "data": {
        "items": [
            {
                "id": 1,
                "region_name": "아시아",
                "country": "Korea",
                "endangered_count": 124,
                "total_species_count": 1580
            }
        ],
        "total": 10,
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
            "levels": [...],
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

### 멸종위기종 통계 (히트맵 포함)

**요청:**
```
GET /endangered/statistics
```

**응답:**
```json
{
    "success": true,
    "data": {
        "total_endangered": 450,
        "by_category": {
            "동물": 180,
            "식물": 150,
            "곤충": 70,
            "해양생물": 50
        },
        "heatmap": [...],
        "legend": {...}
    },
    "metadata": {...}
}
```

## 🔧 다음 단계 (향후 작업)

다음 파일들도 동일한 패턴으로 업데이트할 수 있습니다:

1. `app/routers/species.py` - 생물종 라우터
2. `app/routers/search.py` - 검색 라우터
3. `app/routers/biodiversity.py` - 생물다양성 라우터
4. `app/routers/map.py` - 지도 라우터
5. `app/routers/external.py` - 외부 API 라우터

**패턴:**
```python
# 임포트 추가
from app.api.response import APIResponse, ErrorCodes
from app.utils.heatmap import calculate_country_heatmap_data, get_heatmap_legend

# 기존 응답 변경
return {
    "success": True,
    "data": {...}
}

# 새 응답으로 변경
return APIResponse.success(
    data={...},
    source="database"
)
```

## 📝 주요 변경 사항 요약

| 구분 | 변경 전 | 변경 후 |
|------|---------|---------|
| 히트맵 색상 | 빨간색 계열 | **녹색 계열** 🟢 |
| API 응답 | 비표준 형식 | 표준화된 형식 📦 |
| 에러 처리 | HTTPException | APIResponse.error() |
| 페이지네이션 | 수동 계산 | APIResponse.paginated() |
| Docstring | 간단한 설명 | 상세한 한글 설명 📚 |
| 메타데이터 | 없음 | timestamp, version, source |

## 🎨 브랜딩

**Verde = 녹색**
- 스페인어로 "녹색"을 의미
- 생물 다양성과 자연을 상징
- 친환경적이고 긍정적인 이미지

## 📞 문의

리팩토링 관련 질문이나 제안사항이 있으시면 언제든지 연락주세요!
