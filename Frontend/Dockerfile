# ═══════════════════════════════════════════════════════════════════════════════
# Manga Translator Frontend — Dockerfile
# Next.js en mode développement (utilise pnpm)
# ═══════════════════════════════════════════════════════════════════════════════

FROM node:20-slim
RUN apt-get update && apt-get install -y openssl && rm -rf /var/lib/apt/lists/*

# ── Installer pnpm ─────────────────────────────────────────────────────────────────
RUN npm install -g pnpm

WORKDIR /app

# ── 1. Dépendances (cachées si package.json ne change pas) ───────────────────
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install

# ── 2. Code source ────────────────────────────────────────────────────────────
COPY . .

EXPOSE 3000

CMD ["pnpm", "run", "dev"]