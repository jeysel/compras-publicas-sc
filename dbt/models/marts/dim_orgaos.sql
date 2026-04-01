-- ─────────────────────────────────────────────────────────────────────────────
-- dim_orgaos.sql
-- Dimensão de unidades gestoras (órgãos públicos)
-- ─────────────────────────────────────────────────────────────────────────────

with orgaos as (

    select * from {{ ref('int_contratos_por_orgao') }}

),

dim as (

    select
        cod_unidade_gestora,
        nm_unidade_gestora,
        cod_gestao,
        nm_gestao,

        qt_contratos,
        qt_fornecedores_distintos,

        vl_total_original,
        vl_total_atual,
        vl_total_aditado,
        vl_total_variacao,
        vl_medio_contrato,
        vl_maior_contrato,
        vl_menor_contrato,

        dt_primeiro_contrato,
        dt_ultimo_contrato,

        -- Ranking por valor total
        rank() over (order by vl_total_atual desc)      as rank_por_valor,

        -- Ranking por quantidade de contratos
        rank() over (order by qt_contratos desc)        as rank_por_quantidade,

        -- Descrição da situação de aditivo
        case
            when vl_total_aditado = 0   then 'Sem aditivo'
            when vl_total_aditado > 0   then 'Com acréscimo'
            when vl_total_aditado < 0   then 'Com supressão'
        end                                             as ds_situacao_aditivo,

        -- Perfil de contratação do órgão
        case
            when qt_contratos >= 1000   then 'Alto volume'
            when qt_contratos >= 100    then 'Médio volume'
            when qt_contratos >= 10     then 'Baixo volume'
            else 'Esporádico'
        end                                             as ds_perfil_contratacao

    from orgaos

)

select * from dim