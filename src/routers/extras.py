# бонусы сами себя не поставят, а бонусный функционал сам себя не напишет, собственно вот для этого существует этот файл

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from src.services.joke_service import get_random_joke
from src.config import settings

router = APIRouter(prefix="/extras", tags=["extras"])

# I wonder if you know what this URL is...
# I wonder if you know how we live in Tokyo (actually I've been living in Beijing only)
RICKROLL_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

@router.get("/joke")
async def joke():
    """Анекдот из моей шикарной коллекции выдает по запросу"""
    return {"joke": get_random_joke()}


@router.get("/self-promotion")
async def self_promotion():
    """А вот это вообще самая полезная функция я вообще не знаю как проект мог существовать без нее ОНА МНЕ НУЖНА Я БЕЗ НЕЕ НИКУДА"""
    return {
        "message": "Подпишись на мой канал я стараюсь постить годный контент :)!",
        "channel": settings.TELEGRAM_CHANNEL,
    }


@router.get("/secret-url")
async def secret_url():
    """Что же это?"""
    return RedirectResponse(url=RICKROLL_URL, status_code=302)
