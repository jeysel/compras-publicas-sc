Como engenheiro de dados
Quero padronizar todas as datas para o formato ISO
Para garantir consistência entre fontes diferentes

Valor: evita erros em transformações e análises.

✔ Critérios de Aceite (BDD)

Dado um conjunto de datas em formatos variados
Quando forem processadas na camada staging
Então todas devem ser convertidas para YYYY-MM-DD

Dado que uma data inválida for encontrada
Quando a normalização ocorrer
Então ela deve ser registrada em log
E marcada como nula ou descartada conforme regra definida
