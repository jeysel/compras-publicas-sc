# Spec 024 — Mover dedup + top-N de `concentracao-fornecedor` do cliente pro SQL

## Tipo

Correção de performance / decisão de arquitetura (mudança de contrato do endpoint `/api/v1/concentracao-fornecedor`).

## Status

Implementado e validado em 2026-08-21.

## Resumo

`web/src/charts/concentracao-fornecedor.ts` chamava a API com `top_n=30000` em todo carregamento da home, pra garantir cobertura da mart inteira antes de deduplicar por `id_contratado` e cortar pro top-10 no JavaScript do cliente. Isso buscava a mart inteira (27.849 linhas) a cada visita e já causou OOM em produção. Correção: dedup (`DISTINCT ON`) + top-N passam a acontecer no SQL, no Postgres; a API volta a retornar só as linhas necessárias (default `top_n=10`, teto `le=100`), e o cliente não faz mais nenhuma lógica de agregação.

## Contexto

Achado durante investigação de OOM em produção (2026-08-21). A causa raiz já estava documentada como pendência conhecida em [[012-eixo-frontend-biblioteca-grafico]] (Casos de borda): o grão de `marts.mart_concentracao_fornecedor` é `(cod_unidade_gestora, id_contratado)` — um fornecedor que contratou com vários órgãos aparece uma vez por órgão (até 126+ linhas pro mesmo fornecedor, no dado real). Na época, a decisão registrada foi fazer o dedup no cliente buscando a mart inteira (`top_n=30000`), sem endereçar o custo disso. Esta spec fecha essa pendência.

## Investigação

Confirmado via psql (`docker compose exec postgres psql`) antes de escrever qualquer SQL novo, não presumido:

**1. `rank_estado`/`vl_total_fornecedor_estado` já vêm pré-agregados por fornecedor** — idênticos em todas as linhas do mesmo `id_contratado`, independente de quantos órgãos ele tenha:

```sql
SELECT id_contratado, count(*) AS n_linhas, count(DISTINCT rank_estado) AS n_ranks_distintos,
       count(DISTINCT vl_total_fornecedor_estado) AS n_valores_distintos
FROM marts.mart_concentracao_fornecedor
GROUP BY id_contratado ORDER BY n_linhas DESC LIMIT 5;
```

```
   id_contratado    | n_linhas | n_ranks_distintos | n_valores_distintos
--------------------+----------+-------------------+---------------------
 83.043.745/0001-65 |      126 |                 1 |                   1
 08.336.783/0001-90 |       93 |                 1 |                   1
 83.413.591/0003-18 |       87 |                 1 |                   1
 82.508.433/0001-17 |       87 |                 1 |                   1
 18.712.730/0001-80 |       84 |                 1 |                   1
```

Consequência: a "duplicação" não exige nenhum `SUM()` novo no SQL — é dedup puro (`DISTINCT ON`), não agregação. O valor de `vl_total_fornecedor_estado` já é a soma correta, calculada rio acima (`int_concentracao_fornecedor_estado`, spec 007/021).

**2. O caminho filtrado por `cod_unidade_gestora` não tem duplicação** — o grão `(cod_unidade_gestora, id_contratado)` já é único dentro de um único órgão:

```sql
SELECT cod_unidade_gestora, id_contratado, count(*)
FROM marts.mart_concentracao_fornecedor
GROUP BY 1,2 HAVING count(*) > 1 LIMIT 5;
-- (0 rows)
```

Só o ranking estadual (`rank_estado`, sem filtro de órgão) precisa de dedup.

**3. Equivalência de resultado confirmada antes de aplicar no código.** A query proposta (`DISTINCT ON (id_contratado) ... ORDER BY id_contratado, rank_estado`, depois reordenada por `rank_estado` e limitada) foi rodada isoladamente e o top-10 resultante bate com o que o dedup client-side produziria: como `rank_estado` é atribuído por `RANK() OVER (ORDER BY vl_total_fornecedor_estado DESC)` rio acima, ordenar por `rank_estado` ascendente é equivalente a ordenar por `vl_total_fornecedor_estado` descendente — mesma ordenação que o cliente aplicava depois do dedup.

Achado incidental (não é bug, é deriva de dado entre 2026-08-20 e 2026-08-21): o top-1 estadual mudou de `PIATA COMERCIO DE PECAS LTDA` (R$ 10,5 bi, registrado em [[012-eixo-frontend-biblioteca-grafico]] como outlier não corrigido) para `CENTRO DE INFORMATICA E AUTOMACAO DO ESTADO DE SC S A` (R$ 2,14 bi). Consistente com o tratamento de `fl_valor_suspeito` aplicado em `int_concentracao_fornecedor_estado` (REQ-11/REQ-12 de [[021-levantamento-outliers-valor-extremo]], fechado em 2026-08-21) — não investigado a fundo aqui por estar fora do escopo desta spec (esta spec é sobre onde o dedup acontece, não sobre qualidade do dado).

## Requirements

### Funcionais

- REQ-1: Quando a requisição a `/api/v1/concentracao-fornecedor` não informar `cod_unidade_gestora`, o sistema DEVE deduplicar por `id_contratado` no SQL (`DISTINCT ON`) antes de ordenar por `rank_estado` e aplicar `LIMIT`.
- REQ-2: Quando a requisição informar `cod_unidade_gestora`, o sistema DEVE manter a query original (sem `DISTINCT ON`) — o grão já é único nesse caminho, dedup seria redundante.
- REQ-3: O sistema DEVE limitar `top_n` a no máximo 100 (`Query(le=100)`), como rede de segurança contra requisições que voltem a pedir a mart inteira.
- REQ-4: O valor default de `top_n` DEVE ser 10, refletindo que a resposta agora é o número real de linhas desejadas, não mais um proxy para "cobrir a mart inteira".

### Não-funcionais

- REQ-5: O frontend (`concentracao-fornecedor.ts`) NÃO DEVE conter lógica de dedup/agregação — a API já entrega o dado pronto para renderização.
- REQ-6: A mudança NÃO DEVE alterar os valores exibidos (mesmos fornecedores, mesmos valores) em relação ao comportamento anterior — validado via comparação de query antes da implementação (ver Investigação, item 3).

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| Onde deduplicar | SQL (`DISTINCT ON (id_contratado)`), não SUM/GROUP BY | `vl_total_fornecedor_estado`/`rank_estado` já vêm pré-agregados por fornecedor pela camada dbt (`int_concentracao_fornecedor_estado`) — dedup é suficiente, agregação de novo seria redundante e arriscaria divergir do valor fonte |
| Contrato do endpoint | `top_n` passa a significar "linhas retornadas" (não mais "linhas buscadas antes do dedup do cliente"); default 10, teto 100 | Fecha a pendência registrada em [[012-eixo-frontend-biblioteca-grafico]] (Casos de borda) sem quebrar consumidores que já usam o default |
| Onde vive a lógica de "top-N distintos" | Só no backend; cliente removido de `concentracao-fornecedor.ts` | Evita buscar a mart inteira por requisição (causa raiz do OOM); mantém o front como camada fina de renderização, consistente com a decisão original da spec 012 |

### Componentes afetados

- `api/app/routers/concentracao_fornecedor.py` — query condicional (`DISTINCT ON` só no caminho sem `cod_unidade_gestora`), `top_n` com `le=100`, default 10.
- `web/src/charts/concentracao-fornecedor.ts` — remove `topFornecedoresDistintos()` e a busca com `top_n=30000`; passa a pedir `top_n=10` direto.

## Casos de borda

- Empate exato em `vl_total_fornecedor_estado` entre dois fornecedores diferentes: `rank_estado` (atribuído rio acima por `RANK()`) determina o desempate, mesma regra já em vigor antes desta mudança — não alterado por esta spec.
- Se um novo consumidor da API pedir `top_n` sem filtro de órgão esperando "a mart inteira" (comportamento antigo via `top_n=30000`), o teto `le=100` vai rejeitar — mudança de contrato deliberada (REQ-3/REQ-4), não um bug.

## Fora do escopo

- Investigar a fundo a mudança de top-1 estadual (`PIATA` → `CENTRO DE INFORMATICA...`) entre 2026-08-20 e 2026-08-21 — parece consistente com o tratamento de `fl_valor_suspeito` de [[021-levantamento-outliers-valor-extremo]], mas não foi confirmado linha a linha aqui.
- Revisitar os outros três endpoints (`escalada-custo`, `contratos-temporal`, `diversidade-vencedores`) — nenhum deles tem o padrão `top_n` alto + dedup client-side; não há indício de que compartilhem esse problema.

## Referências de código

- `api/app/routers/concentracao_fornecedor.py` — query com `DISTINCT ON` condicional.
- `web/src/charts/concentracao-fornecedor.ts` — chamada simplificada, sem dedup client-side.

## Ver também

- [[012-eixo-frontend-biblioteca-grafico]] (pendência original, Casos de borda)
- [[021-levantamento-outliers-valor-extremo]] (tratamento de `fl_valor_suspeito` em `int_concentracao_fornecedor_estado`, provável causa da deriva de dado observada)
