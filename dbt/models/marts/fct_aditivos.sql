-- ─────────────────────────────────────────────────────────────────────────────
-- fct_aditivos.sql
-- Fato de aditivos contratuais
--
-- NOTA ARQUITETURAL:
-- O CSV atual do Portal Transparência SC fornece apenas os TOTAIS consolidados
-- dos aditivos por contrato (vl_aditado, dias_aditados).
-- Esta tabela representa os contratos que possuem aditivo, com as métricas
-- disponíveis. A evolução futura seria uma fonte detalhada com 1 linha por
-- aditivo, permitindo análise de cada evento individualmente.
--
-- Regra de negócio:
--   Valor econômico real do contrato = vl_original + vl_aditado = vl_atual
-- ─────────────────────────────────────────────────────────────────────────────

with contratos as (

    select * from {{ ref('stg_contratos') }}
    where vl_aditado > 0
       or dias_aditados > 0

),

fct as (

    select
        -- ── Chaves ───────────────────────────────────────────────────────
        nu_contrato,
        id_contratado,
        cod_unidade_gestora,
        cod_gestao,
        nm_modalidade,

        -- ── Dimensões descritivas ────────────────────────────────────────
        nm_contratado,
        nm_unidade_gestora,
        ds_situacao,
        de_tipo_contrato,

        -- ── Datas do contrato original ───────────────────────────────────
        dt_assinatura,
        dt_inicio,
        dt_fim,
        dt_fim_atual,
        ano_assinatura,
        mes_assinatura,

        -- ── Valores ──────────────────────────────────────────────────────
        vl_original,
        vl_aditado,
        vl_atual,
        vl_variacao,

        -- ── Prazos ───────────────────────────────────────────────────────
        dias_originais,
        dias_aditados,
        dias_atuais,

        -- ── Métricas de aditivo ──────────────────────────────────────────
        vl_variacao * 100.0
            / nullif(vl_original, 0)                as perc_alteracao_valor,

        dias_aditados * 100.0
            / nullif(dias_originais, 0)             as perc_alteracao_prazo,

        case
            when vl_aditado > 0 and dias_aditados > 0
                then 'Valor e Prazo'
            when vl_aditado > 0 and dias_aditados = 0
                then 'Somente Valor'
            when vl_aditado = 0 and dias_aditados > 0
                then 'Somente Prazo'
            else 'Sem alteração'
        end                                         as tp_aditivo,

        case
            when vl_variacao > 0 then 'Acréscimo'
            when vl_variacao < 0 then 'Supressão'
            else 'Sem variação de valor'
        end                                         as tp_variacao_valor,

        case
            when vl_variacao * 100.0 / nullif(vl_original, 0) > 25
                then 'Acima de 25% — Atenção'
            when vl_variacao * 100.0 / nullif(vl_original, 0) > 0
                then 'Até 25%'
            else 'Redução ou sem variação'
        end                                         as faixa_variacao

    from contratos

)

select * from fct