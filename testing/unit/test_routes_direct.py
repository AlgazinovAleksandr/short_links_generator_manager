import pytest
import src.cache as cache_module
from unittest.mock import MagicMock
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from src.routers.auth import register, login, set_favorite_word, reset_favorite_word
from src.routers.links import (
    shorten_link, search_by_original_url, get_stats, get_qr_code,
    redirect_to_url, update_link, delete_link,
)
from src.schemas.user import UserCreate, LoginRequest, FavoriteWordRequest
from src.schemas.link import LinkCreate, LinkUpdate
from src.cache import delete_cached_link


def make_request(base_url="http://test/"):
    req = MagicMock()
    req.base_url = base_url
    return req

# дожили даже до того, что используем MockRedis
@pytest.fixture
def redis_setup(mock_redis):
    cache_module._redis_client = mock_redis
    yield mock_redis
    cache_module._redis_client = None


# а теперь покроем тестами вообще все что только возможно (регистрации, ссылки, qr-коды, и так далее)
async def test_register_route_direct(db: AsyncSession):
    result = await register(UserCreate(username="hsestudent", email="hsestudent@example.com", password="iimagatop"), db)
    assert result.username == "hsestudent"

async def test_register_duplicate_username_route_direct(db: AsyncSession):
    await register(UserCreate(username="dup_name", email="dup1@example.com", password="aaaaaaaaaaaaaaaaaaaaaaaaaaaa"), db)
    with pytest.raises(HTTPException) as exc:
        await register(UserCreate(username="dup_name", email="dup2@example.com", password="aaaaaaaaaaaaaaaaaaaaaaaaaaaa"), db)
    assert exc.value.status_code == 400

async def test_register_duplicate_email_route_direct(db: AsyncSession):
    await register(UserCreate(username="helpme1", email="helpme@example.com", password="pass"), db)
    with pytest.raises(HTTPException) as exc:
        await register(UserCreate(username="helpme2", email="helpme@example.com", password="pass"), db)
    assert exc.value.status_code == 400

async def test_login_route_direct(db: AsyncSession):
    await register(UserCreate(username="kreativnayaindustria", email="kreativnays@example.com", password="YAKREATIVNAYA"), db)
    result = await login(LoginRequest(username="kreativnayaindustria", password="YAKREATIVNAYA"), db)
    assert result.access_token

async def test_login_wrong_password_route_direct(db: AsyncSession):
    await register(UserCreate(username="californiadreaming", email="antheskyisgrey@example.com", password="antheskyisgrey"), db)
    with pytest.raises(HTTPException) as exc:
        await login(LoginRequest(username="californiadreaming", password="wrong"), db)
    assert exc.value.status_code == 401

# чувствую себя прям тестировщиком (то бэкендер то тестировщик что же будет дальше надеюсь андроид-разработкой не заставят заниматься)
async def test_set_favorite_word_route_direct(db: AsyncSession):
    user = await register(UserCreate(username="everybodylovescats", email="cat@example.com", password="andeverybodywannabeasuperstar"), db)
    result = await set_favorite_word(FavoriteWordRequest(word="CATS"), db, user)
    assert result.favorite_word == "CATS"


async def test_reset_favorite_word_route_direct(db: AsyncSession):
    user = await register(UserCreate(username="SNOOP", email="snoop@example.com", password="pass"), db)
    await set_favorite_word(FavoriteWordRequest(word="DOGS"), db, user)
    result = await reset_favorite_word(db, user)
    assert result.favorite_word is None

# hello, how are you doing my dear friend?
async def test_shorten_link_route_direct(db: AsyncSession, redis_setup):
    result = await shorten_link(LinkCreate(original_url="https://ru.wikipedia.org/wiki/%D0%A1%D0%B2%D0%B8%D0%BD%D1%8B%D0%B5"), make_request(), db, None)
    assert result.short_url is not None
    assert result.short_code in result.short_url


async def test_shorten_link_custom_alias_route_direct(db: AsyncSession, redis_setup):
    result = await shorten_link(
        LinkCreate(original_url="https://en.wikipedia.org/wiki/India", custom_alias="tikkamasala"), # it is my alias ya ego em!
        make_request(), db, None,
    )
    assert result.short_code == "tikkamasala"


async def test_shorten_link_custom_alias_conflict_route_direct(db: AsyncSession, redis_setup):
    await shorten_link(LinkCreate(original_url="https://www.python.org/", custom_alias="CLASH"), make_request(), db, None) # I used to play clash of clans when I was a kid
    with pytest.raises(HTTPException) as exc:
        await shorten_link(LinkCreate(original_url="https://github.com/AlgazinovAleksandr/short_links_generator_manager", custom_alias="CLASH"), make_request(), db, None)
    assert exc.value.status_code == 400


async def test_search_route_direct(db: AsyncSession, redis_setup):
    await shorten_link(LinkCreate(original_url="https://www.postgresql.org/"), make_request(), db, None)
    result = await search_by_original_url("https://www.postgresql.org/", make_request(), db)
    assert result.original_url == "https://www.postgresql.org/"


async def test_search_not_found_route_direct(db: AsyncSession):
    with pytest.raises(HTTPException) as exc:
        await search_by_original_url("https://somesomenonnonexistingurllllll.com/", make_request(), db)
    assert exc.value.status_code == 404


async def test_search_expired_route_direct(db: AsyncSession, redis_setup):
    await shorten_link(
        LinkCreate(original_url="https://www.expiredlink.com/", expires_at=datetime(2000, 1, 1, tzinfo=timezone.utc)),
        make_request(), db, None,
    )
    with pytest.raises(HTTPException) as exc:
        await search_by_original_url("https://www.expiredlink.com/", make_request(), db)
    assert exc.value.status_code == 404


async def test_get_stats_route_direct(db: AsyncSession, redis_setup):
    link = await shorten_link(LinkCreate(original_url="https://www.postgresql.org/"), make_request(), db, None)
    result = await get_stats(link.short_code, db)
    assert result.short_code == link.short_code


async def test_get_stats_not_found_route_direct(db: AsyncSession):
    with pytest.raises(HTTPException) as exc:
        await get_stats("notexist", db)
    assert exc.value.status_code == 404


async def test_get_stats_expired_route_direct(db: AsyncSession, redis_setup):
    link = await shorten_link(
        LinkCreate(original_url="https://www.python.org/", expires_at=datetime(2000, 1, 1, tzinfo=timezone.utc)),
        make_request(), db, None,
    )
    with pytest.raises(HTTPException) as exc:
        await get_stats(link.short_code, db)
    assert exc.value.status_code == 404

# really like this dive into deep learning book
# а вот мы и до моих любимых qr-кодов дошли ура ура ура ура ура ура ура ура ура ура ура
async def test_get_qr_code_route_direct(db: AsyncSession, redis_setup):
    link = await shorten_link(LinkCreate(original_url="https://d2l.ai/"), make_request(), db, None)
    result = await get_qr_code(link.short_code, db)
    assert result.media_type == "image/png"


async def test_get_qr_code_not_found_route_direct(db: AsyncSession):
    with pytest.raises(HTTPException) as exc:
        await get_qr_code("notexist", db)
    assert exc.value.status_code == 404


async def test_get_qr_code_expired_route_direct(db: AsyncSession, redis_setup):
    link = await shorten_link(
        LinkCreate(original_url="https://www.python.org/", expires_at=datetime(2000, 1, 1, tzinfo=timezone.utc)),
        make_request(), db, None,
    )
    with pytest.raises(HTTPException) as exc:
        await get_qr_code(link.short_code, db)
    assert exc.value.status_code == 404

# давайте теперь пройдемся по кэшированиям
async def test_redirect_no_cache_route_direct(db: AsyncSession, redis_setup):
    link = await shorten_link(LinkCreate(original_url="https://en.wikipedia.org/wiki/India"), make_request(), db, None)
    await delete_cached_link(link.short_code)
    result = await redirect_to_url(link.short_code, db)
    assert result.status_code == 302


async def test_redirect_cache_hit_route_direct(db: AsyncSession, redis_setup):
    link = await shorten_link(LinkCreate(original_url="https://redis.io/"), make_request(), db, None)
    result = await redirect_to_url(link.short_code, db)
    assert result.status_code == 302


async def test_redirect_not_found_route_direct(db: AsyncSession, redis_setup):
    with pytest.raises(HTTPException) as exc:
        await redirect_to_url("totnotfound", db)
    assert exc.value.status_code == 404


async def test_redirect_expired_no_cache_route_direct(db: AsyncSession, redis_setup):
    link = await shorten_link(
        LinkCreate(original_url="https://www.python.org/", expires_at=datetime(2000, 1, 1, tzinfo=timezone.utc)),
        make_request(), db, None,
    )
    await delete_cached_link(link.short_code)
    with pytest.raises(HTTPException) as exc:
        await redirect_to_url(link.short_code, db)
    assert exc.value.status_code == 410

# в этот раз Майкл Джексон в следующий раз будет Michael Jordan
async def test_update_link_route_direct(db: AsyncSession, redis_setup):
    user = await register(UserCreate(username="michaeljackson", email="michaeljackson@example.com", password="pass"), db)
    link = await shorten_link(LinkCreate(original_url="https://alembic.sqlalchemy.org/en/notlatest/"), make_request(), db, user)
    result = await update_link(link.short_code, LinkUpdate(original_url="https://alembic.sqlalchemy.org/en/latest/"), make_request(), db, user)
    assert result.original_url == "https://new.test.com"


async def test_update_link_new_code_route_direct(db: AsyncSession, redis_setup):
    user = await register(UserCreate(username="прикладнойпайтон", email="python@example.com", password="pass"), db)
    link = await shorten_link(LinkCreate(original_url="https://fastapi.tiangolo.com/"), make_request(), db, user)
    result = await update_link(link.short_code, LinkUpdate(new_short_code="newshortcoe"), make_request(), db, user)
    assert result.short_code == "newshortcoe"


async def test_update_link_code_conflict_route_direct(db: AsyncSession, redis_setup):
    user = await register(UserCreate(username="sanya", email="sanya@example.com", password="pass"), db)
    await shorten_link(LinkCreate(original_url="https://www.docker.com/", custom_alias="TAKEN"), make_request(), db, user)
    link2 = await shorten_link(LinkCreate(original_url="https://d2l.ai/"), make_request(), db, user)
    with pytest.raises(HTTPException) as exc:
        await update_link(link2.short_code, LinkUpdate(new_short_code="TAKEN"), make_request(), db, user)
    assert exc.value.status_code == 400


async def test_update_link_not_found_route_direct(db: AsyncSession, redis_setup):
    user = await register(UserCreate(username="nobody", email="nobody@example.com", password="pass"), db)
    with pytest.raises(HTTPException) as exc:
        await update_link("notexist", LinkUpdate(original_url="https://example.com"), make_request(), db, user)
    assert exc.value.status_code == 404

# оставлять ссылку на докер - это база
async def test_update_link_wrong_user_route_direct(db: AsyncSession, redis_setup):
    user1 = await register(UserCreate(username="michaeljackson", email="michaeljackson@example.com", password="pass"), db)
    user2 = await register(UserCreate(username="прикладнойпайтон", email="python@example.com", password="pass"), db)
    link = await shorten_link(LinkCreate(original_url="https://www.docker.com/"), make_request(), db, user1)
    with pytest.raises(HTTPException) as exc:
        await update_link(link.short_code, LinkUpdate(original_url="https://en.wikipedia.org/wiki/Docker_(software)"), make_request(), db, user2)
    assert exc.value.status_code == 403


async def test_delete_link_route_direct(db: AsyncSession, redis_setup):
    user = await register(UserCreate(username="прикладнойпайтон", email="python@example.com", password="pass"), db)
    link = await shorten_link(LinkCreate(original_url="https://en.wikipedia.org/wiki/Docker_(software)"), make_request(), db, user)
    await delete_link(link.short_code, db, user)
    with pytest.raises(HTTPException) as exc:
        await get_stats(link.short_code, db)
    assert exc.value.status_code == 404

# если честно это достаточно мягко скажем рутинное задание
async def test_delete_link_not_found_route_direct(db: AsyncSession, redis_setup):
    user = await register(UserCreate(username="nobody", email="nobody@example.com", password="pass"), db)
    with pytest.raises(HTTPException) as exc:
        await delete_link("notexist", db, user)
    assert exc.value.status_code == 404

# каких только тестов не напишешь ради высокого coverage rate
async def test_delete_link_wrong_user_route_direct(db: AsyncSession, redis_setup):
    user1 = await register(UserCreate(username="michaeljackson", email="michaeljackson@example.com", password="pass"), db)
    user2 = await register(UserCreate(username="sanya", email="sanya@example.com", password="pass"), db)
    link = await shorten_link(LinkCreate(original_url="https://d2l.ai/"), make_request(), db, user1)
    with pytest.raises(HTTPException) as exc:
        await delete_link(link.short_code, db, user2)
    assert exc.value.status_code == 403
