-- ─────────────────────────────────────────────────────────────────────────────
-- fct_contratos.sql
-- Tabela fato principal — todos os contratos com métricas enriquecidas
-- ─────────────────────────────────────────────────────────────────────────────

with contratos as (

    select * from {{ ref('stg_contratos') }}

),

datas as (

    select
        dt_data,
        nm_mes,
        nm_trimestre,
        sigla_trimestre,
        fl_fim_de_semana,
        primeiro_dia_mes,
        ultimo_dia_mes
    from {{ ref('dim_datas') }}

),

fornecedores as (

    select
        id_contratado,
        rank_por_valor          as rank_fornecedor_por_valor,
        rank_por_quantidade     as rank_fornecedor_por_quantidade,
        porte_fornecedor,
        ds_situacao_aditivo     as ds_situacao_aditivo_fornecedor,
        qt_contratos            as qt_total_contratos_fornecedor
    from {{ ref('dim_fornecedores') }}

),

orgaos as (

    select
        cod_unidade_gestora,
        cod_gestao,
        rank_por_valor          as rank_orgao_por_valor,
        rank_por_quantidade     as rank_orgao_por_quantidade,
        ds_perfil_contratacao
    from {{ ref('dim_orgaos') }}

),

fct as (

    select
        -- ── Chaves ───────────────────────────────────────────────────────
        c.nu_contrato,
        c.id_contratado,
        c.cod_unidade_gestora,
        c.cod_gestao,
        c.nm_modalidade,

        -- ── Dimensões descritivas ────────────────────────────────────────
        c.nm_contratado,
        c.nm_unidade_gestora,
        c.nm_gestao,
        c.ds_situacao,
        c.de_tipo_contrato,
        c.nm_regime_execucao,
        c.nm_local_execucao,
        c.ds_objeto,

        -- ── Datas ────────────────────────────────────────────────────────
        c.dt_assinatura,
        c.dt_inicio,
        c.dt_fim,
        c.dt_fim_atual,
        c.ano_assinatura,
        c.mes_assinatura,

        -- ── Prazos ───────────────────────────────────────────────────────
        c.dias_originais,
        c.dias_aditados,
        c.dias_atuais,

        -- ── Valores ──────────────────────────────────────────────────────
        c.vl_original,
        c.vl_atual,
        coalesce(c.vl_aditado, 0)   as vl_aditado,
        c.vl_garantia,
        c.vl_variacao,

        -- ── Descrições de negócio ─────────────────────────────────────────
        case
            when c.vl_variacao > 0  then 'Acréscimo'
            when c.vl_variacao < 0  then 'Decréscimo'
            else 'Sem variação'
        end                                             as tp_variacao,

        case
            when coalesce(c.vl_aditado, 0) > 0  then 'Com acréscimo'
            when coalesce(c.vl_aditado, 0) < 0  then 'Com supressão'
            else 'Sem aditivo'
        end                                             as ds_situacao_aditivo,

        case
            when coalesce(c.vl_aditado, 0) > 0 then true
            else false
        end                                             as fl_possui_aditivo,

        case
            when c.dias_aditados > 0    then 'Prazo prorrogado'
            when c.dias_aditados < 0    then 'Prazo reduzido'
            else 'Prazo sem alteração'
        end                                             as ds_situacao_prazo,

        coalesce(c.vl_variacao, 0) * 100.0
            / nullif(c.vl_original, 0)                  as perc_variacao,

        -- ── Enriquecimento do fornecedor ─────────────────────────────────
        f.rank_fornecedor_por_valor,
        f.rank_fornecedor_por_quantidade,
        f.porte_fornecedor,
        f.ds_situacao_aditivo_fornecedor,
        f.qt_total_contratos_fornecedor,

        -- ── Enriquecimento do órgão ──────────────────────────────────────
        o.rank_orgao_por_valor,
        o.rank_orgao_por_quantidade,
        o.ds_perfil_contratacao,

        -- ── Enriquecimento da data de assinatura ─────────────────────────
        d.nm_mes,
        d.nm_trimestre,
        d.sigla_trimestre,
        d.primeiro_dia_mes,
        d.ultimo_dia_mes

    from contratos      c
    left join datas        d on c.dt_assinatura       = d.dt_data
    left join fornecedores f on c.id_contratado       = f.id_contratado
    left join orgaos       o on c.cod_unidade_gestora = o.cod_unidade_gestora
                             and c.cod_gestao         = o.cod_gestao

)

select * from fct