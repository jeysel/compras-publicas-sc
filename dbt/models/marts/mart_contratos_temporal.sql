-- ─────────────────────────────────────────────────────────────────────────────
-- mart_contratos_temporal.sql
-- Série temporal de valor contratado (spec 007) — estende
-- int_contratos_evolucao_anual (mantido como está, reaproveitado aqui via
-- ref, não recriado) com o que faltava (achado spec 013):
--   1. variação ano a ano (mesmo mês, ano corrente vs. ano-1)
--   2. média móvel de 3 anos
--   3. recorte por órgão e por modalidade na mesma tabela
--
-- Grão: (tp_recorte, ano_assinatura, mes_assinatura, cod_unidade_gestora,
-- nm_modalidade) — cod_unidade_gestora/nm_modalidade só preenchidos no
-- recorte a que pertencem; nulos nos outros dois (não é dado ausente, é
-- "não se aplica a este recorte").
-- ─────────────────────────────────────────────────────────────────────────────

with geral as (

    select
        'Geral'                                         as tp_recorte,
        ano_assinatura,
        mes_assinatura,
        cast(null as varchar)                           as cod_unidade_gestora,
        cast(null as varchar)                           as nm_unidade_gestora,
        cast(null as varchar)                           as nm_modalidade,

        qt_contratos,
        vl_total_original,
        vl_total_atual,
        vl_total_variacao,

        qt_contratos_acumulado_ano,
        vl_acumulado_ano

    from {{ ref('int_contratos_evolucao_anual') }}

),

por_orgao as (

    select
        'Órgão'                                         as tp_recorte,
        ano_assinatura,
        mes_assinatura,
        cod_unidade_gestora,
        nm_unidade_gestora,
        cast(null as varchar)                           as nm_modalidade,

        qt_contratos,
        vl_total_original,
        vl_total_atual,
        vl_total_variacao,

        cast(null as bigint)                            as qt_contratos_acumulado_ano,
        cast(null as numeric)                           as vl_acumulado_ano

    from {{ ref('int_contratos_evolucao_por_orgao') }}

),

por_modalidade as (

    select
        'Modalidade'                                    as tp_recorte,
        ano_assinatura,
        mes_assinatura,
        cast(null as varchar)                           as cod_unidade_gestora,
        cast(null as varchar)                           as nm_unidade_gestora,
        nm_modalidade,

        qt_contratos,
        vl_total_original,
        vl_total_atual,
        vl_total_variacao,

        cast(null as bigint)                            as qt_contratos_acumulado_ano,
        cast(null as numeric)                           as vl_acumulado_ano

    from {{ ref('int_contratos_evolucao_por_modalidade') }}

),

unificado as (

    select * from geral
    union all
    select * from por_orgao
    union all
    select * from por_modalidade

),

com_ano_anterior as (

    select
        *,

        -- LAG() para o valor do mesmo mês no ano anterior (dentro do mesmo
        -- recorte/órgão/modalidade). Guardado contra buraco de ano: só
        -- aceita o valor do LAG se o ano do LAG for exatamente ano-1 — sem
        -- essa checagem, LAG() pularia silenciosamente pro ano disponível
        -- mais próximo quando um ano estiver ausente no recorte (comum em
        -- Órgão/Modalidade, que têm cobertura temporal mais esparsa que o
        -- Geral), reportando uma "variação ano a ano" que na verdade seria
        -- de 2+ anos de distância.
        lag(ano_assinatura) over (
            partition by tp_recorte, cod_unidade_gestora, nm_modalidade, mes_assinatura
            order by ano_assinatura
        )                                                as _ano_lag,

        lag(vl_total_atual) over (
            partition by tp_recorte, cod_unidade_gestora, nm_modalidade, mes_assinatura
            order by ano_assinatura
        )                                                as _vl_lag,

        -- Média móvel de 3 anos: RANGE (não ROWS) sobre ano_assinatura —
        -- soma pelo valor do ano, não pela posição da linha. Isso garante
        -- que, se houver buraco (ano sem contrato no recorte), a janela
        -- ainda reflete os últimos 3 anos-calendário reais, não as últimas
        -- 3 linhas existentes (que poderiam abranger 5+ anos de distância).
        avg(vl_total_atual) over (
            partition by tp_recorte, cod_unidade_gestora, nm_modalidade, mes_assinatura
            order by ano_assinatura
            range between 2 preceding and current row
        )                                                as vl_media_movel_3anos

    from unificado

),

final as (

    select
        tp_recorte,
        ano_assinatura,
        mes_assinatura,
        cod_unidade_gestora,
        nm_unidade_gestora,
        nm_modalidade,

        qt_contratos,
        vl_total_original,
        vl_total_atual,
        vl_total_variacao,

        qt_contratos_acumulado_ano,
        vl_acumulado_ano,

        case when _ano_lag = ano_assinatura - 1 then _vl_lag end
                                                         as vl_mesmo_mes_ano_anterior,

        case when _ano_lag = ano_assinatura - 1
             then vl_total_atual - _vl_lag
        end                                              as vl_variacao_ano_anterior,

        case when _ano_lag = ano_assinatura - 1 and _vl_lag <> 0
             then round(
                 (vl_total_atual - _vl_lag) * 100.0 / _vl_lag,
                 2
             )
        end                                              as perc_variacao_ano_anterior,

        round(vl_media_movel_3anos, 2)                   as vl_media_movel_3anos

    from com_ano_anterior

)

select * from final
