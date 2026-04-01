---
title: Fornecedores
---

# Fornecedores

Análise dos fornecedores contratados pelo estado de Santa Catarina.

---

## Visão Geral

```sql kpis_fornecedores
select
    count(*)                    as total_fornecedores,
    sum(qt_contratos)           as total_contratos,
    sum(vl_total_atual)         as vl_total,
    max(vl_total_atual)         as vl_maior
from compras.dim_fornecedores
```

<BigValue data={kpis_fornecedores} value="total_fornecedores" title="Total de Fornecedores" fmt="num1k"/>
<BigValue data={kpis_fornecedores} value="total_contratos"    title="Total de Contratos"    fmt="num1k"/>
<BigValue data={kpis_fornecedores} value="vl_total"           title="Valor Total"           fmt="num1b"/>
<BigValue data={kpis_fornecedores} value="vl_maior"           title="Maior Fornecedor"      fmt="num1b"/>

---

## Distribuição por Porte

```sql porte_fornecedor
select
    porte_fornecedor            as porte,
    count(*)                    as qt_fornecedores,
    sum(qt_contratos)           as qt_contratos,
    sum(vl_total_atual)         as vl_total
from compras.dim_fornecedores
group by 1
order by vl_total desc
```

<BarChart
    data={porte_fornecedor}
    x="porte"
    y="qt_fornecedores"
    title="Quantidade de Fornecedores por Porte"
/>

<DataTable data={porte_fornecedor} title="Distribuição por Porte">
    <Column id="porte"           title="Porte"/>
    <Column id="qt_fornecedores" title="Fornecedores" fmt="num0"/>
    <Column id="qt_contratos"    title="Contratos"    fmt="num0"/>
    <Column id="vl_total"        title="Valor Total"  fmt="num1b"/>
</DataTable>

---

## Top 20 Fornecedores por Valor

```sql top_fornecedores
select
    rank_por_valor              as ranking,
    nm_contratado               as fornecedor,
    porte_fornecedor            as porte,
    qt_contratos,
    qt_orgaos_distintos         as orgaos,
    vl_total_atual              as vl_total,
    vl_total_aditado            as vl_aditado,
    ds_situacao_aditivo         as situacao_aditivo
from compras.dim_fornecedores
order by ranking
limit 20
```

<DataTable data={top_fornecedores} title="Top 20 Fornecedores por Valor Total">
    <Column id="ranking"          title="#"/>
    <Column id="fornecedor"       title="Fornecedor"/>
    <Column id="porte"            title="Porte"/>
    <Column id="qt_contratos"     title="Contratos"       fmt="num0"/>
    <Column id="orgaos"           title="Órgãos"          fmt="num0"/>
    <Column id="vl_total"         title="Valor Total"     fmt="num1b"/>
    <Column id="vl_aditado"       title="Aditivos"        fmt="num1b"/>
    <Column id="situacao_aditivo" title="Situação Aditivo"/>
</DataTable>

---

## Top 20 por Quantidade de Contratos

```sql top_fornecedores_qt
select
    rank_por_quantidade         as ranking,
    nm_contratado               as fornecedor,
    porte_fornecedor            as porte,
    qt_contratos,
    qt_orgaos_distintos         as orgaos,
    vl_total_atual              as vl_total
from compras.dim_fornecedores
order by ranking
limit 20
```

<BarChart
    data={top_fornecedores_qt}
    x="fornecedor"
    y="qt_contratos"
    title="Top 20 Fornecedores por Quantidade de Contratos"
    swapXY=true
/>