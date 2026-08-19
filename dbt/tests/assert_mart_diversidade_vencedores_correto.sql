-- Falha se qt_fornecedores_distintos ou qt_contratos de qualquer linha da
-- mart divergirem do recálculo direto (count distinct id_contratado / count(*))
-- em stg_contratos para o mesmo (cod_unidade_gestora, nu_processo). Mesma
-- checagem feita manualmente em 3 processos na sessão de implementação
-- (spec 007), agora automatizada pra toda a tabela.

with recalculado as (

    select
        cod_unidade_gestora,
        nu_processo,
        count(distinct id_contratado)  as qt_fornecedores_recalc,
        count(*)                       as qt_contratos_recalc

    from {{ ref('stg_contratos') }}
    where not (
        nu_processo is null
        or trim(nu_processo) = ''
        or regexp_replace(nu_processo, '[^0-9]', '', 'g') = ''
        or regexp_replace(nu_processo, '[^0-9]', '', 'g') ~ '^0+$'
    )
    group by 1, 2

)

select
    m.cod_unidade_gestora,
    m.nu_processo,
    m.qt_fornecedores_distintos,
    r.qt_fornecedores_recalc,
    m.qt_contratos,
    r.qt_contratos_recalc

from {{ ref('mart_diversidade_vencedores') }} m
join recalculado r
  on m.cod_unidade_gestora = r.cod_unidade_gestora
 and m.nu_processo         = r.nu_processo
where m.qt_fornecedores_distintos <> r.qt_fornecedores_recalc
   or m.qt_contratos              <> r.qt_contratos_recalc
