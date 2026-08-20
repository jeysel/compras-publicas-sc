# Spec 016 — Levantamento: mudança de schema do `contratos.csv` do portal

## Tipo

Investigação (levantamento). Somente leitura — nenhum código alterado nesta sessão (`stg_contratos.sql`, `dbt/seeds/contratos.csv`, `dbt/scripts/ingest.sh` intocados).

## Status

Levantamento concluído. Decisão sobre como (e se) adaptar `ingest.sh`/`stg_contratos.sql` **não tomada aqui** — fica para uma spec de Design própria, com o usuário.

## Resumo

A guarda de validação de schema de `ingest.sh` (linha 120: comparação exata de `head -n 1` do CSV baixado contra `head -n 1` do seed versionado) rejeitou corretamente a ingestão mais recente: o CSV publicado hoje pelo portal tem **59 colunas maiúsculas**, o seed versionado (`dbt/seeds/contratos.csv`) tem **51 colunas minúsculas**. Nenhum dado foi corrompido — a guarda funcionou como projetado (spec 009). Este levantamento mapeia exatamente o que mudou.

Achado central: as 8 colunas novas são genuinamente aditivas — nenhuma das 51 colunas do schema antigo foi removida ou renomeada. A divergência de case (minúsculo vs. maiúsculo) é cosmética. O achado mais relevante para as specs 007/012 (chave de fornecedor = `idcontratado` íntegro) é que `IDCONTRATADOMASCARADO`, apesar do nome, **não é mascaramento/redação de dado** — é o mesmo CNPJ de `IDCONTRATADO`, só formatado com pontuação (`01.993.902/0001-39` em vez de `1993902000139`). Confirmado byte a byte em amostra de 30 linhas.

## Investigação

### 1. Download do CSV atual e comparação de cabeçalho

```
curl -sS -o contratos_atual.csv "https://dados.sc.gov.br/dataset/93dab950-e805-4388-8418-cfb3b73f1623/resource/8bb98383-7043-4d2f-ae32-9377656e71ee/download/contratos.csv"
```

```
$ head -1 contratos_atual.csv | awk -F';' '{print NF}'
59
$ head -1 dbt/seeds/contratos.csv | awk -F';' '{print NF}'
51
$ wc -l contratos_atual.csv
141666 contratos_atual.csv
$ wc -l dbt/seeds/contratos.csv
98560 dbt/seeds/contratos.csv
$ wc -c contratos_atual.csv
122184246
```

Nota: as contagens de 46/58 colunas mencionadas na hipótese inicial eram de memória — a contagem real e exata é **51 → 59** (8 colunas novas, 0 removidas). O volume de linhas também cresceu: 98.560 → 141.666 (+43.106 linhas, +43,7%), independente da mudança de schema — mais dados históricos ou período coberto maior, não investigado a fundo nesta rodada.

`HEAD` no portal:

```
HTTP/1.1 200 OK
ETag: "1757412122.95-122184246"
Last-Modified: Tue, 09 Sep 2025 10:02:02 GMT
```

O `Last-Modified` indica que o arquivo no formato atual está publicado desde **09/09/2025** — a divergência não é uma mudança de hoje, é uma mudança que já existia há quase um ano e só foi detectada agora (primeira vez que a rotina de ingestão rodou contra o portal desde então, ou primeira vez que o ETag mudou o suficiente para dsiparar o passo 4 do `ingest.sh`).

### 2. Mapeamento sistemático de colunas (case-insensitive)

```python
atual = pd.read_csv('contratos_atual.csv', sep=';', nrows=100)
antigo_cols = pd.read_csv('dbt/seeds/contratos.csv', sep=';', nrows=1).columns.tolist()
```

**Colunas do seed atual (51, minúsculas):**
`cdunidadegestora, nmunidadegestora, cdgestao, nmgestao, nucontrato, idcontratado, contratado, resumo, objeto, dtinicio, dtfim, dtfimatual, dtassinatura, situacao, nuprocesso, vloriginal, vlatual, nmfiscal, nuedital, nmbempublico, nmregimeexecucao, detipocontrato, detipodocumentolegal, nudocumentolegal, demulta, nuautorizacaoorgao, nuprazo, nminterveniente, nmlocalexecucao, nmmodalidade, nmrepcredor, nmrepinterveniente, nmrepug, dtautorizacao, dtinclusao, dtlimiteproposta, vlgarantia, vlpercgarantia, vlpercmulta, nutitulo, vladitado, cdugfiscalizador, ugfiscalizador, cdgestaofiscalizador, gestaofiscalizador, bempublico, deesptitulo, dataproposta, diasoriginais, diasaditados, diasatuais`

**Colunas do portal agora (59, maiúsculas):** as 51 acima (mesmo nome, maiúsculo) **+** `ORIGEM, DTINIBUSCA, NUPROCESSOFORMATADO, TAGS, INDICE, IDCONTRATADOMASCARADO, CDCREDOR, CDFISCAL`.

**Só no schema novo (8):** `cdcredor, cdfiscal, dtinibusca, idcontratadomascarado, indice, nuprocessoformatado, origem, tags`
**Só no schema antigo (0):** nenhuma. Todas as 51 colunas do seed existem no portal, sob o mesmo nome (case-insensitive).
**Em ambos, mesma base (51):** confirma que nada foi renomeado — só a caixa (upper/lower) mudou, e o schema não removeu nada.

### 3. `IDCONTRATADOMASCARADO` — não é mascaramento de dado

Hipótese de risco checada: o portal teria passado a redigir/ocultar CNPJ, o que quebraria a chave de `dim_fornecedor` (specs 007/012).

```
IDCONTRATADO     IDCONTRATADOMASCARADO   formatado_calculado(IDCONTRATADO)   bate
01993902000139   01.993.902/0001-39      01.993.902/0001-39                  True
06099082000150   06.099.082/0001-50      06.099.082/0001-50                  True
...(30 linhas testadas, 100% batem)
```

`IDCONTRATADOMASCARADO` = `IDCONTRATADO` formatado com a máscara de exibição de CNPJ (`00.000.000/0001-00`). "Mascarado" aqui é o sentido de UI ("input mask"), não de segurança/redação. `IDCONTRATADO` continua presente, íntegro, sem pontuação, exatamente como sempre esteve — **a chave usada hoje em `dim_fornecedor` não foi afetada.**

Outras colunas candidatas a identificador de fornecedor, pra registro:
- `CONTRATADO` — razão social (já usada, sem mudança).
- `NMREPCREDOR` — nome de representante do credor; nula na quase totalidade da amostra (10/10 nulos em 100 linhas). Já existia no schema antigo, não é novidade.
- `CDCREDOR` — inteiro sequencial pequeno (ex.: `112664`, `225858`), claramente um ID interno do SICOP para o credor, distinto do CNPJ. Não teve overlap de valor testado com `IDCONTRATADO` — são domínios diferentes (CDCREDOR é um ID interno curto, não CNPJ).

### 4. Chaves já usadas em `stg_contratos.sql` — presentes e inalteradas

```
NUCONTRATO: ['CT-00009/2024/SPAF', 'CT-00009/2025/SPAF', 'CT-00011/2024/SPAF', ...]
CDUNIDADEGESTORA: [290001, 290001, 290001, ...]
NUPROCESSO: ['SPAF 96/2023', 'SPAF 428/2024', 'SCC 16404/2021', ...]
```

Todas as três presentes, mesmo nome (maiúsculo), mesmo formato de valor observado na amostra — sem sinal da mudança de padrão que já ocorreu antes com `nucontrato` (spec 005/006, não repetida aqui).

### 5. As 8 colunas novas, uma a uma

| Coluna | Amostra | Nulos (amostra 100-2000) | O que é |
|---|---|---|---|
| `ORIGEM` | `SICOP` (100% das 2000 linhas amostradas) | 0 | Sistema de origem do registro. Valor constante na amostra — não investigado se existe outro valor em linhas fora da amostra. |
| `DTINIBUSCA` | `2024-07-02 00:00:00.0`, `2009-06-15 00:00:00.0` | 0/100 | Timestamp, formato `YYYY-MM-DD HH:MM:SS.f`. Nome sugere "data de início de busca/indexação" — não é uma data de negócio do contrato (não confundir com `dtinicio`). |
| `CDCREDOR` | `112664`, `225858`, `631591` | 0/100 | ID interno sequencial do credor no SICOP (ver item 3 acima). |
| `NMFISCAL` | `FÁBIO FARINA; MANOELA BORSA` | 1/100 | **Já existia no schema antigo** (está nas 51 colunas em comum) — não é campo novo, listado aqui só porque o levantamento original pediu pra checar. Múltiplos nomes separados por `;`. |
| `CDFISCAL` | `2608587657; 3036053986` | 1/100 | Par de `NMFISCAL` — IDs numéricos dos fiscais, mesma separação por `;`, mesma posição de nulo. Genuinamente novo. |
| `NUPROCESSOFORMATADO` | `SPAF 00000096/2023` (vs. `NUPROCESSO` = `SPAF 96/2023`) | 560/2000 (28%) | Mesma informação de `NUPROCESSO`, com a parte numérica preenchida com zeros à esquerda até 8 dígitos. Redundante — confirmado comparando as duas colunas lado a lado (15 linhas, todas consistentes). Nulo bem mais que `NUPROCESSO` (que já tem placeholders `" "` documentados nas specs 005/006). |
| `TAGS` | vazio nas primeiras 2000 linhas | 2000/2000 na amostra | Coluna quase sempre vazia — mas não 100% vazia no arquivo completo: 9.916 de 141.665 linhas (7%) têm valor, checado via `awk` no arquivo inteiro (não só na amostra pandas). Conteúdo real não inspecionado nesta rodada. |
| `INDICE` | string longa, pipe-delimitada (`SICOP|290001|SECRETARIA...|CT-00009/2024/SPAF|MORE...|01993902000139||...`) | 0/2000 | Concatenação de ~15 outros campos já existentes (unidade gestora, número de contrato, contratado, objeto, datas, valor) num único campo pipe-delimitado — parece um campo de índice de busca full-text gerado pelo SICOP, não um dado novo de negócio. Redundante com colunas já existentes. |

## Requirements

Não fechado nesta spec — é levantamento puro. Ver Casos de borda para as decisões pendentes que qualquer spec de Design subsequente vai precisar resolver.

## Design

Não fechado nesta spec. Nenhuma mudança aplicada a `ingest.sh`, `stg_contratos.sql`, `stg_contratos.yml`, ou `dbt/seeds/contratos.csv`.

### Componentes afetados

Nenhum — investigação apenas.

## Casos de borda

Pendências identificadas que uma spec de Design (017?) precisa decidir, não decididas aqui:

1. **Resolvido — ver [[017-validacao-schema-tolerante]].** Comparação de header em `ingest.sh` era case-sensitive e sensível a colunas extras. A guarda atual (`ingest.sh:120`) fazia `[[ "$header_novo" != "$header_atual" ]]` — comparação de string exata. Qualquer mudança de case ou coluna adicional (mesmo aditiva e inofensiva, como confirmado aqui) travava a ingestão indefinidamente até intervenção manual. A spec 017 trocou por checagem de subconjunto case-insensitive (colunas esperadas ⊆ colunas do arquivo novo), validada contra os 4 cenários (aditivo real, truncado, coluna genuinamente ausente, no-op). Nota: a spec 017 também achou que essa correção sozinha não é suficiente pra processar o CSV real de ponta a ponta hoje — dois bloqueios novos e independentes (comportamento do `dbt seed` sem `--full-refresh`; ~0,78% de linhas malformadas no CSV real) ficaram registrados como pendência não resolvida na 017.
2. **`dbt seed` infere colunas do CSV.** Como `dbt/seeds/schema/contratos.yml` só documenta 4 colunas (não declara tipo/contrato rígido para as 51), adicionar as 8 colunas novas ao seed não quebraria o `dbt seed` em si — só o `stg_contratos.sql` continuaria selecionando as mesmas 51 (via nome, case-insensitive no Postgres/dbt) e ignorando as 8 novas silenciosamente. Isso é aceitável como comportamento de transição, mas decidir se `NUPROCESSOFORMATADO`, `CDFISCAL`, `CDCREDOR` ou `ORIGEM` deveriam ser incorporados a `stg_contratos.sql` é decisão de Design, não tomada aqui.
3. **`TAGS` e `INDICE` não foram inspecionados no arquivo inteiro (só amostra + uma checagem `awk` pontual em `TAGS`).** Se alguma spec futura decidir usar essas colunas, vale nova investigação com o arquivo completo antes.
4. **Crescimento de +43,7% no número de linhas (98.560 → 141.666) não foi investigado** — pode ser expansão de período coberto pelo portal, mudança de critério de inclusão, ou outra causa. Não relacionado à mudança de schema, mas achado colateral relevante caso apareçam contratos fora do intervalo 2016–2026 hoje documentado em `stg_contratos.sql:4`.

## Fora do escopo

- Qualquer alteração em `ingest.sh`, `stg_contratos.sql`, `stg_contratos.yml`, `dbt/seeds/contratos.csv` ou `dbt/seeds/schema/contratos.yml` — fica para spec de Design subsequente.
- Investigação de conteúdo real de `TAGS` no arquivo completo.
- Investigação da causa do crescimento de +43,7% em número de linhas.
- Decisão sobre se `CDCREDOR` deveria substituir ou complementar `IDCONTRATADO` como chave de fornecedor — o levantamento só confirma que são domínios diferentes, não qual é preferível.

## Referências de código

- `dbt/scripts/ingest.sh:112-128` (guarda de validação de schema que rejeitou a ingestão)
- `dbt/seeds/contratos.csv` (seed versionado, schema antigo — 51 colunas)
- `dbt/seeds/schema/contratos.yml` (documentação parcial de 4 colunas)
- `dbt/models/staging/stg_contratos.sql` (todas as 51 colunas do schema antigo referenciadas por nome; nenhuma das 8 novas)

## Ver também

- [[009-automacao-da-ingestao]] (spec que define a guarda de validação de schema)
- [[005-grao-do-dado-contrato-vs-aditivo]] e [[006-backfill-historico]] (histórico de mudança de padrão em `nucontrato`/`nuprocesso`, mencionado como precedente checado no item 4)
- [[007-marts-e-metricas]] e [[012-eixo-frontend-biblioteca-grafico]] (chave `idcontratado` de `dim_fornecedor`, confirmada intacta no item 3)
