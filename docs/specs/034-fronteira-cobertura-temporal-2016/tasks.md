# Tasks — Spec 034 (fronteira de cobertura temporal: 2016 como piso)

Status: [x] concluído em 03/09/2026 — **tasks.md retroativo**

**Retroativo: reconstruído a partir do que a spec registra como executado em 2026-09-03; os comandos foram escritos depois, não são o log literal da execução.**

Formato de tarefa: o mesmo de [`_tasks.md`](../_tasks.md) (`Nível`, `Caminhos`, `Aceite`, `Parar antes de commit`). Em cada linha de `Aceite`, a marca diz a origem: **[registrado]** = o comando e/ou a saída aparecem na spec 034 (seções "Validação" e "Cutover executado"); **[reconstruído]** = a spec registra o resultado, mas o comando foi escrito agora para tornar o aceite repetível. Toda saída vem da spec; os números aparecem sem separador de milhar (a spec escreve `104.574`; o banco devolve `104574`).

Duas regras do template não se aplicam a esta instância, porque o template (2026-10-19) é posterior à execução: a branch dedicada (a spec registra push em `main` com CI) e "nenhuma tarefa comita" (a execução original comitou `a39f3db` e `8966c77`). Por isso o `TN` abaixo omite o item de "nenhum `git commit`".

Spec: [`spec.md`](spec.md) (requisitos 1 a 5 e não-funcionais 1 a 3).

---

### T1 — Corte único em `stg_contratos` e teste dbt que o vigia

Nível: médio (a mudança está na camada de staging e se propaga por herança a todos os models a jusante: intermediate, dims, facts e marts).
Caminhos: `dbt/models/staging/stg_contratos.sql`, `dbt/models/staging/schema/stg_contratos.yml`, `dbt/tests/assert_stg_contratos_cobertura_oficial.sql`.
Aceite:
- Com o filtro **removido** (`where true` na CTE `cobertura_oficial`), `dbt build` → `FAIL 1 assert_stg_contratos_cobertura_oficial` (1 linha: `CT-TESTE-PRE2016`). É o estado ANTES: prova que o teste não é tautológico. [registrado: "Teste negativo"; o `where true` é a forma exata registrada, o comando `dbt build` é a forma curta]
- Com o filtro **restaurado**, sobre o seed real (`dbt seed` + `dbt build`) → `PASS=134 WARN=0 ERROR=0 SKIP=0`. [registrado: "Cenário A"]
- `select count(*) from raw.contratos;` → `76041`; `select count(*) from stg_contratos;` → `74377` (76041 − 1664, exato). [reconstruído: a spec registra as métricas e os valores, não as consultas]
- `select min(ano_assinatura), max(ano_assinatura) from stg_contratos;` → `2016 | 2025`. [reconstruído]
- `select count(*) from stg_contratos where ano_assinatura < 2016;` → `0`; o mesmo em `fct_contratos` e em `mart_escalada_custo` → `0` em cada. [reconstruído]
- `select count(*) from raw.contratos where extract(year from dtassinatura) < 2016;` → `1664` (2013: 35, 2014: 110, 2015: 1519): a cauda continua em `raw`, não foi apagada. [reconstruído]
Parar antes de commit: sim.

### T2 — Piso 2016 no endpoint `anos-disponiveis`

Nível: baixo (uma expressão SQL; o piso é redundante com o corte do dbt de propósito, por causa do intervalo entre o deploy da API e o reprocessamento).
Caminhos: `api/app/routers/anos_disponiveis.py`.
Aceite:
- ANTES, em produção: `GET /api/v1/anos-disponiveis` → `{"ano_min":1994,"ano_max":2026}`. [registrado: "Levantamento"; o `GET` é a forma exata do endpoint]
- `GREATEST(MIN(ano_assinatura), 2016)`, simulado sobre uma `fct_contratos` com uma linha de 2005 → `2016`. [registrado: "Piso do endpoint"]
- DEPOIS, em produção: `GET /api/v1/anos-disponiveis` → `ano_min` igual a `2016`. [registrado: tabela do cutover; o `GET` é reconstruído]
Parar antes de commit: sim.

### T3 — Fixture e teste de integração do contrato pré-2016

Nível: baixo (só testes; nenhum código de produção).
Caminhos: `api/tests/fixtures/contratos.py`, `api/tests/integration/test_cobertura_oficial.py`, `api/tests/integration/test_anos_disponiveis.py`.
Aceite:
- `dbt build` sobre o seed de fixture, que ganhou a linha `CT-TESTE-PRE2016` (2014) → `PASS=134 WARN=0 ERROR=0`. [registrado: "Cenário B"]
- `select count(*) from raw.contratos;` → `9`; `select count(*) from stg_contratos;` → `8`. [reconstruído]
- `select count(*) from raw.contratos where nucontrato = 'CT-TESTE-PRE2016';` → `1`; `select count(*) from <tabela> where nu_contrato = 'CT-TESTE-PRE2016';` em `stg_contratos`, `fct_contratos` e `mart_escalada_custo` → `0` em cada. [reconstruído; `nucontrato` é a coluna em `raw`, `nu_contrato` a das camadas seguintes]
- `pytest` sobre `api/tests` → `32 passed` (26 de integração + 6 rápidos). [registrado: resultado; o comando exato foi omitido pela spec]
Parar antes de commit: sim.

### T4 — Deploy da API e metodologia (staging automático, produção por promoção)

Nível: alto (altera o que está no ar; a promoção para produção é manual, spec 015).
Caminhos: `api/app/templates/metodologia.html`, `deploy/k8s/overlays/production/kustomization.yaml`.
Aceite:
- Commits `a39f3db` (implementação) e `8966c77` (promoção de produção para `a39f3db`); CI verde com a suíte em `32 passed`. [registrado]
- Staging sincroniza sozinho; produção sincroniza na promoção, com resultado `Succeeded` e 2 pods prontos. [registrado; o comando de sincronização e de verificação ficam fora deste arquivo, porque trazem nome de infraestrutura (regra 1 da constitution)]
- `curl -s -o /dev/null -w "%{http_code}" https://contratos-sc.jeysel.dev/metodologia` → `200`, com o parágrafo novo em "Fonte e período". [reconstruído: a spec registra `/metodologia` entre as rotas com 200]
Parar antes de commit: sim.

### T5 — Reprocessar o dbt em produção, sem `seed` nem `build`

Nível: alto (escreve nas marts de produção; um `dbt seed` ou `dbt build` sobrescreveria os upserts da spec 030 em `raw.contratos`).
Caminhos: nenhum arquivo (executa no host, pela imagem do pipeline; o comando de execução fica fora deste arquivo, pela regra 1).
Aceite:
- `dbt run` → `PASS=24`. [registrado]
- `dbt test` → `PASS=109`, incluindo `assert_stg_contratos_cobertura_oficial` em PASS. [registrado]
- A sequência usa só `run` e `test`: nenhum `dbt seed`, nenhum `dbt build`, porque o `dbt seed` sobrescreveria os upserts da spec 030 em `raw.contratos`. [registrado como regra do passo]
Parar antes de commit: sim.

### T6 — Medir ANTES e DEPOIS em produção

Nível: baixo (somente leitura).
Caminhos: nenhum arquivo.
Aceite (cada linha mede o estado antes do T5 e o mesmo comando depois dele; banco `compras_publicas`):
- `select count(*) from raw.contratos;` → antes `104574` (24937 anteriores a 2016); depois `104574`, **inalterado**. [valores registrados; consulta reconstruída]
- `select count(*), min(ano_assinatura) from stg_contratos;` → antes `104574 | 1994`; depois `79637 | 2016`. [valores registrados; consulta reconstruída]
- `select count(*) from mart_escalada_custo;` e `select count(*) from fct_contratos;` → antes `104574` em cada; depois `79637` em cada. [valores registrados; consultas reconstruídas]
- `GET /api/v1/kpis-resumo`, campo `total_contratos` → antes `104574`; depois `79637`. [valores registrados; `GET` reconstruído]
- `GET /api/v1/anos-disponiveis`, campo `ano_min` → antes `1994`; depois `2016`. [valores registrados; `GET` reconstruído]
Parar antes de commit: sim.

### T7 — Smoke das rotas públicas

Nível: baixo (somente leitura).
Caminhos: nenhum arquivo.
Aceite:
- As 9 rotas verificadas (`/`, `/metodologia`, as páginas de gráficos e as rotas `/api/v1/*`) → todas `200`. [registrado: "Smoke test de 9 rotas: todas 200"; a lista completa das 9 não está na spec, então o comando não é reproduzido aqui]
- `raw.contratos` continua com `104574` linhas depois do smoke (a cauda foi preservada, só saiu do escopo analítico). [registrado]
Parar antes de commit: sim.

### TN — Encerrar a execução e relatar (sem commit)

Nível: baixo.
Caminhos: nenhum.
Aceite:
- `git status --porcelain` lista exatamente os arquivos de `Caminhos` das tarefas anteriores. [reconstruído]
- `git diff --stat` é anexado ao relatório final para o usuário revisar. [reconstruído]
Parar antes de commit: sim — este é o ponto de parada definitivo da execução.

---

## Depois das tarefas

1. O Status da spec 034 já registra "No ar em produção (2026-09-03)".
2. O que é **registrado** e o que é **reconstruído** está marcado por linha de `Aceite`: as saídas vêm da spec; os comandos marcados como reconstruídos nunca foram o log literal.
