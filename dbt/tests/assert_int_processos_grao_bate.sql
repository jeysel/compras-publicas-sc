-- Falha se a soma de qt_contratos agrupados em int_processos não bater
-- exatamente com o total de linhas elegíveis (não-placeholder) recalculado
-- direto em stg_contratos. Reconfirmado nesta sessão: 71.559 linhas
-- elegíveis, 43.953 processos únicos (spec 007).

with elegiveis as (

    select count(*) as qt_linhas
    from {{ ref('stg_contratos') }}
    where not (
        nu_processo is null
        or trim(nu_processo) = ''
        or regexp_replace(nu_processo, '[^0-9]', '', 'g') = ''
        or regexp_replace(nu_processo, '[^0-9]', '', 'g') ~ '^0+$'
    )

),

agrupado as (

    select coalesce(sum(qt_contratos), 0) as qt_linhas
    from {{ ref('int_processos') }}

)

select
    elegiveis.qt_linhas as qt_elegiveis,
    agrupado.qt_linhas   as qt_agrupado
from elegiveis, agrupado
where elegiveis.qt_linhas <> agrupado.qt_linhas
