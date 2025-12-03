import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "Verde API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database (SQLite for development)
    DATABASE_URL: str = "sqlite:///./verde.db"

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "verde_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    SECRET_KEY: str = "dev-secret-key"
    # 환경 변수에서 키를 찾고, 없으면 기본 테스트 키 사용
    IUCN_API_KEY: str = os.getenv("IUCN_API_KEY") or os.getenv("VITE_IUCN_API_KEY") or "9bb4facb6d23f48efbf424bb05c0c1ef1cf6f468393bc745d42179ac4aca5fee"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env


settings = Settings()
