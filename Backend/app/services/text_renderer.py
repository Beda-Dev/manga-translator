"""
Service de rendu du texte traduit dans les bulles.
Gère le word-wrapping, le redimensionnement automatique et l'anti-débordement.
Utilise Pillow pour le rendu de texte haute qualité.
"""

import logging
import os
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont

from app.models.schemas import FontOptions, TextRegion

logger = logging.getLogger(__name__)

# Police de repli si la police BD n'est pas disponible
FALLBACK_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",  # macOS
    "C:\\Windows\\Fonts\\arial.ttf",         # Windows
]


def render_translated_text(
    image: np.ndarray,
    regions: List[TextRegion],
    bg_colors: List[Tuple[int, int, int]],
    font_options: FontOptions,
) -> np.ndarray:
    """
    Réécrit le texte traduit dans les bulles de l'image nettoyée.

    Args:
        image: Image nettoyée (BGR, sans texte original)
        regions: Zones de texte avec texte traduit
        bg_colors: Couleurs de fond par région (pour l'adaptation du texte)
        font_options: Options typographiques

    Returns:
        Image avec le texte traduit intégré
    """
    # Convertir BGR → RGB pour Pillow
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_img = PILImage.fromarray(img_rgb)
    draw = ImageDraw.Draw(pil_img)

    for i, region in enumerate(regions):
        if not region.translated_text:
            continue

        bg_color = bg_colors[i] if i < len(bg_colors) else (255, 255, 255)
        # Convertir BGR → RGB pour Pillow
        bg_color_rgb = (bg_color[2], bg_color[1], bg_color[0])

        _render_text_in_region(draw, pil_img, region, bg_color_rgb, font_options)

    # Reconvertir RGB → BGR pour OpenCV
    result = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return result


def _render_text_in_region(
    draw: ImageDraw.Draw,
    image: PILImage.Image,
    region: TextRegion,
    bg_color: Tuple[int, int, int],
    options: FontOptions,
) -> None:
    """
    Rend le texte traduit dans une zone spécifique avec ajustement automatique.

    Algorithme:
    1. Charger la police à la taille maximale
    2. Découper le texte en lignes (word wrap)
    3. Vérifier si ça rentre dans la bbox
    4. Réduire la taille si nécessaire
    5. Dessiner le fond + contour + texte
    """
    x, y, w, h = region.bbox
    text = region.translated_text
    padding = options.text_padding

    # Zone utilisable pour le texte
    available_w = w - 2 * padding
    available_h = h - 2 * padding

    if available_w <= 0 or available_h <= 0:
        return

    font = _load_font(options.font_path, options.size_max)
    font_size = options.size_max

    # Réduire la taille jusqu'à ce que le texte rentre
    while font_size >= options.size_min:
        font = _load_font(options.font_path, font_size)
        lines = _wrap_text(draw, text, font, available_w)
        total_h = _calculate_text_height(draw, lines, font)

        if total_h <= available_h:
            break

        font_size -= 1

    # Si même à la taille min ça ne rentre pas, on tronque
    if font_size < options.size_min:
        font = _load_font(options.font_path, options.size_min)
        lines = _wrap_text(draw, text, font, available_w)
        lines = _truncate_lines(draw, lines, font, available_h)

    # Calculer la position centrée verticalement
    total_h = _calculate_text_height(draw, lines, font)
    text_x = x + padding
    text_y = y + padding + max(0, (available_h - total_h) // 2)

    # Dessiner le fond de la bulle (rectangle propre)
    draw.rectangle(
        [x + 1, y + 1, x + w - 1, y + h - 1],
        fill=bg_color,
    )

    # Parser la couleur de texte
    text_color = _hex_to_rgb(options.color)
    outline_color = _hex_to_rgb(options.outline_color)

    # Dessiner chaque ligne
    for line in lines:
        if not line.strip():
            bbox = draw.textbbox((0, 0), "Ay", font=font)
            text_y += (bbox[3] - bbox[1]) + 2
            continue

        # Centrer horizontalement dans la bbox
        line_bbox = draw.textbbox((0, 0), line, font=font)
        line_w = line_bbox[2] - line_bbox[0]
        line_x = x + padding + max(0, (available_w - line_w) // 2)

        # Dessiner le contour (outline)
        if options.outline_width > 0:
            for dx in range(-options.outline_width, options.outline_width + 1):
                for dy in range(-options.outline_width, options.outline_width + 1):
                    if dx == 0 and dy == 0:
                        continue
                    draw.text(
                        (line_x + dx, text_y + dy),
                        line,
                        font=font,
                        fill=outline_color,
                    )

        # Dessiner le texte principal
        draw.text((line_x, text_y), line, font=font, fill=text_color)

        # Avancer verticalement
        line_bbox = draw.textbbox((0, 0), line, font=font)
        text_y += (line_bbox[3] - line_bbox[1]) + 2

    logger.debug(f"✍️  Texte rendu ({font_size}pt, {len(lines)} lignes): '{text[:30]}...'")


def _wrap_text(
    draw: ImageDraw.Draw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> List[str]:
    """
    Coupe le texte en lignes pour tenir dans max_width pixels.
    Respecte les sauts de ligne existants et gère le word wrap.
    """
    lines = []
    # Séparer d'abord par les sauts de ligne explicites
    paragraphs = text.split("\n")

    for paragraph in paragraphs:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue

        current_line = words[0]

        for word in words[1:]:
            test_line = f"{current_line} {word}"
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_w = bbox[2] - bbox[0]

            if line_w <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        lines.append(current_line)

    return lines


def _calculate_text_height(
    draw: ImageDraw.Draw,
    lines: List[str],
    font: ImageFont.FreeTypeFont,
) -> int:
    """Calcule la hauteur totale du texte en pixels."""
    total = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line or "Ay", font=font)
        total += (bbox[3] - bbox[1]) + 2
    return total


def _truncate_lines(
    draw: ImageDraw.Draw,
    lines: List[str],
    font: ImageFont.FreeTypeFont,
    max_height: int,
) -> List[str]:
    """Coupe les lignes pour tenir dans max_height pixels."""
    result = []
    total = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line or "Ay", font=font)
        line_h = (bbox[3] - bbox[1]) + 2
        if total + line_h > max_height:
            break
        result.append(line)
        total += line_h
    return result


def _load_font(font_path: Optional[str], size: int) -> ImageFont.FreeTypeFont:
    """Charge une police TrueType avec fallback automatique."""
    paths_to_try = []
    if font_path:
        paths_to_try.append(font_path)
    paths_to_try.extend(FALLBACK_FONT_PATHS)

    for path in paths_to_try:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    # Fallback ultime: police bitmap intégrée Pillow
    logger.warning("⚠️  Aucune police TrueType trouvée, utilisation de la police par défaut")
    return ImageFont.load_default()


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convertit une couleur hex (#RRGGBB) en tuple RGB."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
