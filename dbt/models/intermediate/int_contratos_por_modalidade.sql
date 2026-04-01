-- ─────────────────────────────────────────────────────────────────────────────
-- int_contratos_por_modalidade.sql
-- Agregação de contratos por modalidade de licitação
-- ─────────────────────────────────────────────────────────────────────────────

with contratos as (

    select * from {{ ref('stg_contratos') }}

),

agregado as (

    select
        coalesce(nm_modalidade, 'Não informado')        as nm_modalidade,

        count(*)                                        as qt_contratos,
        count(distinct cod_unidade_gestora)             as qt_orgaos_distintos,
        count(distinct id_contratado)                   as qt_fornecedores_distintos,

        coalesce(sum(vl_original), 0)                   as vl_total_original,
        coalesce(sum(vl_atual), 0)                      as vl_total_atual,
        coalesce(sum(vl_aditado), 0)                    as vl_total_aditado,
        coalesce(sum(vl_variacao), 0)                   as vl_total_variacao,

        coalesce(avg(vl_original), 0)                   as vl_medio_contrato,
        coalesce(max(vl_atual), 0)                      as vl_maior_contrato,
        coalesce(min(vl_atual), 0)                      as vl_menor_contrato,

        coalesce(
            count(case when vl_aditado > 0 then 1 end) * 100.0
                / nullif(count(*), 0),
            0
        )                                               as perc_contratos_com_aditivo

    from contratos
    group by 1

),

com_ranking as (

    select
        *,
        rank() over (order by qt_contratos desc)        as rank_por_quantidade,
        rank() over (order by vl_total_atual desc)      as rank_por_valor

    from agregado

)

select * from com_ranking