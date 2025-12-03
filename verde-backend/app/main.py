from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.database import init_db

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION, debug=settings.DEBUG)

# 데이터베이스 초기화
@app.on_event("startup")
async def startup_event():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    return {"message": "Verde API is running"}

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def detailed_health():
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.VERSION}
