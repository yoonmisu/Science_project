from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User, UserRole

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_header),
    db: Session = Depends(get_db)
) -> User:
    """
    현재 인증된 사용자를 가져옵니다.
    JWT 토큰 또는 API 키로 인증할 수 있습니다.
    """
    auth_service = AuthService(db)

    # Try JWT token first
    if token:
        token_data = auth_service.decode_token(token)
        if token_data and token_data.user_id:
            user = auth_service.get_user_by_id(token_data.user_id)
            if user and user.is_active:
                return user

    # Try API key
    if api_key:
        user = auth_service.get_user_by_api_key(api_key)
        if user and user.is_active:
            return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증이 필요합니다",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """활성 사용자만 허용"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """관리자만 허용"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user


async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_header),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    선택적 인증 - 인증되지 않아도 None 반환
    일부 API에서 로그인 여부에 따라 다른 응답을 제공할 때 사용
    """
    if not token and not api_key:
        return None

    auth_service = AuthService(db)

    if token:
        token_data = auth_service.decode_token(token)
        if token_data and token_data.user_id:
            user = auth_service.get_user_by_id(token_data.user_id)
            if user and user.is_active:
                return user

    if api_key:
        user = auth_service.get_user_by_api_key(api_key)
        if user and user.is_active:
            return user

    return None
