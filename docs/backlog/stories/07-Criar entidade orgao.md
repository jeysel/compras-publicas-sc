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
Então devem ser diferenciados por fonte ou identificador únic
