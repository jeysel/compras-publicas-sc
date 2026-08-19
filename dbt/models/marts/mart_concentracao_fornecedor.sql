-- ─────────────────────────────────────────────────────────────────────────────
-- mart_concentracao_fornecedor.sql
-- Concentração de gasto por fornecedor — visão por órgão e por estado (spec 007)
--
-- Distinto de dim_fornecedores.perc_concentracao, que mede concentração
-- INTERNA do fornecedor (maior contrato dele / total dele). Esta mart mede
-- concentração de MERCADO: quanto do gasto do órgão (ou do estado) está
-- concentrado em cada fornecedor.
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

    -- ── Concentração dentro do órgão ─────────────────────────────────────
    o.vl_total_fornecedor_orgao,
    o.vl_total_orgao,
    o.rank_no_orgao,
    o.perc_sobre_total_orgao,

    -- ── Concentração no estado (todos os órgãos) ─────────────────────────
    e.vl_total_fornecedor_estado,
    e.vl_total_estado,
    e.rank_estado,
    e.perc_sobre_total_estado

from orgao          o
left join estado    e  on o.id_contratado       = e.id_contratado
left join fornecedores f on o.id_contratado      = f.id_contratado
left join orgaos     og on o.cod_unidade_gestora = og.cod_unidade_gestora
