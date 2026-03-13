import pytest
from httpx import AsyncClient

# самое важное в нашем функциональном тестировании - это проверить, что ссылки сокращаются и редирект работает
async def test_shorten_link_anonymous(async_client: AsyncClient):
    resp = await async_client.post("/links/shorten", json={"original_url": "https://ru.wikipedia.org/wiki/%D0%A1%D0%B2%D0%B8%D0%BD%D1%8B%D0%B5"})
    assert resp.status_code == 201
    data = resp.json()
    assert "short_code" in data
    assert data["original_url"] == "https://ru.wikipedia.org/wiki/%D0%A1%D0%B2%D0%B8%D0%BD%D1%8B%D0%B5"
    assert data["click_count"] == 0


async def test_shorten_link_with_custom_alias(async_client: AsyncClient):
    resp = await async_client.post("/links/shorten", json={
        "original_url": "https://ru.wikipedia.org/wiki/%D0%A1%D0%B2%D0%B8%D0%BD%D1%8B%D0%B5",
        "custom_alias": "MYNAMEISPATRICK",
    })
    assert resp.status_code == 201
    assert resp.json()["short_code"] == "MYNAMEISPATRICK"

# у меня тут прикольные слова и ссылки, потому что все делается от души!
async def test_shorten_link_duplicate_alias(async_client: AsyncClient):
    await async_client.post("/links/shorten", json={
        "original_url": "https://ru.wikipedia.org/wiki/%D0%A1%D0%B2%D0%B8%D0%BD%D1%8B%D0%B5",
        "custom_alias": "MYNAMEISPATRICK",
    })
    resp = await async_client.post("/links/shorten", json={
        "original_url": "https://github.com/AlgazinovAleksandr/short_links_generator_manager", # ну а че)
        "custom_alias": "MYNAMEISPATRICK",
    })
    assert resp.status_code == 400

# верните мне мой 2099 год
async def test_shorten_with_expiry(async_client: AsyncClient):
    resp = await async_client.post("/links/shorten", json={
        "original_url": "https://en.wikipedia.org/wiki/India",
        "expires_at": "2099-01-01T00:00:00Z",
    })
    assert resp.status_code == 201
    assert resp.json()["expires_at"] is not None


async def test_redirect(async_client: AsyncClient):
    create_resp = await async_client.post("/links/shorten", json={"original_url": "https://en.wikipedia.org/wiki/India"})
    short_code = create_resp.json()["short_code"]

    resp = await async_client.get(f"/links/{short_code}", follow_redirects=False)
    assert resp.status_code == 302
    assert "en.wikipedia.org" in resp.headers["location"]


async def test_redirect_increments_click_count(async_client: AsyncClient):
    create_resp = await async_client.post("/links/shorten", json={"original_url": "https://en.wikipedia.org/wiki/India"})
    short_code = create_resp.json()["short_code"]

    await async_client.get(f"/links/{short_code}", follow_redirects=False)
    await async_client.get(f"/links/{short_code}", follow_redirects=False)

    stats_resp = await async_client.get(f"/links/{short_code}/stats")
    assert stats_resp.json()["click_count"] == 2


async def test_redirect_not_found(async_client: AsyncClient):
    resp = await async_client.get("/links/nonexistent", follow_redirects=False)
    assert resp.status_code == 404

# по устаревшей ссылке не пройдете!
async def test_redirect_expired_link(async_client: AsyncClient):
    create_resp = await async_client.post("/links/shorten", json={
        "original_url": "https://www.python.org/",
        "expires_at": "2000-01-01T00:00:00Z",
    })
    short_code = create_resp.json()["short_code"]
    resp = await async_client.get(f"/links/{short_code}", follow_redirects=False)
    assert resp.status_code == 410

async def test_get_stats(async_client: AsyncClient):
    create_resp = await async_client.post("/links/shorten", json={"original_url": "https://www.postgresql.org/"})
    short_code = create_resp.json()["short_code"]
    resp = await async_client.get(f"/links/{short_code}/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["original_url"] == "https://www.postgresql.org/"
    assert data["short_code"] == short_code
    assert "created_at" in data


async def test_get_stats_not_found(async_client: AsyncClient):
    resp = await async_client.get("/links/notexist/stats")
    assert resp.status_code == 404

async def test_search_by_original_url(async_client: AsyncClient):
    await async_client.post("/links/shorten", json={"original_url": "https://www.postgresql.org/"})
    resp = await async_client.get("/links/search", params={"original_url": "https://www.postgresql.org/"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["original_url"] == "https://www.postgresql.org/"
    assert data["short_url"] is not None
    assert data["short_code"] in data["short_url"]

async def test_search_not_found(async_client: AsyncClient):
    resp = await async_client.get("/links/search", params={"original_url": "https://somesomenonnonexistingurllllll.com/"})
    assert resp.status_code == 404


async def test_search_expired_link(async_client: AsyncClient):
    await async_client.post("/links/shorten", json={
        "original_url": "https://www.expiredlink.com/",
        "expires_at": "2000-01-01T00:00:00Z",
    })
    resp = await async_client.get("/links/search", params={"original_url": "https://www.expiredlink.com/"})
    assert resp.status_code == 404

async def test_update_link_authenticated(async_client: AsyncClient, auth_headers: dict):
    create_resp = await async_client.post(
        "/links/shorten",
        json={"original_url": "https://alembic.sqlalchemy.org/en/notlatest/"},
        headers=auth_headers,
    )
    short_code = create_resp.json()["short_code"]

    resp = await async_client.put(
        f"/links/{short_code}",
        json={"original_url": "https://alembic.sqlalchemy.org/en/latest/"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["original_url"] == "https://alembic.sqlalchemy.org/en/latest/"
    assert data["short_url"] is not None
    assert short_code in data["short_url"]


async def test_update_link_unauthenticated(async_client: AsyncClient):
    create_resp = await async_client.post("/links/shorten", json={"original_url": "https://alembic.sqlalchemy.org/en/notlatest/"})
    short_code = create_resp.json()["short_code"]
    resp = await async_client.put(f"/links/{short_code}", json={"original_url": "https://alembic.sqlalchemy.org/en/latest/"})
    assert resp.status_code == 401

# hi
async def test_update_link_wrong_user(async_client: AsyncClient, auth_headers: dict):
    create_resp = await async_client.post("/links/shorten", json={"original_url": "https://www.docker.com/"}) # no auth headers, so it is АНОНИМНО
    short_code = create_resp.json()["short_code"]
    resp = await async_client.put(
        f"/links/{short_code}",
        json={"original_url": "https://en.wikipedia.org/wiki/Docker_(software)"},
        headers=auth_headers,
    )
    # нельзя чтобы кто попало обновлял чужие ссылки!
    assert resp.status_code == 403


async def test_delete_link_authenticated(async_client: AsyncClient, auth_headers: dict):
    create_resp = await async_client.post(
        "/links/shorten",
        json={"original_url": "https://en.wikipedia.org/wiki/Docker_(software)"},
        headers=auth_headers,
    )
    short_code = create_resp.json()["short_code"]
    resp = await async_client.delete(f"/links/{short_code}", headers=auth_headers)
    assert resp.status_code == 204
    # проверим, что ссылка действительно удалена
    get_resp = await async_client.get(f"/links/{short_code}/stats")
    assert get_resp.status_code == 404

async def test_delete_link_unauthenticated(async_client: AsyncClient):
    create_resp = await async_client.post("/links/shorten", json={"original_url": "https://d2l.ai/"})
    short_code = create_resp.json()["short_code"]
    resp = await async_client.delete(f"/links/{short_code}")
    assert resp.status_code == 401


async def test_delete_link_wrong_user(async_client: AsyncClient, auth_headers: dict):
    create_resp = await async_client.post("/links/shorten", json={"original_url": "https://d2l.ai/"})
    short_code = create_resp.json()["short_code"]
    resp = await async_client.delete(f"/links/{short_code}", headers=auth_headers)
    assert resp.status_code == 403

# Ну вот мы и подошли к нашему доп функционалу
async def test_qr_code(async_client: AsyncClient):
    create_resp = await async_client.post("/links/shorten", json={"original_url": "https://d2l.ai/"})
    short_code = create_resp.json()["short_code"]
    resp = await async_client.get(f"/links/{short_code}/qr")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"


async def test_qr_code_not_found(async_client: AsyncClient):
    resp = await async_client.get("/links/totallynonexistent/qr")
    assert resp.status_code == 404

# qr для истекшей ссылки - как мило)
async def test_qr_code_expired(async_client: AsyncClient):
    create_resp = await async_client.post("/links/shorten", json={
        "original_url": "https://www.python.org/",
        "expires_at": "2000-01-01T00:00:00Z",
    })
    short_code = create_resp.json()["short_code"]
    resp = await async_client.get(f"/links/{short_code}/qr")
    assert resp.status_code == 404

# статистика для истекшей ссылки - тоже прикольно
async def test_get_stats_expired(async_client: AsyncClient):
    create_resp = await async_client.post("/links/shorten", json={
        "original_url": "https://www.python.org/",
        "expires_at": "2000-01-01T00:00:00Z",
    })
    short_code = create_resp.json()["short_code"]
    resp = await async_client.get(f"/links/{short_code}/stats")
    assert resp.status_code == 404

async def test_update_link_not_found(async_client: AsyncClient, auth_headers: dict):
    resp = await async_client.put(
        "/links/doesnotexist",
        json={"original_url": "https://example.com"},
        headers=auth_headers,
    )
    assert resp.status_code == 404

async def test_update_link_new_short_code(async_client: AsyncClient, auth_headers: dict):
    create_resp = await async_client.post(
        "/links/shorten",
        json={"original_url": "https://fastapi.tiangolo.com/"},
        headers=auth_headers,
    )
    old_code = create_resp.json()["short_code"]
    resp = await async_client.put(
        f"/links/{old_code}",
        json={"new_short_code": "NEWCODE"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["short_code"] == "NEWCODE"
    # short_url должен отражать новый код
    assert data["short_url"] is not None
    assert "NEWCODE" in data["short_url"]
    # и по новому коду ссылка должна находиться
    stats_resp = await async_client.get("/links/NEWCODE/stats")
    assert stats_resp.status_code == 200

# вот представьте - мы вот это все тестируем, а на деле нашим сервисом никто не будет пользоваться(
async def test_delete_link_not_found(async_client: AsyncClient, auth_headers: dict):
    resp = await async_client.delete("/links/doesnotexist", headers=auth_headers)
    assert resp.status_code == 404

async def test_shorten_with_favorite_word(async_client: AsyncClient, auth_headers: dict):
    await async_client.post("/auth/me/favorite-word", json={"word": "PIZZA"}, headers=auth_headers) # I love pizza
    resp = await async_client.post(
        "/links/shorten",
        json={"original_url": "https://dodopizza.ru/moscow"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["short_code"].startswith("PIZZA")

async def test_redirect_cache_hit(async_client: AsyncClient):
    create_resp = await async_client.post("/links/shorten", json={"original_url": "https://redis.io/"})
    short_code = create_resp.json()["short_code"]
    # первый запрос — cache miss, второй — cache hit
    await async_client.get(f"/links/{short_code}", follow_redirects=False)
    resp = await async_client.get(f"/links/{short_code}", follow_redirects=False)
    assert resp.status_code == 302
    assert "redis.io" in resp.headers["location"]
