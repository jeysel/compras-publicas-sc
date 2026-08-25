# Spec 025 — Navbar multi-página + 3 relatórios novos (ranking de qualidade, variação de custo/prazo por modalidade)

## Tipo

Nova funcionalidade (redesign de navegação do frontend) + mudança de comportamento (3 endpoints novos, 1 coluna nova em mart existente).

## Status

Em implementação — spec escrita antes do código, por exigência do `CLAUDE.md` deste repo (toda mudança de comportamento relevante vira spec antes de virar código).

## Resumo

O frontend hoje é uma única página (`base.html`, rota `GET /`) com os 4 gráficos existentes empilhados e uma seção de metodologia inline. Um protótipo em Claude Design (anexado à conversa que originou esta spec) define uma home com storytelling (2 cards de achado), navbar com dropdowns "Gráficos" e "Relatórios", página própria por gráfico/relatório, e página própria de metodologia. Esta spec adapta esse protótipo para o stack real do projeto — **Jinja2 multi-página + TypeScript sem framework + ECharts**, sem introduzir SPA nem framework novo — e fecha 3 relatórios novos (ranking de órgãos por qualidade de dado, variação de custo por modalidade, variação de prazo por modalidade) via 3 endpoints novos, agregando no Postgres em vez de no cliente.

## Contexto

Decisão de escopo já fechada antes desta spec (não é objeto de debate aqui):

- Navbar: Início · Gráficos ▾ · Relatórios ▾ · Metodologia.
- Home: 2 cards de achado (maior fornecedor do estado; concentração top-10) + seção "Explorar por gráfico" + seção "Relatórios".
- Gráficos ▾: os 4 já existentes (escalada de custo, diversidade de vencedores, série temporal, concentração de fornecedores), cada um ganhando página própria com contexto textual — sem mudança de lógica de agregação/filtro já implementada.
- Relatórios ▾: 3 novos, sem endpoint pré-existente que sirva a métrica com o filtro de qualidade correto (ver Investigação).
- Metodologia: página própria (hoje é `#metodologia` inline em `base.html`).
- Texto de intro da home usa "a partir de 2016" (sem data final fixa) e descreve a fonte genericamente como "sistemas de gestão do Estado, com os dados disponibilizados no Portal de Transparência oficial" — nunca citar SIGEF nominalmente.
- O aviso de "dados ilustrativos" do protótipo **não se aplica** — este projeto sempre usa dado real via API, não há modo de demonstração. Esse elemento do protótipo é descartado.
- Os badges de nota (A/B/C/D) por cor no ranking de qualidade de dado do protótipo são descartados (confirmado com o usuário) — não há threshold definido em nenhum lugar do escopo fechado, e inventar um agora seria presumir uma regra de negócio não pedida. O relatório mostra os dois percentuais crus (`% aditivo inconsistente`, `% valor suspeito`).

## Investigação

Levantamento feito antes de qualquer código, via leitura direta do repo:

**1. Estrutura atual é mínima — 1 template, 1 rota, 1 bundle.** `api/app/templates/` só tem `base.html`; `api/app/main.py` só registra `GET /`. `web/src/main.ts` já despacha por `document.body.dataset.page` (hoje só existe `"home"`) — esse padrão é reaproveitado para as páginas novas, sem precisar de SPA.

**2. Os 3 relatórios não têm cálculo client-side viável nem endpoint pronto que sirva.** `marts.mart_escalada_custo` (consumida hoje só por `/api/v1/escalada-custo`, streaming, ~76-95k linhas) tem todas as colunas-base necessárias (`nm_unidade_gestora`, `nm_modalidade`, `fl_aditivo_inconsistente`, `fl_valor_suspeito`, `vl_variacao`, `perc_variacao`, `dias_variacao`) — mas agregar no cliente reintroduziria a classe de bug corrigida hoje na spec 024 (buscar dataset completo no browser pra agregação simples). Os endpoints `orgaos`/`modalidades` existentes (`dim_orgaos`/`dim_modalidades`) já têm agregados por órgão/modalidade, mas **não carregam `fl_aditivo_inconsistente`/`fl_valor_suspeito`** (são construídos a partir de `int_contratos_por_orgao`/`int_contratos_por_modalidade`, que somam `vl_aditado` mas não contam as duas flags de qualidade) — não servem para o relatório de ranking de qualidade. Decisão: 3 endpoints novos, `GROUP BY` direto no Postgres sobre `marts.mart_escalada_custo`, mesmo padrão de `orgaos.py`/`modalidades.py`.

**3. "Contrato com aditivo" não é uma flag booleana explícita em `mart_escalada_custo`.** O padrão já usado em `int_contratos_por_modalidade.sql` é `vl_aditado > 0`, mas `vl_aditado` não é exposto por `mart_escalada_custo` (só `vl_variacao`, a métrica oficial — spec 013/014 decidiu não usar `vl_aditado` como métrica, só como sinal de inconsistência). Confirmado em `stg_contratos.sql`: `vl_atual` só diverge de `vl_original` por efeito de aditivo, logo `vl_variacao <> 0` é proxy correto para "aditivo que mudou valor" sem precisar expor `vl_aditado`. Mesmo raciocínio para prazo: `dias_variacao <> 0` (`dias_atuais - dias_originais`) é "aditivo que mudou prazo".

**4a. Achado durante a validação do endpoint de prazo: `dias_originais`/`dias_atuais` têm cobertura muito baixa e concentrada.** Confirmado via `docker compose exec postgres psql` após implementar `/api/v1/variacao-prazo-modalidade` e ver a resposta vir com 1 linha só:

```sql
SELECT count(*) AS total, count(dias_originais) AS tem_dias_orig, count(dias_atuais) AS tem_dias_atual
FROM marts.mart_escalada_custo;
```
```
 total | tem_dias_orig | tem_dias_atual
-------+---------------+----------------
 76041 |          2141 |           5424
```

Confirmado também na `raw.contratos` (mesmos números exatos) — a lacuna já existe na fonte, não é introduzida por nenhuma etapa do pipeline dbt. Pior: os poucos contratos preenchidos estão quase todos na modalidade `nm_modalidade_norm = 'Não informado'` — nenhuma modalidade nomeada (Pregão Eletrônico, Dispensa, etc.) tem uma linha sequer com `dias_variacao <> 0`. Decisão (confirmada com o usuário): implementar o relatório mesmo assim, mas com aviso explícito de baixa cobertura na página — mesmo padrão de nota de exclusão já usado nos gráficos existentes (`setLegendaExclusao`).

**4b. Achado que muda o desenho dos 2 relatórios por modalidade: `nm_modalidade` em `mart_escalada_custo` é valor bruto da fonte, não normalizado.** `int_contratos_por_modalidade.sql` (usado por `dim_modalidades`/`/api/v1/modalidades`) tem um `CASE WHEN` que funde variantes de lei da mesma modalidade (ex.: `Pregão Eletrônico - Lei 10.520` e `Pregão Eletrônico - Lei 14.133` → `Pregão Eletrônico - Leis 10.520/2002 e 14.133/2021`; mesmo padrão para Pregão Presencial, Dispensa, Inexigibilidade). `mart_escalada_custo.sql` não aplica essa normalização — um `GROUP BY nm_modalidade` direto nela produziria uma lista de modalidades divergente do resto do app. Decisão (confirmada com o usuário): adicionar `nm_modalidade_norm` a `mart_escalada_custo`, replicando o mesmo `CASE WHEN`, para os 2 relatórios agruparem de forma consistente com `dim_modalidades`.

## Requirements

### Funcionais

- REQ-1: O sistema DEVE expor uma navbar fixa no topo com os itens Início, Gráficos (dropdown), Relatórios (dropdown) e Metodologia, presente em todas as páginas.
- REQ-2: O dropdown Gráficos DEVE listar as 4 páginas de gráfico existentes (escalada de custo, diversidade de vencedores, série temporal, concentração de fornecedores); cada uma DEVE ter rota própria, mantendo exatamente a lógica de fetch/filtro/renderização já implementada em `web/src/charts/*.ts`.
- REQ-3: O dropdown Relatórios DEVE listar as 3 páginas de relatório novas (ranking de qualidade de dado por órgão, variação de custo por modalidade, variação de prazo por modalidade).
- REQ-4: A home DEVE exibir 2 cards de achado (maior fornecedor do estado; concentração dos 10 maiores) com dado real, buscado de `/api/v1/concentracao-fornecedor` sem `cod_unidade_gestora` — sem valor hardcoded.
- REQ-5: A home DEVE exibir uma seção "Explorar por gráfico" (linkando as 4 páginas de gráfico) e uma seção "Relatórios" (linkando as 3 páginas de relatório).
- REQ-6: A metodologia DEVE ter página própria (rota dedicada), com o mesmo conteúdo hoje presente em `#metodologia` de `base.html`.
- REQ-7: QUANDO a requisição a `/api/v1/qualidade-dado-orgao` for feita, o sistema DEVE retornar, por `cod_unidade_gestora`/`nm_unidade_gestora`: quantidade de contratos, quantidade e percentual com `fl_aditivo_inconsistente = true`, quantidade e percentual com `fl_valor_suspeito = true` — agregado no SQL sobre `marts.mart_escalada_custo`, sem filtrar nenhum contrato (as duas flags são a métrica, não um filtro aqui).
- REQ-8: QUANDO a requisição a `/api/v1/variacao-custo-modalidade` for feita, o sistema DEVE retornar, por `nm_modalidade_norm`: quantidade de contratos com `vl_variacao <> 0` e a média de `perc_variacao` desses contratos — excluindo contratos com `fl_aditivo_inconsistente = true` ou `fl_valor_suspeito = true`, mesmo critério de exclusão já usado em `escalada-custo.ts`.
- REQ-9: QUANDO a requisição a `/api/v1/variacao-prazo-modalidade` for feita, o sistema DEVE retornar, por `nm_modalidade_norm`: quantidade de contratos com `dias_variacao <> 0` e a média de `dias_variacao` desses contratos — mesma exclusão do REQ-8.
- REQ-9a: A página do relatório de variação de prazo DEVE exibir aviso explícito de que `dias_originais`/`dias_atuais` estão preenchidos em só ~7% dos contratos na fonte (achado 4a da Investigação) — a tabela/gráfico não deve ser apresentado sem esse contexto, sob risco de o usuário interpretar "sem dado" como "sem aditivo de prazo". **Revisto parcialmente em 2026-08-25 por [[032-limitacao-dias-variacao-modalidade]]:** o aviso em si permanece (mantido nesta forma), mas a parte de manter o relatório promovido no menu/home foi revertida — achado confirmado estável (mesmos números 4 dias depois), relatório tirado da navegação, rota/endpoint mantidos intactos.
- REQ-10: `mart_escalada_custo` DEVE ganhar a coluna `nm_modalidade_norm`, com a mesma normalização de `int_contratos_por_modalidade.sql` (fusão de variantes de lei por modalidade), para os endpoints dos REQ-8/REQ-9 agruparem de forma consistente com `dim_modalidades`.

### Não-funcionais

- REQ-11: Nenhum dos 3 endpoints novos DEVE fazer streaming de linha-a-contrato para o cliente — a resposta é o agregado (uma linha por órgão/modalidade), payload pequeno, sem risco de repetir o padrão de OOM da spec 024/anterior a ela.
- REQ-12: As páginas novas NÃO DEVEM alterar o comportamento, formatação de moeda ou mascaramento de CPF/CNPJ já implementado nos 4 gráficos existentes.
- REQ-13: A navegação entre páginas DEVE ser feita por link/rota real (`<a href>` ou navegação de browser padrão), não roteamento client-side — mantém o projeto fora do território de SPA, conforme decisão de escopo.

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| Onde os 3 relatórios agregam | SQL (`GROUP BY` em `marts.mart_escalada_custo`), endpoints novos | `dim_orgaos`/`dim_modalidades` não carregam as flags de qualidade; agregar no cliente repetiria o padrão de bug da spec 024 |
| "Contrato com aditivo" | `vl_variacao <> 0` (custo) / `dias_variacao <> 0` (prazo) | `vl_aditado` não é exposto pela mart (spec 013/014 decidiu não usá-lo como métrica); a divergência de valor/prazo só existe por efeito de aditivo |
| Normalização de modalidade nos relatórios | Nova coluna `nm_modalidade_norm` em `mart_escalada_custo`, réplica do `CASE WHEN` de `int_contratos_por_modalidade.sql` | Mantém a lista de modalidades consistente em todo o app; lógica de categorização fica só na camada dbt (onde já vive), evita duplicar em SQL dentro do router Python |
| Nota A/B/C/D no ranking de qualidade | Descartada — mostra só os percentuais | Threshold não definido em nenhum lugar do escopo fechado; inventar um agora seria presumir regra de negócio não pedida |
| Arquitetura de página | Jinja2 multi-página (1 template + 1 rota por página), `main.ts` estende o dispatch por `data-page` já existente | Mantém "sem framework novo"; reaproveita padrão já em uso, só multiplica o número de templates/rotas |
| Aviso de "dados ilustrativos" do protótipo | Descartado | Este projeto sempre serve dado real via API — não existe modo demonstração |

### Componentes afetados

- `dbt/models/marts/mart_escalada_custo.sql` + `dbt/models/marts/schema/marts_escalada_custo.yml` — nova coluna `nm_modalidade_norm`.
- `api/app/routers/qualidade_dado_orgao.py`, `variacao_custo_modalidade.py`, `variacao_prazo_modalidade.py` (novos) — 1 `GROUP BY` cada.
- `api/app/schemas/qualidade_dado_orgao.py`, `variacao_custo_modalidade.py`, `variacao_prazo_modalidade.py` (novos).
- `api/app/main.py` — registra os 3 routers novos (prefixo `/api/v1`) e as 8 rotas de página novas.
- `api/app/templates/` — `base.html` vira layout com navbar; 8 templates filhos novos (`home.html`, 4× gráfico, 3× relatório) + `metodologia.html`.
- `web/src/main.ts` — estende o dispatch por `data-page` pras 8 páginas novas.
- `web/src/charts/qualidade-dado-orgao.ts`, `variacao-custo-modalidade.ts`, `variacao-prazo-modalidade.ts` (novos) — renderização de tabela, sem ECharts (protótipo usa tabela pra ranking; os 2 relatórios de modalidade usam gráfico de barra horizontal, mesmo padrão de `concentracao-fornecedor.ts`).
- `web/src/style.css` — estilos de navbar/dropdown/cards/tabela.

## Casos de borda

- `/api/v1/variacao-prazo-modalidade` retorna, no dado real de 2026-08-21, só 1 linha (`Não informado`, 707 contratos) — as 21 modalidades nomeadas não têm nenhum contrato com `dias_variacao <> 0` porque a fonte não preenche `diasoriginais`/`diasatuais` pra elas (achado 4a). Não é bug do endpoint; é refletido fielmente na página via aviso de cobertura (REQ-9a).
- Órgão ou modalidade com 0 contratos que atendam ao filtro de exclusão (REQ-8/9): não aparece na resposta agregada (comportamento padrão de `GROUP BY`, não um erro).
- `nm_unidade_gestora`/`nm_modalidade_norm` nulos: mantidos como grupo próprio (`NULL`), consistente com o tratamento de "Não informado" já usado em `int_contratos_por_modalidade.sql` — a query dos REQ-8/9 herda o `coalesce(nm_modalidade, 'Não informado')` já presente nesse `CASE WHEN`.
- Card de achado da home ("maior fornecedor") depende de `/api/v1/concentracao-fornecedor` responder; se a API falhar, a home não deve quebrar as outras seções — mesmo padrão de tratamento de erro já usado em `escalada-custo.ts` (`if (!resposta.ok) { ... }`).

## Fora do escopo

- Filtro interativo por órgão/modalidade nas páginas de gráfico/relatório (os query params já existem em alguns endpoints, mas não há widget de filtro na UI hoje nem neste redesign).
- Qualquer classificação de "nota"/score por órgão além dos percentuais crus (ver Design).
- Revisitar a normalização de modalidade em outros lugares do app (`dim_modalidades` já está correta; esta spec só estende a mesma lógica pra `mart_escalada_custo`).

## Referências de código

- `api/app/main.py`, `api/app/templates/base.html`, `web/src/main.ts` — estrutura atual (single-page).
- `api/app/routers/concentracao_fornecedor.py` — padrão de agregação SQL a seguir nos 3 endpoints novos.
- `dbt/models/intermediate/int_contratos_por_modalidade.sql` — `CASE WHEN` de normalização a replicar em `nm_modalidade_norm`.
- `dbt/models/marts/mart_escalada_custo.sql`, `dbt/models/marts/schema/marts_escalada_custo.yml` — mart a estender.

## Ver também

- [[012-eixo-frontend-biblioteca-grafico]] (decisão original de stack: Jinja2 + TS sem framework + ECharts)
- [[013-levantamento-dbt-legado]] (contexto de `fl_aditivo_inconsistente`)
- [[021-levantamento-outliers-valor-extremo]] (contexto de `fl_valor_suspeito`)
- [[024-dedup-topn-sql-concentracao-fornecedor]] (padrão de agregação no SQL em vez do cliente, motivação direta desta spec)
