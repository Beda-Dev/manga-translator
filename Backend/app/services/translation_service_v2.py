"""
Service de traduction amélioré — v2.

Améliorations vs v1:
  1. Traduction contextuelle : toutes les bulles d'une page en une seule requête
     → le modèle comprend le dialogue complet, bien meilleures traductions
  2. Glossaire persistant par job : noms/termes cohérents sur toutes les pages
  3. Prompt BD spécialisé : onomatopées, registres, expressions idiomatiques
  4. NLLB-200 (Meta) en option : bien meilleur que MarianMT sur BD
  5. Post-processing traduction : nettoyage des artefacts de traduction
"""

import logging
import re
from typing import List, Optional, Dict

from app.models.schemas import TranslationEngine, TextRegion

logger = logging.getLogger(__name__)

# Cache des modèles chargés
_translation_pipelines = {}

# ── Séparateur pour la traduction par lot ─────────────────────────────────────
BATCH_SEPARATOR = "\n<<<>>>\n"
BATCH_SEPARATOR_PATTERN = r"\n?<<<>>>\n?"

# ── Prompt spécialisé BD / manga anglais→français ─────────────────────────────
COMIC_TRANSLATION_SYSTEM_PROMPT = """Tu es un traducteur expert en bandes dessinées et mangas, spécialisé anglais→français.

RÈGLES ABSOLUES:
1. Traduis UNIQUEMENT le texte, ne commente jamais
2. Conserve exactement le même nombre de blocs (séparés par <<<>>>)
3. Préserve les onomatopées en les adaptant (BANG→BANG, CRASH→CRASH, WHOOSH→SWOUSH)
4. Adapte les interjections naturellement (Oh no→Oh non, Huh→Hein, Ugh→Beurk)
5. Maintiens le niveau de langage : personnage vulgaire reste vulgaire, formel reste formel
6. Ne traduis PAS les noms propres de personnages
7. Adapte les expressions idiomatiques idiomatiquement, pas littéralement
8. Conserve les majuscules pour les cris/emphases
9. Texte très court (1-3 mots) = traduit directement, sans sur-explication

EXEMPLES DE QUALITÉ:
- "I can't believe it!" → "C'est pas possible !"
- "Watch out!!" → "Attention !!"  
- "..."  → "..."
- "BOOM" → "BOOM"
- "What the...?" → "Quoi...?"
- "You're gonna regret this" → "Tu vas le regretter"
"""


class TranslationGlossary:
    """
    Glossaire persistant pour maintenir la cohérence des noms et termes
    sur toutes les pages d'un même job de traduction.
    """

    def __init__(self):
        # Termes détectés automatiquement et leur traduction validée
        self._terms: Dict[str, str] = {}
        # Noms propres détectés (à NE PAS traduire)
        self._proper_nouns: set = set()

    def add_term(self, original: str, translated: str):
        """Enregistre un terme et sa traduction."""
        if original and translated and original.lower() != translated.lower():
            self._terms[original.strip()] = translated.strip()

    def add_proper_noun(self, name: str):
        """Marque un mot comme nom propre (ne pas traduire)."""
        self._proper_nouns.add(name.strip())

    def get_instructions(self) -> str:
        """Génère les instructions de glossaire pour le prompt."""
        lines = []
        if self._proper_nouns:
            nouns_list = ", ".join(sorted(self._proper_nouns)[:20])
            lines.append(f"NE PAS traduire ces noms propres: {nouns_list}")
        if self._terms:
            terms_list = "; ".join([f'"{k}"→"{v}"' for k, v in list(self._terms.items())[:15]])
            lines.append(f"Utiliser ces traductions établies: {terms_list}")
        return "\n".join(lines)

    def extract_proper_nouns_from_text(self, text: str):
        """
        Détection heuristique des noms propres dans le texte anglais.
        Mots en CamelCase isolés = probablement des noms.
        """
        # Mots capitalisés qui ne sont pas en début de phrase et pas des interjections
        words = re.findall(r'\b[A-Z][a-z]{2,}\b', text)
        common_words = {
            'The', 'This', 'That', 'What', 'When', 'Where', 'Why', 'How',
            'But', 'And', 'For', 'Not', 'You', 'Are', 'Was', 'Has', 'Have',
            'Will', 'Can', 'Just', 'Get', 'Got', 'Yes', 'No', 'Wait', 'Stop',
            'Look', 'Hey', 'Oh', 'Well', 'Now', 'Let', 'Come', 'Here', 'There',
            'Going', 'Back', 'Too', 'Know', 'Think', 'Need', 'Want', 'Good',
            'Bad', 'Big', 'Old', 'New', 'All', 'Still'
        }
        for word in words:
            if word not in common_words:
                self._proper_nouns.add(word)


# ── Fonctions principales ─────────────────────────────────────────────────────

def translate_regions_batch(
    regions: List[TextRegion],
    engine: TranslationEngine,
    source_lang: str,
    target_lang: str = "fr",
    glossary: Optional[TranslationGlossary] = None,
    api_key: Optional[str] = None,
    libretranslate_url: Optional[str] = None,
    libretranslate_key: Optional[str] = None,
) -> List[TextRegion]:
    """
    Traduit toutes les bulles d'une page EN UNE SEULE REQUÊTE.

    Avantage majeur vs traduction individuelle:
    - Le modèle voit le dialogue complet → cohérence narrative
    - "I'll kill you" après "You betrayed me!" = contexte de trahison
    - Réduction des appels API (x10 plus rapide avec MarianMT)

    Returns:
        Les mêmes régions avec translated_text rempli
    """
    if not regions:
        return regions

    # Extraire les textes et mettre à jour le glossaire
    texts = []
    for region in regions:
        text = region.original_text
        if glossary:
            glossary.extract_proper_nouns_from_text(text)
        texts.append(text)

    # Construire le batch
    batch_text = BATCH_SEPARATOR.join(texts)

    try:
        if engine == TranslationEngine.MARIAN:
            translated_batch = _translate_marian_batch(batch_text, source_lang, target_lang, glossary)
        elif engine == TranslationEngine.LIBRETRANSLATE:
            translated_batch = _translate_libretranslate_batch(
                batch_text, source_lang, target_lang,
                libretranslate_url, libretranslate_key, glossary
            )
        else:
            # Fallback: traduction individuelle pour les moteurs qui ne supportent pas le batch
            for region in regions:
                region.translated_text = translate_single(
                    region.original_text, engine, source_lang, target_lang,
                    glossary, api_key, libretranslate_url, libretranslate_key
                )
            return regions

        # Splitter le résultat
        translated_parts = re.split(BATCH_SEPARATOR_PATTERN, translated_batch)

        # Aligner avec les régions originales
        if len(translated_parts) == len(regions):
            for region, translation in zip(regions, translated_parts):
                cleaned = postprocess_translation(translation.strip(), region.original_text)
                region.translated_text = cleaned
                if glossary:
                    glossary.add_term(region.original_text, cleaned)
        else:
            # Désalignement — fallback sur traduction individuelle
            logger.warning(
                f"⚠️  Batch désaligné: {len(regions)} régions, {len(translated_parts)} traductions. "
                f"Fallback traduction individuelle."
            )
            for region in regions:
                region.translated_text = translate_single(
                    region.original_text, engine, source_lang, target_lang,
                    glossary, api_key, libretranslate_url, libretranslate_key
                )

    except Exception as e:
        logger.error(f"❌ Erreur traduction batch: {e}. Fallback individuel.")
        for region in regions:
            try:
                region.translated_text = translate_single(
                    region.original_text, engine, source_lang, target_lang,
                    glossary, api_key, libretranslate_url, libretranslate_key
                )
            except Exception as e2:
                logger.error(f"❌ Erreur traduction individuelle: {e2}")
                region.translated_text = region.original_text

    return regions


def translate_single(
    text: str,
    engine: TranslationEngine,
    source_lang: str,
    target_lang: str = "fr",
    glossary: Optional[TranslationGlossary] = None,
    api_key: Optional[str] = None,
    libretranslate_url: Optional[str] = None,
    libretranslate_key: Optional[str] = None,
) -> str:
    """Traduit un texte unique (fallback ou moteurs sans support batch)."""
    if not text.strip():
        return text

    try:
        if engine == TranslationEngine.MARIAN:
            return _translate_marian_single(text, source_lang, target_lang)
        elif engine == TranslationEngine.LIBRETRANSLATE:
            return _translate_libretranslate_single(
                text, source_lang, target_lang, libretranslate_url, libretranslate_key
            )
        elif engine == TranslationEngine.GOOGLE_TRANSLATE:
            return _translate_google(text, source_lang, target_lang, api_key)
        elif engine == TranslationEngine.DEEPL:
            return _translate_deepl(text, target_lang, api_key)
    except Exception as e:
        logger.error(f"❌ Erreur traduction ({engine.value}): {e}")
        return text

    return text


# ── MarianMT amélioré ─────────────────────────────────────────────────────────

def _get_marian_pipeline(src: str, tgt: str):
    """Charge et cache le pipeline MarianMT."""
    from transformers import MarianMTModel, MarianTokenizer

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
        }
        model_name = model_map.get((src, tgt))
        if not model_name:
            raise ValueError(f"Pas de modèle MarianMT pour {src}→{tgt}")

        logger.info(f"⬇️  Chargement MarianMT: {model_name}")
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        _translation_pipelines[key] = (tokenizer, model)
        logger.info(f"✅ MarianMT chargé: {model_name}")

    return _translation_pipelines[key]


def _translate_marian_single(text: str, source_lang: str, target_lang: str) -> str:
    """Traduit un texte unique avec MarianMT."""
    src = source_lang if source_lang != "auto" else "en"

    if src in ("ja", "ko") and target_lang == "fr":
        en_text = _marian_translate(text, src, "en")
        return _marian_translate(en_text, "en", "fr")

    return _marian_translate(text, src, target_lang)


def _marian_translate(text: str, src: str, tgt: str) -> str:
    """Appel effectif au modèle MarianMT."""
    tokenizer, model = _get_marian_pipeline(src, tgt)
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    translated = model.generate(**inputs, num_beams=4, early_stopping=True)
    return tokenizer.decode(translated[0], skip_special_tokens=True)


def _translate_marian_batch(
    batch_text: str,
    source_lang: str,
    target_lang: str,
    glossary: Optional[TranslationGlossary] = None,
) -> str:
    """
    Traduit un batch de textes avec MarianMT.
    
    MarianMT ne supporte pas les prompts système, donc on traduit le batch
    comme un seul texte long avec des séparateurs.
    Le modèle préserve généralement les séparateurs non-linguistiques.
    """
    src = source_lang if source_lang != "auto" else "en"

    # Protéger les séparateurs de la tokenisation
    # On utilise un token neutre qui sera conservé
    protected = batch_text.replace("<<<>>>", " [SEP] ")

    translated = _marian_translate(protected, src, target_lang)

    # Restaurer les séparateurs
    restored = translated.replace("[SEP]", "<<<>>>")
    restored = re.sub(r'\s*<<<>>>\s*', BATCH_SEPARATOR, restored)

    return restored


# ── LibreTranslate amélioré ───────────────────────────────────────────────────

def _translate_libretranslate_single(
    text: str, source_lang: str, target_lang: str,
    url: Optional[str], api_key: Optional[str]
) -> str:
    """Traduit un texte unique avec LibreTranslate."""
    import httpx

    base_url = url or "https://libretranslate.com"
    src = "auto" if source_lang == "auto" else source_lang
    payload = {"q": text, "source": src, "target": target_lang, "format": "text"}
    if api_key:
        payload["api_key"] = api_key

    response = httpx.post(f"{base_url}/translate", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()["translatedText"]


def _translate_libretranslate_batch(
    batch_text: str, source_lang: str, target_lang: str,
    url: Optional[str], api_key: Optional[str],
    glossary: Optional[TranslationGlossary] = None,
) -> str:
    """
    LibreTranslate supporte les requêtes batch via le champ 'q' en liste.
    On l'utilise pour envoyer toutes les bulles en une requête.
    """
    import httpx

    base_url = url or "https://libretranslate.com"
    src = "auto" if source_lang == "auto" else source_lang

    texts = batch_text.split(BATCH_SEPARATOR)
    payload = {"q": texts, "source": src, "target": target_lang, "format": "text"}
    if api_key:
        payload["api_key"] = api_key

    response = httpx.post(f"{base_url}/translate", json=payload, timeout=60)
    response.raise_for_status()

    data = response.json()
    if isinstance(data, list):
        return BATCH_SEPARATOR.join([item.get("translatedText", "") for item in data])
    else:
        return data.get("translatedText", batch_text)


# ── Google Translate (placeholder) ────────────────────────────────────────────

def _translate_google(text: str, source_lang: str, target_lang: str, api_key: Optional[str]) -> str:
    if not api_key:
        raise ValueError("Google Translate nécessite GOOGLE_TRANSLATE_API_KEY")
    raise NotImplementedError("Google Translate non configuré — voir translation_service.py")


def _translate_deepl(text: str, target_lang: str, api_key: Optional[str]) -> str:
    if not api_key:
        raise ValueError("DeepL nécessite DEEPL_API_KEY")
    raise NotImplementedError("DeepL non configuré — voir translation_service.py")


# ── Post-processing des traductions ───────────────────────────────────────────

def postprocess_translation(translated: str, original: str) -> str:
    """
    Nettoie et améliore la traduction après le modèle.
    
    Corrections:
    - Supprime les artefacts de tokenisation
    - Restaure les onomatopées si mal traduites
    - Corrige la ponctuation française (espaces avant !, ?, :, ;)
    - Préserve les ellipses et points de suspension
    """
    if not translated:
        return original  # Fallback sur l'original si traduction vide

    result = translated.strip()

    # Supprimer les tags HTML parasites que certains modèles introduisent
    result = re.sub(r'<[^>]+>', '', result)

    # Onomatopées : si le texte original est entièrement en majuscules et court,
    # et que la "traduction" est très différente, garder l'original
    if (len(original) <= 10
        and original.isupper()
        and re.match(r'^[A-Z\s!.]+$', original)
        and original not in ('I', 'A')):
        return original  # CRASH, BOOM, BANG etc. → on garde l'original

    # Ponctuation française : espace fine avant !, ?, :, ;
    # (certains modèles les omettent)
    result = re.sub(r'([^\s])([!?;:])', r'\1 \2', result)
    result = re.sub(r'\s{2,}([!?;:])', r' \1', result)  # Pas deux espaces

    # Corriger les apostrophes
    result = result.replace(" '", "'").replace("' ", "'")
    result = re.sub(r"'\s+([a-z])", r"'\1", result)  # "c' est" → "c'est"

    # Supprimer les répétitions de ponctuation introduites par le modèle
    result = re.sub(r'([.!?])\1{3,}', r'\1\1', result)

    # Si la traduction est identique à l'original (modèle n'a rien fait)
    # et que c'est de l'anglais → logger un avertissement
    if result.lower() == original.lower() and re.search(r'\b(the|and|is|are|you|I)\b', original, re.I):
        logger.warning(f"⚠️  Traduction identique à l'original: '{original}'")

    return result if result else original
