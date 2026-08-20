# Spec 017 — Validação de schema tolerante em `ingest.sh`

## Tipo

Decisão de arquitetura.

## Status

Implementado e validado isoladamente — os 4 cenários da guarda de schema (Investigação, item 2) passam exatamente como especificado. **O fluxo completo (`dbt seed` + `dbt build` contra o CSV real do portal) não valida de ponta a ponta** — dois bloqueios novos, independentes desta correção, foram descobertos ao testar contra Postgres real e ficam registrados como pendência (Casos de borda), não corrigidos aqui.

## Resumo

A spec 016 (levantamento) achou que a mudança real de schema do `contratos.csv` do portal é estritamente aditiva (8 colunas novas, 0 removidas, chaves estáveis, só divergência de maiúsculas/minúsculas) — mas a guarda de `ingest.sh` fazia comparação de string exata do header inteiro, mais rígida do que a spec 009 original pedia ("colunas esperadas presentes"), e travou uma mudança legítima e inofensiva.

Esta spec troca a guarda por checagem de **subconjunto, case-insensitive**: toda coluna que aparece no header do `seeds/contratos.csv` atual precisa existir no header do CSV baixado (ordem não importa, colunas extras são permitidas e ignoradas, case é normalizado). Continua auto-referencial (compara contra o próprio seed atual, sem lista hardcoded que fica desatualizada) e continua rejeitando qualquer coluna esperada genuinamente ausente.

Ao validar contra o Postgres real (não simulado), a correção em si funciona — mas o teste de ponta a ponta revelou que o pipeline **não processa o CSV real hoje**, por dois motivos que não têm relação com a guarda de schema: comportamento padrão do `dbt seed` e qualidade de dado do CSV do portal. Ver Casos de borda.

## Investigação

### 1. Diff de `ingest.sh`

```diff
--- a/dbt/scripts/ingest.sh
+++ b/dbt/scripts/ingest.sh
@@ -8,8 +8,9 @@
 # 2. Compara com o último ETag salvo em control.pipeline_metadata.
 # 3. Igual -> no-op (exit 0, sem baixar o corpo).
 # 4. Diferente (ou primeira execução) -> baixa o arquivo completo.
-# 5. Valida schema mínimo (header confere com o contratos.csv atual, linhas > 0)
-#    antes de sobrescrever seeds/contratos.csv. Falha aqui não toca em nada.
+# 5. Valida schema mínimo (subconjunto case-insensitive: toda coluna do
+#    contratos.csv atual presente no baixado, linhas > 0 — spec 017) antes de
+#    sobrescrever seeds/contratos.csv. Falha aqui não toca em nada.
 # 6. dbt seed --select contratos && dbt build.
 # 7. Só se 6 for bem-sucedido: grava o novo ETag em pipeline_metadata.
 # 8. Log em arquivo + stdout.
@@ -113,19 +114,38 @@ fi
 # Comparação contra o header do contratos.csv ATUAL (não contra
 # stg_contratos.yml — aquele arquivo documenta as colunas renomeadas de
 # saída do model de staging, não o header bruto do CSV do portal).
+#
+# Checagem de SUBCONJUNTO, case-insensitive (spec 017, achado spec 016): toda
+# coluna que aparece no header do seed ATUAL precisa existir no header do CSV
+# baixado — colunas extras (aditivas) e diferença de maiúscula/minúscula são
+# toleradas. Ainda rejeita qualquer coluna ESPERADA ausente (arquivo
+# corrompido/truncado continua barrado).
 header_novo=$(head -n 1 "$TMP_FILE")
 header_atual=$(head -n 1 "$SEED_FILE")
 linhas=$(($(wc -l < "$TMP_FILE") - 1))
 
-if [[ "$header_novo" != "$header_atual" ]]; then
-    fail "Validação de schema falhou: header do CSV baixado diverge do header atual de ${SEED_FILE}. contratos.csv e pipeline_metadata NÃO foram alterados. Novo: [${header_novo}] | Atual: [${header_atual}]"
+mapfile -t cols_novo < <(echo "$header_novo" | tr '[:upper:]' '[:lower:]' | tr ';' '\n')
+mapfile -t cols_atual < <(echo "$header_atual" | tr '[:upper:]' '[:lower:]' | tr ';' '\n')
+
+declare -A cols_novo_set
+for c in "${cols_novo[@]}"; do cols_novo_set["$c"]=1; done
+
+faltando=()
+for c in "${cols_atual[@]}"; do
+    if [[ -z "${cols_novo_set[$c]:-}" ]]; then
+        faltando+=("$c")
+    fi
+done
+
+if [[ ${#faltando[@]} -gt 0 ]]; then
+    fail "Validação de schema falhou: colunas esperadas ausentes no CSV baixado (comparação case-insensitive): ${faltando[*]}. contratos.csv e pipeline_metadata NÃO foram alterados."
 fi
 
 if [[ "$linhas" -le 0 ]]; then
     fail "Validação de schema falhou: CSV baixado tem 0 linhas de dado. contratos.csv e pipeline_metadata NÃO foram alterados."
 fi
 
-log "Validação de schema OK: header confere, ${linhas} linhas de dado."
+log "Validação de schema OK: todas as ${#cols_atual[@]} colunas esperadas presentes (case-insensitive). Colunas no arquivo novo: ${#cols_novo[@]}."
 
 mv "$TMP_FILE" "$SEED_FILE"
 log "contratos.csv atualizado."
```

### 2. Teste de infraestrutura

Rodado contra Postgres real (`compras_postgres`, mesmo volume usado em dev — não simulado), via imagem construída a partir de `dbt/Dockerfile.pipeline` (mesma imagem usada em produção). Achado de bancada: o build context do Windows local aplica `core.autocrlf=true` no checkout, o que introduzia `\r` no fim de cada linha do CSV e quebrava a comparação de header de forma espúria (`diasatuais` acusado como ausente por causa de um `\r` residual, não por divergência real de coluna). Corrigido gerando o contexto de build a partir de `git archive` normalizado para LF (idêntico byte a byte ao blob armazenado pelo git, confirmado via `diff`) — reproduz fielmente um checkout Linux (produção), sem esse artefato do ambiente de dev Windows. Não é um bug do `ingest.sh` nem do CSV do portal, só do ambiente local usado pra testar.

### 3. Cenário A — header real do portal (59 colunas, maiúsculas, aditivo) — deve PASSAR

Arquivo: primeiras 1000 linhas de dado do CSV real baixado do portal em 2026-08-20 (mesmo link da spec 016).

```
[2026-08-20 12:33:20] ETag do portal: teste-6e1f1d7ab5861500
[2026-08-20 12:33:20] Último ETag salvo: teste-027aed9020ce364b
[2026-08-20 12:33:20] ETag mudou (ou primeira execução) — processando.
[2026-08-20 12:33:20] Validação de schema OK: todas as 51 colunas esperadas presentes (case-insensitive). Colunas no arquivo novo: 59.
[2026-08-20 12:33:20] contratos.csv atualizado.
```

Passou — falhava antes da correção (mesma comparação, ver spec 016).

### 4. Cenário B — header truncado/garbled — deve CONTINUAR FALHANDO

Arquivo: header `cdunidadegestora;nmunidadegestora;cdgest` (mesmo teste da Etapa 6 original da spec 009).

```
[2026-08-20 12:39:27] ERRO: Validação de schema falhou: colunas esperadas ausentes no CSV baixado (comparação case-insensitive): cdgestao nmgestao nucontrato idcontratado contratado resumo objeto dtinicio dtfim dtfimatual dtassinatura situacao nuprocesso vloriginal vlatual nmfiscal nuedital nmbempublico nmregimeexecucao detipocontrato detipodocumentolegal nudocumentolegal demulta nuautorizacaoorgao nuprazo nminterveniente nmlocalexecucao nmmodalidade nmrepcredor nmrepinterveniente nmrepug dtautorizacao dtinclusao dtlimiteproposta vlgarantia vlpercgarantia vlpercmulta nutitulo vladitado cdugfiscalizador ugfiscalizador cdgestaofiscalizador gestaofiscalizador bempublico deesptitulo dataproposta diasoriginais diasaditados diasatuais. contratos.csv e pipeline_metadata NÃO foram alterados.
```

Falhou como esperado (exit 1) — confirma que a tolerância não virou "aceita qualquer coisa".

### 5. Cenário C — header real menos `NUCONTRATO` — deve FALHAR citando a coluna

Arquivo: header do Cenário A com a coluna `NUCONTRATO` removida (58 colunas).

```
[2026-08-20 12:39:28] ERRO: Validação de schema falhou: colunas esperadas ausentes no CSV baixado (comparação case-insensitive): nucontrato. contratos.csv e pipeline_metadata NÃO foram alterados.
```

Falhou citando especificamente `nucontrato`, como esperado.

### 6. Cenário D — no-op (mesmo ETag) — não deve chegar na validação de schema

`control.pipeline_metadata` ajustado manualmente pra conter o mesmo ETag do arquivo de teste (`teste-6e1f1d7ab5861500`), depois `ingest.sh` rodado de novo com o mesmo arquivo:

```
[2026-08-20 12:40:08] ETag do portal: teste-6e1f1d7ab5861500
[2026-08-20 12:40:09] Último ETag salvo: teste-6e1f1d7ab5861500
[2026-08-20 12:40:09] ETag inalterado — sem mudança. Encerrando (no-op).
EXIT CODE: 0
```

Saiu antes da validação de schema, sem regressão.

### 7. Fluxo completo (download real, não `INGEST_TEST_SOURCE_OVERRIDE`) — NÃO fecha

Download real do portal confirmado: 141.666 linhas totais, 59 colunas, `ETag: "1757412122.95-122184246"` (mesmo arquivo da spec 016). A guarda de schema (item 1-6 acima) passa normalmente contra esse arquivo. Mas o pipeline completo trava em dois pontos **depois** da validação de schema, nenhum deles causado por esta correção:

**7.1 — `dbt seed` sem `--full-refresh` falha contra a tabela existente.**

`raw.contratos` já existe no Postgres de dev com o schema antigo (51 colunas — confirmado via `\d raw.contratos`, 51 linhas em `information_schema.columns`). O comportamento padrão do `dbt seed` (dbt-core 1.9, adapter Postgres) quando a tabela já existe e não é passado `--full-refresh` é `TRUNCATE` + `INSERT` na tabela existente — não recria as colunas:

```
Database Error in seed contratos (seeds/contratos.csv)
  column "origem" of relation "contratos" does not exist
  LINE 2: ...insert into "compras_publicas"."raw"."contratos" (ORIGEM, CD...
```

Com `dbt seed --select contratos --full-refresh`, esse erro específico desaparece (a tabela é recriada com as 59 colunas) — mas aí bate no problema seguinte.

**7.2 — CSV real do portal tem linhas com contagem de campo malformada.**

Mesmo com `--full-refresh`, rodar contra o arquivo completo (141.666 linhas) dá erro de compilação do `dbt seed`:

```
Compilation Error in seed contratos (seeds/contratos.csv)
  Row 2687 has 63 values, but Table only has 59 columns.
```

Confirmado com parser CSV com reconhecimento de aspas (Python `csv.reader`, não `awk` ingênuo — que não respeita aspas e por isso não serve pra essa checagem):

```python
import csv
with open("contratos_portal_full.csv", encoding="utf-8", newline="") as f:
    r = csv.reader(f, delimiter=";")
    header = next(r)
    n = len(header)  # 59
    bad = sum(1 for row in r if len(row) != n)
```

```
total linhas de dado: 96239
total linhas com contagem de campo divergente: 747
```

Amostra das primeiras divergências (numeração 1-indexed incluindo header, conta linhas *lógicas* do CSV — já considera campos com quebra de linha embutida entre aspas):

```
linha 2689: 63 campos (esperado 59)
linha 4088: 61 campos (esperado 59)
linha 10163: 10 campos (esperado 59)
linha 10164: 1 campos (esperado 59)
linha 10165: 46 campos (esperado 59)
```

Inspeção da linha 2689 mostra os dois últimos campos (`NMFISCAL`, `CDFISCAL` — colunas novas, spec 016 item 5) contendo múltiplos valores separados por `; ` dentro de um único campo entre aspas duplas — a causa exata da divergência de contagem não foi determinada nesta sessão (aspas mal-fechadas em outro ponto da linha, campo textual com aspas literais não escapadas, ou outra causa). **747 de 96.239 linhas de dado (0,78%) são afetadas.** `dbt seed` falha no primeiro erro, não pula linhas malformadas — bloqueia a carga inteira.

**Conclusão do item 7:** a correção da guarda de schema (esta spec) está correta e resolve exatamente o que a spec 016 achou. Mas ela sozinha **não é suficiente pra processar o CSV real do portal hoje** — dois bloqueios adicionais, não descobertos antes desta sessão, seguem impedindo `dbt seed`/`dbt build` de terminar com sucesso. Nenhum dos dois foi corrigido aqui (decisão explícita — ver Status). Não foi possível reportar contagem real de `select count(*) from raw.contratos` pedida no item 3 do prompt de implementação, porque a carga não completa.

## Requirements

### Funcionais

1. QUANDO o CSV baixado tiver todas as colunas do `seeds/contratos.csv` atual presentes (comparação case-insensitive, ordem irrelevante), O sistema DEVE prosseguir com a ingestão, independente de colunas extras presentes no arquivo baixado.
2. QUANDO uma ou mais colunas do `seeds/contratos.csv` atual estiverem ausentes no CSV baixado (mesmo com normalização de case), O sistema DEVE falhar a validação, listar especificamente as colunas ausentes na mensagem de erro, e NÃO DEVE sobrescrever `seeds/contratos.csv` nem `pipeline_metadata`.
3. A comparação DEVE seguir auto-referencial — contra o header do `seeds/contratos.csv` atualmente versionado, não contra uma lista hardcoded separada que precisaria ser mantida manualmente.

### Não-funcionais

1. A mudança DEVE manter o comportamento já existente de "falha não toca em nada" ([[009-automacao-da-ingestao]], Requirement funcional 5) — inalterado por esta spec.

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| Tipo de comparação | Subconjunto (colunas esperadas ⊆ colunas do arquivo novo), não igualdade exata | Achado da spec 016: a mudança real do portal foi estritamente aditiva. Igualdade exata é mais rígida do que a spec 009 original pedia ("colunas esperadas presentes") e trava mudanças aditivas inofensivas. |
| Case | Normalizado para minúsculo antes de comparar | O portal já mudou de minúsculo pra maiúsculo uma vez (spec 016) sem nenhuma mudança de significado — tratar isso como falha exigiria intervenção manual toda vez que o portal decidir mudar convenção de case, sem ganho real de segurança. |
| Fonte da lista de colunas esperadas | `seeds/contratos.csv` atual (auto-referencial), não lista hardcoded | Mesmo raciocínio da guarda original (spec 009) — evita lista que fica desatualizada por conta própria. |
| Colunas extras no arquivo novo | Toleradas e ignoradas nesta etapa | `stg_contratos.sql` já seleciona por nome (Caso de borda 2 da spec 016) — colunas extras não usadas simplesmente não aparecem no staging. Decisão de incorporá-las ou não ao modelo é separada, não desta spec. |
| Coluna esperada genuinamente ausente | Continua bloqueando, com a coluna citada na mensagem de erro | Trade-off aceito conscientemente (ver Casos de borda) — proteção real contra arquivo corrompido/truncado ou mudança de schema que remove/renomeia coluna de verdade. |

### Componentes afetados

- `dbt/scripts/ingest.sh` (linhas ~112-151 antes da mudança) — única mudança de código desta spec.

## Casos de borda

1. **Coluna removida ou renomeada de verdade (não só case) continua bloqueando a ingestão.** Comportamento correto e intencional — é exatamente o cenário que a guarda existe pra pegar (Cenário C validado acima). Só a falsa-alarme de colunas aditivas/case foi eliminada, não a proteção real.
2. **[Não resolvido nesta spec] `dbt seed` sem `--full-refresh` falha na primeira ingestão de um CSV com coluna nova**, porque a tabela `raw.contratos` já existe com o schema antigo e o comportamento padrão do dbt é `TRUNCATE`+`INSERT`, não recriar colunas (achado do item 7.1 da Investigação). `ingest.sh` hoje roda `dbt seed --select contratos` sem essa flag. Decisão sobre se `--full-refresh` deveria ser permanente (mudança de comportamento: a tabela é sempre recriada do zero a cada execução, não só truncada) fica para spec própria — não decidida aqui.
3. **[Não resolvido nesta spec] ~0,78% das linhas do CSV real do portal (747 de 96.239) têm contagem de campo divergente do header** quando parseadas com reconhecimento de aspas (achado do item 7.2 da Investigação). Causa raiz exata não determinada. `dbt seed` falha no primeiro erro (não pula linhas malformadas), bloqueando a carga inteira do arquivo atual até essa questão ser investigada e decidida em spec própria.
4. **Consequência dos itens 2 e 3 acima:** a guarda de schema desta spec, sozinha, não é suficiente pra fazer o CSV real do portal (formato atual, 59 colunas) fluir de ponta a ponta pelo pipeline hoje. A guarda faz exatamente o que deveria fazer (validar schema); os dois bloqueios são de uma camada diferente (materialização do `dbt seed` e qualidade de dado do CSV), fora do escopo desta spec.

## Fora do escopo

- Corrigir o comportamento do `dbt seed` em relação a `--full-refresh` (Caso de borda 2).
- Investigar ou corrigir as 747 linhas malformadas do CSV real (Caso de borda 3).
- Qualquer mudança em `stg_contratos.sql`, `stg_contratos.yml`, ou incorporação das 8 colunas novas ao modelo de staging (já era fora do escopo da spec 016, Caso de borda 2 daquela spec).
- Investigação da causa do crescimento de +43,7% em número de linhas (já registrado como fora do escopo da spec 016).

## Referências de código

- `dbt/scripts/ingest.sh:112-151` — validação de schema tolerante (esta spec).
- `dbt/seeds/contratos.csv` — fonte da lista de colunas esperadas (auto-referencial).
- `dbt/Dockerfile.pipeline` — imagem usada para validar esta spec contra Postgres real.

## Ver também

- [[016-levantamento-schema-csv-portal]] (levantamento que originou esta decisão)
- [[009-automacao-da-ingestao]] (spec que define a guarda de validação de schema original, ver Design, linha "Validação antes do `dbt run`")
