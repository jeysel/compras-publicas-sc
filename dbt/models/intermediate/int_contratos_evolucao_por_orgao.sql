-- ─────────────────────────────────────────────────────────────────────────────
-- int_contratos_evolucao_por_orgao.sql
-- Evolução de contratos por ano/mês de assinatura, recortada por órgão
-- (spec 007 — recorte que faltava em int_contratos_evolucao_anual).
-- ─────────────────────────────────────────────────────────────────────────────

with contratos as (

    select * from {{ ref('stg_contratos') }}

),

mensal as (

    select
        ano_assinatura,
        mes_assinatura,
        cod_unidade_gestora,
        mode() within group (order by nm_unidade_gestora) as nm_unidade_gestora,

        count(*)                                        as qt_contratos,
        count(distinct id_contratado)                   as qt_fornecedores_distintos,

        coalesce(sum(vl_original), 0)                   as vl_total_original,
        coalesce(sum(vl_atual), 0)                      as vl_total_atual,
        coalesce(sum(vl_variacao), 0)                   as vl_total_variacao

    from contratos
    where ano_assinatura is not null
      -- exclui linhas com fl_valor_suspeito=true (spec 021) — mesmo motivo
      -- de int_contratos_evolucao_anual.sql, filtro precisa vir antes do SUM.
      and coalesce(fl_valor_suspeito, false) = false
    group by 1, 2, 3

)

select * from mensal
order by cod_unidade_gestora, ano_assinatura, mes_assinatura
