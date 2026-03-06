"""
Route POST /translate
Point d'entrée principal pour lancer une traduction.
"""

import asyncio
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.job_manager import job_store
from app.models.schemas import (
    FontOptions, OCREngine, OutputFormat, SourceLanguage,
    TranslateResponse, TranslationEngine, TranslationOptions,
)
from app.services.translation_pipeline import TranslationPipeline

logger = logging.getLogger(__name__)
router = APIRouter()

# Extensions acceptées
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".cbz", ".cbr", ".pdf", ".zip"}
MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # En octets


@router.post("", response_model=TranslateResponse, summary="Lancer une traduction")
async def start_translation(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Image, CBZ, CBR ou PDF à traduire"),
    # Options principales
    ocr_engine: OCREngine = Form(default=OCREngine.EASYOCR),
    translation_engine: TranslationEngine = Form(default=TranslationEngine.MARIAN),
    source_lang: SourceLanguage = Form(default=SourceLanguage.AUTO),
    target_lang: str = Form(default="fr"),
    output_format: OutputFormat = Form(default=OutputFormat.CBZ),
    # Options de police (JSON encodé)
    font_options_json: Optional[str] = Form(default=None, alias="font_options"),
    # Clés API (optionnelles, surchargent les variables d'env)
    google_vision_key: Optional[str] = Form(default=None),
    google_translate_key: Optional[str] = Form(default=None),
    deepl_key: Optional[str] = Form(default=None),
    libretranslate_url: Optional[str] = Form(default=None),
    libretranslate_key: Optional[str] = Form(default=None),
):
    """
    Lance une traduction asynchrone.

    - **file**: Fichier image (JPG/PNG/WebP) ou archive (CBZ/CBR/PDF/ZIP)
    - **ocr_engine**: Moteur OCR (`easyocr`, `paddleocr`, `tesseract`, `google_vision`)
    - **translation_engine**: Moteur de traduction (`marian`, `libretranslate`, `google_translate`, `deepl`)
    - **source_lang**: Langue source (`auto`, `en`, `ja`, `ko`, `zh`)
    - **target_lang**: Langue cible (défaut: `fr`)
    - **output_format**: Format de sortie (`cbz`, `pdf`, `zip`)
    - **font_options**: JSON avec les options typographiques

    Retourne un `job_id` pour suivre la progression via `GET /status/{job_id}`.
    """

    # ── Validation du fichier ──────────────────────────────────────────────────
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté: {ext}. Formats acceptés: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Vérifier la taille du fichier
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux. Maximum: {settings.MAX_FILE_SIZE_MB}MB"
        )

    # ── Parser les options de police ───────────────────────────────────────────
    font_options = FontOptions()
    if font_options_json:
        try:
            font_data = json.loads(font_options_json)
            font_options = FontOptions(**font_data)
        except Exception as e:
            logger.warning(f"⚠️  Options de police invalides: {e}, utilisation des défauts")

    # ── Construire les options de traduction ───────────────────────────────────
    options = TranslationOptions(
        ocr_engine=ocr_engine,
        translation_engine=translation_engine,
        source_lang=source_lang,
        target_lang=target_lang,
        output_format=output_format,
        font_options=font_options,
        google_vision_key=google_vision_key or settings.GOOGLE_VISION_API_KEY,
        google_translate_key=google_translate_key or settings.GOOGLE_TRANSLATE_API_KEY,
        deepl_key=deepl_key or settings.DEEPL_API_KEY,
        libretranslate_url=libretranslate_url or settings.LIBRETRANSLATE_URL,
        libretranslate_key=libretranslate_key or settings.LIBRETRANSLATE_API_KEY,
    )

    # ── Sauvegarder le fichier uploadé ─────────────────────────────────────────
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

    # Estimation du nombre de pages (approximative avant extraction)
    estimated_pages = _estimate_pages(file.filename, content)

    job = job_store.create_job(
        filename=file.filename,
        total_pages=estimated_pages,
        options=options.model_dump(mode="json"),
    )

    # Sauvegarder le fichier source
    input_path = os.path.join(settings.UPLOAD_DIR, f"{job.job_id}_{file.filename}")
    with open(input_path, "wb") as f:
        f.write(content)

    output_dir = os.path.join(settings.OUTPUT_DIR, job.job_id)
    os.makedirs(output_dir, exist_ok=True)

    # ── Lancer le pipeline en arrière-plan ────────────────────────────────────
    background_tasks.add_task(
        _run_pipeline,
        job_id=job.job_id,
        input_path=input_path,
        output_dir=output_dir,
        options=options,
    )

    logger.info(f"🚀 Job {job.job_id} lancé pour: {file.filename}")

    return TranslateResponse(
        job_id=job.job_id,
        message=f"Traduction lancée pour '{file.filename}'",
        total_pages=estimated_pages,
        status_url=f"/status/{job.job_id}",
        download_url=f"/download/{job.job_id}",
    )


async def _run_pipeline(
    job_id: str,
    input_path: str,
    output_dir: str,
    options: TranslationOptions,
):
    """Lance le pipeline de traduction en arrière-plan."""
    try:
        pipeline = TranslationPipeline(job_id=job_id, options=options)
        await pipeline.run(input_path, output_dir)
    except Exception as e:
        logger.error(f"❌ Pipeline {job_id} échoué: {e}", exc_info=True)
    finally:
        # Nettoyage du fichier source uploadé
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
        except Exception:
            pass


def _estimate_pages(filename: str, content: bytes) -> int:
    """Estimation rapide du nombre de pages sans extraction complète."""
    ext = Path(filename).suffix.lower()
    if ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp"):
        return 1
    elif ext in (".cbz", ".zip"):
        import zipfile
        import io
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                return sum(
                    1 for name in zf.namelist()
                    if Path(name).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
                )
        except Exception:
            return 1
    elif ext == ".pdf":
        # Estimation grossière basée sur la taille (~200KB par page)
        return max(1, len(content) // (200 * 1024))
    return 1
