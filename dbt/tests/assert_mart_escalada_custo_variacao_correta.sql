-- Falha se vl_variacao de qualquer linha divergir de (vl_atual - vl_original)
-- — a métrica oficial de escalada de custo (spec 013/014) precisa ser
-- exatamente essa conta, não vl_aditado.

select
    cod_unidade_gestora,
    nu_contrato,
    vl_original,
    vl_atual,
    vl_variacao,
    (vl_atual - vl_original) as calculo_esperado

from {{ ref('mart_escalada_custo') }}
where round(coalesce(vl_variacao, 0), 2)
    <> round(coalesce(vl_atual, 0) - coalesce(vl_original, 0), 2)
