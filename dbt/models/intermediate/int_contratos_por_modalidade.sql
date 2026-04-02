-- ─────────────────────────────────────────────────────────────────────────────
-- int_contratos_por_modalidade.sql
-- Agregação de contratos por modalidade de licitação
-- Pregão Eletrônico das Leis 10.520/2002 e 14.133/2021 são concatenados
-- pois representam a mesma modalidade em legislações diferentes
-- ─────────────────────────────────────────────────────────────────────────────

with contratos as (

    select * from {{ ref('stg_contratos') }}

),

normalizado as (

    select
        *,
        case
            when nm_modalidade in (
                'Pregão Eletrônico - Lei 10.520',
                'Pregão Eletrônico Lei 14.133'
            ) then 'Pregão Eletrônico - Leis 10.520/2002 e 14.133/2021'
            when nm_modalidade in (
                'Pregão Presencial - Lei 10.520',
                'Pregão Presencial Lei 14.133'
            ) then 'Pregão Presencial - Leis 10.520/2002 e 14.133/2021'
            when nm_modalidade in (
                'Dispensa de Licitação - Lei 8.666',
                'Dispensa de Licitação - Lei 14.133'
            ) then 'Dispensa de Licitação - Leis 8.666/1993 e 14.133/2021'
            when nm_modalidade in (
                'Licitação Inexigível - Lei 8.666',
                'Licitação Inexigível - Lei 14.133'
            ) then 'Licitação Inexigível - Leis 8.666/1993 e 14.133/2021'
            when nm_modalidade in (
                'Dispensa de Licitação por Valor - Lei 8.666'
            ) then 'Dispensa por Valor - Lei 8.666/1993'
            else coalesce(nm_modalidade, 'Não informado')
        end as nm_modalidade_norm

    from contratos

),

agregado as (

    select
        nm_modalidade_norm                              as nm_modalidade,

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

    from normalizado
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