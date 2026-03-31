# ─────────────────────────────────────────────────────────────────────────────
# DBT Core — Compras Públicas
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Instala dbt-core + adaptador PostgreSQL
RUN pip install --no-cache-dir \
    dbt-core==1.9.* \
    dbt-postgres==1.9.*

WORKDIR /usr/app/dbt

# Copia o projeto dbt
COPY . .

ENTRYPOINT ["dbt"]
CMD ["--help"]