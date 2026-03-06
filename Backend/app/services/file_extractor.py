"""
Service d'extraction de fichiers.
Gère CBZ, CBR, PDF et images simples → liste de chemins d'images.
"""

import logging
import os
import shutil
import zipfile
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Extensions d'images supportées
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


class FileExtractor:
    """Extrait les pages d'images depuis différents formats de fichiers."""

    def extract(self, file_path: str, output_dir: str) -> List[str]:
        """
        Extrait toutes les images d'un fichier source.

        Args:
            file_path: Chemin vers le fichier source (image, CBZ, CBR, PDF)
            output_dir: Répertoire où extraire les images

        Returns:
            Liste triée des chemins d'images extraites
        """
        os.makedirs(output_dir, exist_ok=True)
        ext = Path(file_path).suffix.lower()

        logger.info(f"📂 Extraction de: {Path(file_path).name} (format: {ext})")

        if ext in IMAGE_EXTENSIONS:
            return self._handle_single_image(file_path, output_dir)
        elif ext == ".cbz":
            return self._extract_cbz(file_path, output_dir)
        elif ext == ".cbr":
            return self._extract_cbr(file_path, output_dir)
        elif ext == ".pdf":
            return self._extract_pdf(file_path, output_dir)
        elif ext == ".zip":
            return self._extract_zip(file_path, output_dir)
        else:
            raise ValueError(f"Format non supporté: {ext}")

    def _handle_single_image(self, file_path: str, output_dir: str) -> List[str]:
        """Copie une image unique vers le répertoire de sortie."""
        dest = os.path.join(output_dir, Path(file_path).name)
        shutil.copy2(file_path, dest)
        logger.info(f"🖼️  Image unique copiée: {dest}")
        return [dest]

    def _extract_cbz(self, file_path: str, output_dir: str) -> List[str]:
        """Extrait un fichier CBZ (ZIP d'images)."""
        images = []
        with zipfile.ZipFile(file_path, "r") as zf:
            members = sorted(zf.namelist())
            for member in members:
                if Path(member).suffix.lower() in IMAGE_EXTENSIONS:
                    # Éviter les path traversal
                    safe_name = Path(member).name
                    target = os.path.join(output_dir, safe_name)
                    with zf.open(member) as src, open(target, "wb") as dst:
                        dst.write(src.read())
                    images.append(target)

        logger.info(f"📦 CBZ extrait: {len(images)} images")
        return sorted(images)

    def _extract_cbr(self, file_path: str, output_dir: str) -> List[str]:
        """
        Extrait un fichier CBR (RAR d'images).
        Nécessite: pip install rarfile + unrar installé sur le système.
        """
        try:
            import rarfile
        except ImportError:
            raise ImportError(
                "Le support CBR nécessite 'rarfile': pip install rarfile\n"
                "Et l'utilitaire système 'unrar': sudo apt-get install unrar"
            )

        images = []
        with rarfile.RarFile(file_path, "r") as rf:
            members = sorted(rf.namelist())
            for member in members:
                if Path(member).suffix.lower() in IMAGE_EXTENSIONS:
                    safe_name = Path(member).name
                    target = os.path.join(output_dir, safe_name)
                    with rf.open(member) as src, open(target, "wb") as dst:
                        dst.write(src.read())
                    images.append(target)

        logger.info(f"📦 CBR extrait: {len(images)} images")
        return sorted(images)

    def _extract_pdf(self, file_path: str, output_dir: str) -> List[str]:
        """
        Convertit chaque page PDF en image PNG.
        Nécessite: pip install pymupdf
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "Le support PDF nécessite 'PyMuPDF': pip install pymupdf"
            )

        images = []
        doc = fitz.open(file_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            # Résolution 150 DPI — bon compromis qualité/performance pour BD
            mat = fitz.Matrix(150 / 72, 150 / 72)
            pix = page.get_pixmap(matrix=mat)
            img_path = os.path.join(output_dir, f"page_{page_num + 1:04d}.png")
            pix.save(img_path)
            images.append(img_path)

        doc.close()
        logger.info(f"📄 PDF extrait: {len(images)} pages")
        return images

    def _extract_zip(self, file_path: str, output_dir: str) -> List[str]:
        """Extrait un ZIP contenant des images."""
        return self._extract_cbz(file_path, output_dir)


def create_output_package(
    translated_images: List[str],
    output_path: str,
    output_format: str,
) -> str:
    """
    Crée le package final (CBZ, PDF ou ZIP) à partir des images traduites.

    Args:
        translated_images: Liste des chemins des images traduites (triées)
        output_path: Chemin du fichier de sortie (sans extension)
        output_format: "cbz" | "pdf" | "zip"

    Returns:
        Chemin complet du fichier créé
    """
    fmt = output_format.lower()

    if fmt in ("cbz", "zip"):
        final_path = f"{output_path}.{fmt}"
        with zipfile.ZipFile(final_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for img_path in sorted(translated_images):
                zf.write(img_path, Path(img_path).name)
        logger.info(f"📦 Package {fmt.upper()} créé: {final_path}")
        return final_path

    elif fmt == "pdf":
        try:
            import fitz
        except ImportError:
            raise ImportError("pip install pymupdf pour le support PDF")

        final_path = f"{output_path}.pdf"
        doc = fitz.open()

        for img_path in sorted(translated_images):
            img_doc = fitz.open(img_path)
            pdfbytes = img_doc.convert_to_pdf()
            img_doc.close()
            imgpdf = fitz.open("pdf", pdfbytes)
            doc.insert_pdf(imgpdf)

        doc.save(final_path)
        doc.close()
        logger.info(f"📄 Package PDF créé: {final_path}")
        return final_path

    else:
        raise ValueError(f"Format de sortie non supporté: {output_format}")