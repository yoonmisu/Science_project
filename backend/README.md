# Verde Backend API

FastAPI + PostgreSQL 기반의 생물다양성 데이터 API 서버입니다.

## 기술 스택

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migration**: Alembic
- **Cache**: Redis
- **Authentication**: JWT (python-jose)

## 빠른 시작

### 1. 환경 설정

```bash
# 환경변수 파일 생성
cp .env.example .env

# 필요시 .env 파일 수정
```

### 2. Docker로 실행 (권장)

```bash
# 모든 서비스 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f api
```

### 3. 로컬 실행

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# PostgreSQL, Redis 실행 (Docker 사용)
docker-compose up -d db redis

# DB 마이그레이션
alembic upgrade head

# 서버 실행
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## API 문서

서버 실행 후 접속:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 주요 API 엔드포인트

### Species (종)
- `GET /api/v1/species` - 종 목록 조회
- `GET /api/v1/species/{id}` - 특정 종 조회
- `POST /api/v1/species` - 종 등록
- `PUT /api/v1/species/{id}` - 종 수정
- `DELETE /api/v1/species/{id}` - 종 삭제

### Search (검색)
- `GET /api/v1/search?q={query}` - 종 검색
- `GET /api/v1/search/suggestions?q={query}` - 자동완성
- `GET /api/v1/search/popular` - 인기 검색어

### Regions (지역)
- `GET /api/v1/regions` - 모든 지역 조회
- `GET /api/v1/regions/{region}` - 특정 지역 조회
- `GET /api/v1/regions/stats` - 지역별 통계
- `POST /api/v1/regions/refresh-stats` - 통계 갱신

### Endangered (멸종위기종)
- `GET /api/v1/endangered` - 멸종위기종 목록
- `GET /api/v1/endangered/critical` - 심각한 멸종위기종
- `GET /api/v1/endangered/stats` - 멸종위기종 통계

## 데이터베이스 마이그레이션

```bash
# 새 마이그레이션 생성
alembic revision --autogenerate -m "description"

# 마이그레이션 적용
alembic upgrade head

# 마이그레이션 롤백
alembic downgrade -1
```

## 프로젝트 구조

```
backend/
├── app/
│   ├── main.py              # FastAPI 앱
│   ├── config.py            # 설정
│   ├── database.py          # DB 연결
│   ├── models/              # SQLAlchemy 모델
│   │   ├── species.py
│   │   ├── search_query.py
│   │   └── region_biodiversity.py
│   ├── schemas/             # Pydantic 스키마
│   │   ├── species.py
│   │   ├── search.py
│   │   └── region.py
│   ├── routers/             # API 라우터
│   │   ├── species.py
│   │   ├── search.py
│   │   ├── regions.py
│   │   └── endangered.py
│   ├── services/            # 비즈니스 로직
│   └── utils/               # 유틸리티
├── alembic/                 # DB 마이그레이션
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 연결 URL | `postgresql://postgres:password@localhost:5432/verde_db` |
| `REDIS_URL` | Redis 연결 URL | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT 시크릿 키 | - |
| `CORS_ORIGINS` | 허용된 CORS 오리진 | `http://localhost:5173` |
| `DEBUG` | 디버그 모드 | `True` |

## 보존 상태 코드

| 코드 | 의미 |
|------|------|
| LC | 관심대상 (Least Concern) |
| NT | 준위협 (Near Threatened) |
| VU | 취약 (Vulnerable) |
| EN | 위기 (Endangered) |
| CR | 심각한 위기 (Critically Endangered) |
| EW | 야생 절멸 (Extinct in the Wild) |
| EX | 절멸 (Extinct) |

## 카테고리

- `animal`: 동물
- `plant`: 식물
- `insect`: 곤충
- `marine`: 해양생물

## 지원 지역

- Korea (한국)
- Japan (일본)
- USA (미국)
- China (중국)
- Russia (러시아)
