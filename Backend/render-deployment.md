# 🚀 Déploiement sur Render.com

## Pourquoi Supabase est obligatoire sur Render

Render.com utilise un **filesystem éphémère**: tous les fichiers sont perdus
à chaque redémarrage ou redéploiement. Supabase Storage est donc indispensable
pour conserver les images traduites entre le traitement et le téléchargement.

```
Sans Supabase:  [Traite] → fichier sur /tmp → [Redémarrage] → ❌ fichier perdu
Avec Supabase:  [Traite] → upload Supabase → [Redémarrage] → ✅ URL toujours valide
```

---

## Étape 1 — Configurer Supabase

1. Créez un compte sur [supabase.com](https://supabase.com) (gratuit)
2. Créez un nouveau projet
3. Allez dans **Storage** → le bucket `manga-translations` sera créé automatiquement
4. Récupérez vos credentials dans **Settings → API**:
   - `Project URL` → `SUPABASE_URL`
   - `anon public key` → `SUPABASE_KEY`

> Le bucket sera créé automatiquement au premier démarrage si les credentials sont corrects.
> Vérifiez que votre bucket est en mode **public** pour que les URLs fonctionnent.

---

## Étape 2 — Déployer sur Render

### Option A: Via render.yaml (recommandé)

1. Poussez ce projet sur GitHub/GitLab
2. Sur [render.com](https://render.com) → **New → Blueprint**
3. Connectez votre repo → Render détecte `render.yaml` automatiquement
4. Dans **Environment Variables**, ajoutez les secrets:

| Variable | Valeur |
|---|---|
| `SUPABASE_URL` | `https://xxxx.supabase.co` |
| `SUPABASE_KEY` | `eyJhbGci...` (anon key) |

### Option B: Manuellement

1. **New → Web Service** → connectez votre repo
2. Configurez:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Dans **Environment**, ajoutez **toutes** les variables du tableau ci-dessous

---

## Variables d'environnement Render

| Variable | Valeur production | Obligatoire |
|---|---|---|
| `USE_SUPABASE` | `true` | ✅ Oui |
| `SUPABASE_URL` | `https://xxxx.supabase.co` | ✅ Oui |
| `SUPABASE_KEY` | `eyJhbGci...` | ✅ Oui |
| `SUPABASE_BUCKET` | `manga-translations` | ✅ Oui |
| `ALLOWED_ORIGINS` | `["https://votre-app.vercel.app"]` | ✅ Oui |
| `OCR_ENGINE` | `easyocr` | ✅ Oui |
| `TRANSLATION_ENGINE` | `marian` | ✅ Oui |
| `MAX_PARALLEL_PAGES` | `2` | Recommandé |
| `MAX_FILE_SIZE_MB` | `50` | Recommandé |
| `DEBUG` | `false` | Recommandé |

---

## Plan Render recommandé

| Plan | RAM | Prix | Adapté |
|---|---|---|---|
| **Free** | 512MB | Gratuit | ⚠️ Limité, sleeps après inactivité |
| **Starter** | 512MB | ~$7/mois | ✅ Correct pour test |
| **Standard** | 2GB | ~$25/mois | ✅ Recommandé pour production |

> ⚠️ Sur le plan **Free**, le service "dort" après 15min d'inactivité.
> Le premier traitement après une période d'inactivité prendra ~30s de démarrage.
> Pour usage régulier, préférez **Starter** ou plus.

> ⚠️ EasyOCR + MarianMT téléchargent leurs modèles au **premier démarrage** (~500MB).
> Sur Render, les modèles sont retéléchargés après chaque redéploiement
> sauf si vous utilisez un **Persistent Disk** (option payante).

---

## Architecture en production

```
Next.js (Vercel)
    ↓ POST /translate (multipart)
FastAPI (Render)
    ↓ Extraction pages
    ↓ OCR (EasyOCR)
    ↓ Traduction (MarianMT)
    ↓ Inpainting (OpenCV)
    ↓ Rendu (Pillow)
    ↓ Upload
Supabase Storage
    ↓ URL publique
Next.js (Vercel) ← GET /status/{job_id} → URL Supabase → <img src="...">
```

---

## Test de déploiement

```bash
# Vérifier que le service est en ligne
curl https://votre-service.onrender.com/health

# Réponse attendue:
# {"status":"ok","version":"1.0.0","ocr_engine":"easyocr","translation_engine":"marian"}
```
