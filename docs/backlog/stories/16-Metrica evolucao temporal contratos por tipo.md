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


