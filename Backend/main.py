"""
Manga/Webtoon Translation Backend
FastAPI application entry point
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.routes import translate, status, download, health
from app.core.config import settings
from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    logger.info("🚀 Starting Manga Translator Backend...")
    logger.info(f"OCR Engine: {settings.OCR_ENGINE}")
    logger.info(f"Translation Engine: {settings.TRANSLATION_ENGINE}")
    yield
    logger.info("🛑 Shutting down Manga Translator Backend...")


app = FastAPI(
    title="Manga/Webtoon Translator API",
    description="Backend IA pour la traduction automatique de bandes dessinées et webtoons",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middlewares ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── Routes ───────────────────────────────────────────────────────────────────
app.include_router(health.router, tags=["Health"])
app.include_router(translate.router, prefix="/translate", tags=["Translation"])
app.include_router(status.router, prefix="/status", tags=["Status"])
app.include_router(download.router, prefix="/download", tags=["Download"])
