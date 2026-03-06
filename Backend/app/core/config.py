"""
Configuration centrale de l'application.
Toutes les variables d'environnement et paramètres configurables sont ici.
"""

from typing import List, Literal, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "Manga Translator"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://your-frontend.vercel.app"]

    # ── Répertoires de stockage local ────────────────────────────────────────
    UPLOAD_DIR: str = "/tmp/manga_translator/uploads"
    OUTPUT_DIR: str = "/tmp/manga_translator/outputs"
    TEMP_DIR: str = "/tmp/manga_translator/temp"

    # ── Moteur OCR ───────────────────────────────────────────────────────────
    # Options: "easyocr" | "paddleocr" | "tesseract" | "google_vision"
    OCR_ENGINE: Literal["easyocr", "paddleocr", "tesseract", "google_vision"] = "easyocr"

    # Langues source supportées par l'OCR
    OCR_SOURCE_LANG: str = "en"  # "en", "ja", "ko", "zh"

    # Clé API Google Vision (placeholder — laisser vide pour utiliser open source)
    GOOGLE_VISION_API_KEY: Optional[str] = None  # "YOUR_GOOGLE_VISION_API_KEY"

    # ── Moteur de traduction ─────────────────────────────────────────────────
    # Options: "libretranslate" | "marian" | "google_translate" | "deepl"
    TRANSLATION_ENGINE: Literal["libretranslate", "marian", "google_translate", "deepl"] = "marian"

    # Langue cible
    TRANSLATION_TARGET_LANG: str = "fr"

    # LibreTranslate (auto-hébergé ou instance publique)
    LIBRETRANSLATE_URL: str = "https://libretranslate.com"
    LIBRETRANSLATE_API_KEY: Optional[str] = None  # "YOUR_LIBRETRANSLATE_KEY"

    # Google Translate (placeholder)
    GOOGLE_TRANSLATE_API_KEY: Optional[str] = None  # "YOUR_GOOGLE_TRANSLATE_KEY"

    # DeepL (placeholder)
    DEEPL_API_KEY: Optional[str] = None  # "YOUR_DEEPL_API_KEY"

    # Modèle MarianMT (HuggingFace) — téléchargé automatiquement
    MARIAN_MODEL_EN_FR: str = "Helsinki-NLP/opus-mt-en-fr"
    MARIAN_MODEL_JA_FR: str = "Helsinki-NLP/opus-mt-ja-fr"
    MARIAN_MODEL_KO_EN: str = "Helsinki-NLP/opus-mt-ko-en"  # Ko→En puis En→Fr
    MARIAN_MODEL_ZH_FR: str = "Helsinki-NLP/opus-mt-zh-fr"

    # ── Polices et typographie ───────────────────────────────────────────────
    FONT_PATH: str = "app/assets/fonts/Bangers-Regular.ttf"  # Police BD par défaut
    FONT_SIZE_MAX: int = 24
    FONT_SIZE_MIN: int = 8
    FONT_COLOR: str = "#000000"       # Noir
    FONT_OUTLINE_COLOR: str = "#FFFFFF"  # Contour blanc
    FONT_OUTLINE_WIDTH: int = 1
    TEXT_PADDING: int = 4              # Pixels de marge dans la bulle

    # ── Supabase Storage (placeholder) ──────────────────────────────────────
    SUPABASE_URL: Optional[str] = None          # "https://xxxx.supabase.co"
    SUPABASE_KEY: Optional[str] = None          # "YOUR_SUPABASE_ANON_KEY"
    SUPABASE_BUCKET: str = "manga-translations"
    USE_SUPABASE: bool = False  # Mettre True pour activer le stockage cloud

    # ── Traitement parallèle ─────────────────────────────────────────────────
    MAX_PARALLEL_PAGES: int = 4
    MAX_FILE_SIZE_MB: int = 100

    # ── Nettoyage automatique ────────────────────────────────────────────────
    CLEANUP_AFTER_HOURS: int = 24  # Suppression des fichiers temporaires

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()