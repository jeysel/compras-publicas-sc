---
title: Modalidades de Licitação
---

> A modalidade de licitação define as regras do processo competitivo para contratação pública. A escolha correta da modalidade é fundamental para garantir transparência, competitividade e economicidade nas compras governamentais.

---

## Panorama das Modalidades

Santa Catarina utiliza **23 modalidades distintas** de contratação, refletindo a diversidade de objetos e valores contratados — desde pequenas compras por dispensa até grandes obras licitadas em concorrência pública.

```sql kpis_modalidades
select
    count(*)                    as total_modalidades,
    sum(qt_contratos)           as total_contratos,
    sum(vl_total_atual)         as vl_total
from compras.dim_modalidades
```

<BigValue data={kpis_modalidades} value="total_modalidades" title="Modalidades Distintas" fmt="num0"/>
<BigValue data={kpis_modalidades} value="total_contratos"   title="Total de Contratos"    fmt="num1k"/>
<BigValue data={kpis_modalidades} value="vl_total"          title="Valor Total"           fmt="num1b"/>

---

## Qual modalidade predomina?

O **Pregão Eletrônico** é de longe a modalidade mais utilizada — respondendo por quase **50% de todos os contratos**. Isso reflete uma tendência positiva: o pregão eletrônico promove maior competitividade ao permitir que qualquer fornecedor habilitado participe de forma remota, reduzindo custos e aumentando a transparência.

A transição da Lei 8.666/1993 para a Lei 14.133/2021 também é visível nos dados — modalidades com a nova lei aparecem separadamente, mas representam o mesmo processo licitatório sob nova legislação.

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

<DataTable data={modalidades_qt} title="Ranking Completo de Modalidades" index=false>
    <Column id="ranking"      title="Ranking"/>
    <Column id="modalidade"   title="Modalidade"/>
    <Column id="qt_contratos" title="Qtd. Contratos"  fmt="num0"/>
    <Column id="orgaos"       title="Órgãos"          fmt="num0"/>
    <Column id="fornecedores" title="Fornecedores"    fmt="num0"/>
    <Column id="vl_total"     title="Valor Total"     fmt="num1b"/>
    <Column id="perc_qt"      title="% Contratos"     fmt="num2"/>
    <Column id="perc_valor"   title="% Valor"         fmt="num2"/>
    <Column id="perc_aditivo" title="% Com Aditivo"   fmt="num2"/>
</DataTable>

---

## Quais modalidades geram mais aditivos?

A taxa de aditivos por modalidade revela um padrão importante: modalidades associadas a **obras e serviços de engenharia** tendem a ter maior incidência de aditivos — o que é esperado dado a complexidade e imprevisibilidade desses contratos. Já o Pregão Eletrônico, usado principalmente para compras de bens e serviços padronizados, apresenta taxas bem menores.

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

---

> 💡 Volte para a [Visão Geral](/Analytics-Engineer/compras-publicas) ou explore os [Órgãos](/Analytics-Engineer/compras-publicas/orgaos), [Fornecedores](/Analytics-Engineer/compras-publicas/fornecedores), [Evolução Temporal](/Analytics-Engineer/compras-publicas/evolucao) e [Aditivos Contratuais](/Analytics-Engineer/compras-publicas/aditivos).