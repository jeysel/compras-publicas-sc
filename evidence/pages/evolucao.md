---
title: Evolução Temporal
---

# Evolução Temporal

Análise da evolução dos contratos públicos de Santa Catarina ao longo do tempo.

---

## Evolução Anual

```sql evolucao_anual
select
    ano_assinatura::integer                     as ano,
    count(*)                                    as qt_contratos,
    count(distinct id_contratado)               as qt_fornecedores,
    count(distinct cod_unidade_gestora)         as qt_orgaos,
    sum(vl_original)                            as vl_total_original,
    sum(vl_atual)                               as vl_total_atual,
    sum(coalesce(vl_aditado, 0))                as vl_total_aditado,
    avg(vl_original)                            as vl_medio
from compras.fct_contratos
where ano_assinatura between 2016 and 2025
group by ano_assinatura
order by ano_assinatura
```

<LineChart
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

<DataTable data={evolucao_anual} title="Resumo Anual">
    <Column id="ano"               title="Ano"/>
    <Column id="qt_contratos"      title="Contratos"     fmt="num0"/>
    <Column id="qt_fornecedores"   title="Fornecedores"  fmt="num0"/>
    <Column id="qt_orgaos"         title="Órgãos"        fmt="num0"/>
    <Column id="vl_total_original" title="Valor Original" fmt="num1b"/>
    <Column id="vl_total_atual"    title="Valor Atual"   fmt="num1b"/>
    <Column id="vl_total_aditado"  title="Valor Aditado" fmt="num1b"/>
    <Column id="vl_medio"          title="Valor Médio"   fmt="num1k"/>
</DataTable>

---

## Evolução Mensal

```sql evolucao_mensal
select
    ano_assinatura::integer || '-' || lpad(mes_assinatura::text, 2, '0') as ano_mes,
    ano_assinatura::integer             as ano,
    mes_assinatura::integer             as mes,
    count(*)                            as qt_contratos,
    sum(vl_atual)                       as vl_total_atual
from compras.fct_contratos
where ano_assinatura between 2016 and 2025
group by ano_assinatura, mes_assinatura
order by ano_assinatura, mes_assinatura
```

<LineChart
    data={evolucao_mensal}
    x="ano_mes"
    y="qt_contratos"
    title="Quantidade de Contratos por Mês"
    xAxisTitle="Mês"
    yAxisTitle="Quantidade"
    xType="category"
/>

---

## Aditivos ao Longo do Tempo

```sql aditivos_anual
select
    ano_assinatura::integer                                     as ano,
    count(case when fl_possui_aditivo then 1 end)               as com_aditivo,
    count(case when not fl_possui_aditivo then 1 end)           as sem_aditivo,
    sum(coalesce(vl_aditado, 0))                                as vl_total_aditado
from compras.fct_contratos
where ano_assinatura between 2016 and 2025
group by ano_assinatura
order by ano_assinatura
```

<BarChart
    data={aditivos_anual}
    x="ano"
    y={["com_aditivo", "sem_aditivo"]}
    title="Contratos Com e Sem Aditivo por Ano"
    xAxisTitle="Ano"
    yAxisTitle="Quantidade"
    xType="category"
    type="stacked"
/>