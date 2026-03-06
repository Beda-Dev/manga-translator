"""
Service de stockage — Supabase Storage + fallback local.

⚠️  IMPORTANT RENDER.COM:
    Render a un système de fichiers ÉPHÉMÈRE. Les fichiers en /tmp
    disparaissent à chaque redémarrage ou redéploiement.
    → Mettre USE_SUPABASE=true en production sur Render.

Modes:
  - USE_SUPABASE=false : stockage local (dev / Docker auto-hébergé)
  - USE_SUPABASE=true  : Supabase Storage (Render, production)
"""

import io
import logging
import os
from pathlib import Path
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """
    Abstraction complète du stockage.

    En mode LOCAL  → les fichiers sont lus/écrits sur le disque.
    En mode SUPABASE → tous les fichiers transitent par Supabase Storage.
                       Les fichiers locaux temporaires sont supprimés après upload.
    """

    def __init__(self):
        self._client = None
        if settings.USE_SUPABASE:
            self._init_supabase()
        else:
            logger.info("📁 Stockage: mode LOCAL (USE_SUPABASE=false)")

    # ── Initialisation ─────────────────────────────────────────────────────────

    def _init_supabase(self):
        """Initialise et valide la connexion Supabase."""
        try:
            from supabase import create_client, Client
        except ImportError:
            raise ImportError(
                "supabase-py non installé.\n"
                "Ajoutez 'supabase' à requirements.txt et relancez."
            )

        if not settings.SUPABASE_URL:
            raise ValueError("SUPABASE_URL manquant dans .env")
        if not settings.SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY manquant dans .env")

        self._client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

        # Vérifier que le bucket existe, le créer si nécessaire
        self._ensure_bucket()
        logger.info(f"✅ Supabase Storage initialisé — bucket: '{settings.SUPABASE_BUCKET}'")

    def _ensure_bucket(self):
        """Crée le bucket s'il n'existe pas encore."""
        try:
            buckets = self._client.storage.list_buckets()
            bucket_names = [b.name for b in buckets]
            if settings.SUPABASE_BUCKET not in bucket_names:
                self._client.storage.create_bucket(
                    settings.SUPABASE_BUCKET,
                    options={"public": True},  # Accès public pour les URLs de téléchargement
                )
                logger.info(f"✅ Bucket '{settings.SUPABASE_BUCKET}' créé")
            else:
                logger.info(f"✅ Bucket '{settings.SUPABASE_BUCKET}' trouvé")
        except Exception as e:
            # Ne pas planter si la vérification échoue (droits insuffisants, etc.)
            logger.warning(f"⚠️  Impossible de vérifier/créer le bucket: {e}")

    # ── API publique ───────────────────────────────────────────────────────────

    @property
    def is_cloud(self) -> bool:
        """True si Supabase est actif, False si stockage local."""
        return settings.USE_SUPABASE and self._client is not None

    def upload_file(self, local_path: str, remote_path: str) -> Optional[str]:
        """
        Upload un fichier vers Supabase Storage (si activé).

        Args:
            local_path: Chemin local du fichier à uploader
            remote_path: Chemin distant dans le bucket (ex: "jobs/abc123/output.cbz")

        Returns:
            URL publique Supabase si cloud, None si mode local
        """
        if not self.is_cloud:
            logger.debug(f"📁 [Local] Fichier conservé: {local_path}")
            return None

        try:
            with open(local_path, "rb") as f:
                file_bytes = f.read()

            # Déterminer le Content-Type
            content_type = _mime_for_path(remote_path)

            self._client.storage.from_(settings.SUPABASE_BUCKET).upload(
                path=remote_path,
                file=file_bytes,
                file_options={
                    "content-type": content_type,
                    "upsert": "true",   # Écraser si le fichier existe déjà
                },
            )

            public_url = self._client.storage.from_(
                settings.SUPABASE_BUCKET
            ).get_public_url(remote_path)

            logger.info(f"☁️  Uploadé sur Supabase: {remote_path}")
            return public_url

        except Exception as e:
            logger.error(f"❌ Erreur upload Supabase ({remote_path}): {e}", exc_info=True)
            return None

    def upload_bytes(self, data: bytes, remote_path: str) -> Optional[str]:
        """
        Upload des bytes directement vers Supabase (sans fichier temporaire).

        Utile pour les images traitées en mémoire.
        """
        if not self.is_cloud:
            return None

        try:
            content_type = _mime_for_path(remote_path)
            self._client.storage.from_(settings.SUPABASE_BUCKET).upload(
                path=remote_path,
                file=data,
                file_options={"content-type": content_type, "upsert": "true"},
            )
            return self._client.storage.from_(settings.SUPABASE_BUCKET).get_public_url(
                remote_path
            )
        except Exception as e:
            logger.error(f"❌ Erreur upload bytes Supabase ({remote_path}): {e}")
            return None

    def download_file(self, remote_path: str) -> Optional[bytes]:
        """
        Télécharge un fichier depuis Supabase Storage.

        Returns:
            Contenu du fichier en bytes, ou None si erreur
        """
        if not self.is_cloud:
            return None

        try:
            data = self._client.storage.from_(settings.SUPABASE_BUCKET).download(
                remote_path
            )
            return data
        except Exception as e:
            logger.error(f"❌ Erreur download Supabase ({remote_path}): {e}")
            return None

    def get_public_url(self, remote_path: str) -> Optional[str]:
        """Retourne l'URL publique d'un fichier Supabase."""
        if not self.is_cloud:
            return None
        try:
            return self._client.storage.from_(settings.SUPABASE_BUCKET).get_public_url(
                remote_path
            )
        except Exception as e:
            logger.error(f"❌ Erreur get_public_url ({remote_path}): {e}")
            return None

    def delete_file(self, remote_path: str) -> bool:
        """Supprime un fichier du bucket Supabase."""
        if not self.is_cloud:
            return False
        try:
            self._client.storage.from_(settings.SUPABASE_BUCKET).remove([remote_path])
            logger.info(f"🗑️  Supprimé de Supabase: {remote_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur suppression Supabase ({remote_path}): {e}")
            return False

    def delete_job_files(self, job_id: str) -> int:
        """
        Supprime tous les fichiers d'un job depuis Supabase.
        Appelé par le nettoyage automatique après CLEANUP_AFTER_HOURS.

        Returns:
            Nombre de fichiers supprimés
        """
        if not self.is_cloud:
            return 0
        try:
            prefix = f"jobs/{job_id}/"
            files = self._client.storage.from_(settings.SUPABASE_BUCKET).list(prefix)
            if not files:
                return 0
            paths = [f"{prefix}{f['name']}" for f in files]
            self._client.storage.from_(settings.SUPABASE_BUCKET).remove(paths)
            logger.info(f"🗑️  {len(paths)} fichiers supprimés pour le job {job_id}")
            return len(paths)
        except Exception as e:
            logger.error(f"❌ Erreur suppression job Supabase ({job_id}): {e}")
            return 0

    # ── Helpers chemins ────────────────────────────────────────────────────────

    @staticmethod
    def remote_path_for_job(job_id: str, filename: str) -> str:
        """
        Retourne le chemin distant standard pour un fichier de job.
        Ex: "jobs/abc123/output.cbz"
        """
        return f"jobs/{job_id}/{filename}"

    @staticmethod
    def remote_path_for_page(job_id: str, page_filename: str) -> str:
        """
        Retourne le chemin distant pour une page traduite.
        Ex: "jobs/abc123/pages/page_0001.png"
        """
        return f"jobs/{job_id}/pages/{page_filename}"


# ── Helpers privés ─────────────────────────────────────────────────────────────

def _mime_for_path(path: str) -> str:
    """Retourne le Content-Type correspondant à l'extension du fichier."""
    ext = Path(path).suffix.lower()
    return {
        ".cbz": "application/vnd.comicbook+zip",
        ".zip": "application/zip",
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(ext, "application/octet-stream")


# Singleton global — importé partout dans l'app
storage_service = StorageService()