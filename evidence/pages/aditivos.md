---
title: Aditivos Contratuais
---

# Aditivos Contratuais

Análise dos contratos que sofreram alterações de valor ou prazo.

> **Regra de negócio:** Valor econômico real = Valor Original + Valor Aditado = Valor Atual

---

## Visão Geral

```sql kpis_aditivos
select
    count(*)                    as total_com_aditivo,
    sum(vl_original)            as vl_total_original,
    sum(vl_aditado)             as vl_total_aditado,
    sum(vl_atual)               as vl_total_atual
from compras.fct_aditivos
```

<BigValue data={kpis_aditivos} value="total_com_aditivo"  title="Contratos com Aditivo"  fmt="num0"/>
<BigValue data={kpis_aditivos} value="vl_total_original"  title="Valor Original Total"   fmt="num1b"/>
<BigValue data={kpis_aditivos} value="vl_total_aditado"   title="Valor Total Aditado"    fmt="num1b"/>
<BigValue data={kpis_aditivos} value="vl_total_atual"     title="Valor Atual Total"      fmt="num1b"/>

---

## Tipo de Aditivo

```sql tipo_aditivo
select
    tp_aditivo              as tipo,
    count(*)                as qt_contratos,
    sum(vl_aditado)         as vl_total_aditado
from compras.fct_aditivos
group by 1
order by qt_contratos desc
```

<BarChart
    data={tipo_aditivo}
    x="tipo"
    y="qt_contratos"
    title="Contratos por Tipo de Aditivo"
/>

<DataTable data={tipo_aditivo} title="Tipo de Aditivo">
    <Column id="tipo"             title="Tipo"/>
    <Column id="qt_contratos"     title="Contratos"     fmt="num0"/>
    <Column id="vl_total_aditado" title="Valor Aditado" fmt="num1b"/>
</DataTable>

---

## Faixa de Variação

```sql faixa_variacao
select
    faixa_variacao                                  as faixa,
    count(*)                                        as qt_contratos,
    sum(vl_aditado)                                 as vl_total_aditado,
    round(avg(perc_alteracao_valor)::numeric, 2)    as perc_medio
from compras.fct_aditivos
group by 1
order by qt_contratos desc
```

<DataTable data={faixa_variacao} title="Faixa de Variação de Valor">
    <Column id="faixa"            title="Faixa"/>
    <Column id="qt_contratos"     title="Contratos"            fmt="num0"/>
    <Column id="vl_total_aditado" title="Valor Aditado"        fmt="num1b"/>
    <Column id="perc_medio"       title="% Médio de Alteração" fmt="num2"/>
</DataTable>

---

## Top 20 Maiores Aditivos

```sql top_aditivos
select
    nu_contrato,
    nm_contratado                                   as fornecedor,
    nm_unidade_gestora                              as orgao,
    vl_original,
    vl_aditado,
    vl_atual,
    round(perc_alteracao_valor::numeric, 2)         as perc_alteracao,
    tp_aditivo                                      as tipo
from compras.fct_aditivos
order by vl_aditado desc
limit 20
```

<DataTable data={top_aditivos} title="Top 20 Maiores Aditivos por Valor">
    <Column id="nu_contrato"    title="Contrato"/>
    <Column id="fornecedor"     title="Fornecedor"/>
    <Column id="orgao"          title="Órgão"/>
    <Column id="vl_original"    title="Valor Original"  fmt="num1b"/>
    <Column id="vl_aditado"     title="Valor Aditado"   fmt="num1b"/>
    <Column id="vl_atual"       title="Valor Atual"     fmt="num1b"/>
    <Column id="perc_alteracao" title="% Alteração"     fmt="num2"/>
    <Column id="tipo"           title="Tipo"/>
</DataTable>