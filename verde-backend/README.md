# 🌿 Verde Backend API

Verde는 전 세계 생물 다양성 데이터를 시각화하고 탐색할 수 있는 플랫폼입니다. 이 저장소는 FastAPI 기반의 백엔드 API 서버입니다.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 목차

- [기능](#-기능)
- [기술 스택](#-기술-스택)
- [시작하기](#-시작하기)
- [API 엔드포인트](#-api-엔드포인트)
- [환경변수](#-환경변수)
- [테스트](#-테스트)
- [배포](#-배포)
- [라이선스](#-라이선스)

## ✨ 기능

### 핵심 기능
- **생물종 관리**: 전 세계 생물종 데이터 CRUD
- **검색 시스템**: 실시간 검색어 랭킹, 자동완성
- **지역별 통계**: 국가/지역별 생물 다양성 통계
- **멸종위기종**: 보전 상태별 필터링 및 통계

### 부가 기능
- **캐싱**: Redis 기반 고성능 캐싱
- **페이지네이션**: 모든 목록 API 지원
- **필터링/정렬**: 다양한 조건으로 데이터 필터링
- **API 문서**: Swagger UI 자동 생성

## 🛠 기술 스택

| 분류 | 기술 |
|------|------|
| **Framework** | FastAPI 0.115 |
| **Language** | Python 3.11 |
| **Database** | PostgreSQL 15 |
| **Cache** | Redis 7 |
| **ORM** | SQLAlchemy 2.0 |
| **Migration** | Alembic |
| **Validation** | Pydantic 2.0 |
| **Server** | Uvicorn |
| **Reverse Proxy** | Nginx |
| **Container** | Docker |

## 🚀 시작하기

### 사전 요구사항

- Docker & Docker Compose
- Python 3.11+ (로컬 개발 시)
- PostgreSQL 15+ (로컬 개발 시)
- Redis 7+ (로컬 개발 시)

### Docker로 실행 (권장)

```bash
# 1. 저장소 클론
git clone https://github.com/your-username/verde-backend.git
cd verde-backend

# 2. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 SECRET_KEY 등 수정

# 3. 서비스 시작
docker-compose up -d

# 4. 데이터베이스 마이그레이션
docker-compose exec app alembic upgrade head

# 5. 초기 데이터 삽입
docker-compose exec app python -m app.seed

# 6. 서비스 확인
curl http://localhost/health
```

### 로컬에서 실행

```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경변수 설정
cp .env.example .env
# DATABASE_URL, REDIS_URL 수정

# 4. 데이터베이스 마이그레이션
alembic upgrade head

# 5. 초기 데이터 삽입
python -m app.seed

# 6. 서버 실행
uvicorn app.main:app --reload --port 8000
```

### API 문서 확인

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 API 엔드포인트

### Health Check
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | 서비스 상태 확인 |

### Species (생물종)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/species` | 종 목록 조회 |
| GET | `/api/v1/species/{id}` | 특정 종 상세 |
| GET | `/api/v1/species/random` | 오늘의 랜덤 종 |
| GET | `/api/v1/species/popular` | 인기 종 목록 |
| POST | `/api/v1/species` | 종 등록 |
| PUT | `/api/v1/species/{id}` | 종 수정 |
| DELETE | `/api/v1/species/{id}` | 종 삭제 |

### Search (검색)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/search` | 검색 수행 |
| GET | `/api/v1/search/trending` | 실시간 인기 검색어 |
| GET | `/api/v1/search/suggestions` | 검색어 자동완성 |
| GET | `/api/v1/search/popular` | 전체 인기 검색어 |
| GET | `/api/v1/search/realtime` | 실시간 랭킹 |

### Regions (지역)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/regions` | 지역 목록 |
| GET | `/api/v1/regions/{region}/species` | 지역별 종 목록 |
| GET | `/api/v1/regions/{region}/biodiversity` | 지역별 통계 |
| POST | `/api/v1/regions` | 지역 등록 |

### Endangered (멸종위기종)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/endangered` | 멸종위기종 목록 |
| GET | `/api/v1/endangered/most-mentioned` | 조회수 Top 10 |
| GET | `/api/v1/endangered/statistics` | 통계 |
| GET | `/api/v1/endangered/critical` | 멸종위기 상태만 |
| GET | `/api/v1/endangered/region/{region}` | 지역별 멸종위기종 |

### Statistics (통계)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/stats` | 전체 통계 |

## ⚙️ 환경변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `DATABASE_URL` | PostgreSQL 연결 URL | `postgresql://postgres:password@db:5432/verde_db` |
| `REDIS_URL` | Redis 연결 URL | `redis://redis:6379/0` |
| `SECRET_KEY` | JWT 시크릿 키 | (필수 설정) |
| `DEBUG` | 디버그 모드 | `False` |
| `CORS_ORIGINS` | CORS 허용 Origin | `["http://localhost:5173"]` |
| `APP_NAME` | 앱 이름 | `Verde API` |
| `APP_VERSION` | 앱 버전 | `1.0.0` |

자세한 환경변수 목록은 [.env.example](.env.example)을 참조하세요.

## 🧪 테스트

```bash
# 전체 테스트 실행 (커버리지 포함)
pytest

# 특정 파일만 테스트
pytest tests/test_species.py

# 커버리지 리포트 생성
pytest --cov=app --cov-report=html

# HTML 리포트 확인
open htmlcov/index.html
```

### 테스트 구성

- `tests/test_species.py` - 생물종 API 테스트
- `tests/test_search.py` - 검색 API 테스트
- `tests/test_regions.py` - 지역 API 테스트
- `tests/test_endangered.py` - 멸종위기종 API 테스트

**목표 커버리지**: 80% 이상

## 🚢 배포

### Docker Compose (프로덕션)

```bash
# 프로덕션 환경 시작
docker-compose -f docker-compose.yml up -d

# 로그 확인
docker-compose logs -f app

# 서비스 중지
docker-compose down
```

### Railway 배포

1. Railway 프로젝트 생성
2. GitHub 저장소 연결
3. 환경변수 설정
4. 자동 배포 활성화

### 수동 배포

```bash
# 이미지 빌드
docker build -t verde-api .

# 컨테이너 실행
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=... \
  -e REDIS_URL=... \
  -e SECRET_KEY=... \
  verde-api
```

## 📁 프로젝트 구조

```
verde-backend/
├── app/
│   ├── main.py              # FastAPI 앱 진입점
│   ├── config.py            # 환경 설정
│   ├── database.py          # DB 연결
│   ├── cache.py             # Redis 캐시
│   ├── models/              # SQLAlchemy 모델
│   ├── schemas/             # Pydantic 스키마
│   ├── routers/             # API 라우터
│   ├── services/            # 비즈니스 로직
│   └── seed.py              # 초기 데이터
├── alembic/                 # DB 마이그레이션
├── tests/                   # 테스트 코드
├── nginx/                   # Nginx 설정
├── scripts/                 # 유틸리티 스크립트
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## 🤝 기여하기

기여를 환영합니다! [CONTRIBUTING.md](CONTRIBUTING.md)를 참조해주세요.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📞 문의

- **Issues**: [GitHub Issues](https://github.com/your-username/verde-backend/issues)
- **Email**: contact@verde.app

---

Made with 💚 by Verde Team
