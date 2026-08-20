# 019 — Processamento robusto do CSV real: filtro de colunas e reparo/quarentena de linhas malformadas

## Tipo

Decisão de arquitetura — resolve os Casos de borda 1, 2 e 3 da spec 018 (levantamento).

## Status

Implementado e validado de ponta a ponta contra o portal real (5 cenários, output literal na seção Validação). Todos os Requirements funcionais e não-funcionais fechados. Um achado incidental fora do escopo original desta spec (bug pré-existente na validação de header da spec 017, CRLF vs LF) bloqueava 100% das execuções reais e foi corrigido — ver item "Achado incidental" na Validação.

## Resumo

A spec 018 achou dois bloqueios reais impedindo o CSV real do portal (59 colunas, 96.239 linhas) de fluir pelo pipeline: (1) `dbt seed` sem `--full-refresh` falha porque o CSV baixado tem colunas que a tabela não tem, e `--full-refresh` "resolve" isso recriando o schema via inferência de tipo do `agate` — que erra feio (datas viram `text`, dinheiro vira `double precision`, `IDCONTRATADO`/CNPJ quase estoura `integer`); (2) 69 registros reais (não 747 linhas, depois do agrupamento em clusters) têm aspas internas escapadas de forma não-padrão (`\"` em vez de `""`), o que estilhaça a linha em múltiplos fragmentos — incluindo pelo menos 2 contratos de alto valor (R$ 14-19 milhões e R$ 2,1-2,2 milhões).

Esta spec decide: **nunca rodar `--full-refresh` automaticamente** — em vez disso, filtrar o CSV baixado pro subconjunto de colunas já conhecido antes de alimentar o `dbt seed`, tornando incorporar coluna nova um ato deliberado (spec própria), não algo que a automação decide sozinha sob risco de inferência errada. E **tentar reparar as linhas malformadas antes de quarentenar** — nunca descartar silenciosamente, dado que já confirmamos que registros de alto valor podem estar entre elas.

## Contexto

- [[018-levantamento-bloqueios-seed-csv-real]]: achado central — schema "correto" da tabela hoje não é protegido por `column_types`, e `--full-refresh` sem essa proteção regride tipos silenciosamente.
- [[017-validacao-schema-tolerante]]: a guarda de header (subconjunto case-insensitive) já garante que as colunas *esperadas* estão presentes — esta spec assume que essa guarda já passou antes de qualquer processamento aqui descrito.
- [[016-levantamento-schema-csv-portal]]: mapeamento das 8 colunas novas — nenhuma delas é usada por `stg_contratos.sql` hoje; incorporá-las é decisão separada e futura, não tomada aqui.
- O container de ingestão (`dbt/Dockerfile.pipeline`) já inclui `python3`/`pip` — a lógica desta spec usa a stdlib `csv` do Python (parser com reconhecimento de aspas, RFC4180), sem dependência nova.

## Requirements

### Funcionais

1. Depois da validação de header (spec 017) e antes de sobrescrever `seeds/contratos.csv`, O sistema DEVE processar o CSV baixado através de um script dedicado (`dbt/scripts/process_csv.py` ou nome equivalente), não mais um `mv` direto do arquivo baixado.

2. O script de processamento DEVE selecionar e reordenar **somente** as colunas que já existem no `seeds/contratos.csv` atual (mesmo conjunto validado pela guarda de header da spec 017), descartando colunas novas do arquivo baixado — a incorporação de coluna nova ao modelo é decisão de spec própria, não automática.

3. O sistema NÃO DEVE rodar `dbt seed --full-refresh` como parte do fluxo automático de ingestão — o `dbt seed` (incremental, `TRUNCATE`+`INSERT`) DEVE continuar funcionando porque o arquivo já foi filtrado pro schema conhecido no passo anterior.

4. Para cada linha do CSV baixado, O sistema DEVE tentar parsear com o parser CSV padrão (reconhecimento de aspas RFC4180). QUANDO uma linha falhar a contagem de campo esperada, O sistema DEVE tentar reparar aplicando a heurística de substituição `\"` → `""` (achado da spec 018) e reparsear antes de desistir da linha.

5. QUANDO uma linha, mesmo após a tentativa de reparo do item 4, continuar com contagem de campo divergente, O sistema NÃO DEVE descartá-la silenciosamente — DEVE gravá-la (conteúdo original, sem reparo) num arquivo de quarentena separado (`dbt/seeds/contratos_quarentena.csv` ou caminho equivalente), com o número da linha original e o motivo, e seguir processando o restante do arquivo.

6. O log da execução DEVE reportar, de forma visível (não só no arquivo de log, também no exit/resumo): quantas linhas foram processadas com sucesso, quantas foram reparadas, e quantas foram pra quarentena — nunca um número de quarentena maior que zero deve passar despercebido no log.

7. QUANDO o arquivo de quarentena acumular linhas de execuções anteriores, O sistema DEVE anexar (não sobrescrever) — quarentena é registro cumulativo até alguém revisar e decidir o destino de cada linha.

### Não-funcionais

1. O reparo (item 4) DEVE ser aplicado apenas dentro do valor de campos de texto (não deve alterar a estrutura de delimitação `;` em si) — a substituição é textual e ingênua o suficiente para, em tese, reparar um `\"` que não devesse ser reparado; isso é um risco aceito conscientemente (ver Casos de borda), não uma garantia de reparo perfeito.

2. O desempenho do processamento (item 1-6) para o volume atual (~96 mil linhas) DEVE permanecer na mesma ordem de grandeza do `dbt seed` isolado (spec 018, item 9: ~228s) — não DEVE dobrar o tempo total da rotina de forma perceptível. Validar na implementação, não presumido aqui.

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| `--full-refresh` automático | **Nunca** — substituído por filtro de coluna antes do `dbt seed` | Achado da spec 018: `--full-refresh` sem `column_types` regride tipo de coluna silenciosamente (datas→text, dinheiro→double precision, CNPJ quase overflow). Filtrar colunas resolve a causa raiz (mismatch de coluna) sem esse risco. |
| Onde a lógica roda | Script Python dedicado, dentro da imagem já existente (stdlib `csv`, sem dependência nova) | Bash puro não faz parsing CSV com reconhecimento de aspas de forma confiável — e já sabemos, pela própria spec 018, que a fonte tem aspas mal-escapadas que exigem parser de verdade, não `awk`/split ingênuo. |
| Coluna nova do portal | Descartada silenciosamente do arquivo de trabalho (não do CSV baixado bruto, que seguirá existindo em `TMP_FILE` até ser sobrescrito) — incorporação é spec futura | Mantém o pipeline automático estável; evita que a automação tome decisão de modelagem sozinha. |
| Linha malformada | Tentar reparar (`\"` → `""` + reparse); se falhar, quarentena — nunca descarte silencioso | Já confirmado (spec 018) que pelo menos 2 dos casos são contratos de alto valor — descartar sem tentativa de reparo seria perda de dado real de interesse público. |
| Quarentena | Arquivo separado, cumulativo, linha original preservada + motivo | Preserva o dado bruto pra revisão manual futura, sem bloquear o restante do pipeline nem se perder entre execuções. |
| `column_types` no seed | Não implementado nesta spec — deixado como item de higiene futura, menor urgência agora que o filtro de coluna evita `--full-refresh` no fluxo automático | Achado da spec 018 (custo do `--full-refresh` é desprezível) deixa de ser argumento decisivo, já que a spec 018 propositalmente evita usá-lo automaticamente. Se algum dia um `--full-refresh` manual for necessário, `column_types` continua sendo pré-requisito — registrado, não esquecido. |

### Componentes afetados

- `dbt/scripts/ingest.sh`: passo 5 (validação/substituição do seed) muda de `mv "$TMP_FILE" "$SEED_FILE"` direto para invocar o script de processamento novo.
- `dbt/scripts/process_csv.py` (novo): filtro de coluna + reparo/quarentena de linha.
- `dbt/seeds/contratos_quarentena.csv` (novo, gerado em runtime — decidir na implementação se entra no `.gitignore` do ambiente de produção ou se é copiado pra fora do container via volume, já que o container é efêmero e a quarentena precisa sobreviver entre execuções).

## Validação

Implementação: `dbt/scripts/process_csv.py` (filtro de coluna + reparo/quarentena, stdlib `csv`) integrado em `dbt/scripts/ingest.sh` (passo 5.1, entre a validação de header da spec 017 e o `dbt seed`). Testado com o CSV real do portal (mesmo ETag `1757412122.95-122184246` das specs 016/017/018 — arquivo não mudou desde então).

### Cenário 1 — 51 colunas conhecidas, sem problema

Fixture: primeiras 100 linhas lógicas do `seeds/contratos.csv` atual (identificadas via `csv.reader.line_num`, não `head -n`, porque o seed real tem campos com quebra de linha embutida — 98.560 linhas físicas para 76.041 linhas lógicas).

```
process_csv: 100 linhas lidas | 100 ok | 0 reparadas | 0 em quarentena
```

Comparação campo-a-campo (não byte-a-byte — o `csv.writer` usa `QUOTE_MINIMAL`, o arquivo original usa aspas em todo campo; conteúdo idêntico, formatação de citação difere) entre entrada e saída: **0 linhas com diferença de valor**, 101/101 linhas comparadas.

### Cenário 2 — CSV real do portal (59 colunas) → filtro pra 51

Download real (`curl`, 122.184.246 bytes, 141.666 linhas físicas, 59 colunas — igual à spec 018):

```
process_csv: 96239 linhas lidas | 95492 ok | 16 reparadas | 731 em quarentena
```

Header de saída idêntico (mesmo conteúdo, só `\r\n` do seed vs `\n` da saída — ver Achado incidental) ao header atual de 51 colunas, mesma ordem. `96239 = 95492 + 16 + 731` — bate exatamente com as 747 linhas malformadas da spec 018 (95492 "ok direto" também bate com os 95.492 do item 7 da spec 018, que removeu manualmente as 747 linhas problemáticas).

### Cenário 3 — linhas malformadas reais (69 incidentes da spec 018)

Das 747 linhas malformadas: **16 reparadas com sucesso, 731 em quarentena** (88 clusters de linhas consecutivas na quarentena — mais que os 69 originais porque remover as 16 reparadas do meio de alguns clusters multi-linha os divide em fragmentos menores, o que é esperado).

Caso de alto valor (linha 2689, contrato `CT-00006/2013/SIE`, R$ 14,4–19,8 milhões, spec 018 item 5): **reparado com sucesso**, presente na saída filtrada, ausente da quarentena — confirmado por busca literal do valor `14444280` (1 ocorrência na saída, 0 na quarentena). Campo `OBJETO` reparado contém `""Programa Caminhos do Desenvolvimento""` (aspas duplicadas corretas, RFC4180) em vez do `\"` original.

Segundo caso de alto valor (linha 4088, `PJ-00152/2016`, R$ 2,1 milhões, spec 018 item 5): também **reparado com sucesso** (`2141000` presente na saída).

Tempo de processamento: 2,3s para as 96.239 linhas — não mede-se perceptível no total da rotina (NFR 2).

### Cenário 4 — quarentena cumulativa entre execuções

Duas rodadas sequenciais (arquivos diferentes, uma linha malformada irreparável cada), mesmo `QUARANTINE_FILE`:

```
=== RUN 1 ===
process_csv: 2 linhas lidas | 1 ok | 0 reparadas | 1 em quarentena
=== RUN 2 ===
process_csv: 2 linhas lidas | 1 ok | 0 reparadas | 1 em quarentena
=== conteúdo acumulado da quarentena ===
numero_linha;motivo;linha_bruta
3;contagem de campos: esperado 51, obtido 2;"linha_quebrada_run1;so_dois_campos
"
3;contagem de campos: esperado 51, obtido 2;"linha_quebrada_run2;so_dois_campos
"
```

Header gravado uma única vez, linhas das duas execuções presentes — anexação confirmada (Requirement funcional 7).

### Cenário 5 — fluxo completo de ponta a ponta

`docker compose run --rm pipeline` (serviço novo em `docker-compose.yml`, mesma imagem `Dockerfile.pipeline` da produção) contra Postgres local e download real do portal.

```
[...] ETag do portal: 1757412122.95-122184246
[...] Validação de schema OK: todas as 51 colunas esperadas presentes (case-insensitive). Colunas no arquivo novo: 59.
[...] process_csv: 96239 linhas lidas | 95492 ok | 16 reparadas | 731 em quarentena (/var/log/compras-publicas/contratos_quarentena.csv)
[...] AVISO: 731 linha(s) foram para quarentena nesta execução (/var/log/compras-publicas/contratos_quarentena.csv).
[...] contratos.csv atualizado (filtrado via process_csv.py).
[...] Finished running 1 seed, 12 table models, 104 data tests, 11 view models in 199.61s
[...] Done. PASS=128 WARN=0 ERROR=0 SKIP=0 TOTAL=128
[...] pipeline_metadata atualizado com ETag: 1757412122.95-122184246
[...] Fim da rotina de ingestão (sucesso)
```

`select count(*) from raw.contratos` (consulta real via `psql`, não `wc -l`): **95508** — bate exatamente com `95492 ok + 16 reparadas` do `process_csv.py` desta execução. Schema confirmado inalterado (`character varying`/`text`, sem regressão de tipo — nenhum `--full-refresh` rodou). Quarentena desta execução: **731 linhas** (conferido via `csv.reader`, não `wc -l` — o arquivo de quarentena cumulativo tem campos com quebra de linha real embutida, herdada das linhas malformadas originais, então contagem de linha física não corresponde a contagem de registro).

### Achado incidental — bug pré-existente na validação de header (spec 017)

Fora do escopo original desta spec, mas descoberto ao rodar o Cenário 5 e **bloqueava 100% das execuções reais**, não um caso de borda raro: `header_atual=$(head -n 1 "$SEED_FILE")` em `ingest.sh` (validação de header, spec 017, já modificada sem commit antes desta sessão) captura um `\r` residual porque `$(...)` só remove `\n` à direita, não `\r` — o `seeds/contratos.csv` committado usa `CRLF` e o download real do portal usa `LF`. O último nome de coluna do header (`diasatuais`) chegava como `"diasatuais\r"` e nunca batia com `"diasatuais"`, falhando a validação de subconjunto mesmo com a coluna presente. Corrigido com `tr -d '\r'` na captura de ambos os headers (`ingest.sh`, mesmo trecho). Sem essa correção, o Cenário 5 não fecha e a rotina real falharia sempre, hoje, em produção.

## Casos de borda

- **O reparo pode, em tese, corromper um `\"` legítimo** (ex.: um caractere de escape que não devesse virar aspas dupla) — risco aceito conscientemente (Requirement não-funcional 1), porque a alternativa (não tentar reparar) descarta ou quarenta 100% dos casos, incluindo os reparáveis. Se isso se provar um problema real na prática, reforçar a heurística fica pra spec futura.
- **Quarentena crescendo sem revisão** — o Requirement funcional 7 (anexar, não sobrescrever) evita perda de dado, mas não evita acúmulo indefinido se ninguém revisar. Não há mecanismo de alerta automático desta spec — fica documentado como responsabilidade operacional, não resolvido em código.
- **O container é efêmero** (`docker-compose run --rm`) — o arquivo de quarentena, se gravado só dentro do container, se perde a cada execução. Precisa de volume persistente (mesmo padrão já usado pro `/var/log/compras-publicas`) — detalhe de implementação a resolver, sinalizado aqui pra não ser esquecido.
- **Coluna esperada (das 51 já conhecidas) ausente no arquivo baixado** — isso já é coberto pela guarda da spec 017 (roda antes desta spec, no fluxo do `ingest.sh`) — não é responsabilidade desta spec re-verificar.

## Fora do escopo

- Implementar `column_types` completo no seed (ver Design — item de higiene futura, não urgente com esta decisão).
- Determinar exatamente qual combinação de `\"` produz estilhaçamento vs. as ocorrências que não produzem (spec 018, item 5, não resolvido lá nem aqui).
- Incorporar qualquer uma das 8 colunas novas ao modelo (`stg_contratos.sql`) — decisão de modelagem separada, spec própria quando/se decidido.
- Mecanismo de alerta automático para quarentena acumulada.
- Normalizar concentração de erro por órgão (spec 018, Caso de borda 6).

## Referências de código

- `dbt/scripts/process_csv.py` (novo) — filtro de coluna + reparo/quarentena de linha, stdlib `csv`.
- `dbt/scripts/ingest.sh:29-40` — `FILTERED_FILE`, `QUARANTINE_FILE` (novo, mesmo `LOG_DIR`).
- `dbt/scripts/ingest.sh:133-139` — `tr -d '\r'` na captura de header (achado incidental, não originalmente desta spec).
- `dbt/scripts/ingest.sh:165-184` — chamada a `process_csv.py`, log do resumo, `AVISO` de quarentena visível (Requirement funcional 6), `mv "$FILTERED_FILE" "$SEED_FILE"` (não mais o `TMP_FILE` bruto).
- `docker-compose.yml` — serviço `pipeline` (novo, `profiles: ["pipeline"]`), volume `./logs:/var/log/compras-publicas`.
- `.gitignore` — `/logs/` (artefato de log/quarentena do serviço `pipeline` local).
- Infra (repo privado, não alterado): `docker-compose.pipeline.yml` já mapeia `/home/ubuntu/logs/compras-publicas:/var/log/compras-publicas` — cobre o caminho da quarentena sem mudança, confirmado por leitura direta do arquivo.

## Ver também

- [[018-levantamento-bloqueios-seed-csv-real]]
- [[017-validacao-schema-tolerante]]
- [[016-levantamento-schema-csv-portal]]
- [[009-automacao-da-ingestao]]
