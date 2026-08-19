#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# ingest.sh — rotina de ingestão do CSV de contratos (spec 009)
#
# 1. HEAD no link do portal, extrai ETag.
# 2. Compara com o último ETag salvo em control.pipeline_metadata.
# 3. Igual -> no-op (exit 0, sem baixar o corpo).
# 4. Diferente (ou primeira execução) -> baixa o arquivo completo.
# 5. Valida schema mínimo (header confere com o contratos.csv atual, linhas > 0)
#    antes de sobrescrever seeds/contratos.csv. Falha aqui não toca em nada.
# 6. dbt seed --select contratos && dbt build.
# 7. Só se 6 for bem-sucedido: grava o novo ETag em pipeline_metadata.
# 8. Log em arquivo + stdout.
#
# Teste (Etapa 6 do prompt de implementação): defina INGEST_TEST_SOURCE_OVERRIDE
# apontando pra um CSV local para pular o curl e usar esse arquivo como se
# fosse o download — usado pra simular primeira execução / arquivo corrompido
# sem depender do portal real.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

DOWNLOAD_URL="https://dados.sc.gov.br/dataset/93dab950-e805-4388-8418-cfb3b73f1623/resource/8bb98383-7043-4d2f-ae32-9377656e71ee/download/contratos.csv"
SEED_FILE="/usr/app/dbt/seeds/contratos.csv"
TMP_FILE="/tmp/contratos_download.csv"
LOG_DIR="/var/log/compras-publicas"
LOG_FILE="${LOG_DIR}/ingest-$(date +%Y%m%d).log"
ETAG_CHAVE="contratos_etag"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

fail() {
    log "ERRO: $*"
    exit 1
}

psql_query() {
    local sql="$1"
    shift
    # Args extras (-v nome=valor) ficam disponíveis como :'nome' na query —
    # psql escapa o valor automaticamente, em vez de interpolar direto na
    # string via shell. A query vai por stdin, não por -c: achado real de
    # implementação — a substituição de :'nome' do psql não roda com -c
    # (testado: "syntax error at or near :"), só com script/stdin.
    PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$POSTGRES_HOST" -p "${POSTGRES_PORT:-5432}" \
        -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        -v ON_ERROR_STOP=1 "$@" \
        -t -A <<< "$sql"
}

log "=== Início da rotina de ingestão ==="

# ── 1. HEAD no portal, extrai ETag ────────────────────────────────────────
if [[ -n "${INGEST_TEST_SOURCE_OVERRIDE:-}" ]]; then
    log "AVISO: INGEST_TEST_SOURCE_OVERRIDE=${INGEST_TEST_SOURCE_OVERRIDE} — modo de teste, usando arquivo local em vez do portal."
    [[ -f "$INGEST_TEST_SOURCE_OVERRIDE" ]] || fail "INGEST_TEST_SOURCE_OVERRIDE aponta pra arquivo inexistente"
    novo_etag="teste-$(sha256sum "$INGEST_TEST_SOURCE_OVERRIDE" | cut -c1-16)"
    cp "$INGEST_TEST_SOURCE_OVERRIDE" "$TMP_FILE"
else
    headers=$(curl -sSI "$DOWNLOAD_URL") || fail "HEAD request ao portal falhou"
    novo_etag=$(echo "$headers" | grep -i '^ETag:' | sed -E 's/^ETag:[[:space:]]*"?([^"[:cntrl:]]*)"?[[:cntrl:]]*$/\1/i')
    [[ -n "$novo_etag" ]] || fail "Não foi possível extrair ETag do HEAD response"
fi

log "ETag do portal: $novo_etag"

# ── 2. Último ETag salvo ──────────────────────────────────────────────────
etag_salvo=$(psql_query "select valor from control.pipeline_metadata where chave = :'etag_chave'" -v etag_chave="$ETAG_CHAVE") || fail "Falha ao consultar pipeline_metadata"
etag_salvo=$(echo "$etag_salvo" | tr -d '[:space:]')

if [[ -z "$etag_salvo" ]]; then
    log "Nenhum ETag salvo (primeira execução) — tratando como mudança."
else
    log "Último ETag salvo: $etag_salvo"
fi

# ── 3. Comparação ─────────────────────────────────────────────────────────
if [[ -n "$etag_salvo" && "$etag_salvo" == "$novo_etag" ]]; then
    log "ETag inalterado — sem mudança. Encerrando (no-op)."
    exit 0
fi

log "ETag mudou (ou primeira execução) — processando."

# ── 4. Download completo ──────────────────────────────────────────────────
if [[ -z "${INGEST_TEST_SOURCE_OVERRIDE:-}" ]]; then
    curl -sS -o "$TMP_FILE" "$DOWNLOAD_URL" || fail "Download do CSV falhou"
fi

# ── 5. Validação de schema mínimo ─────────────────────────────────────────
# Comparação contra o header do contratos.csv ATUAL (não contra
# stg_contratos.yml — aquele arquivo documenta as colunas renomeadas de
# saída do model de staging, não o header bruto do CSV do portal).
header_novo=$(head -n 1 "$TMP_FILE")
header_atual=$(head -n 1 "$SEED_FILE")
linhas=$(($(wc -l < "$TMP_FILE") - 1))

if [[ "$header_novo" != "$header_atual" ]]; then
    fail "Validação de schema falhou: header do CSV baixado diverge do header atual de ${SEED_FILE}. contratos.csv e pipeline_metadata NÃO foram alterados. Novo: [${header_novo}] | Atual: [${header_atual}]"
fi

if [[ "$linhas" -le 0 ]]; then
    fail "Validação de schema falhou: CSV baixado tem 0 linhas de dado. contratos.csv e pipeline_metadata NÃO foram alterados."
fi

log "Validação de schema OK: header confere, ${linhas} linhas de dado."

mv "$TMP_FILE" "$SEED_FILE"
log "contratos.csv atualizado."

# ── 6. dbt seed + dbt build ────────────────────────────────────────────────
cd /usr/app/dbt

if ! dbt seed --select contratos 2>&1 | tee -a "$LOG_FILE"; then
    fail "dbt seed falhou. pipeline_metadata NÃO foi atualizado."
fi

if ! dbt build 2>&1 | tee -a "$LOG_FILE"; then
    fail "dbt build falhou. pipeline_metadata NÃO foi atualizado."
fi

# ── 7. Atualizar ETag (só chega aqui se dbt seed + dbt build tiveram sucesso) ─
# A constraint precisa existir pro ON CONFLICT funcionar. dbt build recria a
# tabela do zero a cada execução (ver comentário no .sql do model) — garantir
# a constraint aqui, depois que o swap do dbt já terminou de vez.
psql_query "create unique index if not exists pipeline_metadata_chave_key on control.pipeline_metadata (chave);" > /dev/null \
    || fail "dbt build teve sucesso mas a criação da constraint de pipeline_metadata falhou"

psql_query "
    insert into control.pipeline_metadata (chave, valor, atualizado_em)
    values (:'etag_chave', :'etag_valor', now())
    on conflict (chave) do update
        set valor = excluded.valor,
            atualizado_em = excluded.atualizado_em;
" -v etag_chave="$ETAG_CHAVE" -v etag_valor="$novo_etag" > /dev/null \
    || fail "dbt build teve sucesso mas a atualização do ETag falhou"

log "pipeline_metadata atualizado com ETag: $novo_etag"
log "=== Fim da rotina de ingestão (sucesso) ==="
