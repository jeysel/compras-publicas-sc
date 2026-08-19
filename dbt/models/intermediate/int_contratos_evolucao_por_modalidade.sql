-- ─────────────────────────────────────────────────────────────────────────────
-- int_contratos_evolucao_por_modalidade.sql
-- Evolução de contratos por ano/mês de assinatura, recortada por modalidade
-- (spec 007 — recorte que faltava em int_contratos_evolucao_anual).
-- nm_modalidade não é normalizada aqui (fica bruta, como em stg_contratos) —
-- a normalização Lei 8.666/14.133 é responsabilidade de
-- int_contratos_por_modalidade, um propósito diferente deste model.
-- ─────────────────────────────────────────────────────────────────────────────

with contratos as (

    select * from {{ ref('stg_contratos') }}

),

mensal as (

    select
        ano_assinatura,
        mes_assinatura,
        nm_modalidade,

        count(*)                                        as qt_contratos,
        count(distinct cod_unidade_gestora)             as qt_orgaos_distintos,

        coalesce(sum(vl_original), 0)                   as vl_total_original,
        coalesce(sum(vl_atual), 0)                      as vl_total_atual,
        coalesce(sum(vl_variacao), 0)                   as vl_total_variacao

    from contratos
    where ano_assinatura is not null
    group by 1, 2, 3

)

select * from mensal
order by nm_modalidade, ano_assinatura, mes_assinatura
