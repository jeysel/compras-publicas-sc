#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# ingest.sh — rotina de ingestão do CSV de contratos (spec 009)
#
# 0. Bootstrap: garante que control.pipeline_metadata existe (DDL idempotente,
#    fora do dbt — ver comentário no bloco abaixo sobre a causa raiz).
# 1. HEAD no link do portal, extrai ETag.
# 2. Compara com o último ETag salvo em control.pipeline_metadata.
# 3. Igual -> no-op (exit 0, sem baixar o corpo).
# 4. Diferente (ou primeira execução) -> baixa o arquivo completo.
# 5. Valida schema mínimo (subconjunto case-insensitive: toda coluna do
#    contratos.csv atual presente no baixado, linhas > 0 — spec 017) antes de
#    sobrescrever seeds/contratos.csv. Falha aqui não toca em nada.
# 5.1. Processa o CSV baixado via process_csv.py (spec 019): filtra pro
#      subconjunto de colunas já conhecido (nunca --full-refresh automático) e
#      tenta reparar/quarentenar linhas malformadas, em vez de deixar o
#      `dbt seed` travar nelas. Só o arquivo FILTRADO substitui seeds/contratos.csv.
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
FILTERED_FILE="/tmp/contratos_filtrado.csv"
LOG_DIR="/var/log/compras-publicas"
LOG_FILE="${LOG_DIR}/ingest-$(date +%Y%m%d).log"
# Mesmo volume já usado pro LOG_DIR (spec 019) — precisa sobreviver entre
# execuções do container efêmero, por isso não vive em /tmp.
QUARANTINE_FILE="${LOG_DIR}/contratos_quarentena.csv"
ETAG_CHAVE="contratos_etag"

export QUARANTINE_FILE

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

# ── 0. Bootstrap: garantir que a tabela de controle existe ─────────────────
# Fora do dbt de propósito (achado real: table do dbt faz DROP+CREATE a cada
# build, inadequado pra estado operacional mutável — mesma causa raiz do
# bug do post_hook/constraint documentado antes). DDL idempotente, roda
# sempre, primeira execução ou não — sem custo real quando a tabela já existe.
psql_query "
    create schema if not exists control;
    create table if not exists control.pipeline_metadata (
        chave varchar primary key,
        valor varchar,
        atualizado_em timestamp
    );
" > /dev/null || fail "Bootstrap de control.pipeline_metadata falhou"

log "Bootstrap: control.pipeline_metadata confirmada."

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
#
# Checagem de SUBCONJUNTO, case-insensitive (spec 017, achado spec 016): toda
# coluna que aparece no header do seed ATUAL precisa existir no header do CSV
# baixado — colunas extras (aditivas) e diferença de maiúscula/minúscula são
# toleradas. Ainda rejeita qualquer coluna ESPERADA ausente (arquivo
# corrompido/truncado continua barrado).
# tr -d '\r': o seed committado usa CRLF e o download real do portal usa LF
# — sem isso, `$(...)` preserva o \r à direita (só engole \n), o último nome
# de coluna sai como "diasatuais\r" e nunca bate com "diasatuais", mesmo
# quando a coluna existe (achado real, spec 019, Cenário 5: bloqueava 100%
# das execuções contra o portal real, não é caso de borda raro).
header_novo=$(head -n 1 "$TMP_FILE" | tr -d '\r')
header_atual=$(head -n 1 "$SEED_FILE" | tr -d '\r')
linhas=$(($(wc -l < "$TMP_FILE") - 1))

mapfile -t cols_novo < <(echo "$header_novo" | tr '[:upper:]' '[:lower:]' | tr ';' '\n')
mapfile -t cols_atual < <(echo "$header_atual" | tr '[:upper:]' '[:lower:]' | tr ';' '\n')

declare -A cols_novo_set
for c in "${cols_novo[@]}"; do cols_novo_set["$c"]=1; done

faltando=()
for c in "${cols_atual[@]}"; do
    if [[ -z "${cols_novo_set[$c]:-}" ]]; then
        faltando+=("$c")
    fi
done

if [[ ${#faltando[@]} -gt 0 ]]; then
    fail "Validação de schema falhou: colunas esperadas ausentes no CSV baixado (comparação case-insensitive): ${faltando[*]}. contratos.csv e pipeline_metadata NÃO foram alterados."
fi

if [[ "$linhas" -le 0 ]]; then
    fail "Validação de schema falhou: CSV baixado tem 0 linhas de dado. contratos.csv e pipeline_metadata NÃO foram alterados."
fi

log "Validação de schema OK: todas as ${#cols_atual[@]} colunas esperadas presentes (case-insensitive). Colunas no arquivo novo: ${#cols_novo[@]}."

# ── 5.1. Filtro de coluna + reparo/quarentena de linha (spec 019) ──────────
# Nunca sobrescreve SEED_FILE com o TMP_FILE bruto — process_csv.py seleciona
# só as colunas já conhecidas (novas ficam de fora até incorporação
# deliberada, spec própria) e tenta reparar linhas malformadas (aspas
# escapadas fora do padrão RFC4180) antes de quarentená-las. Nunca roda
# `dbt seed --full-refresh` como consequência disso — o seed incremental
# funciona porque o arquivo já chega filtrado pro schema conhecido.
resumo=$(python3 /usr/app/dbt/scripts/process_csv.py "$SEED_FILE" "$TMP_FILE" "$FILTERED_FILE") \
    || fail "process_csv.py falhou (erro de processamento, não é quarentena). contratos.csv e pipeline_metadata NÃO foram alterados."
log "$resumo"

if [[ "$resumo" =~ \|\ ([0-9]+)\ em\ quarentena ]]; then
    n_quarentena="${BASH_REMATCH[1]}"
    if [[ "$n_quarentena" -gt 0 ]]; then
        log "AVISO: ${n_quarentena} linha(s) foram para quarentena nesta execução (${QUARANTINE_FILE})."
    fi
fi

mv "$FILTERED_FILE" "$SEED_FILE"
log "contratos.csv atualizado (filtrado via process_csv.py)."

# ── 6. dbt seed + dbt build ────────────────────────────────────────────────
cd /usr/app/dbt

if ! dbt seed --select contratos 2>&1 | tee -a "$LOG_FILE"; then
    fail "dbt seed falhou. pipeline_metadata NÃO foi atualizado."
fi

if ! dbt build 2>&1 | tee -a "$LOG_FILE"; then
    fail "dbt build falhou. pipeline_metadata NÃO foi atualizado."
fi

# ── 7. Atualizar ETag (só chega aqui se dbt seed + dbt build tiveram sucesso) ─
# A constraint (primary key) já existe desde o bootstrap (passo 0) — a
# tabela não é mais gerenciada pelo dbt, então não há swap recriando-a a
# cada execução.
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
