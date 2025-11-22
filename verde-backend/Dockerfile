# =============================================================================
# Verde Backend - Production Dockerfile
# Multi-stage build with security best practices
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

# 빌드 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 가상환경 생성
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Production
# -----------------------------------------------------------------------------
FROM python:3.11-slim as production

# 메타데이터
LABEL maintainer="Verde Team"
LABEL description="Verde Biodiversity Platform API"
LABEL version="1.0.0"

# 보안: 비root 사용자 생성
RUN groupadd -r verde && useradd -r -g verde verde

# 런타임 의존성만 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 가상환경 복사
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 작업 디렉토리 설정
WORKDIR /app

# 애플리케이션 코드 복사
COPY --chown=verde:verde . .

# 보안: 비root 사용자로 전환
USER verde

# 환경변수
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 헬스체크 (Railway는 자체 healthcheck 사용, PORT 환경변수 지원)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# 포트 노출 (Railway는 PORT 환경변수 사용)
# EXPOSE는 문서화 목적, 실제 포트는 PORT 환경변수로 결정

# 실행 명령 (Railway는 PORT 환경변수 사용)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
