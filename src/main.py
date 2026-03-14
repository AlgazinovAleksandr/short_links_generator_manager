from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.routers import auth, links, extras

# pragma: no cover, так как код после yield выполняется только при завершении работы приложения (shutdown)
# А в тестах приложение не останавливается штатно, поэтому тесты не покрывают этот код
@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover
    yield
    from src import cache as cache_module
    if cache_module._redis_client is not None:
        await cache_module._redis_client.aclose()

app = FastAPI(
    title="Let's generate some short links!",
    description="URL shortener service that is very, very cool!",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(auth.router)
app.include_router(links.router)
app.include_router(extras.router)

@app.get("/", tags=["root"])
async def root():
    return {"message": "Everything is running (finally). See /docs for documentation"}
