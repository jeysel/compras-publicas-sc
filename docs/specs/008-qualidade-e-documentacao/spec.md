# 008 — Qualidade e documentação (dicionário de dados, testes)

## Tipo

Decisão de arquitetura — substitui a versão anterior (rascunho extraído do backlog), conectando as stories ao que já está decidido no resto do projeto.

## Status

Design definido. Requirements (EARS) formalizados.

## Resumo

A versão anterior desta spec (extraída do backlog) tinha valor real (dicionário de dados, testes de ingestão/transformação), mas a story 13 (testes de ingestão) foi escrita para um desenho de ingestão (`BaseSource`, scraping) que foi descartado. Esta spec fecha isso conectando as três stories ao que já foi decidido: dicionário de dados via `schema.yml`/`dbt docs` (specs 003-007), testes de ingestão via os pontos de falha já desenhados na spec 009 (CronJob, ETag, validação de schema), testes de transformação via dbt tests nas chaves e métricas já fechadas (specs 003/005/007).

## Contexto

- Observação preservada da versão anterior: o backlog original referenciava "Feature 5.2 — Testes" como arquivo separado de "Feature 5.1 — Documentação", mas só existe o arquivo fundido — inconsistência do backlog original, não desta extração, sem necessidade de correção retroativa.
- Dicionário de dados não depende de ferramenta nova: dbt já suporta `description` por model/coluna em `schema.yml`, e `dbt docs generate` já está documentado como passo manual no README do projeto.
- Spec 009 já desenhou os pontos de falha do pipeline de ingestão real (verificação de `ETag`, validação de schema mínimo antes do `dbt run`, comportamento em caso de arquivo corrompido) — isso substitui o critério de aceite original da story 13 sem precisar de reinterpretação especulativa.
- Specs 003, 005 e 007 já fecharam as chaves e regras de negócio que precisam virar teste estrutural: `(cdunidadegestora, nucontrato)`, `(cdunidadegestora, nuprocesso)`, `idcontratado` como chave de fornecedor, `nmunidadegestora`/`contratado` nunca como chave.

## Requirements

### Funcionais

1. O sistema DEVE documentar, em `schema.yml` do dbt, uma `description` para cada model das camadas staging/core/marts, e para cada coluna que seja chave ou tenha regra de negócio conhecida — no mínimo: `cdunidadegestora`, `nucontrato`, `nuprocesso` (com nota sobre placeholders — spec 007), `idcontratado` (com nota sobre CPF/CNPJ — spec 007), `nmunidadegestora` e `contratado` (com nota "nunca usar como chave" — specs 003/005/007).

2. `dbt docs generate` DEVE continuar disponível como passo documentado (já está no README) — esta spec não adiciona automação nova a esse passo, só formaliza que ele é a fonte do dicionário de dados exigido pela story 12 original.

3. Os testes de ingestão (antiga story 13) DEVEM cobrir os três cenários já desenhados na spec 009: (a) `ETag` igual ao salvo → job não reprocessa; (b) `ETag` diferente → job aciona download e processamento; (c) arquivo com schema inválido (colunas ausentes, contagem de linhas zero, ou malformado como o incidente `contratos-2022.csv` da spec 006) → job falha, não sobrescreve o dado já processado, não atualiza o `ETag` salvo.

4. Os testes de transformação (antiga story 14) DEVEM incluir, no mínimo: testes de schema dbt (`unique`, `not_null`) para as chaves compostas já fechadas (`(cdunidadegestora, nucontrato)` — spec 003/005; `(cdunidadegestora, nuprocesso)` — spec 007); e testes customizados para as regras de negócio das métricas da spec 007 (ex.: `mart_diversidade_vencedores` conta `idcontratado` distintos, não `contratado`).

5. QUANDO uma métrica da spec 007 tiver um valor de referência calculável de forma independente (ex.: escalada de custo de uma amostra pequena, verificada manualmente), O sistema DEVE ter pelo menos um teste dbt comparando o resultado do model contra esse valor — não só teste estrutural (tipo/nulidade), também teste de corretude do cálculo.

### Não-funcionais

1. A documentação de `schema.yml` DEVE ser atualizada no mesmo commit que introduzir ou alterar um model — não DEVE ficar como tarefa separada "pra depois", para não repetir o padrão de spec desatualizada em relação ao código real que já causou retrabalho neste projeto (specs 002/003 remediadas, spec 007 reescrita).

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| Dicionário de dados | `schema.yml` (dbt) + `dbt docs generate` | Já suportado pelo dbt, já documentado no README — não precisa de ferramenta nova, precisa de conteúdo real preenchido |
| Testes de ingestão | Cobrir os 3 cenários já desenhados na spec 009 (ETag igual/diferente/schema inválido) | Substitui o critério de aceite original (escrito pro desenho de `BaseSource` descartado) por algo que já está especificado, não especulativo |
| Testes de transformação | dbt tests: schema (`unique`/`not_null`) + testes customizados de corretude de métrica | Mapeia direto pras chaves e regras já fechadas nas specs 003/005/007 |

### Componentes afetados

- `schema.yml` de cada model das camadas staging/core/marts (specs 003-007).
- Suite de teste do `CronJob` (spec 009) — testes unitários/integração do script de verificação `ETag`/validação de schema, não testes de uma classe `BaseSource` inexistente.
- Testes customizados dbt (`tests/` ou `macros/` de teste singular, conforme convenção do projeto).

## Casos de borda

- Falha de um dbt test durante a execução do `CronJob` (spec 009): deve ser tratada com a mesma disciplina de falha de validação de schema — job termina com erro visível, não segue como se tivesse dado certo.
- Teste de corretude de métrica (Requirement 5) fica sem cobertura se nenhuma métrica tiver valor de referência fácil de calcular manualmente — não é motivo para pular o teste, é motivo para escolher uma amostra pequena o suficiente pra verificar à mão antes de escrever o teste.

## Fora do escopo

- Desenho de ingestão via scraping/API (descartado — ver `docs/backlog-archived/README.md`).
- Cobertura de teste 100% ou métricas de cobertura formais — não foi definido como meta deste projeto.

## Referências de código

_A preencher conforme a implementação._

## Ver também

- [[003-storage-e-chave-unica]]
- [[005-grao-do-dado-contrato-vs-aditivo]]
- [[007-marts-e-metricas]]
- [[009-automacao-da-ingestao]]