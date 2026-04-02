---
title: Aditivos Contratuais
---

> Aditivos contratuais são alterações realizadas após a assinatura do contrato original — podem modificar o valor, o prazo, ou ambos. Embora previstos em lei, aditivos excessivos ou recorrentes merecem atenção do ponto de vista do controle social sobre a gestão dos recursos públicos.

**Regra de negócio:** Valor Atual = Valor Original + Valor Aditado

---

## Contexto Legal

As contratações públicas são regidas por duas legislações vigentes, com limites distintos para aditivos:

**Lei nº 8.666/1993** — legislação anterior, ainda aplicável a contratos firmados antes da transição obrigatória:
- Acréscimos e supressões unilaterais limitados a **25%** do valor inicial para obras, serviços e compras
- Para reformas de edifícios e equipamentos, o limite é de **50%**

**Lei nº 14.133/2021** — nova lei de licitações, obrigatória para novos contratos e renovações (Art. 125):
- **Regra geral:** acréscimos ou supressões unilaterais de até **25%** para compras, obras e serviços
- **Exceção para reformas:** até **50%** de acréscimo
- **Supressões consensuais:** podem ultrapassar 25% desde que haja acordo entre as partes
- Reajustes de preços previstos em contrato (ex: inflação) **não contam** para esses limites e são feitos por apostila

> ⚠️ As alterações não podem transfigurar o objeto da licitação — ou seja, não podem mudar a natureza do que foi contratado originalmente.

---

## Panorama dos Aditivos

De um total de **76 mil contratos**, apenas **1.951** sofreram aditivos — menos de **3% do total**. No entanto, esses contratos respondem por um impacto financeiro significativo: **R$ 1,6 bilhão** em acréscimos sobre um valor original de R$ 9,7 bilhões.

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

## Que tipo de alteração foi feita?

A maioria dos aditivos altera **valor e prazo simultaneamente** — o que sugere que as mudanças geralmente refletem uma renegociação mais ampla do contrato, e não apenas ajustes pontuais.

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
    xAxisTitle="Tipo"
    yAxisTitle="Quantidade"
/>

<DataTable data={tipo_aditivo} title="Tipo de Aditivo" index=false>
    <Column id="tipo"             title="Tipo de Aditivo"/>
    <Column id="qt_contratos"     title="Qtd. Contratos" fmt="num0"/>
    <Column id="vl_total_aditado" title="Valor Aditado"  fmt="num1b"/>
</DataTable>

---

## Qual foi a magnitude das alterações?

A maior parte dos aditivos representa acréscimos dentro dos limites legais previstos. Aditivos que ultrapassam os percentuais permitidos pelas Leis 8.666/1993 e 14.133/2021 devem ter justificativa formal e podem indicar falhas no planejamento da contratação original.

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

<DataTable data={faixa_variacao} title="Faixa de Variação de Valor" index=false>
    <Column id="faixa"            title="Faixa de Variação"/>
    <Column id="qt_contratos"     title="Qtd. Contratos"       fmt="num0"/>
    <Column id="vl_total_aditado" title="Valor Aditado"        fmt="num1b"/>
    <Column id="perc_medio"       title="% Médio de Alteração" fmt="num2"/>
</DataTable>

---

## Quais contratos tiveram os maiores aditivos?

Os 20 maiores aditivos por valor revelam contratos de grande porte — principalmente nas áreas de infraestrutura, segurança pública e saúde — que tiveram seus valores substancialmente revisados após a assinatura. Vale verificar se as alterações estão dentro dos limites legais e se houve justificativa formal registrada.

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

<DataTable data={top_aditivos} title="Top 20 Maiores Aditivos por Valor" index=false>
    <Column id="nu_contrato"    title="Contrato"/>
    <Column id="fornecedor"     title="Fornecedor"/>
    <Column id="orgao"          title="Órgão"/>
    <Column id="vl_original"    title="Valor Original"    fmt="num1b"/>
    <Column id="vl_aditado"     title="Valor Aditado"     fmt="num1b"/>
    <Column id="vl_atual"       title="Valor Atual"       fmt="num1b"/>
    <Column id="perc_alteracao" title="% Alteração"       fmt="num2"/>
    <Column id="tipo"           title="Tipo"/>
</DataTable>

---

> 💡 Volte para a [Visão Geral](/Analytics-Engineer/compras-publicas) ou explore os [Órgãos](/Analytics-Engineer/compras-publicas/orgaos), [Fornecedores](/Analytics-Engineer/compras-publicas/fornecedores) e [Modalidades](/Analytics-Engineer/compras-publicas/modalidades).