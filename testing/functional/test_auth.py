import pytest
from httpx import AsyncClient


# самый базовый тест, что человек может зарегистрироваться и данные сохраняются корректно
async def test_register_success(async_client: AsyncClient):
    resp = await async_client.post("/auth/register", json={
        "username": "michaeljackson",
        "email": "michaeljackson@example.com",
        "password": "password123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "michaeljackson"
    assert data["email"] == "michaeljackson@example.com"
    assert "id" in data


# проверим, что при регистрации с уже существующим юзернеймом или имейлом возвращается ошибка
async def test_register_duplicate_username(async_client: AsyncClient):
    payload = {"username": "sanya", "email": "sanya@example.com", "password": "pass"}
    await async_client.post("/auth/register", json=payload)
    # такой же юзернейм, но другой имейл
    resp = await async_client.post("/auth/register", json={
        "username": "sanya", "email": "sanya2@example.com", "password": "pass"
    })
    assert resp.status_code == 400


async def test_register_duplicate_email(async_client: AsyncClient):
    await async_client.post("/auth/register", json={
        "username": "прикладнойпайтон", "email": "python@example.com", "password": "pass"
    })
    resp = await async_client.post("/auth/register", json={
        "username": "прикладнойпайтон2", "email": "python@example.com", "password": "pass"
    })
    assert resp.status_code == 400


async def test_login_success(async_client: AsyncClient, registered_user: dict, auth_token: str):
    assert auth_token is not None
    assert len(auth_token) > 0

# неверные логин или пароль - это база
async def test_login_wrong_password(async_client: AsyncClient, registered_user: dict):
    resp = await async_client.post("/auth/login", json={
        "username": "testuser", "password": "wrongpass"
    })
    assert resp.status_code == 401

# let's check you, mr nobody (just like in John Wick)
async def test_login_unknown_user(async_client: AsyncClient):
    resp = await async_client.post("/auth/login", json={
        "username": "nobody", "password": "pass"
    })
    assert resp.status_code == 401

async def test_get_me(async_client: AsyncClient, registered_user: dict, auth_headers: dict):
    resp = await async_client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"

async def test_get_me_unauthenticated(async_client: AsyncClient):
    resp = await async_client.get("/auth/me")
    assert resp.status_code == 401

# проверим наше бонусное ноухау в виде любимого слова
# тикка масала это лучшее что я ел за последнее время
async def test_set_favorite_word(async_client: AsyncClient, registered_user: dict, auth_headers: dict):
    resp = await async_client.post("/auth/me/favorite-word", json={"word": "INDIANFOOD"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["favorite_word"] == "INDIANFOOD"

async def test_reset_favorite_word(async_client: AsyncClient, registered_user: dict, auth_headers: dict):
    await async_client.post("/auth/me/favorite-word", json={"word": "INDIANFOOD"}, headers=auth_headers)
    resp = await async_client.delete("/auth/me/favorite-word", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["favorite_word"] is None

# без токена нельзя ничего!
async def test_set_favorite_word_unauthenticated(async_client: AsyncClient):
    resp = await async_client.post("/auth/me/favorite-word", json={"word": "INDIANFOOD"})
    assert resp.status_code == 401