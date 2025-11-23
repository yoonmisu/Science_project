import os
import sys
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime

from app.config import settings


def setup_logging():
    """구조화된 로깅 설정"""
    # 로그 디렉토리 생성
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # 로그 레벨 설정
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # 포맷 설정
    detailed_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    simple_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    json_format = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", '
        '"function": "%(funcName)s", "line": %(lineno)d, "message": "%(message)s"}',
        datefmt="%Y-%m-%dT%H:%M:%S"
    )

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 1. 콘솔 핸들러 (개발용)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_format)
    root_logger.addHandler(console_handler)

    # 2. 전체 로그 파일 (일별 로테이션)
    all_handler = TimedRotatingFileHandler(
        filename=f"{log_dir}/verde.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    all_handler.setLevel(logging.DEBUG)
    all_handler.setFormatter(detailed_format)
    root_logger.addHandler(all_handler)

    # 3. 에러 로그 파일 (크기 기반 로테이션)
    error_handler = RotatingFileHandler(
        filename=f"{log_dir}/error.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_format)
    root_logger.addHandler(error_handler)

    # 4. 액세스 로그 파일
    access_logger = logging.getLogger("access")
    access_handler = TimedRotatingFileHandler(
        filename=f"{log_dir}/access.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(simple_format)
    access_logger.addHandler(access_handler)
    access_logger.propagate = False

    # 5. 보안 로그 파일
    security_logger = logging.getLogger("security")
    security_handler = RotatingFileHandler(
        filename=f"{log_dir}/security.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=20,
        encoding="utf-8"
    )
    security_handler.setLevel(logging.INFO)
    security_handler.setFormatter(detailed_format)
    security_logger.addHandler(security_handler)
    security_logger.propagate = False

    # 6. JSON 로그 (프로덕션 분석용)
    if not settings.DEBUG:
        json_handler = RotatingFileHandler(
            filename=f"{log_dir}/verde.json.log",
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=5,
            encoding="utf-8"
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(json_format)
        root_logger.addHandler(json_handler)

    # 특정 라이브러리 로깅 레벨 조정
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)

    logging.info("Logging configured successfully")
    return root_logger


# 보안 이벤트 로깅 헬퍼
def log_security_event(event_type: str, user_id: int = None, details: dict = None):
    """보안 관련 이벤트 로깅"""
    security_logger = logging.getLogger("security")
    message = f"[{event_type}] user_id={user_id} | {details}"
    security_logger.info(message)


# 액세스 로깅 헬퍼
def log_access(method: str, path: str, status: int, duration: float, user_id: int = None):
    """API 액세스 로깅"""
    access_logger = logging.getLogger("access")
    message = f"{method} {path} {status} {duration:.3f}s user_id={user_id}"
    access_logger.info(message)


class RequestLoggingMiddleware:
    """요청/응답 로깅 미들웨어"""

    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger("access")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = datetime.utcnow()

        # 응답 상태 캡처를 위한 래퍼
        status_code = 500
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # 로깅
            duration = (datetime.utcnow() - start_time).total_seconds()
            method = scope.get("method", "")
            path = scope.get("path", "")

            self.logger.info(f"{method} {path} {status_code} {duration:.3f}s")
