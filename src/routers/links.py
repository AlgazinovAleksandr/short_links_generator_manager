# В этом файле делается основной функционал проекта - непосредственное сокращение ссылок. Настоящая магия, настоящее искусство!
# Самая важная часть проекта

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from fastapi.responses import StreamingResponse
import qrcode
import io

from src.database import get_db
from src.models.link import Link
from src.models.user import User
from src.schemas.link import LinkCreate, LinkUpdate, LinkResponse, LinkStats
from src.services.link_service import (
    create_unique_short_code, get_link_by_short_code,
    get_link_by_original_url, is_link_expired,
    apply_favorite_word, compute_cache_ttl,
)
from src.cache import cache_link, get_cached_link, delete_cached_link
from src.config import settings
from src.routers.auth import get_current_user_optional, get_current_user_required

router = APIRouter(prefix="/links", tags=["links"])

def print_something_funny():
    print("Вот шутка: Почему программисты не любят природу? Потому что там слишком много багов!")
    print("Ну а что вы хотели я сижу уже три дня это пишу скоро будет и не такое")

@router.post("/shorten", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def shorten_link(
    payload: LinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if payload.custom_alias:
        existing = await get_link_by_short_code(db, payload.custom_alias)
        if existing:
            raise HTTPException(status_code=400, detail="Где-то мы уже такое видели...")
        short_code = payload.custom_alias
    else:
        short_code = await create_unique_short_code(db)
        if current_user and current_user.favorite_word:
            short_code = current_user.favorite_word + short_code

    link = Link(
        original_url=str(payload.original_url),
        short_code=short_code,
        user_id=current_user.id if current_user else None,
        expires_at=payload.expires_at,
    )

    db.add(link)
    await db.flush()
    await db.refresh(link)
    ttl = compute_cache_ttl(link, settings.CACHE_TTL)
    await cache_link(short_code, str(payload.original_url), ttl)
    return link

@router.get("/search", response_model=LinkResponse)
async def search_by_original_url(
    original_url: str,
    db: AsyncSession = Depends(get_db),
):
    link = await get_link_by_original_url(db, original_url)
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    if is_link_expired(link):
        await db.delete(link)
        raise HTTPException(status_code=404, detail="Вышел срок годности ссылки")
    return link

@router.get("/{short_code}/stats", response_model=LinkStats)
async def get_stats(short_code: str, db: AsyncSession = Depends(get_db)):
    link = await get_link_by_short_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    if is_link_expired(link):
        await db.delete(link)
        raise HTTPException(status_code=404, detail="Вышел срок годности ссылки")
    return link

@router.get("/{short_code}/qr")
async def get_qr_code(short_code: str, db: AsyncSession = Depends(get_db)):
    """Генерируем QR-код для ссылки потому что QR-коды это круто QR-коды это классно"""
    link = await get_link_by_short_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    if is_link_expired(link):
        raise HTTPException(status_code=404, detail="Вышел срок годности ссылки")
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(link.original_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

# Hi
@router.get("/{short_code}", description="Не тестируй этот метод через UI (метод нужен чисто для внутреннего пользования!)")
async def redirect_to_url(short_code: str, db: AsyncSession = Depends(get_db)):
    cached_url = await get_cached_link(short_code)
    if cached_url:
        link = await get_link_by_short_code(db, short_code)
        if link is None:
            await delete_cached_link(short_code)
            raise HTTPException(status_code=404, detail="Ссылка не найдена")
        if is_link_expired(link):
            await db.delete(link)
            await delete_cached_link(short_code)
            raise HTTPException(status_code=410, detail="Вышел срок годности ссылки")
        link.click_count += 1
        link.last_accessed_at = datetime.now(timezone.utc)
        db.add(link)
        redirect_url = cached_url
    else:
        link = await get_link_by_short_code(db, short_code)
        if not link:
            raise HTTPException(status_code=404, detail="Ссылка не найдена")
        if is_link_expired(link):
            await db.delete(link)
            raise HTTPException(status_code=410, detail="Вышел срок годности ссылки")
        link.click_count += 1
        link.last_accessed_at = datetime.now(timezone.utc)
        db.add(link)
        redirect_url = link.original_url
        ttl = compute_cache_ttl(link, settings.CACHE_TTL)
        await cache_link(short_code, redirect_url, ttl)

    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


@router.put("/{short_code}", response_model=LinkResponse)
async def update_link(
    short_code: str,
    payload: LinkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    link = await get_link_by_short_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    if link.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Для модификации этой ссылки нужно быть ее создателем!")
    if payload.original_url:
        link.original_url = str(payload.original_url)
    if payload.new_short_code:
        conflict = await get_link_by_short_code(db, payload.new_short_code)
        if conflict and conflict.id != link.id:
            raise HTTPException(status_code=400, detail="Такой короткий код ссылуи уже занят!")
        old_code = link.short_code
        link.short_code = payload.new_short_code
        await delete_cached_link(old_code)
    db.add(link)
    await db.flush()
    await delete_cached_link(short_code)
    ttl = compute_cache_ttl(link, settings.CACHE_TTL)
    await cache_link(link.short_code, link.original_url, ttl)
    await db.refresh(link)
    return link

@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    link = await get_link_by_short_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    if link.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Для удаления этой ссылки нужно быть ее создателем!")
    await delete_cached_link(short_code)
    await db.delete(link)
