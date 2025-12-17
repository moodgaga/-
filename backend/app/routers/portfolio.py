from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import uuid
from pathlib import Path
from app.database import get_db
from app.models import Portfolio, User
from app.schemas import PortfolioCreate, PortfolioUpdate, PortfolioResponse, PortfolioWithOwnerResponse
from app.auth import get_current_active_user

router = APIRouter()

# Настройки для хранения файлов
# Путь относительно корня backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads" / "portfolio"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.get("/portfolio", response_model=List[PortfolioResponse])
async def get_my_portfolio(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить портфолио текущего пользователя"""
    portfolio_items = db.query(Portfolio).filter(
        Portfolio.user_id == current_user.id
    ).order_by(Portfolio.order_index, Portfolio.created_at).all()
    return portfolio_items


@router.post("/portfolio/upload-image", status_code=status.HTTP_201_CREATED)
async def upload_portfolio_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """Загрузить изображение для портфолио"""
    # Проверка расширения файла
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый формат файла. Разрешенные форматы: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Генерируем уникальное имя файла
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{file_ext}"
    file_path = UPLOAD_DIR / filename
    
    # Сохраняем файл
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Возвращаем URL для доступа к файлу
        image_url = f"/api/v1/portfolio/images/{filename}"
        return {"image_url": image_url, "filename": filename}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при загрузке файла: {str(e)}"
        )


@router.get("/portfolio/images/{filename}")
async def get_portfolio_image(filename: str):
    """Получить изображение портфолио"""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Изображение не найдено"
        )
    
    return FileResponse(file_path)


@router.post("/portfolio", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio_item(
    portfolio_data: PortfolioCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Создать новый элемент портфолио"""
    db_item = Portfolio(
        user_id=current_user.id,
        **portfolio_data.dict()
    )
    # Сохранение в базу данных
    try:
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при сохранении проекта в базу данных: {str(e)}"
        )


@router.get("/portfolio/{item_id}", response_model=PortfolioResponse)
async def get_portfolio_item(
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить элемент портфолио по ID"""
    db_item = db.query(Portfolio).filter(
        Portfolio.id == item_id,
        Portfolio.user_id == current_user.id
    ).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Элемент портфолио не найден"
        )
    return db_item


@router.put("/portfolio/{item_id}", response_model=PortfolioResponse)
async def update_portfolio_item(
    item_id: int,
    portfolio_update: PortfolioUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Обновить элемент портфолио"""
    db_item = db.query(Portfolio).filter(
        Portfolio.id == item_id,
        Portfolio.user_id == current_user.id
    ).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Элемент портфолио не найден"
        )
    
    update_data = portfolio_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    # Сохранение изменений в базу данных
    try:
        db.commit()
        db.refresh(db_item)
        return db_item
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении проекта в базе данных: {str(e)}"
        )


@router.delete("/portfolio/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_item(
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Удалить элемент портфолио"""
    db_item = db.query(Portfolio).filter(
        Portfolio.id == item_id,
        Portfolio.user_id == current_user.id
    ).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Элемент портфолио не найден"
        )
    
    # Удаляем файл изображения, если он был загружен
    if db_item.image_url and db_item.image_url.startswith("/api/v1/portfolio/images/"):
        filename = db_item.image_url.split("/")[-1]
        file_path = UPLOAD_DIR / filename
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass  # Игнорируем ошибки при удалении
    
    # Удаление из базы данных
    try:
        db.delete(db_item)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении проекта из базы данных: {str(e)}"
        )


@router.get("/portfolio/public/{item_id}", response_model=PortfolioWithOwnerResponse)
async def get_public_portfolio_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Получить публичный элемент портфолио по ID (для просмотра проектов из публичных анкет)"""
    db_item = db.query(Portfolio).join(User).filter(
        Portfolio.id == item_id,
        Portfolio.is_visible == True,
        User.is_profile_public == True,
        User.is_active == True
    ).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект портфолио не найден или не доступен для публичного просмотра"
        )
    
    # Возвращаем проект с информацией о владельце
    result = {
        "id": db_item.id,
        "user_id": db_item.user_id,
        "title": db_item.title,
        "description": db_item.description,
        "image_url": db_item.image_url,
        "project_url": db_item.project_url,
        "technologies": db_item.technologies,
        "is_visible": db_item.is_visible,
        "order_index": db_item.order_index,
        "created_at": db_item.created_at,
        "updated_at": db_item.updated_at,
        "owner_username": db_item.owner.username,
        "owner_full_name": db_item.owner.full_name
    }
    return result
