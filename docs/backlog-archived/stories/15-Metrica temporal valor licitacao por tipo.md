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


