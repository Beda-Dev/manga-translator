"""
Service d'inpainting v2 — suppression du texte améliorée.

Améliorations vs v1:
  1. Détection du contour réel de la bulle (pas juste un rectangle)
  2. Remplissage en forme de polygone → pas d'artefacts aux coins
  3. Détection de fond blanc automatique pour BD classique
  4. Lissage des bords après inpainting
"""

import logging
from typing import List, Optional, Tuple

import cv2
import numpy as np

from app.models.schemas import TextRegion

logger = logging.getLogger(__name__)


def detect_bubble_contour(
    image: np.ndarray,
    region: TextRegion,
    expand_ratio: float = 0.15,
) -> Optional[np.ndarray]:
    """
    Détecte le contour réel de la bulle de BD autour d'une zone de texte.

    Algorithme:
    1. Extraire une zone légèrement plus grande que la bbox du texte
    2. Convertir en niveaux de gris
    3. Seuillage pour isoler la bulle blanche
    4. Trouver le contour le plus grand (= la bulle)
    5. Retourner le masque en forme de bulle

    Args:
        image: Image BGR complète
        region: Zone de texte (on cherche la bulle autour)
        expand_ratio: Expansion de la bbox pour trouver les bords de la bulle

    Returns:
        Masque numpy (uint8) de la forme de la bulle, ou None si non détecté
    """
    x, y, w, h = region.bbox
    ih, iw = image.shape[:2]

    # Étendre la zone de recherche autour du texte
    expand_x = int(w * expand_ratio)
    expand_y = int(h * expand_ratio)
    x1 = max(0, x - expand_x)
    y1 = max(0, y - expand_y)
    x2 = min(iw, x + w + expand_x)
    y2 = min(ih, y + h + expand_y)

    roi = image[y1:y2, x1:x2]
    if roi.size == 0:
        return None

    # Convertir en niveaux de gris
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # Seuillage adaptatif pour isoler les zones claires (bulles blanches)
    _, thresh = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)

    # Morphologie pour fermer les trous dans la bulle
    kernel = np.ones((5, 5), np.uint8)
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Trouver les contours
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    # Prendre le contour qui contient le centre du texte
    text_center_x = x + w // 2 - x1
    text_center_y = y + h // 2 - y1

    best_contour = None
    for contour in contours:
        if cv2.pointPolygonTest(contour, (text_center_x, text_center_y), False) >= 0:
            best_contour = contour
            break

    if best_contour is None:
        # Fallback: prendre le plus grand contour
        best_contour = max(contours, key=cv2.contourArea)

    # Créer le masque de la bulle dans les coordonnées de l'image complète
    full_mask = np.zeros((ih, iw), dtype=np.uint8)
    # Décaler les coordonnées du contour
    shifted_contour = best_contour + np.array([x1, y1])
    cv2.fillPoly(full_mask, [shifted_contour], 255)

    return full_mask


def remove_text_smart_v2(
    image: np.ndarray,
    regions: List[TextRegion],
    padding: int = 4,
) -> Tuple[np.ndarray, List[Tuple[int, int, int]]]:
    """
    Suppression améliorée du texte avec détection de contour de bulle.

    Pour chaque région:
    1. Tente de détecter le contour réel de la bulle
    2. Si trouvé: remplit le contour avec la couleur de fond
    3. Si non trouvé: fallback sur l'inpainting OpenCV classique

    Returns:
        (image nettoyée, liste des couleurs de fond par région)
    """
    if not regions:
        return image.copy(), []

    result = image.copy()
    bg_colors = []

    for region in regions:
        x, y, w, h = region.bbox

        # Analyser la variance pour choisir la stratégie
        roi = image[max(0, y):min(image.shape[0], y + h),
                    max(0, x):min(image.shape[1], x + w)]

        if roi.size == 0:
            bg_colors.append((255, 255, 255))
            continue

        variance = float(np.var(roi))
        bg_color = _detect_background_color(image, region)

        if variance < 1200:
            # ── Fond uniforme : remplissage rectangulaire simple ──────────────
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(image.shape[1], x + w + padding)
            y2 = min(image.shape[0], y + h + padding)
            result[y1:y2, x1:x2] = bg_color
            bg_colors.append(bg_color)

        elif _is_likely_white_bubble(image, region):
            # ── Bulle blanche classique : essayer de détecter le contour ─────
            try:
                bubble_mask = detect_bubble_contour(image, region)
                if bubble_mask is not None:
                    # Remplir uniquement dans la zone de texte + padding
                    text_mask = np.zeros(image.shape[:2], dtype=np.uint8)
                    cv2.rectangle(
                        text_mask,
                        (max(0, x - padding), max(0, y - padding)),
                        (min(image.shape[1], x + w + padding), min(image.shape[0], y + h + padding)),
                        255, -1
                    )
                    combined_mask = cv2.bitwise_and(bubble_mask, text_mask)

                    # Appliquer le fond dans ce masque
                    result[combined_mask > 0] = bg_color
                    bg_colors.append(bg_color)
                else:
                    raise ValueError("Contour non détecté")
            except Exception:
                # Fallback: remplissage rectangulaire
                x1 = max(0, x - padding)
                y1 = max(0, y - padding)
                x2 = min(image.shape[1], x + w + padding)
                y2 = min(image.shape[0], y + h + padding)
                result[y1:y2, x1:x2] = bg_color
                bg_colors.append(bg_color)

        else:
            # ── Fond complexe : inpainting OpenCV ────────────────────────────
            mask = np.zeros(result.shape[:2], dtype=np.uint8)
            cv2.rectangle(
                mask,
                (max(0, x - padding), max(0, y - padding)),
                (min(result.shape[1], x + w + padding), min(result.shape[0], y + h + padding)),
                255, -1
            )
            result = cv2.inpaint(result, mask, inpaintRadius=4, flags=cv2.INPAINT_TELEA)
            bg_colors.append((255, 255, 255))

    logger.debug(f"✨ Inpainting v2: {len(regions)} zones traitées")
    return result, bg_colors


def _detect_background_color(
    image: np.ndarray,
    region: TextRegion,
    sample_radius: int = 3,
) -> Tuple[int, int, int]:
    """
    Détecte la couleur de fond dominant autour d'une région de texte.
    Échantillonne les pixels juste à l'extérieur de la bbox.
    """
    x, y, w, h = region.bbox
    ih, iw = image.shape[:2]
    samples = []

    # Échantillonner les 4 bords extérieurs
    for px in range(x, min(x + w, iw)):
        # Bord supérieur
        for dy in range(1, sample_radius + 1):
            sy = y - dy
            if 0 <= sy < ih:
                samples.append(image[sy, px])
        # Bord inférieur
        for dy in range(1, sample_radius + 1):
            sy = y + h + dy
            if 0 <= sy < ih:
                samples.append(image[sy, px])

    for py in range(y, min(y + h, ih)):
        # Bord gauche
        for dx in range(1, sample_radius + 1):
            sx = x - dx
            if 0 <= sx < iw:
                samples.append(image[py, sx])
        # Bord droit
        for dx in range(1, sample_radius + 1):
            sx = x + w + dx
            if 0 <= sx < iw:
                samples.append(image[py, sx])

    if not samples:
        return (255, 255, 255)

    # Couleur médiane (plus robuste que la moyenne pour éliminer les outliers)
    samples_array = np.array(samples)
    median_color = np.median(samples_array, axis=0).astype(int)
    return (int(median_color[0]), int(median_color[1]), int(median_color[2]))


def _is_likely_white_bubble(image: np.ndarray, region: TextRegion) -> bool:
    """
    Heuristique : est-ce que cette région est dans une bulle blanche classique?
    Vérifie si les pixels autour de la bbox sont majoritairement blancs/clairs.
    """
    x, y, w, h = region.bbox
    ih, iw = image.shape[:2]

    # Échantillonner quelques pixels autour
    bg_color = _detect_background_color(image, region)

    # Si la couleur médiane est très claire (>200 sur les 3 canaux)
    r, g, b = bg_color[2], bg_color[1], bg_color[0]  # BGR → RGB
    brightness = (r + g + b) / 3
    return brightness > 200


