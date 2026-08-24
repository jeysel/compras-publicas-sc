# Spec 026 — KPIs resumo, top-aditivos, perfil de fornecedores/órgãos e correção de `fl_valor_suspeito` em `dim_orgaos`/`dim_fornecedores`

## Tipo

Correção de qualidade de dado (mudança de comportamento em 2 models dbt existentes) + nova funcionalidade (1 endpoint pequeno de KPIs, 1 endpoint de classificação agregada, 2 páginas de relatório novas reaproveitando endpoint existente) + achado que pausa 1 sub-item (ranking individual de aditivos, ver Investigação item 5).

## Status

Implementado e validado em 2026-08-24, com escopo reduzido pelos achados da Investigação (item 5): KPIs resumo (REQ-4/5), correção de `fl_valor_suspeito` em `dim_orgaos`/`dim_fornecedores` (REQ-1/2/3), `perfil-fornecedores` (REQ-8/9) e `perfil-órgãos` (REQ-10) implementados, testados visualmente (Playwright ad-hoc, 0 erros de console nas 3 páginas novas e nas 8 páginas existentes) e com load test (ver Validação abaixo). Top-aditivos (REQ-6/7 originais) fica pausado — ver Investigação item 5 e Fora do escopo.

### Validação

Load test (REQ-15), container isolado `--memory=512m` (mesmo padrão do incidente de 2026-08-21, spec 024):

```
smoke kpis-resumo: 200
smoke perfil-fornecedores: 200
MEM USAGE / LIMIT: 44MiB / 512MiB (baseline)

5 concorrentes × 2 endpoints: 200 200 200 200 200 (cada)
MEM USAGE / LIMIT: 44.21MiB / 512MiB

50 sequenciais kpis-resumo: 50× HTTP 200
MEM USAGE / LIMIT: 44.09MiB / 512MiB

50 sequenciais perfil-fornecedores: 50× HTTP 200
MEM USAGE / LIMIT: 44.21MiB / 512MiB
```

Memória estável (~44MiB) em todo o teste — sem OOM, sem crescimento entre requisições, dentro do teto de 512Mi.

Verificação visual (Playwright ad-hoc, sem suíte de testes pré-existente no repo — não há Playwright configurado neste projeto, diferente do que o pedido original presumia):

- `/` (home): 4 KPI cards preenchidos com dado real (76.041 / 11.406 / 187 / 38.212), 0 erros de console.
- `/relatorios/perfil-fornecedores`: gráfico de barra renderizado (canvas ECharts presente), 0 erros de console.
- `/relatorios/perfil-orgaos`: gráfico de barra + 2 tabelas de ranking com 10 linhas cada, 0 erros de console. 1ª linha por quantidade: Fundo de Melhoria da Polícia Militar (12.936 contratos); 1ª linha por valor: Secretaria de Estado da Educação (R$ 11.389.625.934,10) — bate com o `rank_limpo` previsto na Investigação item 3.
- 8 páginas pré-existentes (`grafico-*`, `relatorio-qualidade-orgao`, `relatorio-variacao-custo`, `relatorio-variacao-prazo`, `metodologia`): todas HTTP 200, 0 erros de console — sem regressão pela mudança de navbar/CSS.
- `dbt test` (22 testes, incluindo os novos `int_contratos_por_orgao`/`_por_fornecedor`): PASS=22 WARN=0 ERROR=0.

## Resumo

Cinco melhorias inspiradas no site antigo (Evidence.dev, removido do repo em 2026-08-20 — ver Status da migração no `CLAUDE.md`), todas exigindo agregação SQL nova ou reaproveitamento de agregado já existente:

1. **KPIs resumo da home** — endpoint novo, 1 linha, sobre `mart_escalada_custo`. **Reduzido em escopo** (ver Investigação item 5): só campos de contagem (`count`), sem `SUM` de valor.
2. **Top 20 maiores aditivos** — **pausado nesta spec** (ver Investigação item 5): o endpoint foi implementado mas não é registrado em `main.py`/exposto por página nenhuma, porque o ranking individual por `vl_variacao` expõe diretamente outliers de valor que `fl_valor_suspeito` não cobre — publicá-lo destacaria erro de dado como se fosse aditivo real.
3. **Classificação de órgãos por volume de contratação** — achado da Investigação: **já existe**, sem uso, em `marts.dim_orgaos.ds_perfil_contratacao` (exposto por `/api/v1/orgaos`). Não precisa de SQL nem endpoint novo, só página de frontend.
4. **Classificação de fornecedores por porte** — achado da Investigação: a classificação **já existe**, sem uso, em `marts.dim_fornecedores.porte_fornecedor`, mas essa mart **não tem endpoint** (não existe `fornecedores.py`). Precisa de endpoint novo (`GROUP BY` sobre a mart já classificada), não de SQL de classificação novo.
5. **Ranking de órgãos por quantidade vs. valor** — achado da Investigação: **já existe**, sem uso, em `dim_orgaos.rank_por_quantidade`/`rank_por_valor`. Não precisa de SQL nem endpoint novo, só página de frontend (reaproveita o mesmo `/api/v1/orgaos` do item 3).

Achado adicional, fora do escopo original mas que se tornou bloqueante para os itens 3 e 5 (ver Investigação): `int_contratos_por_orgao.sql` e `int_contratos_por_fornecedor.sql` — os 2 models que alimentam `dim_orgaos`/`dim_fornecedores` — são os únicos agregados de valor do projeto que **não excluem** `fl_valor_suspeito=true` do `SUM` (todo o resto do app já faz essa exclusão desde a spec 021). Confirmado com o usuário: corrigir agora, dentro desta spec, antes de expor `rank_por_valor`/`porte_fornecedor` em página nova — mesmo padrão de exclusão já usado em `int_contratos_evolucao_anual.sql`/`_por_orgao.sql`/`_por_modalidade.sql` e em `int_concentracao_fornecedor_estado.sql`/`_por_orgao.sql`.

## Contexto

Regra da sessão que motivou este levantamento (3 incidentes de OOM em produção em 2026-08-21, specs 013/014/019/021/024): toda agregação nova usa `GROUP BY` no Postgres, nunca fetch completo + processamento no cliente; todo endpoint novo passa por load test antes de promover. Este levantamento seguiu essa regra à risca — nenhuma query rodou "no achismo": toda contagem abaixo veio de `docker compose exec postgres psql` contra o dado real de dev, antes de desenhar qualquer endpoint.

## Investigação

**1. Volumes reais confirmados via psql (2026-08-24, dado de dev), antes de decidir formato de resposta:**

```sql
SELECT
  count(*) AS total_contratos,
  count(DISTINCT id_contratado) AS fornecedores_distintos,
  count(DISTINCT cod_unidade_gestora) AS orgaos_distintos,
  sum(vl_atual) FILTER (WHERE coalesce(fl_valor_suspeito,false)=false) AS valor_total,
  sum(vl_variacao) FILTER (WHERE vl_variacao <> 0 AND coalesce(fl_valor_suspeito,false)=false) AS total_aditivos,
  count(*) FILTER (WHERE vl_variacao <> 0) AS contratos_com_aditivo
FROM marts.mart_escalada_custo;
```
```
 total_contratos | fornecedores_distintos | orgaos_distintos |  valor_total   | total_aditivos | contratos_com_aditivo
------------------+------------------------+------------------+----------------+----------------+-----------------------
           76041 |                  11406 |              187 | 47214663449.40 |    37864523.37 |                 38212
```

```sql
SELECT
  count(*) FILTER (WHERE vl_variacao > 0) AS aditivo_positivo,
  count(*) FILTER (WHERE vl_variacao > 0 AND coalesce(fl_aditivo_inconsistente,false)=false
                     AND coalesce(fl_valor_suspeito,false)=false) AS aditivo_positivo_limpo
FROM marts.mart_escalada_custo;
```
```
 aditivo_positivo | aditivo_positivo_limpo
-------------------+-------------------------
              9241 |                    8422
```

Volume real de "aditivo real" (acréscimo, sem inconsistência/suspeita) é 8.422 linhas — top 20 é uma fração trivial disso, sem risco de volume.

**2. `dim_orgaos` e `dim_fornecedores` já existem no schema `marts` e já têm exatamente as classificações/rankings pedidos nos itens 5, 6 e 7 — achado que muda o design original.** Confirmado via `\d marts.dim_orgaos` / `\d marts.dim_fornecedores` e leitura de `dbt/models/marts/dim_orgaos.sql`/`dim_fornecedores.sql`:

- `dim_orgaos.ds_perfil_contratacao`: `CASE WHEN qt_contratos >= 1000 THEN 'Alto volume' WHEN >= 100 THEN 'Médio volume' WHEN >= 10 THEN 'Baixo volume' ELSE 'Esporádico' END` — os mesmos 4 limiares pedidos no item de classificação de órgãos.
- `dim_orgaos.rank_por_valor` / `rank_por_quantidade`: `RANK() OVER (ORDER BY vl_total_atual/qt_contratos DESC)` — os dois rankings pedidos no item de separação volume vs. valor.
- `dim_fornecedores.porte_fornecedor`: `CASE WHEN vl_total_atual >= 10000000 THEN 'Grande' WHEN >= 1000000 THEN 'Médio' WHEN >= 100000 THEN 'Pequeno' ELSE 'Micro' END` — os mesmos 4 limiares pedidos no item de porte de fornecedor.

Distribuição real (dado de dev, antes da correção do item 3 abaixo):

```sql
SELECT ds_perfil_contratacao, count(*), min(qt_contratos), max(qt_contratos) FROM marts.dim_orgaos GROUP BY 1;
```
```
 ds_perfil_contratacao | count | min  |  max
------------------------+-------+------+-------
 Alto volume            |    13 | 1006 | 12968
 Baixo volume           |    80 |   10 |    97
 Esporádico             |    26 |    1 |     8
 Médio volume           |    68 |  100 |   848
```

```sql
SELECT porte_fornecedor, count(*), sum(vl_total_atual) FROM marts.dim_fornecedores GROUP BY 1;
```
```
 porte_fornecedor | count |      sum
-------------------+-------+----------------
 Grande            |   533 | 73818980967.24
 Micro              |  6432 |   140000277.29
 Médio              |  1438 |  4666165807.66
 Pequeno            |  3003 |  1079336027.06
```

`/api/v1/orgaos` já existe e já expõe `dim_orgaos` inteira (187 linhas, sem paginação, usado hoje só para popular filtro). **Não existe** router para `dim_fornecedores` (`ls api/app/routers/` confirma: nenhum `fornecedores.py`).

**3. Achado bloqueante: `int_contratos_por_orgao.sql`/`int_contratos_por_fornecedor.sql` não excluem `fl_valor_suspeito`, ao contrário de todo o resto do app.** `grep fl_valor_suspeito dbt/models/` mostra que `int_contratos_evolucao_anual.sql`, `_por_orgao.sql`, `_por_modalidade.sql`, `int_concentracao_fornecedor_estado.sql` e `_por_orgao.sql` filtram `coalesce(fl_valor_suspeito, false) = false` antes do `SUM` (spec 021). Os dois models que alimentam `dim_orgaos`/`dim_fornecedores` (via `int_contratos_por_orgao.sql`/`int_contratos_por_fornecedor.sql`) não têm esse filtro — comparados linha a linha com o schema yml (`dbt/models/intermediate/schema/int_contratos.yml`), confirma-se que nunca tiveram.

Magnitude real do gap, confirmada via psql antes de decidir corrigir:

```sql
SELECT count(*), sum(vl_atual) AS atual, sum(vl_atual) FILTER (WHERE coalesce(fl_valor_suspeito,false)=false) AS limpo
FROM staging.stg_contratos;
```
```
 total |     atual      |     limpo      |      gap
--------+-----------------+-----------------+----------------
 76041 | 79704483079.25 | 47214663449.40 | 32489819629.85
```

Gap de ~R$ 32,5 bi (~40% do total bruto) — coerente com os outliers de `fl_valor_suspeito` já documentados nas specs 021/024 (ex.: PIATA COMERCIO DE PECAS LTDA, R$ 10,5 bi, spec 012/024).

Impacto concreto no ranking por valor de órgãos — top 10 atual vs. top 10 recalculado excluindo `fl_valor_suspeito`:

```
 cod_unidade_gestora | nm_unidade_gestora                                          | rank_atual | rank_limpo
-----------------------+--------------------------------------------------------------+------------+------------
 530001               | Secretaria de Estado da Infraestrutura e Mobilidade         |          1 |          2
 450001               | Secretaria de Estado da Educação                            |          2 |          1
 540096               | Fundo Penitenciário do Estado de SC - FUPESC                |          3 |          3
 540091               | Fundo Rotativo da Penitenciária Industrial de Joinville     |          4 |         65
 160085               | Fundo de Melhoria do Corpo de Bombeiros Militar             |          5 |          9
 160084               | Fundo de Melhoria da Polícia Civil                          |          6 |          6
 480091               | Fundo Estadual de Saúde                                     |          7 |          4
 160020               | Departamento Estadual de Trânsito (DETRAN)                  |          8 |          8
 160097               | Fundo de Melhoria da Polícia Militar                        |          9 |          5
 440023               | Empresa de Pesquisa Agropecuária e Extensão Rural de SC S.A.|         10 |          7
```

O rank 1↔2 troca de posição e, mais grave, o rank 4 (Fundo Rotativo da Penitenciária Industrial de Joinville) cai para a posição 65 quando o outlier suspeito é excluído — o órgão só aparecia no top 5 por efeito de um valor implausível, não de contratação real. Publicar esse ranking numa página nova sem a correção propagaria um erro de dado conhecido para um lugar mais visível do app.

Impacto na classificação por porte de fornecedor (`dim_fornecedores.porte_fornecedor`):

```sql
-- fornecedores cujo porte muda ao recalcular vl_total sem fl_valor_suspeito
 fornecedores_com_porte_diferente | total
------------------------------------+-------
                                  2 | 11406
```

Só 2 fornecedores em 11.406 mudam de faixa — impacto pequeno em contagem, mas real; corrigido pela mesma mudança de SQL (não é um caso separado).

**4. Confirmado antes de implementar: seguir o padrão existente (`WHERE` excluindo a linha inteira) em vez de uma variante que preservasse `qt_contratos` intocado.** Testado via psql qual seria o impacto de cada abordagem antes de escolher:

```sql
-- qt_contratos recalculado excluindo linha suspeita inteira, comparado ao ds_perfil_contratacao atual
 orgaos_perfil_diferente | orgaos_qt_diferente | total
---------------------------+----------------------+-------
                         0 |                   46 |   187
```

46 órgãos têm `qt_contratos` levemente diferente (1-poucos contratos suspeitos a menos), mas **nenhum muda de categoria** de `ds_perfil_contratacao` — a diferença nunca cruza um limiar (1000/100/10). Como o impacto prático é nulo na classificação e o padrão de linha inteira já é o estabelecido em todo o resto do pipeline (specs 021), a correção segue esse padrão em vez de inventar uma variante híbrida (só excluir do SUM, preservar COUNT) sem precedente no código.

**Decisão confirmada com o usuário:** corrigir `int_contratos_por_orgao.sql`/`int_contratos_por_fornecedor.sql` dentro desta spec, replicando o filtro já usado nos outros `int_` models (REQ-1/REQ-2 abaixo) — em vez de documentar como pendência e adiar. Itens 5 e 7 do pedido original **não geram endpoint novo** — confirmado com o usuário reaproveitar `/api/v1/orgaos` sem mudança de contrato, só consumido de forma diferente no frontend novo.

**5. Achado maior, encontrado ao testar `/api/v1/top-aditivos` com dado real (2026-08-24): `fl_valor_suspeito` tem um gap de detecção que vai além do que a correção do item 3 (Investigação) resolve.** Os 3 padrões de `fl_valor_suspeito` (`stg_contratos.sql`) cobrem: razão `vl_original/vl_atual > 100`, `vl_atual > R$500mi` com razão ≈1, e uma lista fechada de 4 contratos inspecionados manualmente (spec 021). Nenhum dos três cobre o padrão inverso — `vl_atual` explodindo sobre um `vl_original` pequeno, com o valor absoluto abaixo do teto de R$500mi. Confirmado via psql, direto no top-10 de `vl_variacao > 0`:

```sql
SELECT nu_contrato, id_contratado, nm_contratado, vl_original, vl_atual,
       round(vl_atual / nullif(vl_original,0), 1) AS razao_atual_sobre_original
FROM marts.mart_escalada_custo
WHERE vl_variacao > 0 AND coalesce(fl_aditivo_inconsistente,false)=false AND coalesce(fl_valor_suspeito,false)=false
ORDER BY vl_variacao DESC LIMIT 10;
```
```
 nu_contrato   | nm_contratado                          | vl_original  |   vl_atual    | razao
----------------+----------------------------------------+--------------+---------------+--------
 2021CT003318  | CENTRO DE INFORMATICA E AUTOMACAO...    |     77774.74 |  327045892.68 | 4205.0
 2025CT000867  | 51 113 977 GENI GUERREIRO VIEIRA        |    120000.00 |  108108000.00 |  900.9
 2020CT004142  | CYCLO X SOLUCOES EM TI LTDA              |     54188.00 |  101909537.23 | 1880.7
 2021CT005537  | NOVA SC SERVICOS TECNICOS LTDA           |   5269653.84 |  212569682.75 |   40.3
 2018CT014810  | NUTRI SAUDE REFEICOES COLETIVAS LTDA     |   1373042.15 |   82333505.74 |   60.0
```

O gap não é só nesta direção. Verificando a soma de acréscimos limpos (`sum(vl_variacao) FILTER (WHERE vl_variacao > 0 AND fl_valor_suspeito=false)` = R$ 5,49 **bilhões**) contra o KPI `total_aditivos` original (`sum(vl_variacao) FILTER (WHERE vl_variacao <> 0 AND fl_valor_suspeito=false)` = R$ 37,86 **milhões**) — os dois deveriam ser da mesma ordem de grandeza (o segundo é superset do primeiro, só some decréscimos), mas divergem por ~150x. Investigado: há decréscimos gigantes não sinalizados cancelando os acréscimos gigantes não sinalizados:

```sql
SELECT nu_contrato, nm_contratado, vl_original, vl_atual, vl_variacao, fl_valor_suspeito, fl_aditivo_inconsistente
FROM marts.mart_escalada_custo WHERE vl_variacao < -100000000 ORDER BY vl_variacao ASC LIMIT 10;
```
```
 nu_contrato        | nm_contratado                           | vl_original     | vl_atual      | vl_variacao       | fl_valor_suspeito | fl_aditivo_inconsistente
----------------------+------------------------------------------+-----------------+----------------+--------------------+--------------------+---------------------------
 CT-00269/2022        | Fraga Construções e Engenharia LTDA       | 23602153155.36  |    5390370.02  | -23596762785.34    | t                  |
 2016CT006428         | WF5 SOLUCOES LTDA                         |  1172160000.00  |     566102.86  |  -1171593897.14    | t                  |
 2021CT002172         | EDINO VENDRAMI                            |   352252209.59  |     276818.16  |   -351975391.43    | t                  |
 CT-00079/2022/SED    | TOPCOM Construções Ltda.                  |   336546460.00  |    3939286.64  |   -332607173.36    | f                  | t
 2022CT002080         | CENTRO DE INFORMATICA E AUTOMACAO...      |   307934520.00  |          0.00  |   -307934520.00    | f                  |
 2018CT015481         | ORBENK ADMINISTRACAO E SERVICOS LTDA      |   390250209.42  |  112498300.42  |   -277751909.00    | f                  |
 2020CT004370         | CLARO S A                                 |   155939870.64  |    2080737.04  |   -153859133.60    | f                  |
```

`CLARO S A` já está na lista fechada de 4 contratos suspeitos da spec 021 (`2020CT004866`, R$ 6,27 bi) — mas por **outro contrato**; `2020CT004370` (R$ 155,9 mi → R$ 2,1 mi) não é pego pela lista fechada nem pelas 2 regras de razão. No total, **13 contratos com `|vl_variacao| > R$ 100 milhões`** não são cobertos por `fl_valor_suspeito`:

```sql
SELECT count(*) FROM marts.mart_escalada_custo WHERE abs(vl_variacao) > 100000000 AND coalesce(fl_valor_suspeito,false)=false;
-- 13
```

**Decisão confirmada com o usuário, revisando a decisão inicial do item 3:** não expandir a lógica de `fl_valor_suspeito` dentro desta spec (exigiria a mesma inspeção manual linha-a-linha que a spec 021 fez pro Padrão B — investigação própria). Em vez disso: (a) o item "top-aditivos" (item 2) fica pausado — código implementado (`api/app/routers/top_aditivos.py`), mas **não registrado** em `main.py`, sem página de frontend, até uma spec de levantamento própria (nos moldes da 021) mapear o gap; (b) o KPI de resumo (item 1) tem os 2 campos de `SUM` de valor (`valor_total`, `total_aditivos`) removidos do escopo desta spec — fica só com contagens (`count`), que não são sensíveis a um único contrato com valor não sinalizado; (c) `perfil-fornecedores`/`perfil-órgãos` (itens 3/4/5) seguem como planejado, porque operam sobre agregados por entidade (soma de todos os contratos de um fornecedor/órgão, não o valor de 1 contrato isolado) — o mesmo gap existe ali (a correção do REQ-1/REQ-2 usa o `fl_valor_suspeito` que ainda tem o gap dos 13 contratos), mas o registro fica como pendência conhecida, não como bloqueio, dado que o efeito de um único outlier não sinalizado se dilui numa soma de dezenas/centenas de contratos por entidade, ao contrário de um ranking individual de 1 linha.

## Requirements

### Funcionais

- REQ-1: `int_contratos_por_orgao.sql` DEVE excluir linhas com `fl_valor_suspeito=true` via `WHERE coalesce(fl_valor_suspeito, false) = false`, exatamente o mesmo padrão (linha inteira fora do agregado, não só das colunas de valor) já usado em `int_contratos_evolucao_por_orgao.sql`/`_anual.sql`/`_por_modalidade.sql`. Isso também reduz `qt_contratos`/`qt_fornecedores_distintos` nos 46 órgãos que têm ao menos 1 contrato suspeito (confirmado via psql, ver Investigação) — comportamento aceito por ser consistente com o padrão já estabelecido no resto do pipeline, não uma exceção nova.
- REQ-2: `int_contratos_por_fornecedor.sql` DEVE receber a mesma exclusão do REQ-1 (linha inteira, `WHERE`), incluindo o efeito em `qt_contratos`/`perc_concentracao` (que deriva de `vl_atual`).
- REQ-3: `dim_orgaos.rank_por_valor` e `dim_fornecedores.rank_por_valor`/`porte_fornecedor` DEVEM refletir os valores corrigidos (REQ-1/REQ-2) sem mudança de lógica própria — o `RANK()`/`CASE` já existente nessas dimensões continua correto, só o valor de entrada muda.
- REQ-4: QUANDO a requisição a `/api/v1/kpis-resumo` for feita, o sistema DEVE retornar um objeto único (não lista, sem paginação) com: total de contratos, fornecedores distintos, órgãos distintos e quantidade de contratos com aditivo (`vl_variacao <> 0`) — agregado em uma única query `SELECT` (sem `GROUP BY`) sobre `marts.mart_escalada_custo`. NÃO inclui `SUM` de valor (`valor_total`/`total_aditivos`) — removido do escopo desta spec pelo achado da Investigação item 5 (gap de `fl_valor_suspeito` sensível a outlier individual em campos de `SUM`).
- REQ-5: A home DEVE exibir os 4 KPIs do REQ-4 como cards, mesmo estilo visual dos 2 cards de achado já existentes (`finding-card`), buscando de `/api/v1/kpis-resumo` sem valor hardcoded.
- REQ-6/REQ-7: **Removidos desta spec** (top-aditivos) — ver Investigação item 5 e Fora do escopo. `GET /api/v1/top-aditivos` existe em código (`api/app/routers/top_aditivos.py`) mas não é registrado em `main.py`; nenhuma página de frontend é criada.
- REQ-8: QUANDO a requisição a `/api/v1/perfil-fornecedores` for feita, o sistema DEVE retornar, por `porte_fornecedor`, a quantidade de fornecedores e a soma de `vl_total_atual` — agregado com `GROUP BY porte_fornecedor` sobre `marts.dim_fornecedores` (a classificação já vem pronta da mart, corrigida pelo REQ-2; o endpoint não reclassifica nada, só agrega o que já existe).
- REQ-9: A página `/relatorios/perfil-fornecedores` DEVE exibir um gráfico de barra horizontal (mesmo padrão ECharts de `variacao-custo-modalidade.ts`) com a distribuição de fornecedores por porte (REQ-8).
- REQ-10: A página `/relatorios/perfil-orgaos` DEVE exibir: (a) um gráfico de barra horizontal com a distribuição de órgãos por `ds_perfil_contratacao`, calculada no cliente a partir da resposta já pequena (187 linhas) de `/api/v1/orgaos` — não é uma nova chamada de agregação SQL, é contagem de categoria sobre um array já buscado uma vez, mesmo padrão já em uso em `achados-home.ts` (`top.reduce(...)` sobre uma resposta de 10 linhas); (b) duas tabelas/rankings lado a lado — "Top 10 órgãos por quantidade de contratos" (`ORDER BY rank_por_quantidade`) e "Top 10 órgãos por valor total" (`ORDER BY rank_por_valor`) — ambas derivadas por `sort`/`slice` do mesmo array de 187 linhas, sem chamada adicional à API.
- REQ-11: Nenhum endpoint novo (REQ-4, REQ-8) DEVE fazer streaming de linha-a-contrato — todas as respostas são agregadas (KPI único, 4 categorias de porte), payload pequeno, sem risco da classe de OOM das specs 013/014/021/024.
- REQ-12: A navbar (`layout.html`) DEVE ganhar 2 itens novos no dropdown Relatórios: "Perfil de fornecedores", "Perfil de órgãos" ("Top aditivos" fica de fora — item pausado).

### Não-funcionais

- REQ-13: Os endpoints novos NÃO DEVEM alterar a formatação de moeda, percentual ou o mascaramento de CPF/CNPJ já implementado (reaproveitam `format.ts`/`masking.py` como estão).
- REQ-14: A correção do REQ-1/REQ-2 DEVE ser validada por comparação explícita (contagem de linhas com classificação/ranking diferente antes/depois), documentada em Investigação — não presumida como "sem impacto" só porque o `CASE`/`RANK()` em si não muda.
- REQ-15: Todo endpoint novo **registrado em `main.py`** (`kpis-resumo`, `perfil-fornecedores`) DEVE passar por load test (50 requisições sequenciais, container com `--memory=512m`, mesmo padrão do incidente de 2026-08-21 — ver `docs/specs/024-.../spec.md`) antes de ser considerado validado. `top-aditivos` não é registrado (REQ-6/7), logo não entra neste load test.

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| Onde corrigir o gap de `fl_valor_suspeito` | `int_contratos_por_orgao.sql`/`int_contratos_por_fornecedor.sql` (camada `intermediate`), não nas dims nem nos routers | Mesmo lugar onde a exclusão já é feita em todo o resto do pipeline (spec 021) — mantém a regra num único ponto por agregado, não duplica filtro no SQL do router |
| Itens 5 (classificação de órgãos) e 7 (ranking volume/valor) | Sem endpoint novo — reaproveita `/api/v1/orgaos` (`dim_orgaos`) já existente | `ds_perfil_contratacao`/`rank_por_valor`/`rank_por_quantidade` já vêm prontos da mart; criar endpoint novo seria duplicar dado já servido |
| Item 6 (porte de fornecedor) | Endpoint novo `GET /api/v1/perfil-fornecedores`, `GROUP BY porte_fornecedor` sobre `dim_fornecedores` já classificada | Mart já tem `porte_fornecedor` pronto, mas não tem router; agregar por porte no SQL evita mandar 11.406 linhas pro cliente só pra contar 4 categorias |
| Top-aditivos | Código implementado, mas **não registrado**/sem página | Ranking individual de 1 contrato expõe diretamente outliers de valor que `fl_valor_suspeito` não cobre (Investigação item 5) — publicar seria mostrar erro de dado como achado real |
| KPIs resumo | 1 query sem `GROUP BY`, resposta é objeto único, **sem campos de `SUM` de valor** | Volume fixo (1 linha), sem necessidade de paginação; `SUM(vl_atual)`/`SUM(vl_variacao)` removidos porque ficam sensíveis a outlier individual não coberto por `fl_valor_suspeito` (Investigação item 5) |
| Onde entram as 2 páginas de "perfil" | `/relatorios/perfil-fornecedores` e `/relatorios/perfil-orgaos`, páginas próprias no dropdown Relatórios | Mesmo padrão de página-por-relatório da spec 025; conteúdo (classificação + ranking) não cabe como seção dentro de página já existente sem sobrecarregar o layout |

### Componentes afetados

- `dbt/models/intermediate/int_contratos_por_orgao.sql`, `int_contratos_por_fornecedor.sql` — adiciona `WHERE coalesce(fl_valor_suspeito, false) = false` antes do `SUM`/`AVG`/`MAX`/`MIN` de valor (REQ-1/REQ-2).
- `dbt/models/intermediate/schema/int_contratos.yml` — atualiza descrição dos 2 models pra documentar a exclusão.
- `api/app/routers/kpis_resumo.py`, `perfil_fornecedores.py` (novos, registrados); `top_aditivos.py` (novo, implementado, **não registrado** — ver Investigação item 5).
- `api/app/schemas/kpis_resumo.py`, `perfil_fornecedores.py` (novos); `top_aditivos.py` reaproveita `EscaladaCusto` (nenhum schema próprio).
- `api/app/main.py` — registra 2 routers novos (`kpis_resumo`, `perfil_fornecedores`) e 2 rotas de página novas (`/relatorios/perfil-fornecedores`, `/relatorios/perfil-orgaos`).
- `api/app/templates/relatorio_perfil_fornecedores.html`, `relatorio_perfil_orgaos.html` (novos); `home.html` (cards de KPI); `layout.html` (2 itens novos no dropdown Relatórios).
- `web/src/charts/perfil-fornecedores.ts`, `perfil-orgaos.ts`, `kpis-resumo.ts` (novos).
- `web/src/main.ts` — estende o dispatch por `data-page`.

## Casos de borda

- Fornecedor cujos únicos contratos são todos `fl_valor_suspeito=true`: some da agregação depois do REQ-2 — **confirmado no dado real** após `dbt run`: `dim_fornecedores` caiu de 11.406 para 11.403 linhas (3 fornecedores com 100% dos contratos suspeitos desaparecem), mesmo comportamento de `GROUP BY` sem linha correspondente já documentado como não-erro na spec 025. `dim_orgaos` manteve 187 linhas — nenhum órgão tem 100% dos contratos suspeitos.
- `/api/v1/perfil-fornecedores` com porte sem nenhum fornecedor (não deve ocorrer no dado real, mas syntacticamente possível se um limiar mudar): `GROUP BY` simplesmente não retorna a linha — mesmo comportamento já documentado na spec 025 para os relatórios por modalidade.
- Empate exato em `vl_variacao` no top-aditivos: sem critério de desempate explícito além de `ORDER BY vl_variacao DESC` — ordem entre empatados não é garantida pelo Postgres sem `ORDER BY` secundário; aceitável pro caso de uso (ranking de leitura, não requer estabilidade de posição entre empatados).
- REQ-10(a) conta categorias sobre um array de 187 itens já em memória no cliente — isso não é o antipadrão de "fetch completo + processamento" que motivou a regra da sessão: o antipadrão era buscar o **grão de contrato** (dezenas de milhares de linhas) pra agregar no cliente; aqui o array já é o agregado por órgão, contá-lo em 4 baldes é O(187), não O(76041).

## Fora do escopo

- **Expandir a detecção de `fl_valor_suspeito` pra cobrir os 13 contratos com `|vl_variacao| > R$100mi` não sinalizados (Investigação item 5).** Exigiria a mesma inspeção manual linha-a-linha que a spec 021 fez pro Padrão B — pendência registrada, não resolvida aqui. Enquanto não houver spec própria: `top-aditivos` fica pausado (sem página), e os `SUM` de valor do KPI resumo ficam fora do escopo.
- **Publicar `/relatorios/top-aditivos`** — depende do item acima; endpoint já implementado (`api/app/routers/top_aditivos.py`), só falta registrar e criar a página quando a detecção estiver corrigida.
- Revisitar `fct_contratos.sql`/`dim_modalidades.sql` em busca do mesmo gap de `fl_valor_suspeito` — não investigado nesta spec; se existir, é achado pra spec própria.
- Adicionar filtro interativo (por ano, por modalidade) nas páginas novas — nenhuma delas tem esse requisito pedido, mesmo padrão de "fora do escopo" já registrado na spec 025.
- Badge de nota/cor na classificação de porte ou perfil de contratação — mesma decisão da spec 025 (Contexto): não há threshold de "bom"/"ruim" definido, mostrar só o dado cru.

## Referências de código

- `api/app/routers/qualidade_dado_orgao.py`, `variacao_custo_modalidade.py` — padrão de `GROUP BY`/`FILTER` a seguir nos 3 endpoints novos.
- `api/app/routers/orgaos.py` — endpoint reaproveitado sem mudança pelos itens 5/7.
- `dbt/models/marts/dim_orgaos.sql`, `dim_fornecedores.sql` — classificações/rankings já prontos, reaproveitados.
- `dbt/models/intermediate/int_contratos_por_orgao.sql`, `int_contratos_por_fornecedor.sql` — models a corrigir (REQ-1/REQ-2).
- `dbt/models/intermediate/int_contratos_evolucao_por_orgao.sql` — padrão de exclusão de `fl_valor_suspeito` a replicar.
- `web/src/charts/achados-home.ts` — padrão de agregação client-side sobre resposta já pequena, reaproveitado no REQ-10(a).

## Ver também

- [[021-levantamento-outliers-valor-extremo]] (origem de `fl_valor_suspeito`, tratamento em todo o resto do pipeline)
- [[024-dedup-topn-sql-concentracao-fornecedor]] (padrão de agregação no SQL, motivação da regra de sessão que originou este levantamento)
- [[025-navbar-paginas-relatorios]] (padrão de página-por-relatório, dropdown Relatórios, endpoints `GROUP BY` sobre `mart_escalada_custo`)
