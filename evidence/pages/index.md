---
title: Compras Públicas SC
---

# Compras Públicas de Santa Catarina

Pipeline de dados analíticos sobre contratos públicos do estado de Santa Catarina.
**Fonte:** [Portal Transparência SC](https://www.transparencia.sc.gov.br/) | **Período:** 2016 a 2026

---

## Visão Geral

```sql kpis
select
    count(*)                                            as total_contratos,
    count(distinct id_contratado)                       as total_fornecedores,
    count(distinct cod_unidade_gestora)                 as total_orgaos,
    sum(vl_original)                                    as vl_total_original,
    sum(vl_atual)                                       as vl_total_atual,
    sum(coalesce(vl_aditado, 0))                        as vl_total_aditado,
    count(case when fl_possui_aditivo then 1 end)       as contratos_com_aditivo
from compras.fct_contratos
```

<BigValue data={kpis} value="total_contratos"       title="Total de Contratos"       fmt="num1k"/>
<BigValue data={kpis} value="total_fornecedores"    title="Fornecedores"             fmt="num1k"/>
<BigValue data={kpis} value="total_orgaos"          title="Órgãos Públicos"          fmt="num0"/>
<BigValue data={kpis} value="vl_total_atual"        title="Valor Total Contratado"   fmt="num1b"/>
<BigValue data={kpis} value="vl_total_aditado"      title="Total em Aditivos"        fmt="num1b"/>
<BigValue data={kpis} value="contratos_com_aditivo" title="Contratos com Aditivo"    fmt="num1k"/>

---

## Evolução Anual de Contratos

```sql evolucao_anual
select
    ano_assinatura::integer             as ano,
    count(*)                            as qt_contratos,
    sum(vl_original)                    as vl_total_original,
    sum(vl_atual)                       as vl_total_atual
from compras.fct_contratos
where ano_assinatura between 2016 and 2025
group by ano_assinatura
order by ano_assinatura
```

<BarChart
    data={evolucao_anual}
    x="ano"
    y="qt_contratos"
    title="Quantidade de Contratos por Ano"
    xAxisTitle="Ano"
    yAxisTitle="Quantidade"
    xType="category"
/>

<LineChart
    data={evolucao_anual}
    x="ano"
    y="vl_total_atual"
    title="Valor Total Contratado por Ano (R$)"
    xAxisTitle="Ano"
    yAxisTitle="Valor (R$)"
    xType="category"
/>

---

## Distribuição por Situação de Aditivo

```sql situacao_aditivo
select
    ds_situacao_aditivo     as situacao,
    count(*)                as qt_contratos,
    sum(vl_atual)           as vl_total
from compras.fct_contratos
group by 1
order by 2 desc
```

<DataTable data={situacao_aditivo} title="Contratos por Situação de Aditivo">
    <Column id="situacao"     title="Situação"/>
    <Column id="qt_contratos" title="Qtd. Contratos" fmt="num0"/>
    <Column id="vl_total"     title="Valor Total"    fmt="num1b"/>
</DataTable>

---

## Top 10 Modalidades

```sql top_modalidades
select
    nm_modalidade           as modalidade,
    qt_contratos,
    vl_total_atual          as vl_total
from compras.dim_modalidades
order by qt_contratos desc
limit 10
```

<BarChart
    data={top_modalidades}
    x="modalidade"
    y="qt_contratos"
    title="Top 10 Modalidades por Quantidade de Contratos"
    swapXY=true
/>

---

## Top 10 Órgãos por Valor

```sql top_orgaos
select
    rank_por_valor          as ranking,
    nm_unidade_gestora      as orgao,
    qt_contratos,
    vl_total_atual          as vl_total
from compras.dim_orgaos
order by ranking
limit 10
```

<DataTable data={top_orgaos} title="Top 10 Órgãos por Valor Total Contratado">
    <Column id="ranking"      title="#"/>
    <Column id="orgao"        title="Órgão"/>
    <Column id="qt_contratos" title="Contratos" fmt="num0"/>
    <Column id="vl_total"     title="Valor Total" fmt="num1b"/>
</DataTable>

---

## Top 10 Fornecedores por Valor

```sql top_fornecedores
select
    rank_por_valor          as ranking,
    nm_contratado           as fornecedor,
    porte_fornecedor        as porte,
    qt_contratos,
    vl_total_atual          as vl_total
from compras.dim_fornecedores
order by ranking
limit 10
```

<DataTable data={top_fornecedores} title="Top 10 Fornecedores por Valor Total Contratado">
    <Column id="ranking"      title="#"/>
    <Column id="fornecedor"   title="Fornecedor"/>
    <Column id="porte"        title="Porte"/>
    <Column id="qt_contratos" title="Contratos" fmt="num0"/>
    <Column id="vl_total"     title="Valor Total" fmt="num1b"/>
</DataTable>