"""
Gestionnaire de jobs de traduction.
Stocke l'état de chaque job en mémoire (remplaçable par Redis pour la prod).
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

from app.models.schemas import JobStatus, PageResult, TranslationJob

logger = logging.getLogger(__name__)


class JobStore:
    """
    Store en mémoire pour les jobs de traduction.
    Pour la production, remplacer par Redis ou une base de données.
    """

    def __init__(self):
        self._jobs: Dict[str, TranslationJob] = {}

    def create_job(
        self,
        filename: str,
        total_pages: int,
        options: dict,
    ) -> TranslationJob:
        """Crée un nouveau job et retourne son ID."""
        job_id = str(uuid.uuid4())
        job = TranslationJob(
            job_id=job_id,
            filename=filename,
            total_pages=total_pages,
            options=options,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
        )
        self._jobs[job_id] = job
        logger.info(f"📋 Job créé: {job_id} | Fichier: {filename} | Pages: {total_pages}")
        return job

    def get_job(self, job_id: str) -> Optional[TranslationJob]:
        """Récupère un job par son ID."""
        return self._jobs.get(job_id)

    def update_status(self, job_id: str, status: JobStatus, error: Optional[str] = None):
        """Met à jour le statut d'un job."""
        job = self._jobs.get(job_id)
        if job:
            job.status = status
            if error:
                job.error_message = error
            if status == JobStatus.COMPLETED:
                job.completed_at = datetime.utcnow()
            logger.info(f"🔄 Job {job_id}: {status.value}")

    def add_page_result(self, job_id: str, page_result: PageResult):
        """Ajoute le résultat d'une page au job."""
        job = self._jobs.get(job_id)
        if job:
            job.pages.append(page_result)
            job.processed_pages = len(job.pages)
            job.progress = round((job.processed_pages / job.total_pages) * 100, 1)
            logger.info(
                f"📄 Job {job_id}: page {page_result.page_index + 1}/{job.total_pages} "
                f"— {page_result.status} ({job.progress}%)"
            )

    def set_output_path(self, job_id: str, output_path: str, output_url: Optional[str] = None):
        """Enregistre le chemin du fichier final traduit."""
        job = self._jobs.get(job_id)
        if job:
            job.output_path = output_path
            job.output_url = output_url

    def list_jobs(self) -> List[TranslationJob]:
        """Retourne tous les jobs."""
        return list(self._jobs.values())

    def delete_job(self, job_id: str) -> bool:
        """Supprime un job."""
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False


# Singleton global
job_store = JobStore()