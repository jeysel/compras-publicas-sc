Como desenvolvedor de dados

Quero uma classe abstrata base_source.py

Para padronizar o comportamento de todas as fontes de ingestão

Valor: garante consistência, reuso e facilidade de manutenção.

✔ Critérios de Aceite (BDD)

Dado que o pipeline precisa suportar múltiplas fontes
Quando uma nova fonte for implementada
Então ela deve herdar de BaseSource
E implementar obrigatoriamente os métodos authenticate(), fetch_data(), normalize() e save_raw()

Dado que uma fonte executa o método run()
Quando ocorrer qualquer falha
Então a classe deve registrar logs padronizados
E lançar exceções claras e tratáveis
