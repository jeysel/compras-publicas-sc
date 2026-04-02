---
title: Fornecedores
---

> Quem são as empresas e organizações que mais fornecem ao governo de Santa Catarina? Esta análise revela a concentração do mercado fornecedor, o perfil por porte e os principais parceiros comerciais do estado.

---

## Panorama dos Fornecedores

O estado contratou **11,4 mil fornecedores distintos** no período analisado — uma base relativamente diversa. No entanto, como veremos, uma pequena parcela concentra a maior parte do valor contratado, o que é um padrão comum em compras governamentais.

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

## Como se distribuem por porte?

A classificação por porte é baseada no valor total contratado: **Grande** (acima de R$ 10M), **Médio** (R$ 1M a R$ 10M), **Pequeno** (R$ 100K a R$ 1M) e **Micro** (abaixo de R$ 100K). Fornecedores de grande porte concentram a maior parcela do valor total, enquanto micro e pequenos fornecedores representam a maior quantidade de empresas.

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
    xAxisTitle="Porte"
    yAxisTitle="Quantidade"
/>

<DataTable data={porte_fornecedor} title="Distribuição por Porte" index=false>
    <Column id="porte"           title="Porte"/>
    <Column id="qt_fornecedores" title="Fornecedores" fmt="num0"/>
    <Column id="qt_contratos"    title="Contratos"    fmt="num0"/>
    <Column id="vl_total"        title="Valor Total"  fmt="num1b"/>
</DataTable>

---

## Quem recebeu mais recursos?

Os 20 maiores fornecedores por valor revelam empresas que mantêm relacionamento contínuo com múltiplos órgãos do estado. A presença de fornecedores com poucos contratos e alto valor total indica contratos de grande escala — típicos de obras de infraestrutura e serviços continuados.

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

<DataTable data={top_fornecedores} title="Top 20 Fornecedores por Valor Total" index=false>
    <Column id="ranking"          title="Ranking"/>
    <Column id="fornecedor"       title="Fornecedor"/>
    <Column id="porte"            title="Porte"/>
    <Column id="qt_contratos"     title="Qtd. Contratos"   fmt="num0"/>
    <Column id="orgaos"           title="Órgãos"           fmt="num0"/>
    <Column id="vl_total"         title="Valor Total"      fmt="num1b"/>
    <Column id="vl_aditado"       title="Aditivos"         fmt="num1b"/>
    <Column id="situacao_aditivo" title="Situação Aditivo"/>
</DataTable>

---

## Quem tem mais contratos?

Fornecedores com alto volume de contratos e valor médio baixo geralmente atuam em **compras de insumos e materiais** — como peças, medicamentos e material de escritório. Esse perfil é diferente dos grandes contratos de obras e serviços continuados.

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

---

> 💡 Volte para a [Visão Geral](/Analytics-Engineer/compras-publicas) ou explore os [Órgãos](/Analytics-Engineer/compras-publicas/orgaos), [Modalidades](/Analytics-Engineer/compras-publicas/modalidades), [Evolução Temporal](/Analytics-Engineer/compras-publicas/evolucao) e [Aditivos Contratuais](/Analytics-Engineer/compras-publicas/aditivos).