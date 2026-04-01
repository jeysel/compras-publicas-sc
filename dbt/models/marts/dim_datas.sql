-- ─────────────────────────────────────────────────────────────────────────────
-- dim_datas.sql
-- Dimensão calendário — lê da tabela raw.dim_datas populada pela
-- procedure raw.sp_popula_dim_datas() executada no 01_init.sql
-- Período: 2015-01-01 a 2030-12-31 (gerado independente dos contratos)
-- ─────────────────────────────────────────────────────────────────────────────

with source as (

    select * from {{ source('raw', 'dim_datas') }}

),

dim as (

    select
        dt_data,
        ano,
        mes,
        dia,
        trimestre,
        semana_ano,
        dia_semana_num,
        nm_mes,
        nm_mes_abrev,
        nm_dia_semana,
        ano_mes,
        nm_trimestre,
        sigla_trimestre,
        fl_fim_de_semana,
        primeiro_dia_mes,
        ultimo_dia_mes

    from source

)

select * from dim