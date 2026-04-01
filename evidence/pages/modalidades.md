---
title: Modalidades de Licitação
---

# Modalidades de Licitação

Análise das modalidades utilizadas nas contratações públicas de Santa Catarina.

---

## Visão Geral

```sql kpis_modalidades
select
    count(*)                    as total_modalidades,
    sum(qt_contratos)           as total_contratos,
    sum(vl_total_atual)         as vl_total
from compras.dim_modalidades
```

<BigValue data={kpis_modalidades} value="total_modalidades" title="Total de Modalidades" fmt="num0"/>
<BigValue data={kpis_modalidades} value="total_contratos"   title="Total de Contratos"   fmt="num1k"/>
<BigValue data={kpis_modalidades} value="vl_total"          title="Valor Total"          fmt="num1b"/>

---

## Ranking por Quantidade

```sql modalidades_qt
select
    rank_por_quantidade                             as ranking,
    nm_modalidade                                   as modalidade,
    qt_contratos,
    qt_orgaos_distintos                             as orgaos,
    qt_fornecedores_distintos                       as fornecedores,
    vl_total_atual                                  as vl_total,
    round(perc_sobre_total_qt::numeric, 2)          as perc_qt,
    round(perc_sobre_total_valor::numeric, 2)       as perc_valor,
    round(perc_contratos_com_aditivo::numeric, 2)   as perc_aditivo
from compras.dim_modalidades
order by ranking
```

<BarChart
    data={modalidades_qt}
    x="modalidade"
    y="qt_contratos"
    title="Modalidades por Quantidade de Contratos"
    swapXY=true
/>

<DataTable data={modalidades_qt} title="Ranking Completo de Modalidades">
    <Column id="ranking"      title="#"/>
    <Column id="modalidade"   title="Modalidade"/>
    <Column id="qt_contratos" title="Contratos"     fmt="num0"/>
    <Column id="orgaos"       title="Órgãos"        fmt="num0"/>
    <Column id="fornecedores" title="Fornecedores"  fmt="num0"/>
    <Column id="vl_total"     title="Valor Total"   fmt="num1b"/>
    <Column id="perc_qt"      title="% Contratos"   fmt="num2"/>
    <Column id="perc_valor"   title="% Valor"       fmt="num2"/>
    <Column id="perc_aditivo" title="% Com Aditivo" fmt="num2"/>
</DataTable>

---

## Taxa de Aditivos por Modalidade

```sql aditivos_modalidade
select
    nm_modalidade                                       as modalidade,
    round(perc_contratos_com_aditivo::numeric, 2)       as perc_aditivo,
    qt_contratos,
    vl_total_aditado                                    as vl_aditado
from compras.dim_modalidades
where nm_modalidade != 'Não informado'
order by perc_aditivo desc
```

<BarChart
    data={aditivos_modalidade}
    x="modalidade"
    y="perc_aditivo"
    title="% de Contratos com Aditivo por Modalidade"
    swapXY=true
/>