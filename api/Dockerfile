# ─────────────────────────────────────────────────────────────────────────────
# Compras Públicas — API (FastAPI, spec 012) + frontend (spec 012/022)
#
# Multi-stage: stage 1 builda o frontend (web/) com Node; stage 2 é a base
# Ubuntu 24.04 (mesma do serviço dbt) rodando a API, com o resultado do
# build copiado para api/app/static.
#
# Contexto de build é a raiz do repo (não ./api) — o stage Node precisa
# acessar web/.
# ─────────────────────────────────────────────────────────────────────────────
FROM node:22-slim AS frontend-build

WORKDIR /web

COPY web/package*.json ./
# --legacy-peer-deps: package.json fixa typescript ~6.0.2, mas openapi-typescript@^7.13.0
# (dev-only, usado só por generate-types) declara peer typescript@^5.x — conflito
# pré-existente no lockfile, não introduzido por este Dockerfile.
RUN npm ci --legacy-peer-deps

COPY web/ ./
RUN npm run build

# ─────────────────────────────────────────────────────────────────────────────
FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    locales \
    tzdata \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN locale-gen pt_BR.UTF-8
ENV LANG=pt_BR.UTF-8 \
    LANGUAGE=pt_BR:pt \
    LC_ALL=pt_BR.UTF-8 \
    TZ=America/Sao_Paulo \
    PYTHONUNBUFFERED=1

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /usr/app/api

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ .
COPY --from=frontend-build /api/app/static/ ./app/static/

EXPOSE 8000

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
