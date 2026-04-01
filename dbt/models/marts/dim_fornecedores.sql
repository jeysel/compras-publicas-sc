-- ─────────────────────────────────────────────────────────────────────────────
-- dim_fornecedores.sql
-- Dimensão de fornecedores (contratados)
-- ─────────────────────────────────────────────────────────────────────────────

with fornecedores as (

    select * from {{ ref('int_contratos_por_fornecedor') }}

),

dim as (

    select
        id_contratado,
        nm_contratado,

        qt_contratos,
        qt_orgaos_distintos,
        qt_modalidades_distintas,

        vl_total_original,
        vl_total_atual,
        vl_total_aditado,
        vl_total_variacao,
        vl_medio_contrato,
        vl_maior_contrato,
        vl_menor_contrato,

        perc_concentracao,

        dt_primeiro_contrato,
        dt_ultimo_contrato,

        -- Ranking por valor total contratado
        rank() over (order by vl_total_atual desc)      as rank_por_valor,

        -- Ranking por quantidade de contratos
        rank() over (order by qt_contratos desc)        as rank_por_quantidade,

        -- Classificação por porte (baseado no valor total)
        case
            when vl_total_atual >= 10000000  then 'Grande'
            when vl_total_atual >= 1000000   then 'Médio'
            when vl_total_atual >= 100000    then 'Pequeno'
            else 'Micro'
        end                                             as porte_fornecedor,

        -- Descrição da situação de aditivo
        case
            when vl_total_aditado = 0   then 'Sem aditivo'
            when vl_total_aditado > 0   then 'Com acréscimo'
            when vl_total_aditado < 0   then 'Com supressão'
        end                                             as ds_situacao_aditivo,

        -- Descrição da variação de valor
        case
            when vl_total_variacao = 0  then 'Sem variação'
            when vl_total_variacao > 0  then 'Valor aumentou'
            when vl_total_variacao < 0  then 'Valor reduziu'
        end                                             as ds_variacao_valor

    from fornecedores

)

select * from dim