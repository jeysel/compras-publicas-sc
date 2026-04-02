---
title: Tecnologia da Informação
---

> O Estado de Santa Catarina investe significativamente em tecnologia — desde a aquisição de licenças de software até o desenvolvimento de sistemas próprios. Esta análise revela o perfil completo das contratações de TI, os principais fornecedores e os órgãos que mais investem em tecnologia.

---

## Panorama Geral de TI

```sql kpis_ti
select
    count(*)                            as qt_contratos,
    count(distinct id_contratado)       as qt_fornecedores,
    count(distinct cod_unidade_gestora) as qt_orgaos,
    sum(vl_original)                    as vl_total_original,
    sum(vl_atual)                       as vl_total_atual,
    sum(vl_aditado)                     as vl_total_aditado,
    avg(vl_original)                    as vl_medio
from compras.fct_contratos_ramo
where ramo_atividade like 'TI -%'
```

<BigValue data={kpis_ti} value="qt_contratos"     title="Contratos de TI"      fmt="num0"/>
<BigValue data={kpis_ti} value="qt_fornecedores"  title="Fornecedores"         fmt="num0"/>
<BigValue data={kpis_ti} value="qt_orgaos"        title="Órgãos"               fmt="num0"/>
<BigValue data={kpis_ti} value="vl_total_atual"   title="Valor Total"          fmt="num1b"/>
<BigValue data={kpis_ti} value="vl_medio"         title="Valor Médio"          fmt="num1m"/>
<BigValue data={kpis_ti} value="vl_total_aditado" title="Total em Aditivos"    fmt="num1m"/>

---

## Distribuição por Subcategoria

O setor de TI se divide em quatro subcategorias que refletem diferentes tipos de contratação. O **licenciamento** representa a aquisição de produtos prontos, enquanto **manutenção, suporte e desenvolvimento** indicam serviços especializados de maior complexidade e valor agregado.

```sql ti_subcategorias
select
    ramo_atividade                      as subcategoria,
    count(*)                            as qt_contratos,
    count(distinct id_contratado)       as qt_fornecedores,
    sum(vl_atual)                       as vl_total,
    avg(vl_original)                    as vl_medio
from compras.fct_contratos_ramo
where ramo_atividade like 'TI -%'
group by 1
order by qt_contratos desc
```

<BarChart
    data={ti_subcategorias}
    x="subcategoria"
    y="qt_contratos"
    title="Contratos por Subcategoria de TI"
    swapXY=true
/>

<DataTable data={ti_subcategorias} title="Resumo por Subcategoria" index=false>
    <Column id="subcategoria"    title="Subcategoria"/>
    <Column id="qt_contratos"    title="Qtd. Contratos" fmt="num0"/>
    <Column id="qt_fornecedores" title="Fornecedores"   fmt="num0"/>
    <Column id="vl_total"        title="Valor Total"    fmt="num1m"/>
    <Column id="vl_medio"        title="Valor Médio"    fmt="num1m"/>
</DataTable>

---

## Quais órgãos mais investem em TI?

A concentração de contratos de TI em poucos órgãos revela onde a transformação digital do estado está mais avançada. Órgãos com alto investimento em TI tendem a ter sistemas mais complexos e maior dependência de fornecedores especializados.

```sql orgaos_ti
select
    nm_unidade_gestora                  as orgao,
    count(*)                            as qt_contratos,
    count(distinct id_contratado)       as qt_fornecedores,
    sum(vl_atual)                       as vl_total
from compras.fct_contratos_ramo
where ramo_atividade like 'TI -%'
group by 1
order by vl_total desc
limit 15
```

<BarChart
    data={orgaos_ti}
    x="orgao"
    y="vl_total"
    title="Top 15 Órgãos por Valor Total em TI"
    swapXY=true
/>

<DataTable data={orgaos_ti} title="Top 15 Órgãos por Investimento em TI" index=false>
    <Column id="orgao"           title="Órgão"/>
    <Column id="qt_contratos"    title="Qtd. Contratos" fmt="num0"/>
    <Column id="qt_fornecedores" title="Fornecedores"   fmt="num0"/>
    <Column id="vl_total"        title="Valor Total"    fmt="num1m"/>
</DataTable>

---

## Quem são os principais fornecedores de TI?

```sql fornecedores_ti
select
    nm_contratado                       as fornecedor,
    count(*)                            as qt_contratos,
    count(distinct cod_unidade_gestora) as qt_orgaos,
    sum(vl_atual)                       as vl_total,
    sum(vl_aditado)                     as vl_aditado
from compras.fct_contratos_ramo
where ramo_atividade like 'TI -%'
group by 1
order by vl_total desc
limit 20
```

<DataTable data={fornecedores_ti} title="Top 20 Fornecedores de TI por Valor" index=false>
    <Column id="fornecedor"    title="Fornecedor"/>
    <Column id="qt_contratos"  title="Qtd. Contratos" fmt="num0"/>
    <Column id="qt_orgaos"     title="Órgãos"         fmt="num0"/>
    <Column id="vl_total"      title="Valor Total"    fmt="num1m"/>
    <Column id="vl_aditado"    title="Aditivos"       fmt="num1m"/>
</DataTable>

---

## Desenvolvimento de Software em Detalhe

O desenvolvimento de software sob medida representa o nível mais estratégico das contratações de TI — o estado investe em sistemas próprios que atendem necessidades específicas da administração pública. Com apenas **34 contratos**, são as contratações de maior complexidade e valor agregado por contrato.

```sql kpis_dev
select
    count(*)                            as qt_contratos,
    count(distinct id_contratado)       as qt_fornecedores,
    sum(vl_atual)                       as vl_total,
    avg(vl_original)                    as vl_medio
from compras.fct_contratos_ramo
where ramo_atividade = 'TI - Desenvolvimento de Software'
```

<BigValue data={kpis_dev} value="qt_contratos"    title="Contratos de Desenvolvimento" fmt="num0"/>
<BigValue data={kpis_dev} value="qt_fornecedores" title="Fornecedores"                 fmt="num0"/>
<BigValue data={kpis_dev} value="vl_total"        title="Valor Total"                  fmt="num1m"/>
<BigValue data={kpis_dev} value="vl_medio"        title="Valor Médio por Contrato"     fmt="num1m"/>

```sql fornecedores_dev
select
    nm_contratado                       as fornecedor,
    count(*)                            as qt_contratos,
    count(distinct cod_unidade_gestora) as qt_orgaos,
    sum(vl_atual)                       as vl_total,
    sum(vl_aditado)                     as vl_aditado
from compras.fct_contratos_ramo
where ramo_atividade = 'TI - Desenvolvimento de Software'
group by 1
order by vl_total desc
```

<DataTable data={fornecedores_dev} title="Fornecedores de Desenvolvimento de Software" index=false>
    <Column id="fornecedor"    title="Fornecedor"/>
    <Column id="qt_contratos"  title="Qtd. Contratos" fmt="num0"/>
    <Column id="qt_orgaos"     title="Órgãos"         fmt="num0"/>
    <Column id="vl_total"      title="Valor Total"    fmt="num1m"/>
    <Column id="vl_aditado"    title="Aditivos"       fmt="num1m"/>
</DataTable>

```sql contratos_dev
select
    nu_contrato,
    nm_contratado                       as fornecedor,
    nm_unidade_gestora                  as orgao,
    ds_objeto                           as objeto,
    ano_assinatura::integer             as ano,
    vl_original,
    vl_atual,
    vl_aditado,
    ds_situacao                         as situacao
from compras.fct_contratos_ramo
where ramo_atividade = 'TI - Desenvolvimento de Software'
order by vl_atual desc
```

<DataTable data={contratos_dev} title="Todos os Contratos de Desenvolvimento de Software" index=false>
    <Column id="fornecedor"    title="Fornecedor"/>
    <Column id="ano"           title="Ano"/>
    <Column id="vl_original"   title="Valor Original" fmt="num1m"/>
    <Column id="vl_atual"      title="Valor Atual"    fmt="num1m"/>
    <Column id="vl_aditado"    title="Aditivo"        fmt="num1m"/>
    <Column id="nu_contrato"   title="Contrato"/>
    <Column id="situacao"      title="Situação"/>
    <Column id="orgao"         title="Órgão"/>
    <Column id="objeto"        title="Objeto"/>
</DataTable>

---

## Todos os Contratos de TI

```sql contratos_ti
select
    nu_contrato,
    ramo_atividade                      as subcategoria,
    nm_contratado                       as fornecedor,
    nm_unidade_gestora                  as orgao,
    ds_objeto                           as objeto,
    ano_assinatura::integer             as ano,
    vl_original,
    vl_atual,
    vl_aditado,
    ds_situacao                         as situacao
from compras.fct_contratos_ramo
where ramo_atividade like 'TI -%'
order by vl_atual desc
limit 100
```

<DataTable data={contratos_ti} title="Top 100 Contratos de TI por Valor" index=false>
    <Column id="fornecedor"    title="Fornecedor"/>
    <Column id="subcategoria"  title="Subcategoria"/>
    <Column id="ano"           title="Ano"/>
    <Column id="vl_original"   title="Valor Original" fmt="num1m"/>
    <Column id="vl_atual"      title="Valor Atual"    fmt="num1m"/>
    <Column id="vl_aditado"    title="Aditivo"        fmt="num1m"/>
    <Column id="nu_contrato"   title="Contrato"/>
    <Column id="situacao"      title="Situação"/>
    <Column id="orgao"         title="Órgão"/>
    <Column id="objeto"        title="Objeto"/>
</DataTable>

---

## Contratos Agrupados por Fornecedor

Esta visão consolida todos os contratos de TI por fornecedor, permitindo identificar empresas com relacionamento de longo prazo com o estado e o volume total de negócios de cada uma.

```sql contratos_ti_por_fornecedor
select
    nm_contratado                               as fornecedor,
    ramo_atividade                              as subcategoria,
    string_agg(nu_contrato, ', ' order by ano_assinatura) as numeros_contrato,
    count(*)                                    as qt_contratos,
    min(ano_assinatura::integer)                as primeiro_ano,
    max(ano_assinatura::integer)                as ultimo_ano,
    count(distinct cod_unidade_gestora)         as qt_orgaos,
    sum(vl_original)                            as vl_total_original,
    sum(vl_atual)                               as vl_total_atual,
    sum(vl_aditado)                             as vl_total_aditado
from compras.fct_contratos_ramo
where ramo_atividade like 'TI -%'
group by 1, 2
order by vl_total_atual desc
```

<DataTable data={contratos_ti_por_fornecedor} title="Fornecedores de TI — Consolidado" index=false>
    <Column id="fornecedor"        title="Fornecedor"/>
    <Column id="subcategoria"      title="Subcategoria"/>
    <Column id="vl_total_original" title="Valor Original" fmt="num1m"/>
    <Column id="vl_total_atual"    title="Valor Total"    fmt="num1m"/>
    <Column id="vl_total_aditado"  title="Aditivos"       fmt="num1m"/>
    <Column id="qt_contratos"      title="Contratos"      fmt="num0"/>
    <Column id="primeiro_ano"      title="Desde"/>
    <Column id="ultimo_ano"        title="Até"/>
    <Column id="qt_orgaos"         title="Órgãos"         fmt="num0"/>
    <Column id="numeros_contrato"  title="Nº Contratos"/>
</DataTable>

---

> 💡 Volte para os [Ramos de Atividade](/Analytics-Engineer/compras-publicas/ramos), [Fornecedores por Ramo](/Analytics-Engineer/compras-publicas/fornecedores-ramo) ou para a [Visão Geral](/Analytics-Engineer/compras-publicas).