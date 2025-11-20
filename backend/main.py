# /main.py

import asyncio
from contextlib import asynccontextmanager

import sqlalchemy
from sqlalchemy.exc import OperationalError
from fastapi import FastAPI
from api.api_router import api_router
from database.connection import engine
from models.base import Base # 🚨 Base 클래스 임포트

# 🚨 모든 모델 파일을 임포트하여 SQLAlchemy 메타데이터에 등록 (필수) 🚨
from models import species_model
from models import observation_model
# from models import [다른_모델_파일]...


# DB 초기화 함수
async def init_db():
    print("Initializing Database...")

    max_retries = 10
    retry_delay = 5  # 5초 간격으로 시도

    for i in range(max_retries):
        try:
            # 엔진 정의 및 연결 시도
            async with engine.begin() as conn:
                # 🚨 PostGIS 확장 프로그램 활성화 (필수)
                await conn.execute(sqlalchemy.text("CREATE EXTENSION IF NOT EXISTS postgis;"))

                # 🚨 모든 테이블 생성 (Base.metadata에 등록된 모델 기반)
                await conn.run_sync(Base.metadata.create_all)

                print("✅ Database connected and tables created successfully.")
                return  # 성공 시 함수 종료

        # 🚨🚨 모든 예외(Exception)를 포괄하여 재시도 로직 실행 🚨🚨
        except Exception as e:
            # socket.gaierror ([Errno -2])를 포함한 모든 초기 연결 오류를 처리
            if i < max_retries - 1:
                print(f"❌ Database connection failed: {e}. Retrying in {retry_delay}s... ({i + 1}/{max_retries})")
                await asyncio.sleep(retry_delay)
            else:
                # 최대 재시도 횟수 초과 시 치명적인 오류 발생
                print(f"❌ Database connection failed permanently after {max_retries} attempts.")
                raise  # 예외를 발생시켜 상위 lifespan 핸들러로 전달

# FastAPI 인스턴스 생성
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 시작 시(startup)와 종료 시(shutdown) 이벤트를 처리합니다.
    """
    print("Application Startup: Initializing Database...")

    # 🚨 시작 이벤트 처리 (yield 이전)
    try:
        # 이전에 추가한 DB 연결 재시도 로직을 포함한 함수 호출
        await init_db()
        print("Database connection successful.")
    except Exception as e:
        print(f"FATAL: Database initialization failed: {e}")
        # DB 연결 실패 시에도 애플리케이션은 일단 시작(yield)될 수 있지만,
        # 이후 엔드포인트에서 오류를 처리해야 합니다.

    yield  # <--- 여기서 애플리케이션이 요청을 받기 시작합니다.

    # 🚨 종료 이벤트 처리 (yield 이후)
    print("Application Shutdown: Cleaning up resources...")
    # 예: await close_db_pool() 또는 다른 정리 작업


# 2. FastAPI 인스턴스 생성 시 lifespan 적용
app = FastAPI(
    title="Verde FastAPI Backend",
    lifespan=lifespan  # 🚨 lifespan 핸들러 적용 🚨
)

# API 라우터 포함
app.include_router(api_router, prefix="/api")