# ─────────────────────────────────────────────────────────────────────────────
# Compras Públicas — PostgreSQL 17
#
# Base: Ubuntu 24.04 LTS (Noble Numbat)
# PostgreSQL: 17 (repositório oficial postgresql.org)
# ─────────────────────────────────────────────────────────────────────────────
FROM ubuntu:24.04
 
ARG DEBIAN_FRONTEND=noninteractive
ARG PG_VERSION=17
 
# ── Sistema base ──────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    locales \
    tzdata \
    gosu \
    && rm -rf /var/lib/apt/lists/*
 
# Locale e timezone Brasil
RUN locale-gen pt_BR.UTF-8
ENV LANG=pt_BR.UTF-8 \
    LANGUAGE=pt_BR:pt \
    LC_ALL=pt_BR.UTF-8 \
    TZ=America/Sao_Paulo
 
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
 
# ── Repositório oficial PostgreSQL ────────────────────────────────────────────
RUN curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
    | gpg --dearmor -o /usr/share/keyrings/postgresql.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/postgresql.gpg] \
    https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" \
    > /etc/apt/sources.list.d/pgdg.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
    postgresql-${PG_VERSION} \
    postgresql-client-${PG_VERSION} \
    postgresql-contrib-${PG_VERSION} \
 && rm -rf /var/lib/apt/lists/*
 
# ── Variáveis de ambiente ─────────────────────────────────────────────────────
ENV PG_VERSION=${PG_VERSION} \
    PGDATA=/var/lib/postgresql/${PG_VERSION}/main \
    POSTGRES_DB=compras_publicas \
    POSTGRES_USER=cp_user \
    POSTGRES_PASSWORD=cp_pass \
    POSTGRES_PORT=5432
 
# ── Scripts de inicialização e entrypoint ────────────────────────────────────
COPY init/         /opt/init/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ── Rede ─────────────────────────────────────────────────────────────────────
# Este container opera na rede "compras_network" definida no docker-compose.yml
# Os demais serviços (dbt, pgadmin, evidence) acessam pelo hostname "postgres"
 
EXPOSE 5432
 
VOLUME ["/var/lib/postgresql/17/main", "/var/log/postgresql"]
 
ENTRYPOINT ["/entrypoint.sh"]