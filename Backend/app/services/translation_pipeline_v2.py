"""
Pipeline de traduction v2 — Orchestrateur principal amélioré.

Changements vs v1:
  1. Intègre le post-processing OCR (nettoyage + ordre de lecture)
  2. Traduction contextuelle par batch (toutes bulles d'une page ensemble)
  3. Glossaire persistant partagé entre toutes les pages
  4. Meilleure gestion des erreurs par page
  5. Inpainting amélioré avec détection de contour de bulle
"""

import asyncio
import logging
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Tuple

import cv2

from app.core.config import settings
from app.core.job_manager import job_store
from app.models.schemas import JobStatus, PageResult, TranslationOptions
from app.services.file_extractor import FileExtractor, create_output_package
# Utilisation de l'inpainting amélioré (V2)
from app.services.inpainting_service_v2 import remove_text_smart_v2
from app.services.ocr_service import get_text_regions
from app.services.storage_service import storage_service
from app.services.text_renderer import render_translated_text

# ── Import des nouveaux modules ───────────────────────────────────────────────
from app.services.ocr_postprocessing import postprocess_regions
from app.services.translation_service_v2 import (
    translate_regions_batch,
    TranslationGlossary,
)

logger = logging.getLogger(__name__)


class TranslationPipelineV2:
    """
    Pipeline complet manga/webtoon v2.

    Étapes par page:
      1. OCR → détection zones de texte
      2. Post-processing OCR (nettoyage + ordre de lecture) ← NOUVEAU
      3. Traduction batch contextuelle ← AMÉLIORÉ
      4. Inpainting (suppression texte original via OpenCV)
      5. Rendu (réécriture traduite via Pillow, avec word-wrap)
      6. Upload page vers Supabase (si USE_SUPABASE=true)

    Étape finale:
      7. Packaging CBZ / PDF / ZIP
      8. Upload package → URL publique
    """

    def __init__(self, job_id: str, options: TranslationOptions):
        self.job_id = job_id
        self.options = options
        self.extractor = FileExtractor()
        # Glossaire partagé entre toutes les pages du job ← NOUVEAU
        self.glossary = TranslationGlossary()

    async def run(self, input_path: str, output_dir: str) -> str:
        job = job_store.get_job(self.job_id)
        if not job:
            raise ValueError(f"Job {self.job_id} introuvable")

        try:
            # 1. Extraction
            job_store.update_status(self.job_id, JobStatus.EXTRACTING)
            extract_dir = os.path.join(output_dir, "pages")
            os.makedirs(extract_dir, exist_ok=True)
            image_paths = self.extractor.extract(input_path, extract_dir)
            logger.info(f"📂 Job {self.job_id}: {len(image_paths)} pages extraites")
            job.total_pages = len(image_paths)

            # 2. Traitement parallèle
            job_store.update_status(self.job_id, JobStatus.PROCESSING)
            translated_dir = os.path.join(output_dir, "translated")
            os.makedirs(translated_dir, exist_ok=True)
            translated_paths = await self._process_pages_parallel(image_paths, translated_dir)

            # 3. Packaging
            job_store.update_status(self.job_id, JobStatus.PACKAGING)
            output_base = os.path.join(output_dir, f"translated_{self.job_id}")
            local_package = create_output_package(
                translated_paths,
                output_base,
                self.options.output_format.value,
            )

            # 4. Upload
            package_url = await self._upload_package(local_package)
            job_store.set_output_path(self.job_id, local_package, package_url)
            job_store.update_status(self.job_id, JobStatus.COMPLETED)

            destination = f"Supabase: {package_url}" if package_url else f"local: {local_package}"
            logger.info(f"✅ Job {self.job_id} terminé — {destination}")
            logger.info(f"📚 Glossaire final: {len(self.glossary._terms)} termes, "
                        f"{len(self.glossary._proper_nouns)} noms propres")

            return package_url or local_package

        except Exception as e:
            logger.error(f"❌ Job {self.job_id} échoué: {e}", exc_info=True)
            job_store.update_status(self.job_id, JobStatus.FAILED, str(e))
            raise

    # ── Traitement parallèle ──────────────────────────────────────────────────

    async def _process_pages_parallel(
        self, image_paths: List[str], output_dir: str
    ) -> List[str]:
        max_workers = min(settings.MAX_PARALLEL_PAGES, len(image_paths))
        translated_paths: List[Optional[str]] = [None] * len(image_paths)
        loop = asyncio.get_event_loop()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._process_single_page, idx, path, output_dir): idx
                for idx, path in enumerate(image_paths)
            }
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    page_result, out_path = await loop.run_in_executor(None, future.result)
                    translated_paths[idx] = out_path or image_paths[idx]
                    job_store.add_page_result(self.job_id, page_result)
                except Exception as e:
                    logger.error(f"❌ Page {idx} échouée: {e}")
                    translated_paths[idx] = image_paths[idx]
                    job_store.add_page_result(self.job_id, PageResult(
                        page_index=idx,
                        filename=Path(image_paths[idx]).name,
                        status="error",
                        error_message=str(e),
                    ))

        return [p for p in translated_paths if p]

    # ── Pipeline d'une page ───────────────────────────────────────────────────

    def _process_single_page(
        self, page_index: int, image_path: str, output_dir: str
    ) -> Tuple[PageResult, Optional[str]]:
        """
        Pipeline complet pour une page.
        OCR → Post-process → Traduction batch → Inpainting → Rendu → Upload
        """
        start = time.time()
        filename = Path(image_path).name
        logger.info(f"🖼️  Page {page_index + 1}: démarrage ({filename})")

        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Image illisible: {image_path}")

            img_height, img_width = image.shape[:2]

            # ── 1. OCR ────────────────────────────────────────────────────────
            logger.info(f"  🔍 Page {page_index + 1}: OCR ({self.options.ocr_engine.value})...")
            regions = get_text_regions(
                image,
                engine=self.options.ocr_engine,
                source_lang=self.options.source_lang.value,
                api_key=self.options.google_vision_key,
            )

            # ── 2. Post-processing OCR ← NOUVEAU ─────────────────────────────
            if regions:
                logger.info(f"  🧹 Page {page_index + 1}: post-processing OCR ({len(regions)} régions)...")
                regions = postprocess_regions(regions, image_height=img_height)
                logger.info(f"  ✅ Post-processing: {len(regions)} régions conservées")

            out_path = os.path.join(output_dir, filename)

            if not regions:
                logger.info(f"  ⏭️  Page {page_index + 1}: aucun texte, copie directe")
                shutil.copy2(image_path, out_path)
                page_url = self._upload_page(out_path, page_index)
                return PageResult(
                    page_index=page_index, filename=filename, status="skipped",
                    translated_image_path=out_path, image_url=page_url,
                    processing_time_ms=int((time.time() - start) * 1000),
                ), out_path

            # ── 3. Traduction batch contextuelle ← AMÉLIORÉ ──────────────────
            logger.info(
                f"  🌐 Page {page_index + 1}: traduction contextuelle "
                f"({len(regions)} bulles en 1 requête)..."
            )
            regions = translate_regions_batch(
                regions=regions,
                engine=self.options.translation_engine,
                source_lang=self.options.source_lang.value,
                target_lang=self.options.target_lang,
                glossary=self.glossary,  # ← Glossaire partagé
                api_key=self.options.google_translate_key,
                libretranslate_url=self.options.libretranslate_url,
                libretranslate_key=self.options.libretranslate_key,
            )

            # Logger les traductions pour debug
            for region in regions:
                logger.debug(
                    f"    '{region.original_text[:40]}' "
                    f"→ '{(region.translated_text or '')[:40]}'"
                )

            # ── 4. Inpainting AMÉLIORÉ (V2) ───────────────────────────────────
            logger.info(f"  🎨 Page {page_index + 1}: suppression intelligente du texte (V2)...")
            cleaned_image, bg_colors = remove_text_smart_v2(image, regions)

            # ── 5. Rendu ──────────────────────────────────────────────────────
            logger.info(f"  ✍️  Page {page_index + 1}: réécriture en français...")
            final_image = render_translated_text(
                cleaned_image, regions, bg_colors, self.options.font_options
            )

            # ── 6. Sauvegarde + Upload ────────────────────────────────────────
            cv2.imwrite(out_path, final_image, [cv2.IMWRITE_PNG_COMPRESSION, 6])
            page_url = self._upload_page(out_path, page_index)

            elapsed = int((time.time() - start) * 1000)
            logger.info(f"  ✅ Page {page_index + 1} OK en {elapsed}ms")

            return PageResult(
                page_index=page_index, filename=filename, status="success",
                text_regions=regions, text_regions_count=len(regions),
                translated_image_path=out_path,
                image_url=page_url, processing_time_ms=elapsed,
            ), out_path

        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            logger.error(f"  ❌ Page {page_index + 1}: {e}", exc_info=True)
            return PageResult(
                page_index=page_index, filename=filename,
                status="error", error_message=str(e), processing_time_ms=elapsed,
            ), None

    # ── Helpers upload ────────────────────────────────────────────────────────

    def _upload_page(self, local_path: str, page_index: int) -> Optional[str]:
        if not storage_service.is_cloud:
            return None
        suffix = Path(local_path).suffix
        remote = storage_service.remote_path_for_page(
            self.job_id, f"page_{page_index:04d}{suffix}"
        )
        return storage_service.upload_file(local_path, remote)

    async def _upload_package(self, local_path: str) -> Optional[str]:
        if not storage_service.is_cloud:
            return None
        remote = storage_service.remote_path_for_job(self.job_id, Path(local_path).name)
        loop = asyncio.get_event_loop()
        url = await loop.run_in_executor(
            None, storage_service.upload_file, local_path, remote
        )
        return url
