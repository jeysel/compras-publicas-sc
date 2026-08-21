-- ─────────────────────────────────────────────────────────────────────────────
-- mart_escalada_custo.sql
-- Escalada de custo por aditivo (spec 007) — mart dedicada, grão de contrato
-- (cod_unidade_gestora, nu_contrato), agregável por órgão/modalidade/período
-- pelo consumidor. vl_variacao (vl_atual - vl_original) é a métrica oficial
-- (spec 013/014); fl_aditivo_inconsistente é exposta como coluna de
-- contexto, não usada como filtro aqui — decisão de excluir ou não fica
-- com quem consome a mart.
-- ─────────────────────────────────────────────────────────────────────────────

with contratos as (

    select * from {{ ref('stg_contratos') }}

),

com_variacao as (

    select
        -- ── Chaves ───────────────────────────────────────────────────────
        cod_unidade_gestora,
        nu_contrato,

        -- ── Dimensões de agregação (órgão/modalidade/período) ─────────────
        nm_unidade_gestora,
        nm_modalidade,
        ano_assinatura,
        mes_assinatura,
        dt_assinatura,

        -- ── Contexto ─────────────────────────────────────────────────────
        id_contratado,
        nm_contratado,

        -- ── Métrica oficial de escalada de valor ────────────────────────
        vl_original,
        vl_atual,
        vl_variacao,
        coalesce(vl_variacao, 0) * 100.0
            / nullif(vl_original, 0)                    as perc_variacao,

        -- ── Equivalente em dias ──────────────────────────────────────────
        dias_originais,
        dias_atuais,
        dias_atuais - dias_originais                    as dias_variacao,

        -- ── Descrição de negócio ─────────────────────────────────────────
        case
            when vl_variacao > 0  then 'Acréscimo'
            when vl_variacao < 0  then 'Decréscimo'
            else 'Sem variação'
        end                                              as tp_variacao,

        -- ── Sinal de qualidade (contexto, não filtro — spec 013/014) ─────
        fl_aditivo_inconsistente,

        -- ── Valor implausível (contexto, não filtro — spec 021) ──────────
        fl_valor_suspeito

    from contratos

)

select * from com_variacao
