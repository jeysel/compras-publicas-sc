---
title: Órgãos Públicos
---

# Órgãos Públicos

Análise das unidades gestoras responsáveis pelos contratos públicos de Santa Catarina.

---

## Visão Geral

```sql kpis_orgaos
select
    count(*)                    as total_orgaos,
    sum(qt_contratos)           as total_contratos,
    sum(vl_total_atual)         as vl_total,
    avg(vl_medio_contrato)      as vl_medio
from compras.dim_orgaos
```

<BigValue data={kpis_orgaos} value="total_orgaos"    title="Total de Órgãos"          fmt="num0"/>
<BigValue data={kpis_orgaos} value="total_contratos" title="Total de Contratos"        fmt="num1k"/>
<BigValue data={kpis_orgaos} value="vl_total"        title="Valor Total Contratado"    fmt="num1b"/>
<BigValue data={kpis_orgaos} value="vl_medio"        title="Valor Médio por Contrato"  fmt="num1k"/>

---

## Ranking por Valor Total

```sql ranking_orgaos_valor
select
    rank_por_valor              as ranking,
    nm_unidade_gestora          as orgao,
    qt_contratos,
    qt_fornecedores_distintos   as fornecedores,
    vl_total_atual              as vl_atual,
    vl_total_aditado            as vl_aditado,
    ds_situacao_aditivo         as situacao_aditivo,
    ds_perfil_contratacao       as perfil
from compras.dim_orgaos
order by ranking
limit 20
```

<DataTable data={ranking_orgaos_valor} title="Top 20 Órgãos por Valor Total Contratado">
    <Column id="ranking"          title="#"/>
    <Column id="orgao"            title="Órgão"/>
    <Column id="qt_contratos"     title="Contratos"        fmt="num0"/>
    <Column id="fornecedores"     title="Fornecedores"     fmt="num0"/>
    <Column id="vl_atual"         title="Valor Atual"      fmt="num1b"/>
    <Column id="vl_aditado"       title="Aditivos"         fmt="num1b"/>
    <Column id="situacao_aditivo" title="Situação Aditivo"/>
    <Column id="perfil"           title="Perfil"/>
</DataTable>

---

## Ranking por Quantidade de Contratos

```sql ranking_orgaos_qt
select
    rank_por_quantidade         as ranking,
    nm_unidade_gestora          as orgao,
    qt_contratos,
    ds_perfil_contratacao       as perfil
from compras.dim_orgaos
order by ranking
limit 20
```

<BarChart
    data={ranking_orgaos_qt}
    x="orgao"
    y="qt_contratos"
    title="Top 20 Órgãos por Quantidade de Contratos"
    swapXY=true
/>

---

## Perfil de Contratação

```sql perfil_contratacao
select
    ds_perfil_contratacao       as perfil,
    count(*)                    as qt_orgaos,
    sum(qt_contratos)           as qt_contratos,
    sum(vl_total_atual)         as vl_total
from compras.dim_orgaos
group by 1
order by sum(qt_contratos) desc
```

<DataTable data={perfil_contratacao} title="Distribuição por Perfil de Contratação">
    <Column id="perfil"       title="Perfil"/>
    <Column id="qt_orgaos"    title="Órgãos"     fmt="num0"/>
    <Column id="qt_contratos" title="Contratos"  fmt="num0"/>
    <Column id="vl_total"     title="Valor Total" fmt="num1b"/>
</DataTable>

---

## Situação de Aditivos

```sql aditivos_orgaos
select
    ds_situacao_aditivo         as situacao,
    count(*)                    as qt_orgaos,
    sum(qt_contratos)           as qt_contratos,
    sum(vl_total_aditado)       as vl_total_aditado
from compras.dim_orgaos
group by 1
order by qt_orgaos desc
```

<DataTable data={aditivos_orgaos} title="Situação de Aditivos por Órgão">
    <Column id="situacao"         title="Situação"/>
    <Column id="qt_orgaos"        title="Órgãos"        fmt="num0"/>
    <Column id="qt_contratos"     title="Contratos"     fmt="num0"/>
    <Column id="vl_total_aditado" title="Valor Aditado" fmt="num1b"/>
</DataTable>