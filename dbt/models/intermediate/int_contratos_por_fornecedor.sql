-- ─────────────────────────────────────────────────────────────────────────────
-- int_contratos_por_fornecedor.sql
-- Agregação de contratos por fornecedor (contratado)
-- ─────────────────────────────────────────────────────────────────────────────

with contratos as (

    select * from {{ ref('stg_contratos') }}

),

agregado as (

    select
        id_contratado,
        mode() within group (order by nm_contratado)    as nm_contratado, -- Para utilizar o nome mais utilizado para o fornecedor. As UGs cadastraram o fornecedor com nome diferente

        count(*)                                        as qt_contratos,
        count(distinct cod_unidade_gestora)             as qt_orgaos_distintos,
        count(distinct nm_modalidade)                   as qt_modalidades_distintas,

        coalesce(sum(vl_original), 0)                   as vl_total_original,
        coalesce(sum(vl_atual), 0)                      as vl_total_atual,
        coalesce(sum(vl_aditado), 0)                    as vl_total_aditado,
        coalesce(sum(vl_variacao), 0)                   as vl_total_variacao,

        coalesce(avg(vl_original), 0)                   as vl_medio_contrato,
        coalesce(max(vl_atual), 0)                      as vl_maior_contrato,
        coalesce(min(vl_atual), 0)                      as vl_menor_contrato,

        min(dt_assinatura)                              as dt_primeiro_contrato,
        max(dt_assinatura)                              as dt_ultimo_contrato,

        coalesce(
            max(vl_atual) / nullif(sum(vl_atual), 0) * 100,
            0
        )                                               as perc_concentracao

    from contratos
    group by 1

)

select * from agregado