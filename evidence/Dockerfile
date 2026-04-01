# ─────────────────────────────────────────────────────────────────────────────
# Compras Públicas — Evidence
#
# Base: Ubuntu 24.04 LTS (Noble Numbat)
# Inclui:
#   - Node.js 20 LTS
#   - Evidence.dev
#
# ── Rede ─────────────────────────────────────────────────────────────────────
# Este container opera na rede "compras_network" definida no docker-compose.yml
# Acessa o PostgreSQL pelo hostname "postgres" (não localhost)
#
# Modos de uso:
#   dev   → npm run dev   (http://localhost:3000) — desenvolvimento local
#   build → npm run build (gera /app/build)       — antes de publicar no Pages
# ─────────────────────────────────────────────────────────────────────────────
FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive

# ── Sistema base ──────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    locales \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Locale e timezone Brasil
RUN locale-gen pt_BR.UTF-8
ENV LANG=pt_BR.UTF-8 \
    LANGUAGE=pt_BR:pt \
    LC_ALL=pt_BR.UTF-8 \
    TZ=America/Sao_Paulo

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# ── Node.js 20 LTS ───────────────────────────────────────────────────────────
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia dependências primeiro (cache de layer)
COPY package*.json ./
RUN npm install

# Copia o projeto Evidence
COPY . .

EXPOSE 3000

# Dev por padrão — para build use:
# docker compose run --rm evidence npm run build
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]