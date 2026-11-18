# 🎌 Manga Translator

Traduction automatique de mangas et webtoons en français : on envoie un fichier, l'application détecte le texte des bulles, le traduit, efface l'original et réécrit la traduction dans l'image.

<!-- Ajouter ici une capture avant / après -->

## Fonctionnement

```
Fichier CBZ / CBR / PDF
  → extraction des pages
  → OCR (détection du texte dans les bulles)
  → traduction
  → inpainting OpenCV (effacement du texte original)
  → rendu Pillow (réécriture dans les bulles)
  → fichier traduit à télécharger
```

Les pages sont traitées en parallèle, et le front-end suit l'avancement du traitement en direct (`/status/{job_id}`).

## Stack

| Partie | Technologies |
|---|---|
| Back-end | Python, FastAPI, EasyOCR, MarianMT (Hugging Face), OpenCV, Pillow |
| Front-end | Next.js, React, TypeScript, Tailwind CSS |
| Stockage (optionnel) | Supabase Storage |
| Déploiement | Docker, Docker Compose |

Moteurs configurables via `.env` :
- **OCR** : EasyOCR (par défaut), PaddleOCR, Tesseract, Google Vision
- **Traduction** : MarianMT (par défaut, hors ligne), LibreTranslate, Google Translate, DeepL

## Lancer le projet

```bash
docker-compose up --build
```

- Front-end : http://localhost:3000
- API : http://localhost:8000 (documentation Swagger sur `/docs`)

Détails de l'API, de la configuration et de l'installation sans Docker : voir [`Backend/README.md`](Backend/README.md).

## Structure

```
Backend/    API FastAPI et pipeline de traduction
Frontend/   Interface Next.js (upload, suivi, téléchargement)
```
