-- ─────────────────────────────────────────────────────────────────────────────
-- mart_concentracao_fornecedor.sql
-- Concentração de gasto por fornecedor — visão por órgão e por estado (spec 007)
--
-- Distinto de dim_fornecedores.perc_concentracao, que mede concentração
-- INTERNA do fornecedor (maior contrato dele / total dele). Esta mart mede
-- concentração de MERCADO: quanto do gasto do órgão (ou do estado) está
-- concentrado em cada fornecedor.
--
-- Grão (cod_unidade_gestora, id_contratado, ano_assinatura) desde a spec 029
-- (REQ-3) — antes era (cod_unidade_gestora, id_contratado), agregado sobre
-- todo o histórico. Consumidores que precisam do agregado histórico (ex.:
-- endpoint sem filtro de ano) recalculam SUM/rank/perc no próprio router
-- sobre este grão, em vez de usar rank_no_orgao/perc_sobre_total_orgao/
-- rank_estado/perc_sobre_total_estado diretamente — essas colunas só são
-- válidas dentro de um único ano_assinatura.
-- ─────────────────────────────────────────────────────────────────────────────

with orgao as (

    select * from {{ ref('int_concentracao_fornecedor_por_orgao') }}

),

estado as (

    select * from {{ ref('int_concentracao_fornecedor_estado') }}

),

fornecedores as (

    select id_contratado, nm_contratado from {{ ref('dim_fornecedores') }}

),

orgaos as (

    select cod_unidade_gestora, nm_unidade_gestora from {{ ref('dim_orgaos') }}

)

select
    o.cod_unidade_gestora,
    og.nm_unidade_gestora,
    o.id_contratado,
    f.nm_contratado,
    o.ano_assinatura,

    -- ── Concentração dentro do órgão (no ano) ────────────────────────────
    o.vl_total_fornecedor_orgao,
    o.vl_total_orgao,
    o.rank_no_orgao,
    o.perc_sobre_total_orgao,

    -- ── Concentração no estado, todos os órgãos (no ano) ─────────────────
    e.vl_total_fornecedor_estado,
    e.vl_total_estado,
    e.rank_estado,
    e.perc_sobre_total_estado

from orgao          o
left join estado    e  on o.id_contratado       = e.id_contratado
                      and o.ano_assinatura       = e.ano_assinatura
left join fornecedores f on o.id_contratado      = f.id_contratado
left join orgaos     og on o.cod_unidade_gestora = og.cod_unidade_gestora
