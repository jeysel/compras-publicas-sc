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

        -- Normalização de modalidade (mesmo CASE de int_contratos_por_modalidade.sql,
        -- spec 025) — fatia variantes de lei da mesma modalidade em uma única
        -- categoria, pra agregação por modalidade bater com dim_modalidades.
        case
            when nm_modalidade in (
                'Pregão Eletrônico - Lei 10.520',
                'Pregão Eletrônico Lei 14.133'
            ) then 'Pregão Eletrônico - Leis 10.520/2002 e 14.133/2021'
            when nm_modalidade in (
                'Pregão Presencial - Lei 10.520',
                'Pregão Presencial - Lei 14.133'
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
        end                                              as nm_modalidade_norm,

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
