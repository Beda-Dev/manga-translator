"""
Service de traduction multi-moteurs.

Moteurs supportés:
  - MarianMT    : HuggingFace Transformers — gratuit, hors ligne
  - LibreTranslate : Open source, auto-hébergeable
  - Google Translate: Payant (placeholder)
  - DeepL       : Payant (placeholder)
"""

import logging
from typing import Optional

from app.models.schemas import TranslationEngine

logger = logging.getLogger(__name__)

# Cache des pipelines de traduction
_translation_pipelines = {}


def translate_text(
    text: str,
    engine: TranslationEngine,
    source_lang: str,
    target_lang: str = "fr",
    api_key: Optional[str] = None,
    libretranslate_url: Optional[str] = None,
    libretranslate_key: Optional[str] = None,
) -> str:
    """
    Traduit un texte depuis source_lang vers target_lang.

    Args:
        text: Texte à traduire
        engine: Moteur de traduction
        source_lang: Langue source ("en", "ja", "ko", "zh", "auto")
        target_lang: Langue cible (défaut "fr")
        api_key: Clé API Google Translate ou DeepL
        libretranslate_url: URL de l'instance LibreTranslate
        libretranslate_key: Clé API LibreTranslate

    Returns:
        Texte traduit
    """
    if not text.strip():
        return text

    logger.debug(f"🌐 Traduction [{source_lang}→{target_lang}] via {engine.value}: '{text[:50]}...'")

    try:
        if engine == TranslationEngine.MARIAN:
            return _translate_marian(text, source_lang, target_lang)
        elif engine == TranslationEngine.LIBRETRANSLATE:
            return _translate_libretranslate(text, source_lang, target_lang, libretranslate_url, libretranslate_key)
        elif engine == TranslationEngine.GOOGLE_TRANSLATE:
            return _translate_google(text, source_lang, target_lang, api_key)
        elif engine == TranslationEngine.DEEPL:
            return _translate_deepl(text, target_lang, api_key)
        else:
            raise ValueError(f"Moteur inconnu: {engine}")
    except Exception as e:
        logger.error(f"❌ Erreur traduction ({engine.value}): {e}")
        return text  # Retourner le texte original en cas d'erreur


# ── MarianMT (HuggingFace) ────────────────────────────────────────────────────

def _translate_marian(text: str, source_lang: str, target_lang: str) -> str:
    """
    Traduction avec MarianMT (HuggingFace Transformers).
    pip install transformers sentencepiece torch
    Modèles téléchargés automatiquement depuis HuggingFace.

    Pour le japonais/coréen → français, une traduction en deux étapes est utilisée:
    ja/ko → en → fr (meilleure qualité car les modèles directs sont rares)
    """
    from transformers import MarianMTModel, MarianTokenizer

    def _load_pipeline(src: str, tgt: str):
        """Charge et cache un pipeline de traduction."""
        key = f"marian_{src}_{tgt}"
        if key not in _translation_pipelines:
            model_map = {
                ("en", "fr"): "Helsinki-NLP/opus-mt-en-fr",
                ("ja", "en"): "Helsinki-NLP/opus-mt-ja-en",
                ("ko", "en"): "Helsinki-NLP/opus-mt-ko-en",
                ("zh", "en"): "Helsinki-NLP/opus-mt-zh-en",
                ("zh", "fr"): "Helsinki-NLP/opus-mt-zh-fr",
                ("de", "fr"): "Helsinki-NLP/opus-mt-de-fr",
                ("es", "fr"): "Helsinki-NLP/opus-mt-es-fr",
                ("it", "fr"): "Helsinki-NLP/opus-mt-it-fr",
                ("pt", "fr"): "Helsinki-NLP/opus-mt-pt-fr",
            }
            model_name = model_map.get((src, tgt))
            if not model_name:
                raise ValueError(f"Pas de modèle MarianMT pour {src}→{tgt}")

            logger.info(f"⬇️  Chargement modèle MarianMT: {model_name}")
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            model = MarianMTModel.from_pretrained(model_name)
            _translation_pipelines[key] = (tokenizer, model)

        return _translation_pipelines[key]

    def _translate_once(txt: str, src: str, tgt: str) -> str:
        tokenizer, model = _load_pipeline(src, tgt)
        inputs = tokenizer(txt, return_tensors="pt", padding=True, truncation=True, max_length=512)
        translated = model.generate(**inputs)
        return tokenizer.decode(translated[0], skip_special_tokens=True)

    # Résoudre la langue source (si "auto", on suppose anglais)
    src = source_lang if source_lang != "auto" else "en"

    # Langues sans modèle direct → passer par l'anglais
    if src in ("ja", "ko") and target_lang == "fr":
        en_text = _translate_once(text, src, "en")
        return _translate_once(en_text, "en", "fr")

    return _translate_once(text, src, target_lang)


# ── LibreTranslate ─────────────────────────────────────────────────────────────

def _translate_libretranslate(
    text: str,
    source_lang: str,
    target_lang: str,
    url: Optional[str],
    api_key: Optional[str],
) -> str:
    """
    Traduction via LibreTranslate (open source).
    Instance publique: https://libretranslate.com
    Auto-hébergeable: https://github.com/LibreTranslate/LibreTranslate

    pip install libretranslatepy  (optionnel, on utilise requests ici)
    """
    import httpx

    base_url = url or "https://libretranslate.com"
    src = "auto" if source_lang == "auto" else source_lang

    payload = {
        "q": text,
        "source": src,
        "target": target_lang,
        "format": "text",
    }
    if api_key:
        payload["api_key"] = api_key

    response = httpx.post(f"{base_url}/translate", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()["translatedText"]


# ── Google Translate (placeholder) ────────────────────────────────────────────

def _translate_google(
    text: str,
    source_lang: str,
    target_lang: str,
    api_key: Optional[str],
) -> str:
    """
    Traduction via Google Cloud Translation API v2.
    pip install google-cloud-translate
    Nécessite une clé API valide.

    PLACEHOLDER: Décommenter et configurer avec votre clé.
    """
    if not api_key:
        raise ValueError(
            "Google Translate nécessite GOOGLE_TRANSLATE_API_KEY dans .env"
        )

    # ── PLACEHOLDER GOOGLE TRANSLATE ─────────────────────────────────────────
    # import httpx
    # src = None if source_lang == "auto" else source_lang
    # params = {
    #     "q": text,
    #     "target": target_lang,
    #     "key": api_key,
    # }
    # if src:
    #     params["source"] = src
    # response = httpx.get(
    #     "https://translation.googleapis.com/language/translate/v2",
    #     params=params,
    #     timeout=30,
    # )
    # response.raise_for_status()
    # return response.json()["data"]["translations"][0]["translatedText"]
    # ─────────────────────────────────────────────────────────────────────────

    raise NotImplementedError(
        "Google Translate non configuré. Décommentez le code dans translation_service.py "
        "et ajoutez GOOGLE_TRANSLATE_API_KEY dans .env"
    )


# ── DeepL (placeholder) ───────────────────────────────────────────────────────

def _translate_deepl(text: str, target_lang: str, api_key: Optional[str]) -> str:
    """
    Traduction via DeepL API.
    pip install deepl
    Nécessite une clé API valide.

    PLACEHOLDER: Décommenter et configurer avec votre clé.
    """
    if not api_key:
        raise ValueError("DeepL nécessite DEEPL_API_KEY dans .env")

    # ── PLACEHOLDER DEEPL ─────────────────────────────────────────────────────
    # import deepl
    # translator = deepl.Translator(api_key)
    # deepl_lang = target_lang.upper()
    # if deepl_lang == "FR":
    #     deepl_lang = "FR"
    # result = translator.translate_text(text, target_lang=deepl_lang)
    # return result.text
    # ─────────────────────────────────────────────────────────────────────────

    raise NotImplementedError(
        "DeepL non configuré. Décommentez le code dans translation_service.py "
        "et ajoutez DEEPL_API_KEY dans .env"
    )
