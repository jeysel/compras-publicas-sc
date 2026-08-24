-- ─────────────────────────────────────────────────────────────────────────────
-- int_contratos_por_orgao.sql
-- Agregação de contratos por unidade gestora e gestão
-- ─────────────────────────────────────────────────────────────────────────────

with contratos as (

    select * from {{ ref('stg_contratos') }}

),

agregado as (

    select
        cod_unidade_gestora,
        mode() within group (order by nm_unidade_gestora) as nm_unidade_gestora,
        cod_gestao,
        mode() within group (order by nm_gestao)          as nm_gestao,

        count(*)                                        as qt_contratos,
        count(distinct id_contratado)                   as qt_fornecedores_distintos,

        coalesce(sum(vl_original), 0)                   as vl_total_original,
        coalesce(sum(vl_atual), 0)                      as vl_total_atual,
        coalesce(sum(vl_aditado), 0)                    as vl_total_aditado,
        coalesce(sum(vl_variacao), 0)                   as vl_total_variacao,

        coalesce(avg(vl_original), 0)                   as vl_medio_contrato,
        coalesce(max(vl_atual), 0)                      as vl_maior_contrato,
        coalesce(min(vl_atual), 0)                      as vl_menor_contrato,

        min(dt_assinatura)                              as dt_primeiro_contrato,
        max(dt_assinatura)                              as dt_ultimo_contrato

    from contratos
    -- exclui linhas com fl_valor_suspeito=true (spec 021/026) — mesmo padrão
    -- já usado em int_contratos_evolucao_por_orgao.sql; sem este filtro,
    -- dim_orgaos.rank_por_valor/ds_perfil_contratacao ficam distorcidos por
    -- outliers de valor implausível (spec 026, achado de ~R$ 32,5 bi de gap).
    where coalesce(fl_valor_suspeito, false) = false
    group by 1, 3

)

select * from agregado