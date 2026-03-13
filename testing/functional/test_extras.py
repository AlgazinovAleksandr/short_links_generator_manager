import pytest
from httpx import AsyncClient

# Ссылки сокращать - это прекрасно, но иногда хочется просто посмеяться
async def test_joke_returns_string(async_client: AsyncClient):
    resp = await async_client.get("/extras/joke")
    assert resp.status_code == 200
    data = resp.json()
    assert "joke" in data
    assert isinstance(data["joke"], str)
    assert len(data["joke"]) > 0
    # hahahahahahahhaha the best joke I've ever heard in my life

async def test_self_promotion(async_client: AsyncClient):
    resp = await async_client.get("/extras/self-promotion")
    assert resp.status_code == 200
    data = resp.json()
    assert "channel" in data
    assert "message" in data
    # Such a wonderful channel

async def test_secret_url_redirects(async_client: AsyncClient):
    resp = await async_client.get("/extras/secret-url")
    assert resp.status_code == 200
    data = resp.json()
    assert "url" in data
    assert "youtube" in data["url"] or "youtu" in data["url"] # так как юрл - это ссылка на видео на ютубе, то в данном тесте проверим, что так и есть
    # Of course this is not a Rickroll

async def test_root_endpoint(async_client: AsyncClient):
    resp = await async_client.get("/")
    assert resp.status_code == 200
    assert "message" in resp.json()
