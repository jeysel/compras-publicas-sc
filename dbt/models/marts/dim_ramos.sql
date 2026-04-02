-- ─────────────────────────────────────────────────────────────────────────────
-- dim_ramos.sql
-- Dimensão de ramos de atividade por palavras-chave do objeto do contrato
-- ─────────────────────────────────────────────────────────────────────────────

with ramos as (

    select * from {{ ref('int_contratos_por_ramo') }}

)

select
    ramo_atividade,
    qt_contratos,
    qt_fornecedores,
    qt_orgaos,
    vl_total_original,
    vl_total_atual,
    vl_total_aditado,
    vl_medio_contrato,
    vl_maior_contrato,
    rank_por_quantidade,
    rank_por_valor,
    perc_sobre_total_qt,
    perc_sobre_total_valor
from ramos