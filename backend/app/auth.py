from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
import os
from dotenv import load_dotenv

load_dotenv()

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    default="argon2",  # Argon2 
    deprecated="auto"
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    try:
        # Argon2 и bcrypt 
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError as e:

        if "password cannot be longer than 72 bytes" in str(e):
            return False
        raise


def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    # Argon2
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создание JWT токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Получить пользователя по email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Получить пользователя по username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_username_or_email(db: Session, identifier: str) -> Optional[User]:
    """Получить пользователя по username или email"""
    user = db.query(User).filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Аутентификация пользователя (поддерживает вход по username или email)"""
    try:
        # Ищем пользователя по username или email
        user = get_user_by_username_or_email(db, username)
        if not user:
            return None
        
        # Проверка пароля с обработкой ошибок
        try:
            if not verify_password(password, user.hashed_password):
                return None
        except ValueError as e:
            # Обработка ошибки bcrypt для длинных паролей
            if "password cannot be longer than 72 bytes" in str(e):
                # Если пароль слишком длинный для bcrypt, он неверный
                # (новые пароли используют Argon2, который не имеет ограничений)
                return None
            # Логи  ошибки проверки пароля
            print(f"Ошибка при проверке пароля: {e}")
            return None
        except Exception as e:
            # Логи ошибки проверки пароля
            print(f"Ошибка при проверке пароля: {e}")
            return None
        
        return user
    except Exception as e:
        print(f"Ошибка при аутентификации: {e}")
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Получить текущего пользователя из токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Получить активного пользователя"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Неактивный пользователь")
    return current_user
