-- ─────────────────────────────────────────────────────────────────────────────
-- stg_dim_datas.sql
-- Spinha de datas gerada via dbt_utils.date_spine (spec 020) — substitui a
-- dependência de raw.dim_datas (procedure raw.sp_popula_dim_datas() em
-- 01_init.sql, mecanismo incompatível com produção).
-- Período: 2015-01-01 a 2030-12-31 (mesmo período do gerador anterior).
-- ─────────────────────────────────────────────────────────────────────────────

-- end_date é tratado como exclusivo pela macro (row_number - 1 offsets),
-- por isso o argumento é 2031-01-01 para incluir 2030-12-31 no resultado.
with spine as (

    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2015-01-01' as date)",
        end_date="cast('2031-01-01' as date)"
    ) }}

)

select date_day as dt_data from spine
