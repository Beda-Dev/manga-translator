"""
Service OCR multi-moteurs.
Détecte et extrait le texte des bulles de BD/webtoon.

Moteurs supportés:
  - EasyOCR  : Open source, bon support CJK
  - PaddleOCR: Open source, très performant sur BD
  - Tesseract: Open source, nécessite installation système
  - Google Vision: Payant, très précis (placeholder)
"""

import logging
from typing import List, Optional, Tuple

import numpy as np

from app.models.schemas import OCREngine, TextRegion

logger = logging.getLogger(__name__)

# Cache des instances OCR (évite de recharger les modèles)
_ocr_instances = {}


def get_text_regions(
    image: np.ndarray,
    engine: OCREngine,
    source_lang: str = "en",
    api_key: Optional[str] = None,
) -> List[TextRegion]:
    """
    Détecte et extrait les zones de texte dans une image.

    Args:
        image: Image numpy BGR (format OpenCV)
        engine: Moteur OCR à utiliser
        source_lang: Langue source ("en", "ja", "ko", "zh", "auto")
        api_key: Clé API pour moteurs payants

    Returns:
        Liste de TextRegion avec bbox et texte extrait
    """
    logger.info(f"🔍 OCR avec moteur: {engine.value} | Langue: {source_lang}")

    try:
        if engine == OCREngine.EASYOCR:
            return _ocr_easyocr(image, source_lang)
        elif engine == OCREngine.PADDLEOCR:
            return _ocr_paddleocr(image, source_lang)
        elif engine == OCREngine.TESSERACT:
            return _ocr_tesseract(image, source_lang)
        elif engine == OCREngine.GOOGLE_VISION:
            return _ocr_google_vision(image, api_key)
        else:
            raise ValueError(f"Moteur OCR inconnu: {engine}")
    except Exception as e:
        logger.error(f"❌ Erreur OCR ({engine.value}): {e}")
        return []


# ── EasyOCR ────────────────────────────────────────────────────────────────────

def _ocr_easyocr(image: np.ndarray, source_lang: str) -> List[TextRegion]:
    """
    OCR avec EasyOCR.
    pip install easyocr
    Supporte: en, ja, ko, zh (ch_sim/ch_tra)
    """
    import easyocr

    lang_map = {
        "en": ["en"],
        "ja": ["ja", "en"],
        "ko": ["ko", "en"],
        "zh": ["ch_sim", "en"],
        "auto": ["en", "ja", "ko"],
    }
    langs = lang_map.get(source_lang, ["en"])

    # Cache de l'instance pour éviter le rechargement du modèle
    cache_key = f"easyocr_{'_'.join(langs)}"
    if cache_key not in _ocr_instances:
        logger.info(f"⬇️  Chargement EasyOCR ({langs})...")
        _ocr_instances[cache_key] = easyocr.Reader(langs, gpu=False)

    reader = _ocr_instances[cache_key]
    results = reader.readtext(image)

    regions = []
    for (bbox_points, text, confidence) in results:
        if not text.strip() or confidence < 0.3:
            continue

        # Convertir les 4 points en [x, y, w, h]
        xs = [p[0] for p in bbox_points]
        ys = [p[1] for p in bbox_points]
        x, y = int(min(xs)), int(min(ys))
        w, h = int(max(xs) - x), int(max(ys) - y)

        regions.append(TextRegion(
            bbox=[x, y, w, h],
            original_text=text.strip(),
            confidence=float(confidence),
        ))

    logger.info(f"✅ EasyOCR: {len(regions)} zones détectées")
    return regions


# ── PaddleOCR ──────────────────────────────────────────────────────────────────

def _ocr_paddleocr(image: np.ndarray, source_lang: str) -> List[TextRegion]:
    """
    OCR avec PaddleOCR.
    pip install paddlepaddle paddleocr
    Excellent pour BD grâce à sa détection de texte orienté.
    """
    try:
        from paddleocr import PaddleOCR
    except ImportError:
        raise ImportError(
            "PaddleOCR non installé: pip install paddlepaddle paddleocr"
        )

    lang_map = {"en": "en", "ja": "japan", "ko": "korean", "zh": "ch", "auto": "en"}
    lang = lang_map.get(source_lang, "en")

    cache_key = f"paddleocr_{lang}"
    if cache_key not in _ocr_instances:
        logger.info(f"⬇️  Chargement PaddleOCR ({lang})...")
        _ocr_instances[cache_key] = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)

    ocr = _ocr_instances[cache_key]
    result = ocr.ocr(image, cls=True)

    regions = []
    if not result or not result[0]:
        return regions

    for line in result[0]:
        bbox_points, (text, confidence) = line
        if not text.strip() or confidence < 0.3:
            continue

        xs = [p[0] for p in bbox_points]
        ys = [p[1] for p in bbox_points]
        x, y = int(min(xs)), int(min(ys))
        w, h = int(max(xs) - x), int(max(ys) - y)

        regions.append(TextRegion(
            bbox=[x, y, w, h],
            original_text=text.strip(),
            confidence=float(confidence),
        ))

    logger.info(f"✅ PaddleOCR: {len(regions)} zones détectées")
    return regions


# ── Tesseract ─────────────────────────────────────────────────────────────────

def _ocr_tesseract(image: np.ndarray, source_lang: str) -> List[TextRegion]:
    """
    OCR avec Tesseract.
    pip install pytesseract
    Système: sudo apt-get install tesseract-ocr tesseract-ocr-fra
    """
    try:
        import pytesseract
        from PIL import Image as PILImage
    except ImportError:
        raise ImportError("pip install pytesseract pillow")

    lang_map = {"en": "eng", "ja": "jpn", "ko": "kor", "zh": "chi_sim", "auto": "eng+jpn"}
    lang = lang_map.get(source_lang, "eng")

    # Convertir BGR → RGB pour Pillow
    import cv2
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_img = PILImage.fromarray(img_rgb)

    data = pytesseract.image_to_data(
        pil_img, lang=lang, output_type=pytesseract.Output.DICT
    )

    regions = []
    for i, text in enumerate(data["text"]):
        if not text.strip():
            continue
        confidence = float(data["conf"][i])
        if confidence < 30:
            continue

        x = data["left"][i]
        y = data["top"][i]
        w = data["width"][i]
        h = data["height"][i]

        regions.append(TextRegion(
            bbox=[x, y, w, h],
            original_text=text.strip(),
            confidence=confidence / 100.0,
        ))

    logger.info(f"✅ Tesseract: {len(regions)} zones détectées")
    return regions


# ── Google Vision (placeholder) ───────────────────────────────────────────────

def _ocr_google_vision(image: np.ndarray, api_key: Optional[str]) -> List[TextRegion]:
    """
    OCR avec Google Cloud Vision API.
    pip install google-cloud-vision
    Nécessite une clé API valide.

    PLACEHOLDER: Décommenter et configurer avec votre clé API.
    """
    if not api_key:
        raise ValueError(
            "Google Vision nécessite une clé API. "
            "Configurez GOOGLE_VISION_API_KEY dans .env ou passez-la en paramètre."
        )

    # ── PLACEHOLDER GOOGLE VISION ────────────────────────────────────────────
    # from google.cloud import vision
    # import cv2, base64
    #
    # client = vision.ImageAnnotatorClient(
    #     client_options={"api_key": api_key}
    # )
    # _, buffer = cv2.imencode(".jpg", image)
    # content = buffer.tobytes()
    # vision_image = vision.Image(content=content)
    # response = client.text_detection(image=vision_image)
    #
    # regions = []
    # for annotation in response.text_annotations[1:]:  # Skip full text block
    #     vertices = annotation.bounding_poly.vertices
    #     xs = [v.x for v in vertices]
    #     ys = [v.y for v in vertices]
    #     regions.append(TextRegion(
    #         bbox=[min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys)],
    #         original_text=annotation.description,
    #         confidence=0.99,
    #     ))
    # return regions
    # ─────────────────────────────────────────────────────────────────────────

    raise NotImplementedError(
        "Google Vision non configuré. Décommentez le code dans ocr_service.py "
        "et installez: pip install google-cloud-vision"
    )
