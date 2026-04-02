---
title: Ramos de Atividade
---

> Qual é o perfil do fornecedor do Estado de Santa Catarina? Esta análise classifica os contratos por ramo de atividade com base no objeto contratado, revelando em quais setores o governo mais investe e quantos fornecedores atendem cada segmento.

**Metodologia:** A classificação por ramo é baseada em palavras-chave do campo **objeto do contrato**. Contratos com descrições muito específicas ou atípicas são agrupados em "Outros".

---

## Panorama por Ramo

```sql kpis_ramos
select
    count(*)                    as total_ramos,
    sum(qt_contratos)           as total_contratos,
    sum(qt_fornecedores)        as total_fornecedores,
    sum(vl_total_atual)         as vl_total
from compras.dim_ramos
where ramo_atividade != 'Outros'
```

<BigValue data={kpis_ramos} value="total_ramos"        title="Ramos Identificados"  fmt="num0"/>
<BigValue data={kpis_ramos} value="total_contratos"    title="Contratos Classificados" fmt="num1k"/>
<BigValue data={kpis_ramos} value="total_fornecedores" title="Fornecedores"          fmt="num1k"/>
<BigValue data={kpis_ramos} value="vl_total"           title="Valor Total"           fmt="num1b"/>

---

## Quais ramos têm mais contratos?

**Alimentação** lidera em quantidade — reflexo das compras recorrentes de gêneros alimentícios para a Polícia Militar, merenda escolar e alimentação institucional. **Combustíveis e Energia** e **Veículos e Manutenção** também se destacam, evidenciando o alto custo operacional da frota estadual.

```sql ramos_qt
select
    ramo_atividade              as ramo,
    qt_contratos,
    qt_fornecedores             as fornecedores,
    vl_total_atual              as vl_total,
    perc_sobre_total_qt         as perc_qt,
    perc_sobre_total_valor      as perc_valor,
    rank_por_quantidade         as ranking
from compras.dim_ramos
where ramo_atividade != 'Outros'
order by rank_por_quantidade
```

<BarChart
    data={ramos_qt}
    x="ramo"
    y="qt_contratos"
    title="Quantidade de Contratos por Ramo de Atividade"
    swapXY=true
/>

<DataTable data={ramos_qt} title="Ranking por Quantidade de Contratos" index=false>
    <Column id="ranking"      title="Ranking"/>
    <Column id="ramo"         title="Ramo de Atividade"/>
    <Column id="qt_contratos" title="Qtd. Contratos"  fmt="num0"/>
    <Column id="fornecedores" title="Fornecedores"    fmt="num0"/>
    <Column id="vl_total"     title="Valor Total"     fmt="num1b"/>
    <Column id="perc_qt"      title="% Contratos"     fmt="num2"/>
    <Column id="perc_valor"   title="% Valor"         fmt="num2"/>
</DataTable>

---

## Quais ramos movimentam mais recursos?

**Obras e Construção** lidera em valor apesar de ter relativamente poucos contratos — o que revela o alto valor médio por contrato nesse setor. **Alimentação** e **Combustíveis** também são significativos pelo volume e frequência das contratações.

```sql ramos_valor
select
    ramo_atividade              as ramo,
    vl_total_atual              as vl_total,
    qt_contratos,
    vl_medio_contrato           as vl_medio,
    rank_por_valor              as ranking
from compras.dim_ramos
where ramo_atividade != 'Outros'
order by rank_por_valor
```

<BarChart
    data={ramos_valor}
    x="ramo"
    y="vl_total"
    title="Valor Total Contratado por Ramo de Atividade (R$)"
    swapXY=true
/>

---

## Tecnologia da Informação em detalhe

O setor de TI aparece segmentado em quatro subcategorias, revelando o perfil das contratações tecnológicas do estado. O **Licenciamento de Software** representa aquisição de produtos, enquanto **Manutenção e Suporte** e **Desenvolvimento** refletem serviços especializados.

```sql ti_detalhe
select
    ramo_atividade              as subcategoria,
    qt_contratos,
    qt_fornecedores             as fornecedores,
    vl_total_atual              as vl_total,
    vl_medio_contrato           as vl_medio,
    rank_por_valor              as ranking
from compras.dim_ramos
where ramo_atividade like 'TI -%'
order by qt_contratos desc
```

<DataTable data={ti_detalhe} title="Detalhamento do Setor de TI" index=false>
    <Column id="subcategoria"  title="Subcategoria"/>
    <Column id="qt_contratos"  title="Qtd. Contratos" fmt="num0"/>
    <Column id="fornecedores"  title="Fornecedores"   fmt="num0"/>
    <Column id="vl_total"      title="Valor Total"    fmt="num1b"/>
    <Column id="vl_medio"      title="Valor Médio"    fmt="num1k"/>
</DataTable>

---

## Quantos fornecedores atendem cada ramo?

A relação entre contratos e fornecedores revela a **concentração de mercado** em cada setor. Ramos com poucos fornecedores e muitos contratos indicam maior dependência de um grupo restrito de empresas.

```sql ramos_fornecedores
select
    ramo_atividade              as ramo,
    qt_fornecedores             as fornecedores,
    qt_contratos,
    round(qt_contratos::numeric / nullif(qt_fornecedores, 0), 1) as contratos_por_fornecedor
from compras.dim_ramos
where ramo_atividade != 'Outros'
order by contratos_por_fornecedor desc
```

<BarChart
    data={ramos_fornecedores}
    x="ramo"
    y="contratos_por_fornecedor"
    title="Média de Contratos por Fornecedor"
    swapXY=true
/>

---

> 💡 Volte para a [Visão Geral](/Analytics-Engineer/compras-publicas) ou explore os [Órgãos](/Analytics-Engineer/compras-publicas/orgaos), [Fornecedores](/Analytics-Engineer/compras-publicas/fornecedores), [Modalidades](/Analytics-Engineer/compras-publicas/modalidades), [Evolução Temporal](/Analytics-Engineer/compras-publicas/evolucao) e [Aditivos Contratuais](/Analytics-Engineer/compras-publicas/aditivos).