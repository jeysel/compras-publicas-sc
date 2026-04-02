---
title: Contratos Não Classificados
---

> Esta página reúne os contratos cujo objeto não se enquadra nas categorias identificadas por palavras-chave. São contratos com descrições muito específicas, técnicas ou atípicas — que representam a diversidade e complexidade das contratações públicas estaduais.

**Metodologia:** A classificação por ramo é baseada em palavras-chave do campo objeto do contrato. Contratos com descrições que não correspondem a nenhuma categoria são agrupados aqui como "Outros".

---

## Panorama

```sql kpis_outros
select
    count(*)                            as qt_contratos,
    count(distinct id_contratado)       as qt_fornecedores,
    count(distinct cod_unidade_gestora) as qt_orgaos,
    sum(vl_original)                    as vl_total_original,
    sum(vl_atual)                       as vl_total_atual,
    sum(vl_aditado)                     as vl_total_aditado
from compras.fct_contratos_ramo
where ramo_atividade = 'Outros'
```

<BigValue data={kpis_outros} value="qt_contratos"     title="Contratos"        fmt="num1k"/>
<BigValue data={kpis_outros} value="qt_fornecedores"  title="Fornecedores"     fmt="num1k"/>
<BigValue data={kpis_outros} value="qt_orgaos"        title="Órgãos"           fmt="num0"/>
<BigValue data={kpis_outros} value="vl_total_atual"   title="Valor Total"      fmt="num1b"/>
<BigValue data={kpis_outros} value="vl_total_aditado" title="Total em Aditivos" fmt="num1b"/>

---

## Quais órgãos mais contratam nesta categoria?

```sql orgaos_outros
select
    nm_unidade_gestora                  as orgao,
    count(*)                            as qt_contratos,
    count(distinct id_contratado)       as qt_fornecedores,
    sum(vl_atual)                       as vl_total
from compras.fct_contratos_ramo
where ramo_atividade = 'Outros'
group by 1
order by vl_total desc
limit 15
```

<DataTable data={orgaos_outros} title="Top 15 Órgãos por Valor Total" index=false>
    <Column id="orgao"           title="Órgão"/>
    <Column id="qt_contratos"    title="Qtd. Contratos" fmt="num0"/>
    <Column id="qt_fornecedores" title="Fornecedores"   fmt="num0"/>
    <Column id="vl_total"        title="Valor Total"    fmt="num1b"/>
</DataTable>

---

## Principais fornecedores

```sql fornecedores_outros
select
    nm_contratado                       as fornecedor,
    id_contratado                       as cnpj,
    count(*)                            as qt_contratos,
    count(distinct cod_unidade_gestora) as qt_orgaos,
    sum(vl_atual)                       as vl_total
from compras.fct_contratos_ramo
where ramo_atividade = 'Outros'
group by 1, 2
order by vl_total desc
limit 20
```

<DataTable data={fornecedores_outros} title="Top 20 Fornecedores por Valor Total" index=false>
    <Column id="fornecedor"    title="Fornecedor"/>
    <Column id="qt_contratos"  title="Qtd. Contratos" fmt="num0"/>
    <Column id="qt_orgaos"     title="Órgãos"         fmt="num0"/>
    <Column id="vl_total"      title="Valor Total"    fmt="num1b"/>
</DataTable>

---

## Contratos (Top 100 por Valor)

```sql contratos_outros
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
where ramo_atividade = 'Outros'
order by vl_atual desc
limit 100
```

<DataTable data={contratos_outros} title="Top 100 Contratos Não Classificados por Valor" index=false>
    <Column id="nu_contrato"   title="Contrato"/>
    <Column id="fornecedor"    title="Fornecedor"/>
    <Column id="orgao"         title="Órgão"/>
    <Column id="objeto"        title="Objeto"/>
    <Column id="ano"           title="Ano"/>
    <Column id="vl_original"   title="Valor Original" fmt="num1b"/>
    <Column id="vl_atual"      title="Valor Atual"    fmt="num1b"/>
    <Column id="vl_aditado"    title="Aditivo"        fmt="num1b"/>
    <Column id="situacao"      title="Situação"/>
</DataTable>

---

> 💡 Volte para os [Ramos de Atividade](/Analytics-Engineer/compras-publicas/ramos), [Fornecedores por Ramo](/Analytics-Engineer/compras-publicas/fornecedores-ramo) ou para a [Visão Geral](/Analytics-Engineer/compras-publicas).