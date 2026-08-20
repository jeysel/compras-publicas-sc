-- ─────────────────────────────────────────────────────────────────────────────
-- dim_datas.sql
-- Dimensão calendário — colunas calculadas a partir da spinha de datas
-- gerada em stg_dim_datas (dbt_utils.date_spine, spec 020).
-- Período: 2015-01-01 a 2030-12-31 (gerado independente dos contratos)
-- ─────────────────────────────────────────────────────────────────────────────

with source as (

    select * from {{ ref('stg_dim_datas') }}

),

dim as (

    select
        dt_data,
        extract(year    from dt_data)::integer          as ano,
        extract(month   from dt_data)::integer          as mes,
        extract(day     from dt_data)::integer          as dia,
        extract(quarter from dt_data)::integer          as trimestre,
        extract(week    from dt_data)::integer          as semana_ano,
        extract(dow     from dt_data)::integer          as dia_semana_num,
        to_char(dt_data, 'TMMonth')                     as nm_mes,
        to_char(dt_data, 'TMMon')                       as nm_mes_abrev,
        to_char(dt_data, 'TMDay')                        as nm_dia_semana,
        to_char(dt_data, 'YYYY-MM')                     as ano_mes,
        to_char(dt_data, 'Q"º Tri"')                     as nm_trimestre,
        case extract(quarter from dt_data)::integer
            when 1 then 'Q1'
            when 2 then 'Q2'
            when 3 then 'Q3'
            when 4 then 'Q4'
        end                                              as sigla_trimestre,
        extract(dow from dt_data) in (0, 6)             as fl_fim_de_semana,
        date_trunc('month', dt_data)::date              as primeiro_dia_mes,
        (date_trunc('month', dt_data)
            + interval '1 month - 1 day')::date         as ultimo_dia_mes

    from source

)

select * from dim