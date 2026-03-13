import pytest
import pytest_asyncio
from typing import AsyncGenerator, Optional
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database import get_db
from src import cache as cache_module
from src.models.base import Base

# здесь мы настраиваем наше тестовое окружение чтобы тестироваться по полной!

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

class MockRedis:
    def __init__(self):
        self._store: dict = {}
    async def get(self, key: str) -> Optional[str]:
        return self._store.get(key)
    async def setex(self, key: str, ttl: int, value: str) -> None:
        self._store[key] = value
    async def delete(self, key: str) -> None:
        self._store.pop(key, None)
    async def aclose(self) -> None:
        pass

@pytest.fixture
def engine():
    return create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

@pytest_asyncio.fixture
async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db(engine, create_tables) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()

@pytest.fixture
def mock_redis() -> MockRedis:
    return MockRedis()

@pytest_asyncio.fixture
async def async_client(db: AsyncSession, mock_redis: MockRedis) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    cache_module._redis_client = mock_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    cache_module._redis_client = None

@pytest_asyncio.fixture
async def registered_user(async_client: AsyncClient) -> dict:
    resp = await async_client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
    })
    assert resp.status_code == 201
    return resp.json()

@pytest_asyncio.fixture
async def auth_token(async_client: AsyncClient, registered_user: dict) -> str:
    resp = await async_client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass123",
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]

@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}
