# этот файл - это по сути начало) Через этот МЕХАНИЗМ пользователь регистрируется, получается месседж если он уже зарегистрирован
# а также именно тут он устанавливает любимое слово (фишечка на бонусы), please check readme for more info OH YEAH ;)

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from src.database import get_db
from src.models.user import User
from src.schemas.user import UserCreate, UserResponse, Token, LoginRequest, FavoriteWordRequest
from src.services.auth_service import (
    hash_password, authenticate_user, create_access_token,
    decode_token, get_user_by_username
)
from src.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
_security = HTTPBearer(auto_error=False)

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if credentials is None:
        return None
    username = decode_token(credentials.credentials)
    if username is None:
        return None
    return await get_user_by_username(db, username)

async def get_current_user_required(
    user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    if user is None:
        print('Ничего не найдено(')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_username(db, payload.username)
    if existing:
        raise HTTPException(status_code=400, detail="А вот этот юзернейм уже занят тобой или кем-то другим, так что выбери другой")
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Такой имейл уже кем-то зарегистрирован")
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user

@router.post("/login", response_model=Token)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.username})
    return Token(access_token=token)

@router.get("/me", response_model=UserResponse)

async def get_me(current_user: User = Depends(get_current_user_required)):
    return current_user

async def say_hi(current_user: User = Depends(get_current_user_required)):
    return {"message": f"Привлет, мой дорогой друг {current_user.username}! Желаю тебе хорошего дня!"}

@router.post("/me/favorite-word", response_model=UserResponse)
async def set_favorite_word(
    payload: FavoriteWordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    # ох уж эти любимые слова, как это мило
    current_user.favorite_word = payload.word
    db.add(current_user)
    await db.flush()
    await db.refresh(current_user)
    return current_user


@router.delete("/me/favorite-word", response_model=UserResponse)
async def reset_favorite_word(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    # эти слова так быстро надоедают...
    current_user.favorite_word = None
    db.add(current_user)
    await db.flush()
    await db.refresh(current_user)
    return current_user
