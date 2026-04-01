# ─────────────────────────────────────────────────────────────────────────────
# Compras Públicas — DBT Core
#
# Base: Ubuntu 24.04 LTS (Noble Numbat)
# Inclui:
#   - Python 3.12
#   - dbt-core 1.9
#   - dbt-postgres 1.9
# ─────────────────────────────────────────────────────────────────────────────
FROM ubuntu:24.04
 
ARG DEBIAN_FRONTEND=noninteractive
 
# ── Sistema base ──────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    locales \
    tzdata \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*
 
# Locale e timezone Brasil
RUN locale-gen pt_BR.UTF-8
ENV LANG=pt_BR.UTF-8 \
    LANGUAGE=pt_BR:pt \
    LC_ALL=pt_BR.UTF-8 \
    TZ=America/Sao_Paulo
 
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
 
# ── Virtualenv + DBT ──────────────────────────────────────────────────────────
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
 
RUN pip install --no-cache-dir \
    dbt-core==1.9.* \
    dbt-postgres==1.9.*
 
WORKDIR /usr/app/dbt
 
COPY . .

# ── Rede ─────────────────────────────────────────────────────────────────────
# Este container opera na rede "compras_network" definida no docker-compose.yml
# Acessa o PostgreSQL pelo hostname "postgres" (não localhost)
 
ENTRYPOINT ["dbt"]
CMD ["--help"]