# ═══════════════════════════════════════════════════════════════════════════════
# Manga Translator Backend — Dockerfile OPTIMISÉ
# Stratégie: couches séparées pour le cache Docker
# torch CPU-only (~500MB au lieu de 2.5GB), dépendances lourdes en cache
# ═══════════════════════════════════════════════════════════════════════════════

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    # Cache HuggingFace et EasyOCR dans /app pour persister via volume
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    HF_HOME=/app/.cache/huggingface \
    EASYOCR_MODULE_PATH=/app/.cache/easyocr

# ── 1. Dépendances système (cachées tant que cette couche ne change pas) ────────
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-jpn \
    unrar-free \
    # libgl1-mesa-glx \ 
    # libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── 2. Torch CPU-only EN PREMIER (couche la plus lourde = meilleur cache) ───────
# Version CPU uniquement : ~500MB au lieu de 2.5GB (GPU)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    torch==2.5.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# ── 3. Dépendances IA lourdes (cachées séparément) ──────────────────────────────
RUN pip install --no-cache-dir \
    transformers==4.46.3 \
    sentencepiece==0.2.0 \
    sacremoses==0.1.1 \
    easyocr==1.7.2

# ── 4. Dépendances applicatives légères ─────────────────────────────────────────
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# ── 5. Code source (invalidé seulement quand le code change) ────────────────────
COPY . .

# ── 6. Répertoires de travail ────────────────────────────────────────────────────
RUN mkdir -p /tmp/manga_translator/{uploads,outputs,temp} \
             /app/.cache/huggingface \
             /app/.cache/easyocr \
    && chmod -R 755 /tmp/manga_translator /app/.cache

# ── 7. Utilisateur non-root ──────────────────────────────────────────────────────
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /tmp/manga_translator
USER appuser

EXPOSE 8000

# ✅ Chemin correct: main.py est à la racine du projet
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]