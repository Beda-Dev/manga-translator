"""
Route GET /status/{job_id}
Retourne la progression d'un job de traduction.
"""

import logging
from fastapi import APIRouter, HTTPException
from app.core.job_manager import job_store
from app.models.schemas import StatusResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{job_id}", response_model=StatusResponse, summary="Progression d'un job")
async def get_job_status(job_id: str):
    """
    Retourne l'état détaillé d'un job de traduction.

    - **job_id**: Identifiant du job retourné par `POST /translate`

    Statuts possibles:
    - `pending`: En attente de démarrage
    - `extracting`: Extraction des pages en cours
    - `processing`: Traduction des pages en cours
    - `packaging`: Création du fichier final
    - `completed`: Traduction terminée, prêt à télécharger
    - `failed`: Erreur durant le traitement
    """
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} introuvable")

    # On enrichit les résultats des pages avec les URLs pour le frontend
    mapped_pages = []
    for p in job.pages:
        p_copy = p.model_copy()
        # image_url est déjà l'URL Supabase si cloud, sinon on met la route locale
        if not p_copy.image_url:
            p_copy.image_url = f"/download/{job_id}/page/{p.page_index}"
        
        # download_url est toujours la route locale qui gère Redirect ou FileResponse
        p_copy.download_url = f"/download/{job_id}/page/{p.page_index}"
        mapped_pages.append(p_copy)

    return StatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        total_pages=job.total_pages,
        processed_pages=job.processed_pages,
        pages=mapped_pages,
        output_url=job.output_url,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )
