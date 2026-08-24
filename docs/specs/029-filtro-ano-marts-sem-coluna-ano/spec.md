# Spec 029 — Filtro de ano nos 4 endpoints sem coluna de ano (Grupo C da spec 028)

## Tipo

Nova funcionalidade (extensão do filtro de ano da spec 028 aos 4 endpoints deixados de fora dela) — esta spec cobre **investigação e decisão de design**, não implementação. Mudança de grão em mart que já alimenta produção é risco maior que os itens já implementados na spec 028 (ver o fix de `fl_valor_suspeito`, spec 026, que mudou ~40% dos valores públicos ao corrigir uma mart existente) — decisão consciente de separar "decidir o design" de "escrever o SQL" em duas etapas.

## Status

Investigação e Design concluídos em 2026-08-24. Implementado e validado em 2026-08-24 (mesmo dia), nesta mesma spec — ver seção Validação abaixo. **Aguardando aprovação explícita do usuário antes do commit**, dado o risco da mudança de grão em `mart_concentracao_fornecedor` (constitution, regra 4).

### Decisão de design tomada durante a implementação, além do que REQ-4/REQ-13 diziam literalmente

REQ-13 só listava `/orgaos` e `/perfil-fornecedores` na garantia de "sem parâmetro de ano = comportamento idêntico ao anterior". Ao implementar REQ-3/4, ficou claro que aplicar a mudança de grão de forma ingênua (só adicionar `WHERE ano_assinatura BETWEEN` sobre a mart já no grão novo) quebraria essa mesma garantia para `ConcentracaoFornecedor` também: sem filtro de ano, a mart passaria a ter uma linha por (órgão, fornecedor, ano) em vez de uma por (órgão, fornecedor), e o `DISTINCT ON`/rank antigo do router pegaria valores de um único ano arbitrário, não mais o agregado histórico — uma regressão visível na página hoje em produção.

Decisão tomada (não estava escrita na spec original): o router de `/concentracao-fornecedor` sempre reagrega (SUM) e recalcula rank/perc via SQL no próprio endpoint, sobre o intervalo `ano_inicio`/`ano_fim` informado — ou sobre a mart inteira, sem `WHERE`, quando nenhum dos dois é informado. Isso restaura a garantia "sem filtro = idêntico à produção" também para este endpoint, e generaliza corretamente para intervalo (não só ano único). Ver Validação para a confirmação numérica de que isso funciona.

### Validação

**Volume/multiplicador reconfirmado antes de tocar em qualquer model dbt (2026-08-24, banco de dev local):**

```sql
SELECT COUNT(*) FROM (SELECT DISTINCT id_contratado, cod_unidade_gestora, ano_assinatura FROM marts.fct_contratos) t;
-- 46378
SELECT COUNT(*) FROM (SELECT DISTINCT id_contratado, cod_unidade_gestora FROM marts.fct_contratos) t;
-- 27849
```
Idêntico ao medido na Investigação (46.378 / 27.849 ≈ 1,67×) — nada mudou desde a investigação, seguro prosseguir.

**`dbt build` completo (não só os models tocados) — 0 erro, todos os tests passando:**

```
Finished running 1 seed, 12 table models, 108 data tests, 12 view models in 177.31s
Done. PASS=133 WARN=0 ERROR=0 SKIP=0 TOTAL=133
```

Inclui os 2 tests novos de unicidade (`dbt_utils.unique_combination_of_columns`) substituindo o `unique(id_contratado)` que a mudança de grão de `int_concentracao_fornecedor_estado` quebraria, e os tests pré-existentes de todas as outras marts (nenhum efeito colateral).

**REQ-13 (regressão sem filtro) — volume/valor idêntico à produção nos 4 endpoints, dado real, via HTTP:**

```
diversidade-vencedores  sem filtro: 43953 linhas   (bate com o valor conhecido da Investigação)
orgaos                  sem filtro: 187 linhas     (bate com o valor conhecido da Investigação)
perfil-fornecedores     sem filtro: Grande=531/Médio=1440/Pequeno=3003/Micro=6429  (idêntico à Investigação)
concentracao-fornecedor sem filtro, cod_unidade_gestora=920021, top 5:
  ORCALI 3882579.54 rank=1 35.63% | CONSTRUTORA AJM 2826400.00 rank=2 25.94% |
  CIASC 744358.62 rank=3 6.83% | PAPEL DIGITAL 611107.96 rank=4 5.61% | OCEANICA 467484.98 rank=5 4.29%
  — idêntico byte-a-byte aos valores lidos do banco ANTES de rodar `dbt build` (capturados como controle)
concentracao-fornecedor sem filtro, sem órgão, top 5 estado:
  CIASC 2139489605.99 rank=1 4.53% | PLANATERRA 1370194701.86 rank=2 2.90% | SEPAT 1080638248.01 rank=3 2.29% |
  ORBENK 1076776753.46 rank=4 2.28% | QUALIDADE CONSTRUÇÕES 852868673.12 rank=5 1.81%
  — idêntico byte-a-byte ao controle pré-mudança
```

**REQ-12 (comparação de ranks antes/depois, ano real) — `cod_unidade_gestora=920021`, ano=2016 (escolhido por ter dado real; 2020 não tem contrato nesse órgão, confirmado via `fct_contratos`):**

```
Antes (agregado histórico, todos os anos):
  1º ORCALI 3882579.54 (35.63%) | 2º CONSTRUTORA AJM 2826400.00 (25.94%) | 3º CIASC 744358.62 (6.83%)

Depois (ano_inicio=2016&ano_fim=2016, via router):
  1º ORCALI 2996379.54 (31.68%) | 2º CONSTRUTORA AJM 2826400.00 (29.88%) | 3º CIASC 744358.62 (7.87%)
  vl_total_orgao: 10895851.80 (histórico) → 9459483.83 (só 2016) — menor, como esperado (2016 é subconjunto)

Consistência interna: a resposta do router para ano_inicio=2016&ano_fim=2016 bate, campo a campo,
com a leitura direta de marts.mart_concentracao_fornecedor WHERE ano_assinatura=2016 (os valores
já vêm pré-computados pelo dbt nesse grão) — confirma que a reagregação do router para uma janela
de um único ano é matematicamente equivalente ao cálculo do model dbt, não uma aproximação.

Estado (sem órgão), ano=2020, top 5 — conjunto de fornecedores completamente diferente do histórico
(nenhum dos 5 do agregado histórico aparece), plausível (ranking de UM ano isolado, não o acumulado
de 13 anos): Instituto de Previdência (13,22%), FUPESC (12,39%), DETRAN (7,96%), Defesa Civil (5,48%),
Secretaria de Agricultura (2,85%).
```

**Caso de borda: órgão sem contrato no ano filtrado** — `cod_unidade_gestora=920021&ano_inicio=2020&ano_fim=2020` retorna `[]` (confirmado: esse órgão só tem contrato em 2013/2015/2016 via `fct_contratos`), sem erro 500; página renderiza sem crash (0 erros de console, Playwright).

**Caso de borda: `PerfilOrgaos` com filtro de ano restritivo muda a lista exibida (REQ-5, classificação continua histórica)** — com `ano_inicio=2013&ano_fim=2013` (só 20 órgãos ativos nesse ano, de 187), o Top 10 por quantidade muda de composição (nenhum dos 10 órgãos do agregado histórico aparece — todos rankeados 5º/8º/10º/16º/18º/21º/22º/31º/43º/45º no histórico), confirmando que o filtro de atividade funciona mesmo a classificação sendo histórica; com `ano_inicio=2020` (73 de 187 órgãos ativos), o Top 10 não mudou — esperado, não bug, já que os maiores órgãos por volume histórico tendem a seguir ativos em quase todo ano recente (confirmado comparando as duas janelas, não presumido).

**`tsc --noEmit`**: sem erros. **`npm run build`**: sucesso.

**Performance/memória da reagregação SQL em `ConcentracaoFornecedor` (mesmo padrão de validação dos 3 incidentes de OOM de hoje) — dado real, não presumido:**

`EXPLAIN (ANALYZE, BUFFERS)` do cenário mais pesado (sem `cod_unidade_gestora`, reagrega as 46.305 linhas inteiras da mart):

```
Execution Time: 108.415 ms
HashAggregate: Batches: 5, Memory Usage: 8369kB, Disk Usage: 7000kB (work_mem=4MB, spill esperado)
Sort (dedup por fornecedor): Sort Method: external merge, Disk: 4600kB
```

Comparação com a query ANTIGA (`DISTINCT ON` + `rank_estado` pré-computado), reconstruída rodando o SQL de `git show HEAD` contra uma tabela-scratch no grão antigo (27.822 linhas, recriada a partir de `staging.stg_contratos` — bate com o valor conhecido pré-migração; tabela removida após o teste, não é model dbt):

```
Cenário "sem órgão" (o mais pesado):    antigo 18.574 ms  →  novo 108.415 ms  (~6x mais lento, ainda < 110ms)
Cenário "com cod_unidade_gestora":      antigo  1.896 ms  →  novo   3.563 ms  (~2x mais lento, ainda < 4ms)
```

Degradação real, mas pequena em termos absolutos — nenhum spill de disco passa de ~8MB (`work_mem` de 4MB já espera spill nesse volume, comportamento normal do Postgres, não sintoma de problema), sem indício de crescimento sem limite.

**Load test — 50 requisições sequenciais no cenário mais pesado (`GET /concentracao-fornecedor` sem parâmetro nenhum), memória monitorada via `docker stats` a cada 1s durante toda a rodada:**

```
compras_api:      94.11 MiB, CONSTANTE nas 30 amostras (0 crescimento) — igual ao valor de antes do teste
compras_postgres:  190–221 MiB (2.5–2.9% dos 7.6 GiB do host), sem tendência de crescimento — oscila e
                   CAI ao longo da rodada, não sobe; CPU do postgres pica ~70% nos primeiros 2s (rajada de
                   50 requisições) e volta a 0% no resto da rodada
50 requisições completas em 6.7s (~134ms/req, compatível com os 108ms de execução SQL medidos acima)
```

Diferente dos 3 incidentes de OOM de hoje: aqueles vinham do `response_model` do FastAPI duplicando uma lista de até 200.000 linhas na memória do processo Python antes de serializar (ver comentário em `diversidade_vencedores.py`, achado 2026-08-21). Aqui o payload retornado é sempre pequeno — `top_n` limita a no máximo 100 linhas, mesmo reagregando 46 mil no Postgres — então não há o mesmo mecanismo de duplicação em memória no lado da API. Risco real era só do lado do Postgres (sort/hash-agg maiores), e ficou medido acima: pequeno, com spill de poucos MB, sem crescimento sem limite.

**Playwright (`chromium.launch()`, mesma ressalva de spec 026/028 — sem suíte configurada no repo, verificação ad-hoc):**

- `/graficos/diversidade-vencedores`: dropdowns ano-inicio/ano-fim populados (2016–2026 + "Desde o início"); selecionar ano=2020 gera `?ano_inicio=2020&ano_fim=2020`; combinar depois com órgão gera `?cod_unidade_gestora=920021&ano_inicio=2020&ano_fim=2020` — ano preservado ao trocar órgão. 0 erros de console.
- `/graficos/concentracao-fornecedor`: mesmo padrão de combinação órgão+ano preservando os dois parâmetros. Caso de borda ano_inicio=2023 > ano_fim=2018 testado explicitamente — sem crash, página responde normalmente. 0 erros de console.
- `/relatorios/perfil-fornecedores`: filtro de ano dispara `?ano_inicio=2020&ano_fim=2020`, gráfico recalcula (confirmado via volume HTTP acima). 0 erros de console.
- `/relatorios/perfil-orgaos`: filtro de ano dispara `?ano_inicio=2020&ano_fim=2020` no mesmo `/orgaos` usado pelo dropdown de `filtros.ts` (que continua sem parâmetro, REQ-8) — tabela de ranking atualiza corretamente com o filtro restritivo (2013, ver acima). 0 erros de console.

## Resumo

A spec 028 implementou filtro de ano em 5 endpoints e registrou, como Fora do escopo, 4 endpoints cujas marts agregam sobre todo o histórico sem coluna de ano: `DiversidadeVencedores`, `ConcentracaoFornecedor`, `PerfilFornecedores`, `Orgaos`. Esta spec investiga o que "ano" significa para cada uma dessas 4 entidades e propõe design, com 3 decisões tomadas:

1. **DiversidadeVencedores** (grão: processo) — filtrar pelo ano de `dt_primeiro_contrato`, sem mudar o grão nem o significado da métrica de diversidade.
2. **ConcentracaoFornecedor** (grão: fornecedor×órgão, ranks acumulados) — mudança de grão real, recalculando ranks/percentuais por ano. O risco de volume levantado antes da investigação (13× linhas, no pior caso) não se confirmou: o multiplicador real medido é ~1,67×.
3. **PerfilFornecedores/Orgaos** (dimensões `dim_fornecedores`/`dim_orgaos`) — classificação de porte/perfil continua histórica/acumulada; o filtro de ano é só um filtro de atividade (fornecedor/órgão teve contrato naquele ano), sem redesenhar o grão das dimensões.

Achado adicional relevante para o design: o endpoint `Orgaos` tem dois consumidores distintos no frontend com necessidades diferentes — um lookup puro (dropdown de filtro de órgão) que não precisa de nenhuma mudança, e um gráfico de distribuição real (`perfil-orgaos.ts`) que precisa do filtro de atividade da decisão 3.

## Contexto

Continuação direta de [[028-filtro-ano-graficos-relatorios]], seção "Fora do escopo": *"Filtrar por ano exigiria redesenhar o grão ... decisão de modelagem que merece spec própria, não um `WHERE` incremental."* Esta é essa spec própria.

## Investigação

**1. Schema real das 4 marts/dimensões (via `\d` no Postgres de produção, 2026-08-24):**

```
marts.mart_diversidade_vencedores: grão (cod_unidade_gestora, nu_processo)
  tem dt_primeiro_contrato, dt_ultimo_contrato (date) — NÃO tem ano_assinatura

marts.mart_concentracao_fornecedor: grão (cod_unidade_gestora, id_contratado) via int_concentracao_fornecedor_por_orgao
  e (id_contratado) via int_concentracao_fornecedor_estado
  NÃO tem nenhuma coluna de data/ano

marts.dim_fornecedores: grão (id_contratado)
  tem dt_primeiro_contrato, dt_ultimo_contrato — NÃO tem ano_assinatura
  porte_fornecedor calculado sobre vl_total_atual acumulado (case/when por faixa de valor)

marts.dim_orgaos: grão (cod_unidade_gestora)
  tem dt_primeiro_contrato, dt_ultimo_contrato — NÃO tem ano_assinatura
  ds_perfil_contratacao calculado sobre qt_contratos acumulado (case/when por faixa de volume)
```

`marts.fct_contratos` (grão: contrato) tem `ano_assinatura` (numeric, `extract(year from dt_assinatura)`) — é a fonte de ano usada pelos 5 endpoints já resolvidos na spec 028, mas nenhuma das 4 marts acima herda essa coluna porque todas agregam por processo/fornecedor/órgão sobre o histórico inteiro.

**2. Volume — checado antes de propor qualquer redesenho:**

```sql
SELECT COUNT(DISTINCT ano_assinatura), MIN(ano_assinatura), MAX(ano_assinatura) FROM marts.fct_contratos;
-- 13 anos distintos, 2013–2025
```

Row counts atuais: `fct_contratos`=76.041, `mart_concentracao_fornecedor`=27.822, `dim_fornecedores`=11.403, `mart_diversidade_vencedores`=43.953, `dim_orgaos`=187.

**Multiplicador real de linhas se `mart_concentracao_fornecedor` ganhar `ano_assinatura` no grão** (a preocupação original era até 13× no pior caso teórico):

```sql
SELECT COUNT(*) FROM (SELECT DISTINCT id_contratado, cod_unidade_gestora, ano_assinatura FROM marts.fct_contratos) t;
-- 46.378
SELECT COUNT(*) FROM (SELECT DISTINCT id_contratado, cod_unidade_gestora FROM marts.fct_contratos) t;
-- 27.849
```

Multiplicador real ≈ **1,67×** (46.378 / 27.849) — muito abaixo do pior caso teórico e do volume que causou os incidentes de OOM anteriores nesta mesma sessão de trabalho. A maioria dos pares fornecedor/órgão está concentrada em poucos anos consecutivos, não espalhada pelos 13 anos do dataset.

**3. DiversidadeVencedores — quantos processos abrangem mais de um ano de assinatura:**

```sql
SELECT COUNT(*) AS total_processos, COUNT(*) FILTER (WHERE anos_distintos > 1) AS multi_ano
FROM (SELECT cdunidadegestora, nuprocesso, COUNT(DISTINCT EXTRACT(YEAR FROM dtassinatura::date)) AS anos_distintos
      FROM raw.contratos WHERE dtassinatura IS NOT NULL AND dtassinatura != '' GROUP BY 1, 2) t;
-- total_processos = 44.134, multi_ano = 1.363 (3,1%)
```

**4. PerfilFornecedores — distribuição atual por porte (referência, não muda com esta spec):**

```
porte_fornecedor | count
Micro             | 6429
Pequeno           | 3003
Médio             | 1440
Grande            | 531
```

**5. Frontend — quem consome cada endpoint (`grep`/leitura direta, não presumido):**

- `web/src/charts/filtros.ts` → `popularOrgaos()`: chama `GET /api/v1/orgaos` só para popular o `<select>` de filtro de órgão (usa `cod_unidade_gestora`/`nm_unidade_gestora`, ignora todo o resto do payload). **Não expõe nenhuma estatística agregada** — não tem necessidade funcional de filtro de ano.
- `web/src/charts/perfil-orgaos.ts`: chama o **mesmo** `GET /api/v1/orgaos`, mas para montar um gráfico de distribuição real, agrupando por `ds_perfil_contratacao` (Alto/Médio/Baixo volume/Esporádico). Este sim é candidato real a filtro de ano.
- `web/src/charts/perfil-fornecedores.ts`: chama `GET /api/v1/perfil-fornecedores`, gráfico de barras por `porte_fornecedor` com `qt_fornecedores`/`valor_total`. Candidato real a filtro de ano.
- Nenhum dos 4 routers (`diversidade_vencedores.py`, `concentracao_fornecedor.py`, `perfil_fornecedores.py`, `orgaos.py`) tem parâmetro de ano — confirmado lendo o código de cada um.

## Requirements

### Funcionais

- REQ-1: `mart_diversidade_vencedores` DEVE expor uma coluna de ano derivada de `dt_primeiro_contrato` (ex.: `ano_abertura = extract(year from dt_primeiro_contrato)`), sem alterar o grão `(cod_unidade_gestora, nu_processo)` nem o cálculo de `qt_fornecedores_distintos`/`ds_diversidade`/`rank_por_diversidade`.
- REQ-2: `GET /api/v1/diversidade-vencedores` DEVE aceitar `ano_inicio`/`ano_fim` opcionais, aplicando `WHERE` sobre a coluna do REQ-1 antes do `ORDER BY`/`LIMIT` já existentes.
- REQ-3: `int_concentracao_fornecedor_por_orgao` e `int_concentracao_fornecedor_estado` DEVEM ganhar `ano_assinatura` no `GROUP BY` — grão passa a `(cod_unidade_gestora, id_contratado, ano_assinatura)` e `(id_contratado, ano_assinatura)` respectivamente — recalculando `rank_no_orgao`/`perc_sobre_total_orgao`/`rank_estado`/`perc_sobre_total_estado` particionados por ano.
- REQ-4: `GET /api/v1/concentracao-fornecedor` DEVE aceitar `ano_inicio`/`ano_fim` opcionais, filtrando sobre a granularidade por ano do REQ-3.
- REQ-5: `dim_fornecedores.sql` e `dim_orgaos.sql` NÃO DEVEM ter o grão alterado nem `porte_fornecedor`/`ds_perfil_contratacao` recalculados por ano — a classificação permanece histórica/acumulada (decisão tomada nesta spec).
- REQ-6: `GET /api/v1/perfil-fornecedores` DEVE aceitar `ano_inicio`/`ano_fim` opcionais, que filtram `dim_fornecedores` a fornecedores com ao menos um contrato em `fct_contratos` dentro do intervalo (join/`EXISTS` por `id_contratado` + `ano_assinatura`) antes do `GROUP BY porte_fornecedor` já existente. O `porte_fornecedor` exibido continua sendo a classificação histórica de cada fornecedor.
- REQ-7: `GET /api/v1/orgaos` DEVE aceitar `ano_inicio`/`ano_fim` opcionais, com o mesmo padrão de filtro de atividade do REQ-6 (join contra `fct_contratos` por `cod_unidade_gestora` + `ano_assinatura`), sem alterar `dim_orgaos` nem recalcular `ds_perfil_contratacao`.
- REQ-8: QUANDO `GET /api/v1/orgaos` for chamado sem `ano_inicio`/`ano_fim` (uso atual do dropdown de filtro em `filtros.ts`), o retorno DEVE ser idêntico ao comportamento atual — o parâmetro novo é aditivo e não pode alterar esse consumidor existente.
- REQ-9: A página que usa `/orgaos` para o gráfico de distribuição por perfil (`perfil-orgaos.ts`) DEVE ganhar o par de dropdowns "Ano inicial"/"Ano final" (`initFiltroAnoIntervalo`, já existente desde a spec 028), reconectado ao REQ-7.
- REQ-10: A página de `perfil-fornecedores.ts` DEVE ganhar o mesmo par de dropdowns, reconectado ao REQ-6.
- REQ-11: As páginas/relatórios de `DiversidadeVencedores` e `ConcentracaoFornecedor` DEVEM ganhar os mesmos dropdowns, reconectados aos REQ-2 e REQ-4 respectivamente.

### Não-funcionais

- REQ-12: A mudança de grão do REQ-3 DEVE ser validada comparando `rank_no_orgao`/`rank_estado`/`perc_sobre_total_orgao`/`perc_sobre_total_estado` antes/depois com um ano real do dataset — não apenas ausência de erro HTTP — no mesmo padrão de rigor exigido pela constitution (regra 4) e já aplicado ao fix de `fl_valor_suspeito` (spec 026): forçar a comparação de valor real, não presumir que o SQL está certo por parecer certo.
- REQ-13: Nenhuma mudança desta spec DEVE alterar o retorno de `/api/v1/orgaos` ou `/api/v1/perfil-fornecedores` quando chamados sem parâmetro de ano — confirmado explicitamente na validação da implementação (REQ-8).
- REQ-14: A atribuição de ano em `DiversidadeVencedores` pelo ano de `dt_primeiro_contrato` (REQ-1) DEVE ser validada contra os processos multi-ano documentados na Investigação (1.363 de 44.134, 3,1%) — esses processos ficam atribuídos ao ano de abertura mesmo tendo contrato(s) em ano(s) seguinte(s); comportamento esperado e documentado, não um bug a corrigir depois.

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| DiversidadeVencedores — qual ano usar | Ano de `dt_primeiro_contrato` (ano de abertura do processo) | Só 3,1% dos processos são multi-ano; não muda o grão nem o significado da métrica de diversidade, que continua medida sobre a vida inteira do processo |
| ConcentracaoFornecedor — grão | Recalcular por `ano_assinatura` (mudança de grão real nas 2 intermediate models) | Responde à pergunta certa de transparência ("quem foi o maior fornecedor daquele ano"); volume real medido (~1,67×, 46.378 vs 27.849 pares) descarta o risco de OOM levantado antes da investigação |
| PerfilFornecedores/Orgaos — porte/perfil | Classificação mantida histórica/acumulada; filtro de ano é só de atividade (fornecedor/órgão teve contrato no intervalo) | Evita redesenhar o grão de `dim_fornecedores`/`dim_orgaos`, que são usadas como lookup por `mart_concentracao_fornecedor` (join por `id_contratado`/`cod_unidade_gestora` esperando 1 linha por chave) — mudar esse grão quebraria esses joins |
| Orgaos — dropdown de filtro (`filtros.ts`) | Sem mudança nenhuma nesse caller | Esse consumidor não expõe estatística — é só lookup de nome para popular o `<select>`; o parâmetro novo de ano fica opcional e não utilizado por ele (REQ-8) |
| Filtro de atividade (REQ-6/REQ-7) | `WHERE EXISTS`/join contra `fct_contratos` por chave + `ano_assinatura`, aplicado no router antes do `GROUP BY` já existente | Mesmo padrão dos 3 endpoints "Grupo B" da spec 028 (`WHERE` no router, sem tocar model dbt) — aqui o `WHERE` é sobre uma tabela relacionada (`fct_contratos`), não sobre a própria mart, porque a mart não carrega `ano_assinatura` |

### Componentes afetados

- `dbt/models/marts/mart_diversidade_vencedores.sql` — coluna `ano_abertura` nova (REQ-1).
- `dbt/models/intermediate/int_concentracao_fornecedor_por_orgao.sql`, `int_concentracao_fornecedor_estado.sql` — `ano_assinatura` no `GROUP BY` e nas janelas de rank (REQ-3).
- `dbt/models/marts/mart_concentracao_fornecedor.sql` — passa a ter grão `(órgão, fornecedor, ano)`/`(fornecedor, ano)`.
- `api/app/routers/diversidade_vencedores.py`, `concentracao_fornecedor.py`, `perfil_fornecedores.py`, `orgaos.py` — `ano_inicio`/`ano_fim` (`Query`, opcionais) e `WHERE`/`EXISTS` correspondentes.
- `web/src/charts/diversidade-vencedores.ts`, `concentracao-fornecedor.ts` (ou equivalentes), `perfil-fornecedores.ts`, `perfil-orgaos.ts` — dropdowns de ano via `initFiltroAnoIntervalo` (já existente, `filtros.ts`, spec 028).
- `web/src/charts/filtros.ts` — `popularOrgaos()` permanece sem mudança (REQ-8); nenhuma função nova necessária além das já criadas na spec 028.
- `web/src/api-types.ts` — regenerado (`npm run generate-types`) para refletir os parâmetros novos.

## Casos de borda

- Fornecedor ou órgão sem nenhum contrato no intervalo de ano selecionado desaparece da lista de `PerfilFornecedores`/`Orgaos` (filtro de atividade) — mesmo comportamento de "sem dado no intervalo" já aceito e documentado na spec 028.
- Ano inicial maior que ano final: mesmo tratamento já decidido na spec 028 — `WHERE` nunca satisfeito, retorna lista vazia, sem erro 500.
- Processo multi-ano em `DiversidadeVencedores` (REQ-14): atribuído ao ano de `dt_primeiro_contrato`; ao filtrar por esse ano, os contratos de anos seguintes do mesmo processo continuam contando para `qt_fornecedores_distintos`/`vl_total_*` (a métrica não é recalculada por ano, só o processo é "encaixado" num ano para fins de filtro).
- Fornecedor com contrato em múltiplos anos dentro do intervalo `ano_inicio`–`ano_fim` de `PerfilFornecedores`: aparece uma única vez (o `EXISTS`/`DISTINCT` não duplica), com o `porte_fornecedor` histórico de sempre.

## Fora do escopo

- **Recalcular `porte_fornecedor`/`ds_perfil_contratacao` por ano** (fornecedor/órgão mudando de classificação de um ano para outro). Decisão consciente de manter a classificação histórica (Design) — revisitável em spec futura se o produto pedir explicitamente "qual era o porte do fornecedor naquele ano", o que exigiria redesenhar o grão de `dim_fornecedores`/`dim_orgaos` e revisar todos os lugares que hoje fazem lookup por chave única nessas dimensões.
- **Endpoint que liste os anos com dado real** (em vez de faixa fixa) — mesma decisão já tomada na spec 028, não reaberta aqui.
- **Implementação do dbt/endpoint/frontend em si** — esta spec cobre só investigação e design; a implementação é uma etapa seguinte, com sua própria seção de Validação (dado real antes/depois, no padrão da spec 028, especialmente para o REQ-12).

## Referências de código

- `dbt/models/marts/mart_diversidade_vencedores.sql`, `dim_orgaos.sql`, `dim_fornecedores.sql`, `mart_concentracao_fornecedor.sql` — marts investigadas nesta spec.
- `dbt/models/intermediate/int_processos.sql`, `int_concentracao_fornecedor_por_orgao.sql`, `int_concentracao_fornecedor_estado.sql`, `int_contratos_por_fornecedor.sql`, `int_contratos_por_orgao.sql` — intermediate models por trás das 4 marts.
- `dbt/models/staging/stg_contratos.sql` — fonte de `dt_assinatura`/`ano_assinatura` a nível de contrato.
- `api/app/routers/diversidade_vencedores.py`, `concentracao_fornecedor.py`, `perfil_fornecedores.py`, `orgaos.py` — routers sem filtro de ano, confirmados nesta investigação.
- `web/src/charts/filtros.ts` — `popularOrgaos()` (lookup, REQ-8), `initFiltroAnoUnico`/`initFiltroAnoIntervalo` (componente reaproveitado, spec 028).
- `web/src/charts/perfil-orgaos.ts`, `perfil-fornecedores.ts` — consumidores reais de estatística agregada, candidatos ao filtro desta spec.

## Ver também

- [[028-filtro-ano-graficos-relatorios]] (spec anterior, registrou esta pendência em "Fora do escopo")
- [[026-kpis-classificacoes-rankings]] (formato de registro de pendência conhecida, e precedente de mudança de mart com risco de regressão de valor — `fl_valor_suspeito`)
- [[024-dedup-topn-sql-concentracao-fornecedor]] (design atual de `mart_concentracao_fornecedor`, grão e dedup por `id_contratado`)
- [[007-marts-e-metricas]] (definição original das 4 marts investigadas)
