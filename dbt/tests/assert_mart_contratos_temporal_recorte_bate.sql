-- Falha se a soma de qt_contratos dos recortes 'Órgão' ou 'Modalidade', pra
-- um dado (ano_assinatura, mes_assinatura), não bater com o valor do
-- recorte 'Geral' no mesmo período — os três recortes vêm do mesmo
-- stg_contratos, só particionado diferente; o total tem que ser idêntico.

with geral as (

    select ano_assinatura, mes_assinatura, qt_contratos
    from {{ ref('mart_contratos_temporal') }}
    where tp_recorte = 'Geral'

),

soma_orgao as (

    select ano_assinatura, mes_assinatura, sum(qt_contratos) as qt_soma
    from {{ ref('mart_contratos_temporal') }}
    where tp_recorte = 'Órgão'
    group by 1, 2

),

soma_modalidade as (

    select ano_assinatura, mes_assinatura, sum(qt_contratos) as qt_soma
    from {{ ref('mart_contratos_temporal') }}
    where tp_recorte = 'Modalidade'
    group by 1, 2

)

select
    g.ano_assinatura,
    g.mes_assinatura,
    g.qt_contratos       as qt_geral,
    so.qt_soma           as qt_soma_orgao,
    sm.qt_soma           as qt_soma_modalidade

from geral g
join soma_orgao      so on g.ano_assinatura = so.ano_assinatura and g.mes_assinatura = so.mes_assinatura
join soma_modalidade sm on g.ano_assinatura = sm.ano_assinatura and g.mes_assinatura = sm.mes_assinatura
where g.qt_contratos <> so.qt_soma
   or g.qt_contratos <> sm.qt_soma
