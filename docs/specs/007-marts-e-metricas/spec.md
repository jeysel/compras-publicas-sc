# 007 — Marts e métricas (entidades, licitado vs contratado, competitividade, séries temporais)

## Tipo

Rascunho — extraído do backlog (`docs/backlog-archived/`, stories 07-11 e 15-16, features 3.1/4.1, épicos 3/4). Conteúdo colado como veio, para não se perder — **não é Design fechado, não tem Requirements em EARS ainda.**

## Status

Não iniciada.

## Resumo

`docs/backlog` (épicos, features, stories escritos em 2026-04-28) planejou uma camada core de entidades (Órgão, Compra, Item, Fornecedor, Contrato) e marts de métricas (licitado vs. contratado, competitividade, séries temporais) sobre um desenho de ingestão multi-fonte que foi descartado (ver `docs/backlog-archived/README.md`). O desenho de **entidades e métricas em si** não foi descartado — é o valor real que sobrou do backlog, mas ainda não tem spec própria cobrindo como ele se encaixa na arquitetura real (specs 003-006: dbt + seeds + Postgres, grão "1 registro = 1 contrato", chave `(cdunidadegestora, nucontrato)`, sem entidade "Compra" separada confirmada nos dados reais).

**Nota de revisão (a resolver quando esta spec for aberta de verdade):** o conteúdo abaixo assume uma entidade "Compra"/licitação distinta de "Contrato", com relação um-para-muitos com "Fornecedor" (ex.: story 11, contar fornecedores por compra). Isso **não foi confirmado** contra os dados reais explorados nas specs 003-006 — o dado disponível (`contratos.csv`/`seeds/contratos.csv`) tem grão de contrato único por fornecedor (`idcontratado`/`contratado`), sem uma entidade de licitação/processo licitatório com múltiplos participantes já modelada. Antes de fechar Requirements desta spec, confirmar se esse dado existe em algum lugar (ex.: `nuprocesso`, `nuedital`, `nmmodalidade` já presentes em `contratos.csv` podem ser o material bruto de uma entidade "licitação", mas isso é hipótese, não investigação feita).

## Contexto (colado do backlog, não editado)

### Épico 3 — Core (Modelagem)

> Objetivo: Criar o modelo de dados principal do domínio de compras públicas.
> Justificativa: A camada core representa entidades fundamentais como Órgão, Compra, Item, Fornecedor e Contrato.

### Épico 4 — Marts Analíticos

> Objetivo: Criar métricas analíticas derivadas do core, permitindo análises avançadas.
> Justificativa: Os marts são a camada final de consumo analítico, onde métricas como licitado vs contratado são calculadas.

### Feature 3.1 — Criar entidades principais

> Criar entidades Órgão, Compra, Item, Fornecedor e Contrato.

### Feature 4.1 — Criar métricas principais

> Criar métricas analíticas derivadas do core.

## Requirements (material de partida — colado do backlog, a refinar em EARS quando a spec for aberta de verdade)

### Story 07 — Criar entidade Órgão

```
Como analista de dados
Quero uma entidade padronizada de Órgão
Para identificar corretamente quem realizou a compra

Valor: permite análises por órgão e comparações.

✔ Critérios de Aceite (BDD)

Dado dados brutos de diferentes fontes
Quando forem modelados
Então a entidade Órgão deve conter: ID, nome, esfera, município

Dado que dois órgãos tenham o mesmo nome
Quando forem carregados
Então devem ser diferenciados por fonte ou identificador único
```

### Story 08 — Criar entidade Compra

```
Como analista de compras públicas
Quero uma entidade Compra consolidada
Para analisar modalidades, objetos, datas e valores

Valor: base para métricas de licitado vs contratado.

✔ Critérios de Aceite (BDD)

Dado dados brutos de compras
Quando forem modelados
Então a entidade deve conter modalidade, objeto, datas e valores

Dado que uma compra tenha múltiplos fornecedores
Quando for carregada
Então deve manter relacionamento correto
```

### Story 09 — Criar entidade Contrato

```
Como analista de dados
Quero uma entidade Contrato
Para relacionar valores contratados às compras

Valor: habilita cálculo de economia e eficiência.

✔ Critérios de Aceite (BDD)

Dado dados brutos de contratos
Quando forem modelados
Então a entidade deve conter valor contratado e datas

Dado que um contrato pertença a uma compra
Quando for carregado
Então deve manter relacionamento compra ↔ contrato
```

### Story 10 — Métrica licitado vs. contratado

```
Como gestor público
Quero comparar valores licitados e contratados
Para avaliar economia ou sobrepreço
Valor: métrica central do projeto.

✔ Critérios de Aceite (BDD)

Dado valores licitados e contratados
Quando a métrica for calculada
Então deve gerar o campo economia = licitado - contratado

Dado que a métrica seja agregada
Quando filtrada por órgão, modalidade ou fornecedor
Então os resultados devem refletir corretamente os agrupamentos
```

### Story 11 — Métrica de competitividade

```
Como analista de compras
Quero medir quantos fornecedores participaram de cada compra
Para avaliar competitividade

Valor: permite identificar compras com baixa concorrência.

✔ Critérios de Aceite (BDD)

Dado uma compra com fornecedores associados
Quando a métrica for calculada
Então deve contar corretamente o número de fornecedores

Dado que a métrica seja usada para ranking
Quando agregada
Então deve ordenar corretamente por competitividade
```

### Story 15 — Métrica temporal: valor licitado por tipo

```
Dado um conjunto de licitações contendo valores licitados, datas e modalidade de licitações
Quando a métrica temporal for calculada
Então o pipeline deve gerar uma série histórica agregada por ano e modalidade de licitação
E deve utilizar Window Functions para calcular variações percentuais e médias móveis

Agregação e filtros
Dado que a métrica esteja disponível nos marts
Quando o usuário aplicar filtros por tipo, órgão ou modalidade
Então a série temporal deve refletir corretamente os agrupamentos selecionados

Visualização
Dado que a métrica temporal esteja calculada
Quando os dados forem consumidos por ferramentas analíticas
Então deve ser possível gerar gráficos de linha ou área mostrando a evolução anual
E a estrutura dos dados deve permitir visualizações como:
- Evolução do valor total licitado por tipo
- Comparação entre tipos ao longo do tempo
- Variação percentual ano a ano
- Média móvel (ex.: 3 anos)

Qualidade e consistência
Dado que existam anos sem registros para determinado tipo
Quando a série temporal for construída
Então o pipeline deve preencher com zero ou manter o ano ausente conforme regra definida
Dado que existam valores inválidos ou datas inconsistentes
Quando a métrica for calculada
Então esses registros devem ser descartados ou corrigidos conforme regras de staging
E logs devem registrar as inconsistências

✔ Observações técnicas
- A métrica deve ser construída na camada marts
- Deve utilizar Window Functions, como:
- SUM(value) OVER (PARTITION BY tipo ORDER BY ano)
- LAG() para variação ano a ano
- AVG() OVER (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) para média móvel
- Deve ser armazenada em uma tabela analítica como:
mart_licitacoes_temporal
```

### Story 16 — Métrica temporal: evolução de contratos por tipo

```
Como gestor público
Quero visualizar a evolução temporal dos valores contratados por tipo de contrato
Para analisar tendências, sazonalidades e padrões de contratação ao longo dos anos, considerando também a licitação que originou cada contrato

Valor: permite avaliar comportamento histórico das contratações, identificar períodos de maior gasto, comparar modalidades e entender a relação entre licitações e contratos.

✔ Critérios de Aceite (BDD)

Cálculo da métrica
Dado um conjunto de contratos contendo valores contratados, datas, tipo de contrato e referência à licitação (número, ano e modalidade)
Quando a métrica temporal for calculada
Então o pipeline deve gerar uma série histórica agregada por ano e tipo de contrato
E deve incluir os campos:
- número da licitação
- ano da licitação
- modalidade da licitação
E deve utilizar Window Functions para calcular:
- variação percentual ano a ano
- média móvel (ex.: 3 anos)

Agregação e filtros
Dado que a métrica esteja disponível nos marts
Quando o usuário aplicar filtros por tipo de contrato, órgão, modalidade de licitação ou ano
Então a série temporal deve refletir corretamente os agrupamentos selecionados

Visualização
Dado que a métrica temporal esteja calculada
Quando os dados forem consumidos por ferramentas analíticas
Então deve ser possível gerar gráficos de linha ou área mostrando a evolução anual dos contratos
E a estrutura dos dados deve permitir visualizações como:
- Evolução do valor total contratado por tipo
- Comparação entre tipos ao longo do tempo
- Evolução por modalidade de licitação
- Variação percentual ano a ano
- Média móvel (ex.: 3 anos)

Qualidade e consistência
Dado que existam anos sem registros para determinado tipo de contrato
Quando a série temporal for construída
Então o pipeline deve preencher com zero ou manter o ano ausente conforme regra definida
Dado que existam valores inválidos, datas inconsistentes ou contratos sem vínculo com licitação
Quando a métrica for calculada
Então esses registros devem ser descartados ou corrigidos conforme regras de staging
E logs devem registrar as inconsistências

✔ Observações técnicas
- A métrica deve ser construída na camada marts
- Deve utilizar Window Functions, como:
- SUM(value) OVER (PARTITION BY tipo ORDER BY ano)
- LAG() para variação ano a ano
- AVG() OVER (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) para média móvel
- Deve ser armazenada em uma tabela analítica como:
mart_contratos_temporal
- Deve incluir chave composta para relacionar contrato ↔ licitação:
- numero_licitacao
- ano_licitacao
- modalidade_licitacao
```

## Design

_A preencher quando esta spec for aberta de verdade — depende de resolver a nota de revisão acima (existe ou não uma entidade "licitação"/"compra" separada do "contrato" nos dados reais) e de reconciliar com o grão já fechado em [[005-grao-do-dado-contrato-vs-aditivo]]._

## Casos de borda

_A preencher._

## Fora do escopo

- Desenho de ingestão (descartado — ver `docs/backlog-archived/README.md`).
- Normalização de data/valor monetário (feature 2.1, stories 05-06) — permanece só no arquivo, não migrada para esta spec.

## Referências de código

_A preencher conforme a implementação._

## Ver também

- [[003-storage-e-chave-unica]]
- [[005-grao-do-dado-contrato-vs-aditivo]]
- [[006-backfill-historico]]
- [[008-qualidade-e-documentacao]]
