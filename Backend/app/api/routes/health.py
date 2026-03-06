"""
Health check endpoint.
"""

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Detailed health check endpoint for frontend compatibility."""
    return {
        "status": "ok",
        "version": "1.0.0",  # Matches FastAPI version in main.py
        "ocr_engine": settings.OCR_ENGINE,
        "translation_engine": settings.TRANSLATION_ENGINE,
    }
