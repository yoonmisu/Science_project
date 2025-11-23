from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.database import get_db
from app.services.auth_service import AuthService
from app.dependencies import get_current_active_user, get_current_admin_user
from app.models.user import User, UserRole
from app.schemas.auth import (
    UserCreate,
    UserResponse,
    UserWithApiKey,
    Token,
    ApiKeyResponse,
    MessageResponse,
    PasswordChange
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="회원가입",
    description="새로운 사용자 계정을 생성합니다."
)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """회원가입"""
    auth_service = AuthService(db)

    # Check if email exists
    if auth_service.get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다"
        )

    # Check if username exists
    if auth_service.get_user_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 사용자명입니다"
        )

    user = auth_service.create_user(user_data)
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="로그인",
    description="이메일과 비밀번호로 로그인하여 JWT 토큰을 발급받습니다."
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """로그인 - OAuth2 Password Flow"""
    auth_service = AuthService(db)

    # Authenticate user (username field is used for email)
    user = auth_service.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다"
        )

    # Update last login
    auth_service.update_last_login(user)

    # Create tokens
    tokens = auth_service.create_tokens(user)
    logger.info(f"User logged in: {user.username}")

    return tokens


@router.post(
    "/refresh",
    response_model=Token,
    summary="토큰 갱신",
    description="Refresh 토큰을 사용하여 새로운 Access 토큰을 발급받습니다."
)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Refresh 토큰으로 새 Access 토큰 발급"""
    auth_service = AuthService(db)

    token_data = auth_service.decode_token(refresh_token)
    if not token_data or not token_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다"
        )

    user = auth_service.get_user_by_id(token_data.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다"
        )

    tokens = auth_service.create_tokens(user)
    return tokens


@router.get(
    "/me",
    response_model=UserWithApiKey,
    summary="내 정보 조회",
    description="현재 로그인한 사용자의 정보를 조회합니다."
)
async def get_me(
    current_user: User = Depends(get_current_active_user)
):
    """현재 사용자 정보 조회"""
    return current_user


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="비밀번호 변경",
    description="현재 비밀번호를 확인하고 새 비밀번호로 변경합니다."
)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """비밀번호 변경"""
    auth_service = AuthService(db)

    # Verify current password
    if not auth_service.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 올바르지 않습니다"
        )

    auth_service.change_password(current_user, password_data.new_password)

    return MessageResponse(success=True, message="비밀번호가 변경되었습니다")


# API Key Management
@router.post(
    "/api-key",
    response_model=ApiKeyResponse,
    summary="API 키 생성",
    description="현재 사용자의 API 키를 생성합니다. 기존 키가 있으면 새로 생성됩니다."
)
async def create_api_key(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """API 키 생성"""
    auth_service = AuthService(db)
    api_key = auth_service.generate_user_api_key(current_user)

    return ApiKeyResponse(
        api_key=api_key,
        created_at=current_user.api_key_created_at
    )


@router.delete(
    "/api-key",
    response_model=MessageResponse,
    summary="API 키 삭제",
    description="현재 사용자의 API 키를 삭제합니다."
)
async def revoke_api_key(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """API 키 삭제"""
    if not current_user.api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API 키가 없습니다"
        )

    auth_service = AuthService(db)
    auth_service.revoke_api_key(current_user)

    return MessageResponse(success=True, message="API 키가 삭제되었습니다")


# Admin endpoints
@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="전체 사용자 목록 (관리자)",
    description="모든 사용자 목록을 조회합니다. 관리자 권한이 필요합니다."
)
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """전체 사용자 목록 조회 (관리자용)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.patch(
    "/users/{user_id}/role",
    response_model=UserResponse,
    summary="사용자 역할 변경 (관리자)",
    description="특정 사용자의 역할을 변경합니다. 관리자 권한이 필요합니다."
)
async def update_user_role(
    user_id: int,
    role: UserRole,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """사용자 역할 변경 (관리자용)"""
    auth_service = AuthService(db)

    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )

    # Prevent self-demotion
    if user.id == current_user.id and role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자신의 관리자 권한을 해제할 수 없습니다"
        )

    auth_service.set_user_role(user, role)
    return user


@router.patch(
    "/users/{user_id}/activate",
    response_model=UserResponse,
    summary="사용자 활성화/비활성화 (관리자)",
    description="특정 사용자를 활성화 또는 비활성화합니다. 관리자 권한이 필요합니다."
)
async def toggle_user_active(
    user_id: int,
    is_active: bool,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """사용자 활성화/비활성화 (관리자용)"""
    auth_service = AuthService(db)

    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )

    # Prevent self-deactivation
    if user.id == current_user.id and not is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자신의 계정을 비활성화할 수 없습니다"
        )

    if is_active:
        auth_service.activate_user(user)
    else:
        auth_service.deactivate_user(user)

    return user
