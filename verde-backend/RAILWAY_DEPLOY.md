# Railway 배포 가이드

## 1. Railway 계정 생성

1. [railway.app](https://railway.app) 접속
2. GitHub 계정으로 로그인

## 2. 새 프로젝트 생성

### 방법 A: Dashboard에서 생성

1. **New Project** 클릭
2. **Deploy from GitHub repo** 선택
3. 이 저장소 선택

### 방법 B: CLI로 생성

```bash
# Railway CLI 설치
npm install -g @railway/cli

# 로그인
railway login

# 프로젝트 생성 및 연결
cd verde-backend
railway init
```

## 3. 데이터베이스 추가

Railway Dashboard에서:

1. **+ New** → **Database** → **Add PostgreSQL**
2. **+ New** → **Database** → **Add Redis**

자동으로 환경변수가 생성됩니다:
- `DATABASE_URL` (PostgreSQL)
- `REDIS_URL` (Redis)

## 4. 환경변수 설정

Railway Dashboard → 앱 서비스 → **Variables** 탭에서 추가:

```env
# 필수 설정
SECRET_KEY=7b13fdc0f28f839c830f10f0e74f0a684fd6616f7c79c886982ee9e9de292274
DEBUG=False
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (Railway 도메인으로 변경)
CORS_ORIGINS=["https://your-app.up.railway.app"]

# 앱 정보
APP_NAME=Verde API
APP_VERSION=1.0.0
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Cache TTL
CACHE_RANDOM_SPECIES_TTL=86400
CACHE_TRENDING_TTL=300
CACHE_REGION_STATS_TTL=3600
CACHE_POPULAR_SPECIES_TTL=1800
CACHE_GLOBAL_STATS_TTL=600
```

> **참고**: `DATABASE_URL`과 `REDIS_URL`은 Railway가 자동으로 설정합니다.

## 5. 포트 설정

Railway는 `PORT` 환경변수를 자동 제공합니다.

Dockerfile 수정이 필요합니다 (이미 수정됨):
```dockerfile
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
```

## 6. 배포

### 자동 배포
GitHub에 push하면 자동 배포됩니다.

### 수동 배포 (CLI)
```bash
railway up
```

## 7. 도메인 확인

배포 후 Railway Dashboard에서:
1. 앱 서비스 클릭
2. **Settings** → **Networking** → **Generate Domain**
3. `https://your-app.up.railway.app` 형태의 도메인 생성

## 8. 데이터베이스 마이그레이션

```bash
# Railway 환경에서 명령어 실행
railway run alembic upgrade head
```

또는 Dashboard에서 **Shell** 탭 사용.

## 9. 로그 확인

```bash
railway logs
```

또는 Dashboard에서 **Deployments** → 특정 배포 → **Logs**

---

## 비용

Railway 무료 티어:
- 월 $5 크레딧 (신용카드 등록 시)
- 500시간 실행 시간
- 1GB 메모리

소규모 프로젝트에는 충분합니다.

## 문제 해결

### 빌드 실패
- Dockerfile 경로 확인
- requirements.txt 확인

### 연결 실패
- `DATABASE_URL`, `REDIS_URL` 환경변수 확인
- PostgreSQL/Redis 서비스가 같은 프로젝트에 있는지 확인

### 포트 오류
- `PORT` 환경변수 사용 확인
- Railway는 임의의 포트를 할당함
