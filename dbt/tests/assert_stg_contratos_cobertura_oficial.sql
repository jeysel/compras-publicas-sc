-- Falha se qualquer contrato de stg_contratos tiver ano_assinatura antes de
-- 2016 — a fronteira de cobertura oficial (spec 034). 1994-2015 é cauda
-- documentada: continua em raw.contratos e no seed, mas é cortada na CTE
-- cobertura_oficial de stg_contratos.sql e não pode vazar pras marts.

select
    nu_contrato,
    cod_unidade_gestora,
    dt_assinatura,
    ano_assinatura

from {{ ref('stg_contratos') }}
where ano_assinatura < 2016
