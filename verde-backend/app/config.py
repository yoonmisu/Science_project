from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/verde_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: str = '["http://localhost:5173","http://127.0.0.1:5173"]'

    # App
    DEBUG: bool = True
    APP_NAME: str = "Verde API"
    APP_VERSION: str = "1.0.0"

    # Storage
    STORAGE_TYPE: str = "local"  # local, s3, minio
    STORAGE_BUCKET: str = "verde-images"
    LOCAL_STORAGE_PATH: str = "./uploads"

    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-northeast-2"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False

    # External APIs
    IUCN_API_KEY: str = ""  # IUCN Red List API key

    @property
    def cors_origins_list(self) -> List[str]:
        """CORS origins 파싱 - JSON 배열 또는 쉼표 구분 문자열 지원"""
        origins = self.CORS_ORIGINS.strip()

        # JSON 배열 형식인 경우
        if origins.startswith('['):
            try:
                return json.loads(origins)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 괄호 제거 후 쉼표 구분으로 처리
                origins = origins.strip('[]')

        # 쉼표 구분 문자열인 경우
        return [origin.strip().strip('"\'') for origin in origins.split(',') if origin.strip()]

    @property
    def database_url_fixed(self) -> str:
        """Railway PostgreSQL URL 호환성 처리"""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
