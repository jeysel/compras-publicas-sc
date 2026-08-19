-- ─────────────────────────────────────────────────────────────────────────────
-- int_concentracao_fornecedor_estado.sql
-- Gasto total por fornecedor somando todos os órgãos, com ranking e
-- percentual sobre o total gasto pelo estado (spec 007 — mart_concentracao_fornecedor)
-- ─────────────────────────────────────────────────────────────────────────────

with base as (

    select
        id_contratado,
        sum(vl_atual)                                   as vl_total_fornecedor_estado

    from {{ ref('stg_contratos') }}
    group by 1

),

com_total_estado as (

    select
        *,
        sum(vl_total_fornecedor_estado) over ()         as vl_total_estado,

        rank() over (
            order by vl_total_fornecedor_estado desc
        )                                                as rank_estado

    from base

)

select
    *,
    round(
        vl_total_fornecedor_estado * 100.0 / nullif(vl_total_estado, 0),
        2
    )                                                    as perc_sobre_total_estado

from com_total_estado
