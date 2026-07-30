from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import AppError, app_exception_handler, http_exception_handler, validation_exception_handler
from app.core.logging_config import configure_logging, get_logger
from app.api.routes import router as api_router
from app.database.init_db import initialize_database
from app.database.session import engine

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Application starting")
    initialize_database(engine)
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.add_exception_handler(AppError, app_exception_handler)
app.add_exception_handler(404, http_exception_handler)
app.add_exception_handler(422, validation_exception_handler)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
