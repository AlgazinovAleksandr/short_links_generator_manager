import pytest
import uuid
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.link_service import generate_short_code, SHORT_CODE_LENGTH, ALPHABET, apply_favorite_word, is_link_expired, compute_cache_ttl, create_unique_short_code, get_link_by_short_code, get_link_by_original_url
from src.models.link import Link
from src.models.base import GUID
from datetime import datetime, timezone, timedelta


def test_short_code_length():
    code = generate_short_code()
    assert len(code) == SHORT_CODE_LENGTH

def test_short_code_characters():
    for _ in range(100):
        code = generate_short_code()
        for char in code:
            assert char in ALPHABET

def test_short_code_uniqueness():
    codes = {generate_short_code() for _ in range(1000)}
    assert len(codes) > 990

def test_apply_favorite_word_prepends_to_domain():
    result = apply_favorite_word("https://google.com/search?q=test", "IAMABIRDICANFLY")
    assert result == "https://IAMABIRDICANFLYgoogle.com/search?q=test"


def test_apply_favorite_word_http():
    result = apply_favorite_word("http://example.com", "INEEDTOFEEDMYBIRDBABIES")
    assert result == "http://INEEDTOFEEDMYBIRDBABIESexample.com"


def test_is_link_expired_no_expiry():
    link = Link(original_url="https://example.com", short_code="python")
    link.expires_at = None
    assert is_link_expired(link) is False


def test_is_link_expired_future():
    link = Link(original_url="https://example.com", short_code="sanya")
    link.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    assert is_link_expired(link) is False

# ох уж эти тесты на сроки годности с одной секундой
# это я еще молчу про то что происходит когда тестировщик заходит в бар...
def test_is_link_expired_past():
    link = Link(original_url="https://example.com", short_code="sanya")
    link.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert is_link_expired(link) is True

# заказывает 0 пива, 9999999999 пива, -1 пиво, 1.5 пива, "пиво" пива
def test_compute_cache_ttl_no_expiry():
    link = Link(original_url="https://example.com", short_code="sanya")
    link.expires_at = None
    assert compute_cache_ttl(link, 3600) == 3600

# тесты пройдены успешно, а потом выясняется, что ...
def test_compute_cache_ttl_expiry_sooner():
    link = Link(original_url="https://example.com", short_code="sanya")
    link.expires_at = datetime.now(timezone.utc) + timedelta(seconds=100)
    ttl = compute_cache_ttl(link, 3600)
    assert 95 <= ttl <= 100

# внезапно пришел человек и заказал СИДР. И все...
def test_compute_cache_ttl_default_sooner():
    link = Link(original_url="https://example.com", short_code="sanya")
    link.expires_at = datetime.now(timezone.utc) + timedelta(hours=2)
    ttl = compute_cache_ttl(link, 3600)
    assert ttl == 3600

# а потом еще и спросил, где туалет!
