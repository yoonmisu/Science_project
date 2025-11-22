# Verde Backend API

Verde 생물다양성 플랫폼의 백엔드 API 서버입니다.

## 기술 스택

- **Framework**: FastAPI
- **Database**: PostgreSQL + SQLAlchemy ORM
- **Cache**: Redis
- **Migration**: Alembic
- **Authentication**: JWT (python-jose)

## 프로젝트 구조

```
verde-backend/
├── app/
│   ├── main.py           # FastAPI 앱 진입점
│   ├── config.py         # 환경 설정
│   ├── database.py       # DB 연결
│   ├── cache.py          # Redis 캐시
│   ├── models/           # SQLAlchemy 모델
│   ├── schemas/          # Pydantic 스키마
│   ├── routers/          # API 라우터
│   ├── services/         # 비즈니스 로직
│   └── utils/            # 유틸리티
├── alembic/              # DB 마이그레이션
├── requirements.txt
├── docker-compose.yml
└── .env.example
```

## 설치 및 실행

### 1. 환경 설정

```bash
# 환경변수 파일 생성
cp .env.example .env

# 필요한 값 수정
vim .env
```

### 2. Docker로 실행 (권장)

```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f api
```

### 3. 로컬에서 실행

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# PostgreSQL, Redis 실행 필요

# 서버 시작
uvicorn app.main:app --reload --port 8000
```

## 데이터베이스 마이그레이션

```bash
# 마이그레이션 적용
alembic upgrade head

# 새 마이그레이션 생성
alembic revision --autogenerate -m "Description"

# 마이그레이션 되돌리기
alembic downgrade -1
```

## API 문서

서버 실행 후 아래 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 주요 API 엔드포인트

### Species (종)
- `GET /species/` - 종 목록 조회
- `GET /species/{id}` - 특정 종 조회
- `POST /species/` - 종 등록
- `PUT /species/{id}` - 종 수정
- `DELETE /species/{id}` - 종 삭제

### Search (검색)
- `GET /search/` - 종 검색
- `GET /search/suggestions` - 검색어 자동완성
- `GET /search/popular` - 인기 검색어

### Regions (지역)
- `GET /regions/` - 모든 지역 조회
- `GET /regions/{region}` - 특정 지역 조회
- `GET /regions/{region}/stats` - 지역 통계

### Endangered (멸종위기종)
- `GET /endangered/` - 멸종위기종 목록
- `GET /endangered/stats` - 멸종위기종 통계
- `GET /endangered/critical` - 위급종 목록

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| DATABASE_URL | PostgreSQL 연결 URL | postgresql://postgres:password@localhost:5432/verde_db |
| REDIS_URL | Redis 연결 URL | redis://localhost:6379/0 |
| SECRET_KEY | JWT 시크릿 키 | (설정 필요) |
| CORS_ORIGINS | 허용할 Origin 목록 | ["http://localhost:5173"] |
| DEBUG | 디버그 모드 | True |

## 개발 가이드

### 새 모델 추가

1. `app/models/`에 모델 파일 생성
2. `app/schemas/`에 Pydantic 스키마 생성
3. `app/routers/`에 라우터 생성
4. `app/main.py`에 라우터 등록
5. Alembic 마이그레이션 생성 및 적용

### 코드 스타일

- Python 3.11+
- Type hints 사용
- Pydantic v2 스키마
- SQLAlchemy 2.0 스타일
