from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.database import get_db
from app.models import User, Portfolio
from app.schemas import UserResponse, UserUpdate, PublicProfileResponse, PortfolioResponse
from app.auth import get_current_active_user, get_password_hash, get_user_by_email, get_user_by_username

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Получить информацию о текущем пользователе"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Обновить информацию о текущем пользователе"""
    update_data = user_update.dict(exclude_unset=True)
    
    # Проверка уникальности email
    if "email" in update_data and update_data["email"] != current_user.email:
        existing_user = get_user_by_email(db, email=update_data["email"])
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )
    
    # Проверка уникальности username
    if "username" in update_data and update_data["username"] != current_user.username:
        existing_user = get_user_by_username(db, username=update_data["username"])
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким именем уже существует"
            )
    
    # Хеширование пароля, если он обновляется
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    # Обновление полей
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    # Сохранение изменений в базе данных
    try:
        db.commit()
        db.refresh(current_user)
        return current_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при сохранении данных в базу: {str(e)}"
        )


@router.get("/public", response_model=List[PublicProfileResponse])
async def get_public_profiles(
    db: Session = Depends(get_db)
):
    """Получить список публичных профилей пользователей с портфолио"""
    # Получаем пользователей с публичными профилями и их портфолио
    users = db.query(User).filter(
        User.is_profile_public == True,
        User.is_active == True
    ).options(
        joinedload(User.portfolio_items)
    ).all()
    
    # Формируем ответ с видимыми проектами портфолио
    result = []
    for user in users:
        # Фильтруем только видимые проекты портфолио
        visible_portfolio = [
            item for item in user.portfolio_items 
            if item.is_visible
        ]
        # Сортируем по order_index
        visible_portfolio.sort(key=lambda x: x.order_index)
        
        # Создаем объект профиля
        profile_data = {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email if user.show_email_in_profile else None,
            "telegram": user.telegram,
            "phone": user.phone,
            "portfolio_items": visible_portfolio,
            "created_at": user.created_at
        }
        result.append(profile_data)
    
    return result


@router.get("/public/{user_id}", response_model=PublicProfileResponse)
async def get_public_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Получить публичный профиль конкретного пользователя"""
    user = db.query(User).options(
        joinedload(User.portfolio_items)
    ).filter(
        User.id == user_id,
        User.is_profile_public == True,
        User.is_active == True
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Публичный профиль не найден"
        )
    
    # Фильтруем только видимые проекты портфолио
    visible_portfolio = [
        item for item in user.portfolio_items 
        if item.is_visible
    ]
    visible_portfolio.sort(key=lambda x: x.order_index)
    
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email if user.show_email_in_profile else None,
        "telegram": user.telegram,
        "phone": user.phone,
        "portfolio_items": visible_portfolio,
        "created_at": user.created_at
    }


