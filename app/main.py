import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.v1.prayer_times import router as prayer_times_router
from app.core.config import settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging(settings.debug)

    logger.info(
        "Application startup",
        extra={
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment,
        },
    )

    yield

    logger.info("Application shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "A versioned REST API for calculating Islamic prayer timings "
        "using explicit location and timezone inputs."
    ),
    lifespan=lifespan,
)


@app.get(
    "/",
    tags=["Service"],
    summary="Service information",
)
async def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


app.include_router(health_router)
app.include_router(prayer_times_router)
