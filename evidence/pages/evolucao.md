---
title: Evolução Temporal
---

> Como o volume e o valor das contratações públicas de Santa Catarina mudaram ao longo de 10 anos? Esta análise revela os ciclos de expansão e retração, os impactos de eventos externos e os padrões sazonais das compras governamentais.

---

## Como evoluiu o volume de contratações?

O período analisado revela três fases distintas: **crescimento** entre 2016 e 2018, **retração** entre 2019 e 2021 — influenciada pela pandemia de COVID-19 — e **recuperação** a partir de 2022, com novo pico em 2025.

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

<DataTable data={evolucao_anual} title="Resumo Anual" index=false>
    <Column id="ano"               title="Ano"/>
    <Column id="qt_contratos"      title="Qtd. Contratos"  fmt="num0"/>
    <Column id="qt_fornecedores"   title="Fornecedores"    fmt="num0"/>
    <Column id="qt_orgaos"         title="Órgãos"          fmt="num0"/>
    <Column id="vl_total_original" title="Valor Original"  fmt="num1b"/>
    <Column id="vl_total_atual"    title="Valor Atual"     fmt="num1b"/>
    <Column id="vl_total_aditado"  title="Valor Aditado"   fmt="num1b"/>
    <Column id="vl_medio"          title="Valor Médio"     fmt="num1k"/>
</DataTable>

> 📌 **Anos eleitorais:** Em **2018** e **2022**, anos de eleição para o Governo do Estado, observa-se variação nos volumes contratados. Em 2022, o valor original registrado (R$ 39,8B) contrasta fortemente com o valor atualizado (R$ 15,7B), indicando possível concentração de contratos de longo prazo assinados no período pré-eleitoral.

---

## Existe sazonalidade nas contratações?

A análise mensal revela padrões recorrentes ao longo do ano. Meses como **março e outubro** tendem a concentrar mais contratos — coincidindo com o início do ano fiscal e o período pré-eleitoral em anos de eleição.

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

## Os aditivos cresceram ao longo do tempo?

A proporção de contratos com aditivos se mantém estável ao longo dos anos — o que indica que a prática de alteração contratual não aumentou proporcionalmente ao volume de contratos. A maioria absoluta dos contratos é encerrada sem qualquer modificação.

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

---

> 💡 Volte para a [Visão Geral](/Analytics-Engineer/compras-publicas) ou explore os [Órgãos](/Analytics-Engineer/compras-publicas/orgaos), [Fornecedores](/Analytics-Engineer/compras-publicas/fornecedores), [Modalidades](/Analytics-Engineer/compras-publicas/modalidades) e [Aditivos Contratuais](/Analytics-Engineer/compras-publicas/aditivos).