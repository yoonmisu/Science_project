from datetime import datetime, timedelta
from typing import Optional
import secrets
import logging

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate, TokenData

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    # Password utilities
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    # Token utilities
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Optional[TokenData]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: int = payload.get("sub")
            email: str = payload.get("email")
            role: str = payload.get("role")

            if user_id is None:
                return None

            return TokenData(user_id=user_id, email=email, role=role)
        except JWTError as e:
            logger.warning(f"JWT decode error: {str(e)}")
            return None

    # API Key utilities
    @staticmethod
    def generate_api_key() -> str:
        return secrets.token_urlsafe(48)

    # User operations
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        return self.db.query(User).filter(User.api_key == api_key).first()

    def create_user(self, user_data: UserCreate) -> User:
        hashed_password = self.get_password_hash(user_data.password)

        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=UserRole.USER
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        logger.info(f"New user created: {user.username} (id={user.id})")
        return user

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    def update_last_login(self, user: User) -> None:
        user.last_login = datetime.utcnow()
        self.db.commit()

    def create_tokens(self, user: User) -> dict:
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value if isinstance(user.role, UserRole) else user.role
        }

        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def generate_user_api_key(self, user: User) -> str:
        api_key = self.generate_api_key()
        user.api_key = api_key
        user.api_key_created_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"API key generated for user: {user.username}")
        return api_key

    def revoke_api_key(self, user: User) -> None:
        user.api_key = None
        user.api_key_created_at = None
        self.db.commit()

        logger.info(f"API key revoked for user: {user.username}")

    def change_password(self, user: User, new_password: str) -> None:
        user.hashed_password = self.get_password_hash(new_password)
        self.db.commit()

        logger.info(f"Password changed for user: {user.username}")

    def set_user_role(self, user: User, role: UserRole) -> None:
        user.role = role
        self.db.commit()

        logger.info(f"Role changed for user {user.username}: {role.value}")

    def deactivate_user(self, user: User) -> None:
        user.is_active = False
        self.db.commit()

        logger.info(f"User deactivated: {user.username}")

    def activate_user(self, user: User) -> None:
        user.is_active = True
        self.db.commit()

        logger.info(f"User activated: {user.username}")
