# ═══════════════════════════════════════════════════════════════════════════════
# 🐳 DOCKER CHEATSHEET — Manga Translator
# Toutes les commandes utiles pour le projet
# ═══════════════════════════════════════════════════════════════════════════════
# 📁 Toutes les commandes docker-compose se lancent depuis la RACINE du projet
#    cd "C:\Users\USER\OneDrive\Bureau\projets Nextjs\manga-translator"
# ═══════════════════════════════════════════════════════════════════════════════


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. DÉMARRAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Démarrer tout (sans rebuild — utilise le cache)
docker-compose up

# Démarrer en arrière-plan (détaché)
docker-compose up -d

# Démarrer uniquement le backend
docker-compose up backend

# Démarrer uniquement le frontend
docker-compose up frontend

# Démarrer avec les logs colorés par service
docker-compose up --color


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. BUILD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Build + démarrer tout
docker-compose up --build

# Build + démarrer en arrière-plan
docker-compose up --build -d

# Build uniquement le frontend (backend cache préservé ✅)
docker-compose up --build frontend

# Build uniquement le backend (frontend cache préservé ✅)
docker-compose up --build backend

# Build sans utiliser le cache Docker (repart de zéro ⚠️ long)
docker-compose build --no-cache

# Build sans cache uniquement le frontend
docker-compose build --no-cache frontend

# Build sans cache uniquement le backend
docker-compose build --no-cache backend

# Forcer rebuild frontend (supprimer image + rebuild)
docker rmi manga-translator-frontend -f && docker-compose up --build frontend

# Forcer rebuild backend (supprimer image + rebuild)
docker rmi manga-translator-backend -f && docker-compose up --build backend

# Forcer rebuild tout
docker rmi manga-translator-frontend manga-translator-backend -f && docker-compose up --build

docker rmi manga-translator-backend


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. ARRÊT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Arrêter tous les containers (garde les volumes et images)
docker-compose down

# Arrêter et supprimer les volumes (cache modèles IA perdu ⚠️)
docker-compose down -v

# Arrêter et supprimer les images aussi
docker-compose down --rmi all

# Arrêter uniquement le frontend
docker-compose stop frontend

# Arrêter uniquement le backend
docker-compose stop backend

# Arrêter sans supprimer (pause)
docker-compose pause

# Reprendre après pause
docker-compose unpause

# Tuer immédiatement (force)
docker-compose kill


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. LOGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Voir les logs en temps réel (tous les services)
docker-compose logs -f

# Logs uniquement le backend
docker-compose logs -f backend

# Logs uniquement le frontend
docker-compose logs -f frontend

# Voir les 50 dernières lignes
docker-compose logs --tail=50

# Logs backend avec timestamp
docker-compose logs -f --timestamps backend

# Logs sans couleur (pour copier-coller)
docker-compose logs --no-color backend


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. STATUT & INSPECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Voir les containers du projet (status, ports)
docker-compose ps

# Voir TOUS les containers Docker (tous projets)
docker ps -a

# Voir toutes les images Docker
docker images

# Voir l'espace disque utilisé par Docker
docker system df

# Voir l'espace disque en détail
docker system df -v

# Inspecter le container backend (IP, volumes, config)
docker inspect manga-translator-backend

# Voir les ports exposés
docker-compose port backend 8000
docker-compose port frontend 3000

# Voir les variables d'environnement du backend
docker exec manga-translator-backend env

# Voir les variables d'environnement du frontend
docker exec manga-translator-frontend env


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. ACCÈS AUX CONTAINERS (SHELL)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Ouvrir un shell dans le backend
docker exec -it manga-translator-backend bash

# Ouvrir un shell dans le frontend (alpine = sh, pas bash)
docker exec -it manga-translator-frontend sh

# Exécuter une commande directe dans le backend
docker exec manga-translator-backend python --version
docker exec manga-translator-backend pip list
docker exec manga-translator-backend curl http://localhost:8000/health

# Exécuter une commande dans le frontend
docker exec manga-translator-frontend node --version
docker exec manga-translator-frontend pnpm --version

# Tester la connexion backend → depuis le frontend container
docker exec manga-translator-frontend wget -qO- http://backend:8000/health


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. TESTS & HEALTH CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Health check backend (depuis ton PC)
curl http://localhost:8000/health

# Health check avec affichage formaté (PowerShell)
Invoke-RestMethod http://localhost:8000/health | ConvertTo-Json

# Tester l'API docs
start http://localhost:8000/docs

# Ouvrir le frontend
start http://localhost:3000

# Voir le statut health check Docker
docker inspect --format='{{json .State.Health}}' manga-translator-backend


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. VOLUMES & DONNÉES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Voir les volumes du projet
docker volume ls | findstr manga

# Inspecter le volume des modèles IA
docker volume inspect manga-translator_ai_models_cache

# Inspecter le volume des fichiers temporaires
docker volume inspect manga-translator_manga_temp

# Voir le contenu du volume cache modèles IA
docker run --rm -v manga-translator_ai_models_cache:/data alpine ls -la /data

# Voir les fichiers temporaires (uploads/outputs)
docker run --rm -v manga-translator_manga_temp:/data alpine ls -la /data


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. RESTART
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Redémarrer tous les services
docker-compose restart

# Redémarrer uniquement le backend
docker-compose restart backend

# Redémarrer uniquement le frontend
docker-compose restart frontend


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10. NETTOYAGE (du moins au plus destructif)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ✅ Sûr — Supprimer containers et réseaux arrêtés (garde images et volumes)
docker system prune -f

# ⚠️  Attention — Supprimer aussi les images inutilisées (rebuild nécessaire)
docker system prune -a -f

# 🔴 Destructif — Supprimer TOUT (images + volumes + cache = repart de zéro)
docker system prune -a --volumes -f

# Supprimer uniquement l'image frontend (rebuild frontend au prochain up --build)
docker rmi manga-translator-frontend -f

# Supprimer uniquement l'image backend (rebuild backend au prochain up --build)
docker rmi manga-translator-backend -f

# Supprimer uniquement les volumes du projet (perd le cache modèles IA ⚠️)
docker-compose down -v

# Supprimer un volume spécifique
docker volume rm manga-translator_ai_models_cache
docker volume rm manga-translator_manga_temp

# Libérer le cache de build Docker (garde les images finales)
docker builder prune -f


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 11. RÉSEAU
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Voir le réseau du projet
docker network ls | findstr manga

# Inspecter le réseau (voir les IPs des containers)
docker network inspect manga-translator-network

# Tester la connectivité frontend → backend (dans le réseau Docker)
docker exec manga-translator-frontend wget -qO- http://backend:8000/health


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 12. COMMANDES DU QUOTIDIEN (les plus utilisées)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Le matin → démarrer le projet
docker-compose up -d

# Voir si tout tourne
docker-compose ps

# Voir les logs en direct
docker-compose logs -f

# Le soir → arrêter proprement
docker-compose down

# J'ai modifié du code Python → juste redémarrer le backend
docker-compose restart backend

# J'ai modifié le Dockerfile frontend → rebuild frontend seulement
docker rmi manga-translator-frontend -f && docker-compose up --build frontend

# Ça bug → voir les logs du backend
docker-compose logs --tail=100 backend

# Vérifier l'espace disque Docker
docker system df
