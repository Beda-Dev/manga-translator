"""
Service d'inpainting (suppression du texte original).
Utilise OpenCV pour reconstruire proprement les bulles de BD.

Stratégie:
  1. Créer un masque sur les zones de texte (bbox avec marge)
  2. Appliquer cv2.inpaint pour reconstruire le fond
  3. Optionnel: remplir avec la couleur dominante de la bulle
"""

import logging
from typing import List, Tuple

import cv2
import numpy as np

from app.models.schemas import TextRegion

logger = logging.getLogger(__name__)


def remove_text_from_image(
    image: np.ndarray,
    regions: List[TextRegion],
    padding: int = 3,
    method: str = "telea",
) -> np.ndarray:
    """
    Supprime le texte original de l'image en utilisant l'inpainting OpenCV.

    Args:
        image: Image source (BGR numpy array)
        regions: Zones de texte à supprimer
        padding: Pixels de marge autour de chaque bbox
        method: "telea" (rapide) | "ns" (Navier-Stokes, meilleur pour BD)

    Returns:
        Image avec le texte supprimé
    """
    if not regions:
        return image.copy()

    result = image.copy()
    mask = np.zeros(image.shape[:2], dtype=np.uint8)

    for region in regions:
        x, y, w, h = region.bbox
        # Ajouter du padding pour englober tout le texte
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(image.shape[1], x + w + padding)
        y2 = min(image.shape[0], y + h + padding)

        # Remplir le masque sur la zone de texte
        mask[y1:y2, x1:x2] = 255

    # Dilater légèrement le masque pour couvrir les anti-aliasing
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)

    # Choisir la méthode d'inpainting
    inpaint_method = cv2.INPAINT_TELEA if method == "telea" else cv2.INPAINT_NS
    result = cv2.inpaint(result, mask, inpaintRadius=3, flags=inpaint_method)

    logger.debug(f"🎨 Inpainting: {len(regions)} zones supprimées (méthode: {method})")
    return result


def fill_bubble_background(
    image: np.ndarray,
    region: TextRegion,
    padding: int = 2,
) -> Tuple[np.ndarray, Tuple[int, int, int]]:
    """
    Alternative à l'inpainting: détecte et remplit avec la couleur de fond de la bulle.
    Utile quand la bulle est uni-colore (blanc ou couleur unie).

    Args:
        image: Image source
        region: Zone de texte
        padding: Marge intérieure

    Returns:
        (image modifiée, couleur de fond détectée en BGR)
    """
    x, y, w, h = region.bbox
    result = image.copy()

    # Échantillonner les bords de la bbox pour détecter la couleur du fond
    border_pixels = []

    # Bord supérieur et inférieur
    y_top = max(0, y - 2)
    y_bot = min(image.shape[0] - 1, y + h + 2)
    for cx in range(x, min(x + w, image.shape[1])):
        border_pixels.append(image[y_top, cx])
        border_pixels.append(image[y_bot, cx])

    # Bord gauche et droit
    x_left = max(0, x - 2)
    x_right = min(image.shape[1] - 1, x + w + 2)
    for cy in range(y, min(y + h, image.shape[0])):
        border_pixels.append(image[cy, x_left])
        border_pixels.append(image[cy, x_right])

    if not border_pixels:
        bg_color = (255, 255, 255)  # Blanc par défaut
    else:
        # Couleur médiane des bords
        pixels_array = np.array(border_pixels)
        bg_color = tuple(int(c) for c in np.median(pixels_array, axis=0))

    # Remplir la zone avec la couleur de fond
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(image.shape[1], x + w + padding)
    y2 = min(image.shape[0], y + h + padding)
    result[y1:y2, x1:x2] = bg_color

    return result, bg_color


def smart_remove_text(
    image: np.ndarray,
    regions: List[TextRegion],
) -> Tuple[np.ndarray, List[Tuple[int, int, int]]]:
    """
    Suppression intelligente du texte:
    - Détecte si la bulle est blanche/unie → remplissage simple (plus propre)
    - Sinon → inpainting OpenCV

    Args:
        image: Image source
        regions: Zones de texte

    Returns:
        (image nettoyée, liste des couleurs de fond par région)
    """
    result = image.copy()
    bg_colors = []

    for region in regions:
        x, y, w, h = region.bbox

        # Extraire la région et analyser la variance de couleur
        roi = image[max(0, y):min(image.shape[0], y + h),
                    max(0, x):min(image.shape[1], x + w)]

        if roi.size == 0:
            bg_colors.append((255, 255, 255))
            continue

        # Calculer la variance pour détecter si le fond est uniforme
        variance = float(np.var(roi))

        if variance < 800:
            # Fond uniforme → remplissage simple, plus propre que l'inpainting
            result, bg_color = fill_bubble_background(result, region, padding=3)
            bg_colors.append(bg_color)
        else:
            # Fond complexe → inpainting
            mask = np.zeros(result.shape[:2], dtype=np.uint8)
            mask[max(0, y - 2):min(result.shape[0], y + h + 2),
                 max(0, x - 2):min(result.shape[1], x + w + 2)] = 255
            result = cv2.inpaint(result, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
            bg_colors.append((255, 255, 255))

    logger.debug(f"✨ Smart inpainting: {len(regions)} zones traitées")
    return result, bg_colors
