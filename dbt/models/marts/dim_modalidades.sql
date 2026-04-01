-- ─────────────────────────────────────────────────────────────────────────────
-- dim_modalidades.sql
-- Dimensão de contratos por modalidades de licitação
-- ─────────────────────────────────────────────────────────────────────────────

with modalidades as (

    select * from {{ ref('int_contratos_por_modalidade') }}

),

dim as (

    select
        nm_modalidade,

        qt_contratos,
        qt_orgaos_distintos,
        qt_fornecedores_distintos,

        vl_total_original,
        vl_total_atual,
        vl_total_aditado,
        vl_total_variacao,
        vl_medio_contrato,
        vl_maior_contrato,
        vl_menor_contrato,

        perc_contratos_com_aditivo,

        rank_por_quantidade,
        rank_por_valor,

        -- Percentual sobre o total geral de contratos
        qt_contratos * 100.0
            / nullif(sum(qt_contratos) over (), 0)  as perc_sobre_total_qt,

        -- Percentual sobre o valor total geral
        vl_total_atual * 100.0
            / nullif(sum(vl_total_atual) over (), 0) as perc_sobre_total_valor

    from modalidades

)

select * from dim