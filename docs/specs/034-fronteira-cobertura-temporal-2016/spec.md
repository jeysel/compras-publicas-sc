# 034 — Fronteira de cobertura temporal: 2016 como piso oficial, 1994–2015 como cauda documentada

## Tipo

Decisão de arquitetura (fronteira de escopo temporal) + ajuste de implementação. Deriva de um levantamento feito nesta sessão (2026-09-03) sobre a afirmação "a partir de 1994" que circulava no enunciado do painel.

## Status

**No ar em produção (2026-09-03).** Filtro aplicado em `stg_contratos`, piso replicado no
endpoint `/api/v1/anos-disponiveis`, teste dbt e teste de integração adicionados. Deploy da API
via CI→Argo (staging automático, produção promovida manualmente); marts reprocessadas no
servidor (`dbt run` + `dbt test`, sem `seed`/`build`). Ver seção Deploy / cutover para o output
literal.

## Resumo

O texto de apresentação do painel chegou a sugerir "contratos públicos firmados pelo Estado **a partir de 1994**". A metodologia publicada (`/metodologia`) e a home já diziam outra coisa — "a partir de **2016**" — e o dado real não sustenta nenhuma cobertura contínua antes de ~2013.

Levantamento (abaixo, com output literal):

- `/api/v1/anos-disponiveis` em produção retorna `{"ano_min":1994,"ano_max":2026}`. O piso 1994 é **1 contrato** (DEINFRA, obra rodoviária, assinado 11/1994).
- 1994–2009 inteiro são registros esparsos com **buracos de anos inteiros** (nada em 1995–2000 nem 2002–2003), nenhum ano com mais de ~150 contratos. Volume só passa de mil registros/ano a partir de 2013 (ver Investigação 2).
- O `dbt/seeds/contratos.csv` versionado cobre 2013–2025 (mín. `dtassinatura` = 2013, 35 registros). Tudo antes de 2013 e o ano de 2026 na produção **vieram de upsert manual** ([[030-ingestao-manual-upsert]]), não do seed — o repositório sozinho não reproduz o histórico pré-2013.
- O KPI `total_contratos` da home cai de **104.574** para **≈ 79.637** (24.937 contratos assinados antes de 2016, dos quais 22.079 são de 2013–2015).

**Decisão:** fixar **2016** como fronteira oficial de cobertura (mantendo o que a metodologia já declarava) e tratar 1994–2015 como **cauda documentada** — não é backfill (isso é [[006-backfill-historico]], ainda pendente), não é dado auditado, e não deve aparecer em nenhuma visualização. As linhas continuam existindo em `raw.contratos` e no seed; são cortadas num único ponto (`stg_contratos`), com o corte documentado aqui e na metodologia, não removidas em silêncio.

## Contexto

- A metodologia (`api/app/templates/metodologia.html`) e o rodapé/hero (`layout.html`, `home.html`) já usavam `<span class="ano-cobertura">2016</span>` — mas era só texto: nenhuma camada do pipeline aplicava esse piso. `stg_contratos` passava adiante o que estivesse em `raw.contratos`, e `raw.contratos` acumulou registros de 1994 em diante via upserts manuais (spec 030).
- `/api/v1/anos-disponiveis` (spec 026/028) calcula `MIN(ano_assinatura)` cru sobre `marts.fct_contratos` — é isso que faz os dropdowns de ano do frontend oferecerem "1994" como opção.
- Já existe precedente de "sinalizar/excluir na camada de dado, documentando" — `fl_valor_suspeito` ([[021-levantamento-outliers-valor-extremo]]) e `fl_aditivo_inconsistente` ([[008-qualidade-e-documentacao]]). A diferença aqui: cobertura temporal é uma fronteira de escopo uniforme (um ano de corte), não um julgamento linha a linha — por isso o corte único em `stg_contratos` em vez de flag propagada por mart.

## Investigação

### 1. Intervalo real em produção

```
$ curl -s https://contratos-sc.jeysel.dev/api/v1/anos-disponiveis
{"ano_min":1994,"ano_max":2026}

$ curl -s https://contratos-sc.jeysel.dev/api/v1/kpis-resumo
{"total_contratos":104574,"fornecedores_distintos":15563,"orgaos_distintos":194,"contratos_com_aditivo":48418}
```

### 2. Distribuição por ano e impacto no KPI (produção, 2026-09-03)

Contagem por `ano_assinatura` sobre `marts.mart_escalada_custo` (mesmo grão do KPI
`total_contratos` da home — via `/api/v1/escalada-custo`, 104.574 linhas):

```
1994:     1   <- Departamento Estadual de Infraestrutura, 1 contrato       ┐
1995–2000 (nenhum registro)                                                 │
2001:     1                                                                 │
2002–2003 (nenhum registro)                                                 │
2004:     1                                                                 │
2005:     5    2006:   76    2007:   21    2008:  153    2009:  155          │ cortados
2010:   668    2011:  945    2012:  832                                      │ (24.937)
2013:  3.832                                                                 │
2014: 10.899                                                                 │
2015:  7.348                                                                 ┘
──────────────────────────────────────────────────────────────────────────
2016:  7.744  <- fronteira oficial adotada                                  ┐
2017:  9.607   2018:  8.738   2019:  6.264   2020:  5.924   2021:  6.365     │ mantidos
2022:  7.720   2023:  6.573   2024:  7.005   2025:  9.260   2026:  4.437     │ (79.637)
──────────────────────────────────────────────────────────────────────────  ┘
total 104.574  |  ano < 2016: 24.937  |  ano >= 2016: 79.637
```

**Impacto no KPI da home:** `total_contratos` cai de **104.574** para **≈ 79.637** após o
próximo `dbt build` de produção (o número exato sobe a cada ingestão nova; ~79,6k é o piso).
2013–2015 responde por 22.079 das 24.937 linhas cortadas — não é volume irrelevante, mas é
a fatia sem auditoria cruzada contra os arquivos anuais oficiais do portal (spec 006, Bloco 2).
A alternativa de fixar a fronteira em 2013 (KPI ~101,7k, cortando só 1994–2012) foi considerada
e descartada: contraria o que a metodologia já publicava e mantém 2013–2015 como "oficial" sem
auditoria.

### 3. Seed versionado vs. produção

```
$ python -c "csv.DictReader(dbt/seeds/contratos.csv, ';') -> Counter(dtassinatura[:4])"
2013 35 | 2014 110 | 2015 1519 | 2016 7742 | 2017 9607 | 2018 8736 | 2019 6263
2020 5916 | 2021 6365 | 2022 7695 | 2023 6554 | 2024 6951 | 2025 8548
(total 76041, nenhuma linha com dtassinatura anterior a 2013)
```

O seed não tem nada pré-2013 nem 2026 — a cauda pré-2013 e o ano de 2026 presentes em produção entraram por upsert manual (spec 030). Consequência: o corte em `stg_contratos` protege qualquer reconstrução futura do pipeline a partir do seed **e** a base atual de produção (depois de um `dbt build`).

### 4. Três textos divergiam

| Local | Dizia | Depois desta spec |
|---|---|---|
| Enunciado/apresentação do painel | "a partir de 1994" | "a partir de 2016" |
| `home.html` hero + `link-card-desc`, `layout.html` rodapé | "a partir de 2016" (só texto, sem efeito no dado) | mantido, agora com efeito real no dado |
| `metodologia.html` | "a partir de 2016" | mantido + parágrafo explícito sobre a exclusão pré-2016 |
| `/api/v1/anos-disponiveis` | `MIN` cru → 1994 | piso 2016 |

## Requirements

### Funcionais

1. O sistema DEVE excluir de `stg_contratos` todo registro com `ano_assinatura < 2016`, num único ponto de corte, aplicando-se por herança a todos os models a jusante (intermediate, dims, facts, marts).

2. QUANDO `/api/v1/anos-disponiveis` calcular o menor ano disponível, O sistema DEVE retornar no mínimo 2016, mesmo que `marts.fct_contratos` ainda contenha linhas anteriores (estado possível enquanto o `dbt build` de produção não reprocessa — a ingestão é cron manual gated por ETag, spec 030).

3. O sistema NÃO DEVE apagar, sobrescrever ou alterar os registros pré-2016 em `raw.contratos` nem no seed — a exclusão é só de escopo analítico, a jusante de `stg_contratos`.

4. O sistema DEVE ter um teste dbt (`assert_`) que falhe se qualquer linha de `stg_contratos` tiver `ano_assinatura < 2016`.

5. O sistema DEVE ter cobertura de teste de integração validando que um contrato assinado antes de 2016 não aparece em nenhuma resposta de rota de `/api/v1/*` nem no intervalo de `/api/v1/anos-disponiveis`.

### Não-funcionais

1. A metodologia publicada (`/metodologia`) DEVE registrar explicitamente que existem registros anteriores a 2016 na base de origem, que eles não têm cobertura contínua nem auditoria independente, e que foram excluídos de todos os gráficos e relatórios.

2. O valor do ano de corte (2016) DEVE aparecer uma vez só na camada de dado (`stg_contratos`) e uma vez só na camada de API (`anos_disponiveis.py`), cada ocorrência com comentário citando esta spec — não espalhado por model.

3. Esta spec NÃO DEVE redefinir a decisão de chave/grão ([[003-storage-e-chave-unica]], [[005-grao-do-dado-contrato-vs-aditivo]]) nem o merge de fontes de [[006-backfill-historico]] — só fixa o piso temporal do que é considerado cobertura oficial.

## Design

| Decisão | Racional |
|---|---|
| Corte único em `stg_contratos` (`where ano_assinatura >= 2016`), não flag `fl_*` propagada | Cobertura temporal é fronteira de escopo uniforme, não julgamento linha a linha como `fl_valor_suspeito`. Os 14 models a jusante leem `stg_contratos` via `ref()` — um `where` ali dá 2016+ em todo lugar (escalada de custo, concentração, perfis, diversidade, KPIs, série temporal) com uma linha e sem tocar em nenhuma cláusula de mart |
| 2016, não 2013 (primeiro ano com volume) nem o `MIN` real | Mantém a fronteira que a metodologia **já** publicava — a alternativa exigiria reescrever a metodologia e ainda deixaria 2013–2015 (cobertura parcial vs. o portal oficial, ver spec 006 Bloco 2) dentro do escopo "oficial" sem auditoria |
| Piso também no endpoint `anos-disponiveis`, redundante com o corte no dbt | A ingestão de produção é cron manual gated por ETag (spec 030) — não reprocessa por mudança de código dbt. Até o próximo `dbt build` manual, `fct_contratos` em produção ainda terá linhas pré-2016; o piso no endpoint garante que os dropdowns do frontend fiquem corretos imediatamente. `GREATEST(MIN(ano_assinatura), 2016)` |
| 1994–2015 preservado em `raw.contratos` + seed, não deletado | "Cauda documentada": o dado continua a um `ref()` de distância na camada raw, esta spec registra a extensão exata com output literal, e o corte é um `where` comentado — não um sumiço silencioso. Se [[006-backfill-historico]] avançar, a fatia 2005–2015 é reconciliada lá, não recuperada daqui |
| `dim_datas` (spine 2015-01-01, spec 020) inalterada | Gerada independente dos contratos; `fct_contratos` faz `left join` nela. Com contratos pré-2016 já cortados em `stg_contratos`, as linhas de 2015 da spine simplesmente não casam com nada — inofensivo. Alinhar a spine a 2016 mexeria na decisão da spec 020 sem ganho prático |

### Componentes afetados

- `dbt/models/staging/stg_contratos.sql` — CTE final `cobertura_oficial` com `where ano_assinatura >= 2016` (comentário citando esta spec).
- `dbt/models/staging/schema/stg_contratos.yml` — `description` do model atualizada (piso 2016 é decisão desta spec, não característica da fonte); nota em `ano_assinatura`.
- `dbt/tests/assert_stg_contratos_cobertura_oficial.sql` — novo; retorna linhas com `ano_assinatura < 2016` (deve ser vazio).
- `api/app/routers/anos_disponiveis.py` — `GREATEST(MIN(ano_assinatura), 2016)`, comentário citando esta spec e a spec 030.
- `api/app/templates/metodologia.html` — parágrafo novo em "Fonte e período" / "Limitações conhecidas".
- `api/tests/fixtures/contratos.py` — 1 linha nova, assinada em 2014 (deve ser filtrada em `stg_contratos`).
- `api/tests/integration/test_cobertura_oficial.py` — novo; contrato de 2014 ausente das marts e do `anos-disponiveis`.
- `api/tests/integration/test_anos_disponiveis.py` — asserção inalterada no valor (fixture cobre 2023–2025), comentário atualizado.

## Casos de borda

- **`raw.contratos` de produção ainda com linhas pré-2016 até o próximo `dbt build`**: coberto pelo REQ-2 (piso no endpoint). A série temporal (`mart_contratos_temporal`) e os KPIs (`mart_escalada_custo`) só ficam 100% consistentes com a fronteira depois do reprocessamento — registrar no handoff de quem rodar o próximo `dbt build` manual que esse é o momento em que a cauda some das agregações.
- **Contrato genuíno de vigência longa assinado antes de 2016 e ainda ativo** (ex.: o de 1994 da DEINFRA pode ser real): é excluído do mesmo jeito. Aceito — a fronteira é sobre cobertura/auditoria do conjunto, não sobre a validade de um contrato específico. Se um caso desses for relevante, entra pela reconciliação da spec 006.
- **O registro de 1994 pode ser erro de digitação de data** (`1994` por `2014`/`2019`): não investigado aqui. Não há flag de sanidade de data no pipeline (spec 021 cobre só valor). Fica como pendência registrada, não resolvida — uma spec de levantamento de sanidade de data, nos moldes da 021, seria o lugar.
- **Filtro de ano no frontend (spec 028/029) pedindo um ano < 2016 explicitamente na querystring**: as marts não terão linhas desse ano após o corte, então o retorno é lista vazia / formato esperado — mesmo comportamento de qualquer ano sem dado. Sem tratamento adicional.

## Fora do escopo

- Backfill do histórico oficial 2005–2015 a partir dos arquivos anuais do portal — é [[006-backfill-historico]], ainda pendente de aprovação.
- Investigar se o contrato de 1994 (e os de 2001/2004) são erro de data na fonte.
- Alinhar a spine de `dim_datas` (spec 020) a 2016.
- Qualquer mudança em `fl_valor_suspeito` / `fl_aditivo_inconsistente`.
- Rever o texto da home/hero — já dizia "2016", permanece.

## Validação (2026-09-03)

Rodada localmente contra Postgres real (compose), dois cenários — output literal:

### Cenário A — seed real (`dbt/seeds/contratos.csv`, 76.041 linhas)

```
dbt seed + dbt build  ->  PASS=134 WARN=0 ERROR=0 SKIP=0

| métrica                                | valor |
| raw.contratos total                    | 76041 |
| raw.contratos dtassinatura ano < 2016  | 1664  |   (2013:35 + 2014:110 + 2015:1519)
| stg_contratos total                    | 74377 |   (76041 - 1664, exato)
| stg_contratos min(ano) / max(ano)      | 2016 / 2025 |
| stg_contratos ano < 2016               | 0     |
| fct_contratos ano < 2016               | 0     |
| mart_escalada_custo ano < 2016         | 0     |
```

Os 1.664 registros pré-2016 continuam em `raw.contratos` — cauda preservada, não deletada.

### Cenário B — seed de fixture (spec 033, com a linha nova `CT-TESTE-PRE2016`/2014)

```
dbt build             ->  PASS=134 WARN=0 ERROR=0
pytest (Linux)        ->  32 passed  (26 integração + 6 rápidos)

raw.contratos total = 9  | raw tem CT-TESTE-PRE2016 = 1
stg_contratos total = 8  | stg tem CT-TESTE-PRE2016 = 0
fct_contratos / mart_escalada_custo tem CT-TESTE-PRE2016 = 0
```

### Teste negativo (forçar a falha real antes de aceitar)

Com o `where` da CTE `cobertura_oficial` trocado por `where true`:

```
dbt build  ->  FAIL 1 assert_stg_contratos_cobertura_oficial  (1 linha: CT-TESTE-PRE2016)
```

Confirma que o `assert_` não é tautológico — pega o vazamento. Filtro restaurado, `dbt build` volta a PASS=134.

### Piso do endpoint

```sql
-- simulando fct_contratos ainda com uma linha de 2005 (cenário produção antes do dbt build):
GREATEST(MIN(ano_assinatura), 2016)  ->  2016
```

## Deploy / cutover

A mudança tem duas camadas com caminhos de deploy diferentes:

1. **API (`anos_disponiveis.py` piso 2016 + texto da metodologia)** — segue o fluxo normal:
   push em `main` → CI builda a imagem, roda a suíte, bumpa `overlays/staging` e o Argo CD
   sincroniza staging sozinho. Produção é promoção manual (spec 015): editar
   `overlays/production/kustomization.yaml` para um SHA já validado em staging, commit, push.
   Efeito imediato: `/api/v1/anos-disponiveis` para de retornar 1994; dropdowns de ano começam
   em 2016.

2. **dbt (`stg_contratos` corte)** — a imagem do pipeline é rebuildada pelo CI (`build-pipeline`),
   mas a execução em produção é cron no host gated por ETag (spec 030) — **uma mudança só de
   código dbt não dispara reprocessamento**. Até alguém rodar o `dbt build` manualmente no
   servidor, `marts.*` em produção continua com as 24.937 linhas pré-2016. O piso do endpoint
   (item 1) cobre o `anos-disponiveis` nesse intervalo, mas os KPIs e a série temporal só
   refletem os 79.637 depois do reprocessamento. Passo manual, território do repo `infra`.

Ordem recomendada: (1) API em staging → validar → produção; (2) rodar o pipeline dbt manual no
servidor; (3) conferir `/api/v1/kpis-resumo` (`total_contratos` ~79,6k) e a metodologia no ar.

### Cutover executado — 2026-09-03

1. Commits `a39f3db` (impl) + `8966c77` (promoção `overlays/production` → `a39f3db`). CI verde
   (suíte 32 passed). Staging sincronizou sozinho; produção via
   `kubectl -n argocd patch application compras-publicas-production ... {"operation":{"sync":...}}`
   (sem `automated` — spec 015), sync `Succeeded`, 2 pods `a39f3db` ready.

2. Reprocessamento dbt no host (mesmo padrão do passo 7 de `infra/scripts/importar-contratos.sh`
   — `run` + `test`, **nunca** `seed`/`build`, senão o `dbt seed` sobrescreve os upserts da
   spec 030 em `raw.contratos`):

   ```
   docker run --rm --entrypoint dbt --network jeysel-network \
     --env-file /home/ubuntu/secrets/compras-publicas.env -w /usr/app/dbt \
     ghcr.io/jeysel/compras-publicas-sc/compras-publicas-pipeline:latest  run    # PASS=24
   ...                                                                    test   # PASS=109
   ```
   (`assert_stg_contratos_cobertura_oficial` PASS. Log:
   `/home/ubuntu/logs/compras-publicas/spec034-dbt-20260903_174614.log`.)

3. Verificação em produção (`compras_publicas` no container `postgres`):

   | | antes | depois |
   |---|---|---|
   | `raw.contratos` | 104.574 (24.937 pré-2016) | **104.574 (inalterado)** |
   | `stg_contratos` / `min(ano_assinatura)` | 104.574 / 1994 | **79.637 / 2016** |
   | `mart_escalada_custo` / `fct_contratos` | 104.574 | **79.637** |
   | `GET /api/v1/kpis-resumo` `total_contratos` | 104.574 | **79.637** |
   | `GET /api/v1/anos-disponiveis` `ano_min` | 1994 | **2016** |

   Smoke test de 9 rotas (`/`, `/metodologia`, gráficos, `/api/v1/*`): todas 200.
   `raw.contratos` intacto confirma a cauda documentada — dado preservado, só fora do escopo analítico.

## Referências de código

- `dbt/models/staging/stg_contratos.sql` — CTE `cobertura_oficial`.
- `dbt/tests/assert_stg_contratos_cobertura_oficial.sql`.
- `api/app/routers/anos_disponiveis.py` — `GREATEST(..., 2016)`.
- `api/app/templates/metodologia.html` — seção "Fonte e período".
- `api/tests/integration/test_cobertura_oficial.py`.

## Ver também

- [[006-backfill-historico]] — o backfill oficial pré-2016 que esta spec explicitamente **não** faz.
- [[030-ingestao-manual-upsert]] — como a cauda pré-2013 e o ano de 2026 entraram na produção.
- [[021-levantamento-outliers-valor-extremo]] — precedente de exclusão documentada na camada de dado.
- [[026-kpis-classificacoes-rankings]] / [[028-filtro-ano-graficos-relatorios]] / [[029-filtro-ano-marts-sem-coluna-ano]] — origem do endpoint `anos-disponiveis` e dos filtros de ano.
- [[020-dim_datas-como-model-dbt-nao-fonte-externa]] — a spine de datas que fica como está.
