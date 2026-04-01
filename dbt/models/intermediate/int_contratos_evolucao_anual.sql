-- ─────────────────────────────────────────────────────────────────────────────
-- int_contratos_evolucao_anual.sql
-- Evolução de contratos por ano e mês de assinatura
-- ─────────────────────────────────────────────────────────────────────────────

with contratos as (

    select * from {{ ref('stg_contratos') }}

),

mensal as (

    select
        ano_assinatura,
        mes_assinatura,

        count(*)                                        as qt_contratos,
        count(distinct cod_unidade_gestora)             as qt_orgaos_distintos,
        count(distinct id_contratado)                   as qt_fornecedores_distintos,
        count(distinct nm_modalidade)                   as qt_modalidades_distintas,

        coalesce(sum(vl_original), 0)                   as vl_total_original,
        coalesce(sum(vl_atual), 0)                      as vl_total_atual,
        coalesce(sum(vl_aditado), 0)                    as vl_total_aditado,
        coalesce(sum(vl_variacao), 0)                   as vl_total_variacao,

        coalesce(avg(vl_original), 0)                   as vl_medio_contrato

    from contratos
    where ano_assinatura is not null
    group by 1, 2

),

com_acumulado as (

    select
        *,
        sum(qt_contratos)   over (
            partition by ano_assinatura
            order by mes_assinatura
        )                                               as qt_contratos_acumulado_ano,

        sum(vl_total_atual) over (
            partition by ano_assinatura
            order by mes_assinatura
        )                                               as vl_acumulado_ano

    from mensal

)

select * from com_acumulado
order by ano_assinatura, mes_assinatura