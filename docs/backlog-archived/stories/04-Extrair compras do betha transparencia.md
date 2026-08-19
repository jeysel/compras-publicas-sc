Como pipeline de ingestão

Quero extrair dados de compras do Betha Transparência

Para complementar o conjunto de dados com informações municipais

Valor: amplia cobertura de dados e permite análises comparativas.

✔ Critérios de Aceite (BDD)

Dado que a API ou scraping do Betha está acessível
Quando o pipeline executar a ingestão
Então os dados de compras devem ser extraídos corretamente

Dado que os dados foram extraídos
Quando forem salvos
Então devem ser armazenados em /data/raw/betha

Dado que a ingestão está em execução
Quando ocorrer sucesso ou erro
Então logs devem registrar o status da operação
