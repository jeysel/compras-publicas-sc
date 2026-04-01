-- ─────────────────────────────────────────────────────────────────────────────
-- stg_contratos.sql
-- Padronização e tipagem dos dados brutos de contratos públicos de SC
-- Fonte: raw.contratos (Transparência SC — 2016 a 2026)
-- ─────────────────────────────────────────────────────────────────────────────
 
with source as (
 
    select * from {{ ref('contratos') }}
 
),
 
renamed as (
 
    select
        -- ── Unidade Gestora ──────────────────────────────────────────────
        cdunidadegestora                            as cod_unidade_gestora,
        nmunidadegestora                            as nm_unidade_gestora,
        cdgestao                                    as cod_gestao,
        nmgestao                                    as nm_gestao,
 
        -- ── Identificação do Contrato ────────────────────────────────────
        nucontrato                                  as nu_contrato,
        nuprocesso                                  as nu_processo,
        nuedital                                    as nu_edital,
        nudocumentolegal                            as nu_documento_legal,
        nuautorizacaoorgao                          as nu_autorizacao_orgao,
        nutitulo                                    as nu_titulo,
        nuprazo                                     as nu_prazo,
 
        -- ── Contratado (Fornecedor) ──────────────────────────────────────
        idcontratado                                as id_contratado,
        contratado                                  as nm_contratado,
 
        -- ── Descrição do Contrato ────────────────────────────────────────
        resumo                                      as ds_resumo,
        objeto                                      as ds_objeto,
 
        -- ── Datas ────────────────────────────────────────────────────────
        cast(dtinicio       as date)                as dt_inicio,
        cast(dtfim          as date)                as dt_fim,
        cast(dtfimatual     as date)                as dt_fim_atual,
        cast(dtassinatura   as date)                as dt_assinatura,
        cast(dtautorizacao  as date)                as dt_autorizacao,
        cast(dtinclusao     as date)                as dt_inclusao,
        cast(dtlimiteproposta as date)              as dt_limite_proposta,
        cast(dataproposta   as date)                as dt_proposta,
 
        -- ── Prazos (dias) ────────────────────────────────────────────────
        cast(diasoriginais  as integer)             as dias_originais,
        cast(diasaditados   as integer)             as dias_aditados,
        cast(diasatuais     as integer)             as dias_atuais,
 
        -- ── Valores ──────────────────────────────────────────────────────
        cast(vloriginal     as numeric(18, 2))      as vl_original,
        cast(vlatual        as numeric(18, 2))      as vl_atual,
        cast(vladitado      as numeric(18, 2))      as vl_aditado,
        cast(vlgarantia     as numeric(18, 2))      as vl_garantia,
        cast(vlpercgarantia as numeric(5, 2))       as vl_perc_garantia,
        cast(vlpercmulta    as numeric(5, 2))       as vl_perc_multa,
 
        -- ── Classificações ───────────────────────────────────────────────
        situacao                                    as ds_situacao,
        nmmodalidade                                as nm_modalidade,
        detipocontrato                              as de_tipo_contrato,
        detipodocumentolegal                        as de_tipo_documento_legal,
        nmregimeexecucao                            as nm_regime_execucao,
        demulta                                     as de_multa,
        deesptitulo                                 as de_esp_titulo,
 
        -- ── Bem Público ──────────────────────────────────────────────────
        nmbempublico                                as nm_bem_publico,
        bempublico                                  as fl_bem_publico,
 
        -- ── Representantes ───────────────────────────────────────────────
        nmfiscal                                    as nm_fiscal,
        nmrepcredor                                 as nm_rep_credor,
        nmrepinterveniente                          as nm_rep_interveniente,
        nmrepug                                     as nm_rep_ug,
        nminterveniente                             as nm_interveniente,
 
        -- ── Local de Execução ────────────────────────────────────────────
        nmlocalexecucao                             as nm_local_execucao,
 
        -- ── Fiscalizador ─────────────────────────────────────────────────
        cdugfiscalizador                            as cod_ug_fiscalizador,
        ugfiscalizador                              as nm_ug_fiscalizador,
        cdgestaofiscalizador                        as cod_gestao_fiscalizador,
        gestaofiscalizador                          as nm_gestao_fiscalizador,
 
        -- ── Campos derivados ─────────────────────────────────────────────
        extract(year from cast(dtassinatura as date))   as ano_assinatura,
        extract(month from cast(dtassinatura as date))  as mes_assinatura,
        cast(vlatual as numeric(18,2))
            - cast(vloriginal as numeric(18,2))         as vl_variacao
 
    from source
 
)
 
select * from renamed