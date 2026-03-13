from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.config import settings

# бдшки это круто, бдшки это прекрасно
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Тесты используют изолированную in-memory БД вместо продовой
# Поэтому добавим здесь pragma no cover, чтобы тесты не ругались на эту функцию
async def get_db():  # pragma: no cover
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
