from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationError
from datetime import datetime
from typing import Optional, List


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    telegram: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=1, description="Пароль")


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    telegram: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    is_profile_public: Optional[bool] = None
    show_email_in_profile: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_profile_public: bool
    show_email_in_profile: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# Portfolio Schemas
class PortfolioBase(BaseModel):
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    project_url: Optional[str] = None
    technologies: Optional[str] = None
    is_visible: bool = True
    order_index: int = 0


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    project_url: Optional[str] = None
    technologies: Optional[str] = None
    is_visible: Optional[bool] = None
    order_index: Optional[int] = None


class PortfolioResponse(PortfolioBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PortfolioWithOwnerResponse(PortfolioResponse):
    """Схема для проекта портфолио с информацией о владельце"""
    owner_username: Optional[str] = None
    owner_full_name: Optional[str] = None

    class Config:
        from_attributes = True


class PublicProfileResponse(BaseModel):
    """Схема для публичного профиля пользователя"""
    id: int
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    telegram: Optional[str] = None
    phone: Optional[str] = None
    portfolio_items: List[PortfolioResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


# Item Schemas (existing)
class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_active: bool = True


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ItemResponse(ItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
