Como pipeline de ingestão

Quero extrair contratos vinculados às compras

Para permitir análises de licitado vs contratado

Valor: habilita métricas essenciais do projeto.

✔ Critérios de Aceite (BDD)

Dado que compras foram extraídas
Quando a ingestão de contratos for executada
Então cada contrato deve ser associado à compra correspondente

Dado que contratos foram extraídos
Quando forem salvos
Então devem ser armazenados em /data/raw/transparencia_sc


