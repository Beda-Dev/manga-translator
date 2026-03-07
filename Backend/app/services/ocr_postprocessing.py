"""
Post-processing OCR pour anglais → corrections des erreurs typiques
et tri dans l'ordre de lecture (gauche→droite, haut→bas).
"""

import re
import logging
from typing import List

from app.models.schemas import TextRegion

logger = logging.getLogger(__name__)

# ── Corrections typiques OCR sur texte anglais BD ────────────────────────────
# Format: (pattern_regex, remplacement)
OCR_CORRECTIONS = [
    # Confusions de caractères très communes sur polices BD
    (r'\b([A-Z])1\b', r'\1I'),          # "HE1LO" → "HELLO" (1 → I en contexte)
    (r'\b1([A-Z])', r'I\1'),            # "1T'S" → "IT'S"
    (r'(?<=[A-Za-z])0(?=[A-Za-z])', 'O'),  # "W0RLD" → "WORLD"
    (r'\|(?=[A-Za-z])', 'I'),           # "|t's" → "It's"
    (r'(?<=[A-Za-z])\|', 'I'),          # "WA|T" → "WAIT"
    (r'(?<!\w)rn(?!\w)', 'm'),          # "rn" souvent confondu avec "m"
    (r'(?<!\w)lI\b', 'II'),             # "lI" → "II"

    # Espaces parasites dans les mots (OCR BD très commun)
    (r'([A-Z])\s([A-Z])\s([A-Z])', r'\1\2\3'),   # "H E Y" → "HEY"
    (r'([A-Za-z])\s([A-Za-z])\s([A-Za-z])\s([A-Za-z])', r'\1\2\3\4'),

    # Apostrophes mal reconnues
    (r"'", "'"),      # apostrophe typographique → droite
    (r"`", "'"),      # backtick → apostrophe
    (r"´", "'"),

    # Points de suspension
    (r'\.{4,}', '...'),   # "....." → "..."
    (r'\. \. \.', '...'), # ". . ." → "..."

    # Tirets et traits
    (r'--+', '—'),         # "--" → "—"

    # Nettoyage ponctuation dupliquée
    (r'!!+', '!!'),        # "!!!" → "!!" (garder l'emphase mais limiter)
    (r'\?\?+', '??'),

    # Artefacts communs OCR
    (r'^\W+$', ''),        # Ligne uniquement de caractères spéciaux → vide
    (r'[^\x00-\x7F\u00C0-\u024F]', ''),  # Supprimer chars non-latin parasites
]

# Mots très courts probablement des artefacts OCR
MIN_MEANINGFUL_LENGTH = 1
MIN_CONFIDENCE_THRESHOLD = 0.35


def clean_ocr_text(text: str) -> str:
    """
    Nettoie le texte extrait par OCR.
    Corrige les erreurs typiques sur du texte anglais de BD.
    """
    if not text or not text.strip():
        return text

    result = text.strip()

    # Appliquer les corrections
    for pattern, replacement in OCR_CORRECTIONS:
        result = re.sub(pattern, replacement, result)

    # Normaliser les espaces multiples
    result = re.sub(r' {2,}', ' ', result)
    result = result.strip()

    return result


def filter_noise_regions(regions: List[TextRegion], min_confidence: float = MIN_CONFIDENCE_THRESHOLD) -> List[TextRegion]:
    """
    Filtre les régions qui sont probablement du bruit OCR.

    Critères d'élimination:
    - Confiance trop basse
    - Texte trop court après nettoyage (1-2 chars isolés)
    - Uniquement des chiffres isolés (numéros de page, etc.)
    - Regex de patterns non-textuels
    """
    filtered = []
    noise_patterns = [
        r'^\d+$',              # Uniquement des chiffres → numéro de page
        r'^[^\w]+$',           # Uniquement ponctuation
        r'^[a-zA-Z]$',         # Lettre unique isolée
        r'^\s*$',              # Vide
    ]

    for region in regions:
        # Filtre confiance
        if region.confidence < min_confidence:
            logger.debug(f"🗑️  Région filtrée (confiance {region.confidence:.2f}): '{region.original_text}'")
            continue

        text = clean_ocr_text(region.original_text)

        # Filtre patterns bruit
        is_noise = any(re.match(p, text.strip()) for p in noise_patterns)
        if is_noise:
            logger.debug(f"🗑️  Région filtrée (bruit): '{text}'")
            continue

        # Texte trop court (moins de 2 chars après nettoyage)
        if len(text.strip()) < 2:
            logger.debug(f"🗑️  Région filtrée (trop court): '{text}'")
            continue

        region.original_text = text
        filtered.append(region)

    removed = len(regions) - len(filtered)
    if removed > 0:
        logger.info(f"🧹 OCR post-processing: {removed} régions bruit supprimées, {len(filtered)} conservées")

    return filtered


def sort_regions_reading_order(regions: List[TextRegion], image_height: int = None) -> List[TextRegion]:
    """
    Trie les régions dans l'ordre de lecture occidental : gauche→droite, haut→bas.
    
    Algorithme:
    1. Divise en "lignes" (régions dont les bbox se chevauchent verticalement)
    2. Trie chaque ligne de gauche à droite
    3. Trie les lignes de haut en bas
    
    Ce tri est crucial pour que la traduction contextuelle soit cohérente :
    la bulle en haut à gauche est toujours la première du dialogue.
    """
    if not regions:
        return regions

    # Tolérance de chevauchement vertical pour grouper en "ligne"
    # Une région appartient à la même ligne si son centre Y est dans ±30% de hauteur
    LINE_OVERLAP_RATIO = 0.4

    def get_center(region: TextRegion):
        x, y, w, h = region.bbox
        return x + w / 2, y + h / 2

    def get_line_key(region: TextRegion):
        """Clé de tri pour regrouper les régions par ligne horizontale."""
        x, y, w, h = region.bbox
        return y  # Position Y du haut de la bbox

    # Tri initial par Y pour faciliter le groupement
    sorted_by_y = sorted(regions, key=lambda r: r.bbox[1])

    # Grouper en lignes
    lines = []
    current_line = [sorted_by_y[0]]
    current_line_bottom = sorted_by_y[0].bbox[1] + sorted_by_y[0].bbox[3]

    for region in sorted_by_y[1:]:
        region_top = region.bbox[1]
        region_height = region.bbox[3]

        # Si cette région chevauche la ligne courante
        overlap_threshold = region_height * LINE_OVERLAP_RATIO
        if region_top < current_line_bottom - overlap_threshold:
            current_line.append(region)
            # Mettre à jour le bas de la ligne courante
            region_bottom = region_top + region_height
            current_line_bottom = max(current_line_bottom, region_bottom)
        else:
            lines.append(current_line)
            current_line = [region]
            current_line_bottom = region_top + region_height

    lines.append(current_line)

    # Trier chaque ligne de gauche à droite, puis aplatir
    result = []
    for line in lines:
        sorted_line = sorted(line, key=lambda r: r.bbox[0])  # Tri par X
        result.extend(sorted_line)

    logger.debug(f"📖 Ordre de lecture: {len(result)} régions en {len(lines)} lignes")
    return result


def postprocess_regions(regions: List[TextRegion], image_height: int = None) -> List[TextRegion]:
    """
    Pipeline complet de post-processing OCR:
    1. Filtre le bruit
    2. Nettoie le texte
    3. Trie dans l'ordre de lecture
    """
    if not regions:
        return regions

    # 1. Nettoyage du texte de chaque région
    for region in regions:
        region.original_text = clean_ocr_text(region.original_text)

    # 2. Filtrage du bruit
    cleaned = filter_noise_regions(regions)

    # 3. Tri dans l'ordre de lecture
    ordered = sort_regions_reading_order(cleaned, image_height)

    return ordered
