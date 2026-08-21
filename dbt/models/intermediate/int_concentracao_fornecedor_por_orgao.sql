-- ─────────────────────────────────────────────────────────────────────────────
-- int_concentracao_fornecedor_por_orgao.sql
-- Gasto total por fornecedor dentro de cada órgão, com ranking e percentual
-- sobre o total gasto pelo órgão (spec 007 — mart_concentracao_fornecedor)
-- ─────────────────────────────────────────────────────────────────────────────

with base as (

    select
        cod_unidade_gestora,
        id_contratado,
        sum(vl_atual)                                   as vl_total_fornecedor_orgao

    from {{ ref('stg_contratos') }}
    -- exclui linhas com fl_valor_suspeito=true (spec 021, REQ-11): grão
    -- deste model já é agregado (SUM por órgão/fornecedor), filtro
    -- client-side é impossível depois daqui — precisa acontecer antes do
    -- SUM, mesmo padrão já validado em int_contratos_evolucao_*.
    where coalesce(fl_valor_suspeito, false) = false
    group by 1, 2

),

com_total_orgao as (

    select
        *,
        sum(vl_total_fornecedor_orgao) over (
            partition by cod_unidade_gestora
        )                                                as vl_total_orgao,

        rank() over (
            partition by cod_unidade_gestora
            order by vl_total_fornecedor_orgao desc
        )                                                as rank_no_orgao

    from base

)

select
    *,
    round(
        vl_total_fornecedor_orgao * 100.0 / nullif(vl_total_orgao, 0),
        2
    )                                                    as perc_sobre_total_orgao

from com_total_orgao
