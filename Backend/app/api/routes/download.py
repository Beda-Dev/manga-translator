"""
Routes de téléchargement.

- GET /download/{job_id}          → package complet (CBZ/PDF/ZIP)
- GET /download/{job_id}/page/{n} → image individuelle
- GET /download/{job_id}/pages    → liste toutes les pages

Comportement selon le mode de stockage:
  - USE_SUPABASE=false → FileResponse (fichier local)
  - USE_SUPABASE=true  → RedirectResponse vers l'URL Supabase publique
"""

import logging
import os
import re
import traceback
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

from app.core.job_manager import job_store
from app.models.schemas import JobStatus
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)
router = APIRouter()

MIME_TYPES = {
    ".cbz": "application/vnd.comicbook+zip",
    ".zip": "application/zip",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


@router.get("/{job_id}", summary="Télécharger le package traduit complet")
async def download_package(job_id: str):
    """
    Télécharge ou redirige vers le fichier final traduit (CBZ, PDF ou ZIP).

    - En mode **local** (USE_SUPABASE=false): sert le fichier directement.
    - En mode **Supabase** (USE_SUPABASE=true): redirige vers l'URL publique Supabase.
      Idéal pour Render.com où le filesystem est éphémère.

    Le job doit être au statut `completed`.
    """
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} introuvable")

    if job.status == JobStatus.FAILED:
        raise HTTPException(status_code=422, detail=f"Job échoué: {job.error_message}")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=202,
            detail=f"Job en cours ({job.status.value}) — {job.progress:.0f}% terminé"
        )

    # ── Mode Supabase: redirection vers l'URL publique ────────────────────────
    if storage_service.is_cloud and job.output_url:
        logger.info(f"☁️  Redirection Supabase: {job.output_url}")
        return RedirectResponse(url=job.output_url, status_code=302)

    logger.info(f"📥 Téléchargement local demandé: {job.output_path}")
    if not job.output_path or not os.path.exists(job.output_path):
        logger.error(f"❌ Fichier non trouvé sur le serveur: {job.output_path}")
        raise HTTPException(
            status_code=404,
            detail=(
                "Fichier introuvable sur le serveur. "
                "Sur Render.com, activez USE_SUPABASE=true pour un stockage persistant."
            ),
        )

    try:
        ext = Path(job.output_path).suffix.lower()
        media_type = MIME_TYPES.get(ext, "application/octet-stream")
        
        # Sécurisation du nom de fichier pour les headers HTTP
        clean_stem = re.sub(r'[^\w\s-]', '', Path(job.filename).stem)
        clean_stem = re.sub(r'[-\s]+', '_', clean_stem).strip('_')
        filename = f"translated_{clean_stem}{ext}"
        
        logger.info(f"✅ Envoi du fichier: {filename} ({media_type})")

        return FileResponse(
            path=job.output_path,
            media_type=media_type,
            filename=filename,
        )
    except Exception as e:
        logger.error(f"💥 Erreur lors de l'envoi du package: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur interne lors du téléchargement: {str(e)}")


@router.get("/{job_id}/page/{page_index}", summary="Télécharger une page individuelle")
async def download_page(job_id: str, page_index: int):
    """
    Télécharge ou redirige vers une page traduite individuelle.

    - En mode **Supabase**: redirige vers l'URL publique de la page.
    - En mode **local**: sert l'image directement.
    """
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} introuvable")

    page_result = next((p for p in job.pages if p.page_index == page_index), None)
    if not page_result:
        raise HTTPException(
            status_code=404,
            detail=f"Page {page_index} non trouvée ou pas encore traitée"
        )

    if page_result.status == "error":
        raise HTTPException(
            status_code=422,
            detail=f"Page {page_index} en erreur: {page_result.error_message}"
        )

    # ── Mode Supabase ─────────────────────────────────────────────────────────
    if storage_service.is_cloud and page_result.image_url:
        return RedirectResponse(url=page_result.image_url, status_code=302)

    # ── Mode local ────────────────────────────────────────────────────────────
    img_path = page_result.translated_image_path
    logger.debug(f"🖼️  Image demandée page {page_index}: {img_path}")

    if not img_path:
        logger.warning(f"⚠️  Image non générée pour la page {page_index}")
        raise HTTPException(status_code=404, detail=f"Image page {page_index} pas encore prête ou en erreur")

    if not os.path.exists(img_path):
        logger.error(f"❌ Fichier image manquant: {img_path}")
        raise HTTPException(status_code=404, detail=f"Image page {page_index} introuvable sur le serveur")

    ext = Path(img_path).suffix.lower()
    media_type = MIME_TYPES.get(ext, "image/png")
    logger.info(f"✅ Servir page {page_index}: {img_path} ({media_type})")

    return FileResponse(
        path=img_path,
        media_type=media_type,
        filename=f"page_{page_index + 1:04d}{ext}",
    )


@router.get("/{job_id}/pages", summary="Lister toutes les pages traduites")
async def list_pages(job_id: str):
    """
    Retourne la liste des pages avec leurs URLs de téléchargement ou de preview.

    Le champ `image_url` contient:
    - L'URL Supabase publique (si USE_SUPABASE=true) → utilisable directement en <img>
    - L'URL de l'API `/download/{job_id}/page/{n}` (si local)
    """
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} introuvable")

    pages_info = []
    for page in sorted(job.pages, key=lambda p: p.page_index):
        # URL d'image directe pour le frontend (aperçu)
        image_url = page.image_url or f"/download/{job_id}/page/{page.page_index}"

        pages_info.append({
            "page_index": page.page_index,
            "filename": page.filename,
            "status": page.status,
            "image_url": image_url,               # URL directe pour <img> dans Next.js
            "download_url": f"/download/{job_id}/page/{page.page_index}",
            "text_regions_count": len(page.text_regions),
            "processing_time_ms": page.processing_time_ms,
            "error": page.error_message,
        })

    return {
        "job_id": job_id,
        "status": job.status,
        "progress": job.progress,
        "total_pages": job.total_pages,
        "processed_pages": job.processed_pages,
        "storage_mode": "supabase" if storage_service.is_cloud else "local",
        "package_url": job.output_url or f"/download/{job_id}",
        "pages": pages_info,
    }