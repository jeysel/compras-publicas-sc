---
title: Fornecedores por Ramo de Atividade
---

> Quais fornecedores dominam cada setor? Esta análise cruza o perfil dos fornecedores com os ramos de atividade, revelando especialização, concentração de mercado e os contratos individuais por segmento.

---

## Selecione um Ramo de Atividade

```sql ramos_disponiveis
select distinct
    ramo_atividade              as ramo
from compras.fct_contratos_ramo
where ramo_atividade != 'Outros'
order by ramo_atividade
```

<Dropdown
    data={ramos_disponiveis}
    name=ramo_selecionado
    value=ramo
    title="Ramo de Atividade"
    defaultValue="Alimentação"
/>

---

## Resumo do Ramo Selecionado

```sql kpis_ramo
select
    count(*)                            as qt_contratos,
    count(distinct id_contratado)       as qt_fornecedores,
    count(distinct cod_unidade_gestora) as qt_orgaos,
    sum(vl_original)                    as vl_total_original,
    sum(vl_atual)                       as vl_total_atual,
    sum(vl_aditado)                     as vl_total_aditado
from compras.fct_contratos_ramo
where ramo_atividade = '${inputs.ramo_selecionado.value}'
```

<BigValue data={kpis_ramo} value="qt_contratos"    title="Contratos"          fmt="num0"/>
<BigValue data={kpis_ramo} value="qt_fornecedores" title="Fornecedores"       fmt="num0"/>
<BigValue data={kpis_ramo} value="qt_orgaos"       title="Órgãos"             fmt="num0"/>
<BigValue data={kpis_ramo} value="vl_total_atual"  title="Valor Total"        fmt="num1b"/>
<BigValue data={kpis_ramo} value="vl_total_aditado" title="Total em Aditivos" fmt="num1b"/>

---

## Top Fornecedores no Ramo

```sql top_fornecedores_ramo
select
    nm_contratado                       as fornecedor,
    id_contratado                       as cnpj,
    count(*)                            as qt_contratos,
    count(distinct cod_unidade_gestora) as qt_orgaos,
    sum(vl_original)                    as vl_total_original,
    sum(vl_atual)                       as vl_total_atual,
    sum(vl_aditado)                     as vl_total_aditado
from compras.fct_contratos_ramo
where ramo_atividade = '${inputs.ramo_selecionado.value}'
group by 1, 2
order by vl_total_atual desc
limit 20
```

<DataTable data={top_fornecedores_ramo} title="Top 20 Fornecedores por Valor Total" index=false>
    <Column id="fornecedor"       title="Fornecedor"/>
    <Column id="cnpj"             title="CNPJ"/>
    <Column id="qt_contratos"     title="Qtd. Contratos"  fmt="num0"/>
    <Column id="qt_orgaos"        title="Órgãos"          fmt="num0"/>
    <Column id="vl_total_original" title="Valor Original" fmt="num1b"/>
    <Column id="vl_total_atual"   title="Valor Total"     fmt="num1b"/>
    <Column id="vl_total_aditado" title="Aditivos"        fmt="num1b"/>
</DataTable>

---

## Contratos do Ramo

```sql contratos_ramo
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
where ramo_atividade = '${inputs.ramo_selecionado.value}'
order by vl_atual desc
limit 100
```

<DataTable data={contratos_ramo} title="Contratos do Ramo (Top 100 por Valor)" index=false>
    <Column id="nu_contrato"  title="Contrato"/>
    <Column id="fornecedor"   title="Fornecedor"/>
    <Column id="orgao"        title="Órgão"/>
    <Column id="objeto"       title="Objeto"/>
    <Column id="ano"          title="Ano"/>
    <Column id="vl_original"  title="Valor Original" fmt="num1b"/>
    <Column id="vl_atual"     title="Valor Atual"    fmt="num1b"/>
    <Column id="vl_aditado"   title="Aditivo"        fmt="num1b"/>
    <Column id="situacao"     title="Situação"/>
</DataTable>

---

> 💡 Volte para a [Visão Geral](/Analytics-Engineer/compras-publicas) ou explore os [Ramos de Atividade](/Analytics-Engineer/compras-publicas/ramos), [Fornecedores](/Analytics-Engineer/compras-publicas/fornecedores) e [Órgãos](/Analytics-Engineer/compras-publicas/orgaos).