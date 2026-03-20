Como pipeline de ingestão

Quero extrair dados de compras do portal Transparência SC

Para alimentar a camada raw com dados brutos confiáveis

Valor: habilita o início do fluxo de dados do pipeline.

✔ Critérios de Aceite (BDD)

Dado que o portal Transparência SC está acessível
Quando o pipeline executar a ingestão
Então os dados de compras devem ser extraídos corretamente

Dado que os dados foram extraídos
Quando forem salvos
Então devem ser armazenados em /data/raw/transparencia_sc

Dado que a ingestão está em execução
Quando ocorrer sucesso ou erro
Então logs devem ser registrados com timestamp e contexto
