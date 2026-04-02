---
title: Órgãos Públicos
---

> Quais órgãos do governo de Santa Catarina mais contratam e quanto gastam? Esta análise revela o perfil de cada unidade gestora — desde os grandes contratantes de infraestrutura até os órgãos com contratações mais pontuais.

---

## Panorama dos Órgãos

O estado conta com **187 unidades gestoras** ativas no período analisado. A distribuição é bastante concentrada: poucos órgãos respondem pela maior parte do valor contratado, enquanto a maioria realiza contratações de menor porte.

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

## Quem gasta mais?

A **Secretaria de Estado da Infraestrutura e Mobilidade** lidera com folga em valor total — reflexo direto do alto custo de obras viárias e de engenharia. O **Fundo Penitenciário** e o **Fundo Rotativo da Penitenciária Industrial de Joinville** também se destacam, indicando investimentos significativos no sistema prisional do estado.

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

<DataTable data={ranking_orgaos_valor} title="Top 20 Órgãos por Valor Total Contratado" index=false>
    <Column id="ranking"          title="Ranking"/>
    <Column id="orgao"            title="Órgão"/>
    <Column id="qt_contratos"     title="Qtd. Contratos"   fmt="num0"/>
    <Column id="fornecedores"     title="Fornecedores"     fmt="num0"/>
    <Column id="vl_atual"         title="Valor Atual"      fmt="num1b"/>
    <Column id="vl_aditado"       title="Aditivos"         fmt="num1b"/>
    <Column id="situacao_aditivo" title="Situação Aditivo"/>
    <Column id="perfil"           title="Perfil"/>
</DataTable>

---

## Quem contrata com mais frequência?

Órgãos com alto volume de contratos e valor médio menor geralmente atuam em **compras recorrentes de insumos** — como medicamentos, material escolar e peças de reposição. O **Fundo de Melhoria da Polícia Militar** lidera nessa categoria, refletindo a capilaridade de suas operações em todo o estado.

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

## Como se classificam por perfil?

O perfil de contratação classifica os órgãos pelo volume de contratos firmados: **Alto volume** (1.000+), **Médio volume** (100 a 999), **Baixo volume** (10 a 99) e **Esporádico** (menos de 10). A maioria dos órgãos realiza contratações de baixo a médio volume.

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

<DataTable data={perfil_contratacao} title="Distribuição por Perfil de Contratação" index=false>
    <Column id="perfil"       title="Perfil"/>
    <Column id="qt_orgaos"    title="Órgãos"     fmt="num0"/>
    <Column id="qt_contratos" title="Contratos"  fmt="num0"/>
    <Column id="vl_total"     title="Valor Total" fmt="num1b"/>
</DataTable>

---

## Os órgãos utilizam aditivos?

A maioria dos órgãos opera contratos **sem aditivos** — o que é positivo do ponto de vista da gestão contratual. Os órgãos com aditivos de acréscimo merecem atenção para verificar se as alterações estão dentro dos limites legais e devidamente justificadas.

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

<DataTable data={aditivos_orgaos} title="Situação de Aditivos por Órgão" index=false>
    <Column id="situacao"         title="Situação"/>
    <Column id="qt_orgaos"        title="Órgãos"        fmt="num0"/>
    <Column id="qt_contratos"     title="Contratos"     fmt="num0"/>
    <Column id="vl_total_aditado" title="Valor Aditado" fmt="num1b"/>
</DataTable>

---

> 💡 Volte para a [Visão Geral](/Analytics-Engineer/compras-publicas) ou explore os [Fornecedores](/Analytics-Engineer/compras-publicas/fornecedores), [Modalidades](/Analytics-Engineer/compras-publicas/modalidades), [Evolução Temporal](/Analytics-Engineer/compras-publicas/evolucao) e [Aditivos Contratuais](/Analytics-Engineer/compras-publicas/aditivos).