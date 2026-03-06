# 🎌 Manga Translator Backend

Backend IA complet pour la traduction automatique de bandes dessinées et webtoons.  
Construit avec **FastAPI** + **EasyOCR** + **MarianMT (HuggingFace)** + **OpenCV** + **Pillow**.

---

## 🏗️ Architecture

```
app/
├── main.py                    # Entrée FastAPI + middlewares
├── core/
│   ├── config.py              # ⚙️ Tous les paramètres configurables
│   ├── job_manager.py         # 📋 Gestion des jobs en mémoire
│   └── logging_config.py      # 📝 Logs colorés
├── api/routes/
│   ├── translate.py           # POST /translate
│   ├── status.py              # GET /status/{job_id}
│   ├── download.py            # GET /download/{job_id}
│   └── health.py              # GET /health
├── services/
│   ├── translation_pipeline.py # 🔄 Orchestrateur principal
│   ├── ocr_service.py         # 🔍 OCR multi-moteurs
│   ├── translation_service.py # 🌐 Traduction multi-moteurs
│   ├── inpainting_service.py  # 🎨 Suppression du texte (OpenCV)
│   ├── text_renderer.py       # ✍️  Réécriture dans les bulles (Pillow)
│   ├── file_extractor.py      # 📦 Extraction CBZ/CBR/PDF
│   └── storage_service.py     # ☁️  Supabase Storage (optionnel)
└── models/
    └── schemas.py             # 📐 Modèles Pydantic
```

## Pipeline de traitement par page

```
Image → [OCR] → Zones de texte
              → [Traduction] → Texte traduit
              → [Inpainting OpenCV] → Image nettoyée
              → [Rendu Pillow] → Image finale traduite
```

---

## 🚀 Installation rapide

### Option 1: Docker (recommandé)

```bash
cp .env.example .env
# Éditez .env selon vos besoins
docker-compose up --build
```

### Option 2: Python local

```bash
# Python 3.10+
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Dépendances système (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-fra tesseract-ocr-jpn unrar

cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

---

## 🔧 Configuration

Tous les paramètres sont dans `.env`:

### Moteurs OCR disponibles

| Moteur | Qualité | Vitesse | Coût | Config requise |
|--------|---------|---------|------|----------------|
| `easyocr` | ⭐⭐⭐⭐ | 🐢 Moyen | Gratuit | Aucune |
| `paddleocr` | ⭐⭐⭐⭐⭐ | ⚡ Rapide | Gratuit | `pip install paddlepaddle paddleocr` |
| `tesseract` | ⭐⭐⭐ | ⚡ Rapide | Gratuit | `tesseract-ocr` système |
| `google_vision` | ⭐⭐⭐⭐⭐ | ⚡ Rapide | Payant | `GOOGLE_VISION_API_KEY` |

### Moteurs de traduction disponibles

| Moteur | Qualité | Offline | Coût | Config requise |
|--------|---------|---------|------|----------------|
| `marian` | ⭐⭐⭐⭐ | ✅ Oui | Gratuit | Modèles HuggingFace auto-téléchargés |
| `libretranslate` | ⭐⭐⭐ | ✅ Si auto-hébergé | Gratuit | Instance LT ou clé API |
| `google_translate` | ⭐⭐⭐⭐⭐ | ❌ Non | Payant | `GOOGLE_TRANSLATE_API_KEY` |
| `deepl` | ⭐⭐⭐⭐⭐ | ❌ Non | Freemium | `DEEPL_API_KEY` |

---

## 📡 API

### `POST /translate`

Lance une traduction. Retourne immédiatement un `job_id`.

```bash
curl -X POST http://localhost:8000/translate \
  -F "file=@my-manga.cbz" \
  -F "ocr_engine=easyocr" \
  -F "translation_engine=marian" \
  -F "source_lang=ja" \
  -F "target_lang=fr" \
  -F "output_format=cbz" \
  -F 'font_options={"size_max": 20, "color": "#000000"}'
```

**Réponse:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Traduction lancée pour 'my-manga.cbz'",
  "total_pages": 42,
  "status_url": "/status/550e8400-...",
  "download_url": "/download/550e8400-..."
}
```

### `GET /status/{job_id}`

```bash
curl http://localhost:8000/status/550e8400-...
```

**Réponse:**
```json
{
  "job_id": "550e8400-...",
  "status": "processing",
  "progress": 45.2,
  "total_pages": 42,
  "processed_pages": 19,
  "pages": [...]
}
```

### `GET /download/{job_id}`

Télécharge le fichier final (CBZ/PDF/ZIP).

### `GET /download/{job_id}/page/{n}`

Télécharge une page individuelle.

### `GET /download/{job_id}/pages`

Liste toutes les pages avec leurs URLs.

---

## 🎨 Options de police (font_options)

```json
{
  "size_max": 24,
  "size_min": 8,
  "color": "#000000",
  "outline_color": "#FFFFFF",
  "outline_width": 1,
  "bold": false,
  "italic": false,
  "text_padding": 4,
  "font_path": "/path/to/custom.ttf"
}
```

---

## ☁️ Supabase Storage

Pour stocker les fichiers dans Supabase au lieu du disque local:

```env
USE_SUPABASE=true
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJhbGci...
SUPABASE_BUCKET=manga-translations
```

```bash
pip install supabase
```

---

## 🔗 Intégration Next.js

Voir `docs/frontend-integration.ts` pour un client TypeScript complet avec:
- Envoi de fichier via FormData
- Polling de progression
- Téléchargement du résultat
- Hook React réutilisable

---

## 📋 Formats supportés

**Entrée:** JPG, PNG, WebP, BMP, CBZ, CBR, PDF, ZIP  
**Sortie:** CBZ, PDF, ZIP

---

## 📝 Logs

```
ℹ️  12:00:01 [INFO]  app.main: 🚀 Starting Manga Translator Backend...
ℹ️  12:00:01 [INFO]  app.main: OCR Engine: easyocr
ℹ️  12:00:01 [INFO]  app.main: Translation Engine: marian
ℹ️  12:00:05 [INFO]  job_manager: 📋 Job créé: abc123 | Pages: 42
ℹ️  12:00:05 [INFO]  pipeline: 📂 42 pages extraites
ℹ️  12:00:10 [INFO]  pipeline:   🔍 Page 1: OCR...
ℹ️  12:00:12 [INFO]  pipeline:   🌐 Page 1: traduction de 8 zones...
ℹ️  12:00:13 [INFO]  pipeline:   🎨 Page 1: suppression du texte...
ℹ️  12:00:13 [INFO]  pipeline:   ✍️  Page 1: réécriture du texte...
ℹ️  12:00:14 [INFO]  pipeline:   ✅ Page 1 terminée en 4231ms
```
