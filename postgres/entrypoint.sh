#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Compras Públicas — PostgreSQL Entrypoint
# ─────────────────────────────────────────────────────────────────────────────
set -e

PG_VERSION=${PG_VERSION:-17}
PGDATA=${PGDATA:-/var/lib/postgresql/${PG_VERSION}/main}
PG_HBA="${PGDATA}/pg_hba.conf"
PG_CONF="${PGDATA}/postgresql.conf"
PG_BIN="/usr/lib/postgresql/${PG_VERSION}/bin"

DB=${POSTGRES_DB:-compras_publicas}
USER=${POSTGRES_USER:-cp_user}
PASS=${POSTGRES_PASSWORD:-cp_pass}

echo ">>> Iniciando PostgreSQL ${PG_VERSION}..."

# ── 1. Inicializa o cluster se necessário ────────────────────────────────────
if [ ! -f "${PGDATA}/PG_VERSION" ]; then
    echo ">>> Inicializando cluster PostgreSQL..."
    mkdir -p "${PGDATA}"
    chown -R postgres:postgres "${PGDATA}"
    gosu postgres ${PG_BIN}/initdb \
        --pgdata="${PGDATA}" \
        --username="postgres" \
        --encoding=UTF8 \
        --locale=pt_BR.UTF-8
    echo ">>> Cluster inicializado!"
fi

# ── 2. Configura acesso remoto ───────────────────────────────────────────────
echo ">>> Configurando acesso remoto..."
grep -qxF "listen_addresses = '*'" "${PG_CONF}" || \
    echo "listen_addresses = '*'" >> "${PG_CONF}"

grep -qF "0.0.0.0/0" "${PG_HBA}" || \
    echo "host all all 0.0.0.0/0 md5" >> "${PG_HBA}"

grep -qF "local all postgres trust" "${PG_HBA}" || \
    sed -i "1s/^/local all postgres trust\n/" "${PG_HBA}"

# ── 3. Inicia o PostgreSQL em background (apenas para setup) ─────────────────
echo ">>> Iniciando servidor temporário para setup..."
mkdir -p /var/log/postgresql
chown postgres:postgres /var/log/postgresql

gosu postgres ${PG_BIN}/pg_ctl \
    -D "${PGDATA}" \
    -l "/var/log/postgresql/postgresql.log" \
    -o "-c listen_addresses=''" \
    start

# ── 4. Aguarda ficar pronto ──────────────────────────────────────────────────
echo ">>> Aguardando PostgreSQL ficar pronto..."
until gosu postgres ${PG_BIN}/pg_isready -q; do
    sleep 1
done
echo ">>> PostgreSQL pronto!"

# ── 5. Configura usuário e banco ─────────────────────────────────────────────
echo ">>> Configurando usuário e banco de dados..."

gosu postgres psql -U postgres --command \
    "DO \$\$ BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${USER}') THEN
            CREATE USER ${USER} WITH PASSWORD '${PASS}';
        ELSE
            ALTER USER ${USER} WITH PASSWORD '${PASS}';
        END IF;
    END \$\$;"

gosu postgres psql -U postgres -tc \
    "SELECT 1 FROM pg_database WHERE datname='${DB}'" | \
    grep -q 1 || \
    gosu postgres psql -U postgres \
        --command "CREATE DATABASE ${DB} OWNER ${USER};"

gosu postgres psql -U postgres --command \
    "GRANT ALL PRIVILEGES ON DATABASE ${DB} TO ${USER};"

# ── 6. Executa scripts SQL de inicialização ──────────────────────────────────
if [ -d /opt/init ]; then
    for f in /opt/init/*.sql; do
        echo ">>> Executando script: $(basename $f)"
        gosu postgres psql \
            -U postgres \
            -d "${DB}" \
            -f "$f"
    done
fi

# ── 7. Para o servidor temporário ────────────────────────────────────────────
echo ">>> Parando servidor temporário..."
gosu postgres ${PG_BIN}/pg_ctl \
    -D "${PGDATA}" \
    stop

echo ">>> Setup concluído! Iniciando servidor principal..."

# ── 8. Inicia o servidor principal (foreground) ──────────────────────────────
exec gosu postgres ${PG_BIN}/postgres \
    -D "${PGDATA}" \
    -c "listen_addresses=*"