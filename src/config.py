from pydantic_settings import BaseSettings

# Мы настолько крутые, что у нас даже есть config.py
class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/shortlinks"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CACHE_TTL: int = 3600
    UNUSED_LINK_DAYS: int = 30
    TELEGRAM_CHANNEL: str = "https://t.me/yourchannel"
    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()