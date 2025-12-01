# Verde Backend API

## 🚀 Quick Start (로컬 개발)

### 1. 데이터베이스 생성
```bash
# PostgreSQL 데이터베이스 생성
createdb verde_db
```

### 2. Python 환경 설정
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # macOS/Linux

# 의존성 설치
pip install -r requirements.txt
```

### 3. 데이터 초기화
```bash
# 테이블 생성 및 샘플 데이터 삽입
python scripts/seed_data.py
```

### 4. 백엔드 실행
```bash
uvicorn app.main:app --reload --port 8000
```

### 5. 테스트
- API 문서: http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/

## 📋 API 엔드포인트

### Health Check
- `GET /` - 백엔드 상태 확인

### Species (종)
- `GET /api/v1/species` - 종 목록 (국가/카테고리별)
- `GET /api/v1/species/search` - 검색
- `GET /api/v1/species/random` - 랜덤 종
- `GET /api/v1/species/popular-endangered` - 인기 멸종위기종
- `GET /api/v1/species/endangered` - 멸종위기종 목록
- `GET /api/v1/species/{id}` - 종 상세 정보

## 🧪 API 테스트 예시

```bash
# 대한민국 동물 목록
curl "http://localhost:8000/api/v1/species?country=korea&category=동물"

# 검색
curl "http://localhost:8000/api/v1/species/search?q=호랑이"

# 랜덤 종
curl "http://localhost:8000/api/v1/species/random"
```

## 🔍 프론트엔드 연동

1. 백엔드 실행: `uvicorn app.main:app --reload`
2. 프론트엔드 실행: `npm run dev` (루트 디렉토리에서)
3. 브라우저에서 http://localhost:5173 접속

## 📁 프로젝트 구조

```
verde-backend/
├── app/
│   ├── api/v1/endpoints/
│   │   └── species.py       # Species API
│   ├── core/
│   │   └── config.py         # 설정
│   ├── db/
│   │   └── session.py        # DB 연결
│   ├── models/
│   │   └── species.py        # DB 모델
│   ├── schemas/
│   │   └── species.py        # Pydantic 스키마
│   └── main.py               # FastAPI 앱
├── scripts/
│   └── seed_data.py          # 초기 데이터
├── requirements.txt
└── README.md
```

## 🐛 문제 해결

### PostgreSQL 연결 실패
```bash
# PostgreSQL 실행 확인
brew services list

# 데이터베이스 존재 확인
psql -l | grep verde_db
```

### 데이터가 없음
```bash
python scripts/seed_data.py
```

## 지원 데이터

### 국가
- korea, japan, usa, china, russia

### 카테고리
- 동물, 식물, 곤충, 해양생물
