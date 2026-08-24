-- ─────────────────────────────────────────────────────────────────────────────
-- mart_diversidade_vencedores.sql
-- Diversidade de vencedores por processo licitatório (spec 007). Mede
-- quantos fornecedores DIFERENTES venceram contratos vinculados ao mesmo
-- processo (cod_unidade_gestora, nu_processo) — não quantos participaram/
-- concorreram (esse dado não existe na fonte). Grão: (cod_unidade_gestora,
-- nu_processo).
-- ─────────────────────────────────────────────────────────────────────────────

with processos as (

    select * from {{ ref('int_processos') }}

),

com_classificacao as (

    select
        cod_unidade_gestora,
        nm_unidade_gestora,
        nu_processo,

        qt_contratos,
        qt_fornecedores_distintos,
        qt_modalidades_distintas,

        vl_total_original,
        vl_total_atual,
        vl_total_variacao,

        dt_primeiro_contrato,
        dt_ultimo_contrato,
        extract(year from dt_primeiro_contrato)          as ano_abertura,

        case
            when qt_fornecedores_distintos = 1  then 'Fornecedor único'
            when qt_fornecedores_distintos > 1  then 'Múltiplos fornecedores'
        end                                              as ds_diversidade,

        rank() over (
            order by qt_fornecedores_distintos desc
        )                                                as rank_por_diversidade

    from processos

)

select * from com_classificacao
