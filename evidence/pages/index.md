---
title: Análise das Compras Públicas do Estado de Santa Catarina
---

> Quanto o governo do Estado de Santa Catarina contrata, com quem e como? Este painel analisa **10 anos de contratos públicos** do estado, transformando dados brutos em informação estruturada e acessível.

**Fonte:** [Portal de Transparência do Estado de Santa Catarina](https://www.transparencia.sc.gov.br/) | **Período:** 01/01/2016 a 31/03/2026 | **Registros:** ~76 mil contratos

---

## Panorama Geral

Em 10 anos, o Estado de Santa Catarina firmou mais de **76 mil contratos** com quase **11,5 mil fornecedores diferentes**, movimentando cerca de **R$ 79,7 bilhões**. Desse total, **R$ 1,6 bilhão** corresponde a aditivos contratuais — alterações de valor ou prazo após a assinatura.

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
where ano_assinatura between 2016 and 2025
```

<BigValue data={kpis} value="total_contratos"       title="Contratos"                fmt="num1k"/>
<BigValue data={kpis} value="total_fornecedores"    title="Fornecedores"             fmt="num1k"/>
<BigValue data={kpis} value="total_orgaos"          title="Órgãos Públicos"          fmt="num0"/>
<BigValue data={kpis} value="vl_total_atual"        title="Valor Total Contratado"   fmt="num1b"/>
<BigValue data={kpis} value="vl_total_aditado"      title="Total em Aditivos"        fmt="num1b"/>
<BigValue data={kpis} value="contratos_com_aditivo" title="Contratos com Aditivo"    fmt="num1k"/>

---

## Como evoluiu o volume de contratações?

O pico de contratações ocorreu em **2018**, com quase 10 mil contratos. Após 2018 ocorreu uma queda entre 2019 e 2021, o volume voltou a crescer a partir de 2022 — possivelmente reflexo da retomada pós-pandemia e novos investimentos em infraestrutura.

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

<DataTable data={evolucao_anual} title="Resumo por Ano" index=false>
    <Column id="ano"               title="Ano"/>
    <Column id="qt_contratos"      title="Qtd. Contratos"   fmt="num0"/>
    <Column id="vl_total_original" title="Valor Inicial"    fmt="num1b"/>
    <Column id="vl_total_atual"    title="Valor Atualizado" fmt="num1b"/>
</DataTable>

> 📌 **Anos eleitorais:** Em **2018** e **2022**, anos de eleição para o Governo do Estado, observa-se variação nos volumes contratados — especialmente em 2022, onde o valor original registrado (R$ 39,8B) contrasta fortemente com o valor atualizado (R$ 15,7B), indicando forte redução no valor dos contratos.

---

## Os contratos sofreram alterações?

A grande maioria dos contratos (**97,6%**) não sofreu aditivos. Dos que foram alterados, a maioria teve acréscimo de valor — o que merece atenção do ponto de vista do controle social.

```sql situacao_aditivo
select
    ds_situacao_aditivo     as situacao,
    count(*)                as qt_contratos,
    sum(vl_atual)           as vl_total
from compras.fct_contratos
where ano_assinatura between 2016 and 2025
group by 1
order by 2 desc
```

<DataTable data={situacao_aditivo} title="Contratos por Situação de Aditivo" index=false>
    <Column id="situacao"     title="Situação"/>
    <Column id="qt_contratos" title="Contratos"   fmt="num0"/>
    <Column id="vl_total"     title="Valor Total" fmt="num1b"/>
</DataTable>

---

## Quais modalidades são mais usadas?

O **Pregão Eletrônico** domina amplamente as contratações — modalidade que promove maior competitividade por permitir disputas online entre fornecedores. A predominância dessa modalidade é um indicador positivo de transparência e eficiência no processo licitatório.

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

## Quem mais contrata?

A **Secretaria de Estado da Infraestrutura e Mobilidade** lidera em valor total — esperado dado o alto custo de obras e serviços de engenharia. Já o **Fundo de Melhoria da Polícia Militar** se destaca em quantidade de contratos, refletindo a capilaridade de suas operações.

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

<DataTable data={top_orgaos} title="Top 10 Órgãos por Valor Total Contratado" index=false>
    <Column id="ranking"      title="Ranking"/>
    <Column id="orgao"        title="Órgão"/>
    <Column id="qt_contratos" title="Qtd. Contratos" fmt="num0"/>
    <Column id="vl_total"     title="Valor Total"    fmt="num1b"/>
</DataTable>

---

## Quem são os maiores fornecedores?

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

<DataTable data={top_fornecedores} title="Top 10 Fornecedores por Valor Total Contratado" index=false>
    <Column id="ranking"      title="Ranking"/>
    <Column id="fornecedor"   title="Fornecedor"/>
    <Column id="porte"        title="Porte"/>
    <Column id="qt_contratos" title="Qtd. Contratos" fmt="num0"/>
    <Column id="vl_total"     title="Valor Total"    fmt="num1b"/>
</DataTable>

---

> 💡 **Explore as análises detalhadas** nos painéis de [Órgãos](/Analytics-Engineer/compras-publicas/orgaos), [Fornecedores](/Analytics-Engineer/compras-publicas/fornecedores), [Modalidades](/Analytics-Engineer/compras-publicas/modalidades), [Evolução Temporal](/Analytics-Engineer/compras-publicas/evolucao) e [Aditivos Contratuais](/Analytics-Engineer/compras-publicas/aditivos).