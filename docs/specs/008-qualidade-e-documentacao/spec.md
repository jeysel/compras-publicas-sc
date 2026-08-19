# 008 — Qualidade e documentação (dicionário de dados, testes de ingestão/transformação)

## Tipo

Rascunho — extraído do backlog (`docs/backlog-archived/`, stories 12-14, feature 5.1, épico 5). Conteúdo colado como veio, para não se perder — **não é Design fechado, não tem Requirements em EARS ainda.**

## Status

Não iniciada.

## Resumo

`docs/backlog` planejou uma camada de qualidade/documentação (dicionário de dados, testes automatizados de ingestão e transformação) sobre o pipeline. Esse valor não depende do desenho de ingestão descartado (ver `docs/backlog-archived/README.md`) — dicionário de dados e testes de transformação seguem aplicáveis à arquitetura real (dbt + seeds + Postgres). A **story 13 (testes de ingestão)** é a exceção parcial: seu critério de aceite ("fonte configurada", "falha simulada") foi escrito pensando no desenho de `BaseSource`/scraping descartado — o conceito de testar a fonte de ingestão continua válido, mas o critério de aceite específico precisa ser reinterpretado para o fluxo real (arquivo CSV baixado manualmente/scriptado, não uma classe de fonte com `authenticate()`/`fetch_data()`).

**Observação sobre o backlog original:** o épico 5 referencia "Feature 5.2 — Testes" como feature separada de "Feature 5.1 — Documentação", mas só existe o arquivo `feature-05.1-documentacao_testes.md` (que já cobre os dois temas fundidos) — não é uma lacuna desta extração, é uma inconsistência que já existia no backlog original.

## Contexto (colado do backlog, não editado)

### Épico 5 — Documentação e Testes

> Objetivo: Garantir documentação clara e testes automatizados para estabilidade do pipeline.
> Justificativa: Documentação e testes são essenciais para manutenção, escalabilidade e confiabilidade.
> Features relacionadas: Feature 5.1 — Documentação, Feature 5.2 — Testes

### Feature 5.1 — Documentação e Testes

> Criar documentação técnica e testes automatizados.

## Requirements (material de partida — colado do backlog, a refinar em EARS quando a spec for aberta de verdade)

### Story 12 — Criar dicionário de dados

```
Como qualquer usuário do pipeline
Quero um dicionário de dados
Para entender campos, origens e transformações

Valor: aumenta transparência e governança.

✔ Critérios de Aceite (BDD)

Dado uma tabela do pipeline
Quando documentada
Então cada campo deve ter descrição, tipo e origem
```

### Story 13 — Testes de ingestão

**Nota:** critério de aceite escrito para o desenho de ingestão descartado (`BaseSource`, "fonte configurada"/"falha simulada" no sentido de uma classe de fonte scriptada) — reinterpretar para o fluxo real antes de fechar Requirements.

```
Como engenheiro de dados
Quero testes automatizados para ingestão
Para garantir estabilidade

✔ Critérios de Aceite (BDD)

Dado uma fonte configurada
Quando o teste for executado
Então deve validar retorno não vazio

Dado uma falha simulada
Quando o teste for executado
Então deve validar tratamento correto da exceção
```

### Story 14 — Testes de transformação

```
Como engenheiro de dados
Quero testes para transformações
Para garantir consistência dos dados

✔ Critérios de Aceite (BDD)

Dado dados brutos conhecidos
Quando a transformação ocorrer
Então datas e valores devem ser normalizados corretamente

Dado métricas calculadas
Quando comparadas com valores esperados
Então devem coincidir exatamente
```

## Design

_A preencher quando esta spec for aberta de verdade._

## Casos de borda

_A preencher._

## Fora do escopo

- Desenho de ingestão via scraping/API (descartado — ver `docs/backlog-archived/README.md`).

## Referências de código

_A preencher conforme a implementação._

## Ver também

- [[007-marts-e-metricas]]
