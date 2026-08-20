# 012 — Eixo frontend: biblioteca de gráfico e arquitetura de serving

## Tipo

Decisão de arquitetura — abre o eixo frontend (último dos três definidos no início do planejamento: storage → pipeline → frontend).

## Status

Design principal fechado: biblioteca de gráfico (ECharts), backend (FastAPI), estratégia de renderização (Jinja2 + TypeScript sem framework, tipos gerados via OpenAPI). Requirements (EARS) formalizados no adendo abaixo.

**API FastAPI implementada e validada (2026-08-20)** — os 6 endpoints (`escalada-custo`, `diversidade-vencedores`, `contratos-temporal`, `concentracao-fornecedor`, `orgaos`, `modalidades`) existem em `api/`, testados contra o Postgres de dev real (curl + teste unitário de mascaramento, ver Referências de código). Pendente: camada de renderização (Jinja2 + TypeScript + ECharts) — consome esta API, ainda não implementada.

## Resumo

Decisão tomada fora de spec, nesta sessão: **ECharts** como biblioteca de gráfico, em vez de Plotly (mais popular no Brasil, mas mais "esperado"/comum em portfólio de analytics Python) e Observable Plot (descartado por sobrepor conceitualmente com o motor que já roda por baixo do Evidence, ferramenta que este projeto está deixando). Também decidido: **FastAPI** como backend, e **Jinja2 (esqueleto) + TypeScript sem framework de componente (tipos gerados via OpenAPI)** como estratégia de renderização. Falta ainda: mapear quais marts/endpoints concretos existem (depende da spec 007).

## Contexto

- Motivação de origem (fora de spec, registrada aqui pra não se perder): o projeto é peça de portfólio pra transição de carreira (analista de sistemas/requisitos → analytics engineer). A escolha de não usar Streamlit/PowerBI/Looker é deliberada — quer demonstrar competência de modelagem e serving de dado, não de montagem de BI pronto.
- Risco já identificado e mitigado na discussão: gastar esforço de engenharia em frontend "genérico" (roteamento, auth, componente de UI) desvia do que a vaga de AE avalia. Decisão de manter o backend como camada fina servindo dado já modelado pelo dbt (specs 003-009), não como aplicação web completa.
- Spec 007 (rascunho, ainda não formalizada) já tem o desenho de entidades/métricas que o frontend vai consumir — a ordem correta é fechar 007 antes (ou em paralelo) de decidir os endpoints específicos desta spec.
- FastAPI já é usado no projeto weather-analytics — reaproveitamento consciente, avaliado e confirmado: a diferenciação de portfólio está na camada de dado, não no framework web escolhido.

## Investigação

_A completar. Itens a levantar antes do Design final:_

- Levantar quais marts/modelos da spec 007 (quando formalizada) correspondem a quais visualizações — não desenhar endpoint antes de saber o que a camada de dado efetivamente expõe.
- Confirmar se o `Deployment`/`Ingress` já parametrizados na spec 011 cobrem as necessidades do frontend (ex.: precisa de rota estática pra assets do ECharts/build do Vite, ou tudo serve via FastAPI mesmo — `StaticFiles` do FastAPI servindo o bundle gerado, ou um passo de build separado no `CronJob`/pipeline de deploy).
- Confirmar geração automática de tipos: testar `openapi-typescript` (ou equivalente) contra o schema real do FastAPI assim que os primeiros endpoints existirem — não presumir que a geração funciona sem atrito antes de tentar.

## Requirements

_A preencher após a Investigação e fechamento da spec 007._

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| Biblioteca de gráfico | **ECharts** | Vocabulário visual (treemap, sankey, calendar heatmap) adequado ao domínio de gasto público; performance em Canvas para o volume real de dado (76 mil+ linhas); reforça a tese de portfólio (usado em BI de produção como Superset, não é o padrão "de curso" como Plotly); evita sobreposição conceitual com o motor do Evidence (Observable Plot) |
| Framework de backend | **FastAPI** | Contratos de resposta tipados via Pydantic, mapeáveis 1:1 pras marts (spec 007); docs automáticas (`/docs`) como artefato de portfólio gratuito; async nativo pra múltiplos gráficos carregando em paralelo; já em uso no weather-analytics (reaproveitamento consciente — a diferenciação do portfólio está na camada de dado, não no framework web) |
| Estratégia de renderização | **Jinja2 pro esqueleto (layout, nav, containers dos gráficos) + TypeScript sem framework de componente pra cada gráfico**, com tipos gerados automaticamente do schema OpenAPI do FastAPI (`openapi-typescript` ou equivalente), bundle via Vite em modo vanilla-ts | API JSON real e testável (abre espaço pra consumo futuro por outra ferramenta, ex. BI); contrato de dado tipado ponta a ponta (Pydantic → OpenAPI → TypeScript), sem retrabalho manual de tipo; ECharts tem tipos TS nativos, integração com autocomplete/checagem; evita o peso de um framework de componente (React/Vue/Svelte) — decisão explícita de não seguir esse caminho, ver Casos de borda |

### Componentes afetados

- `api/` (novo) — implementado 2026-08-20, ver Referências de código.

## Casos de borda

- Alternativas consideradas e descartadas pra renderização: framework de componente completo (React/Vue/Svelte) — descartado por peso de engenharia desproporcional ao que uma vaga de analytics engineer avalia, e por preferência explícita do usuário de evitar JavaScript "pesado"; Alpine.js — descartado por não ter tipagem (perderia o benefício de contrato tipado ponta a ponta); htmx puro — descartado por reintroduzir acoplamento servidor/fragmento HTML que anula parte do valor de ter uma API JSON separada e reaproveitável.
- Se o número de gráficos/páginas crescer muito e o TypeScript sem framework começar a repetir bastante boilerplate de inicialização, reavaliar (não decidir agora) se vale introduzir alguma coisa leve de organização — mas essa reavaliação é uma spec própria, não uma correção silenciosa no meio da implementação.

## Fora do escopo

- Reabrir a decisão de storage/pipeline (specs 003-009) — frontend consome o que já foi modelado, não redesenha a camada de dado.
- Autenticação/login — este é um portfólio público, sem necessidade de área logada identificada até o momento.

## Referências de código

Implementado 2026-08-20:

- `api/app/main.py` — app FastAPI, lifespan (abre/fecha pool de conexão), registra os 6 routers sob prefixo `/api/v1`.
- `api/app/config.py` — `Settings` (pydantic-settings), lê `POSTGRES_HOST/PORT/USER/PASSWORD/DB` do `.env`, mesma convenção da spec 003/009.
- `api/app/db.py` — `AsyncConnectionPool` (psycopg 3, `psycopg_pool`), decisão justificada: driver oficial, suporte async nativo, API quase idêntica sync/async, dispensa ORM (marts já são tabelas simples).
- `api/app/masking.py` + `api/tests/test_masking.py` — `classify_id_contratado`/`mask_id_contratado`; 6 testes unitários, todos passando (`python -m pytest api/tests/test_masking.py -v`).
- `api/app/schemas/*.py` — um Pydantic model por mart/dimensão, colunas confirmadas via `\d marts.<tabela>` no Postgres de dev (não presumidas a partir do `.yml`, que estava desatualizado para `dim_orgaos`/`dim_modalidades` — tabela real tem mais colunas).
- `api/app/routers/*.py` — um router por endpoint, SQL parametrizado (`%(nome)s`, nunca f-string com valor), `WHERE` condicional conforme filtro informado.
- `api/Dockerfile`, `docker-compose.yml` (serviço `api`, `profiles: ["api"]`, porta 8000) — mesma convenção Ubuntu 24.04 do serviço `dbt`.
- `api/requirements.txt` — decisão: `requirements.txt` em vez de `pyproject.toml`, por consistência com os demais serviços Python do ecossistema do usuário (`airflow/requirements.txt`, `streamlit/requirements.txt` em weather-analytics), não por convenção já existente neste repo (que não tinha nenhuma até aqui).

Validação real (`docker compose --profile api up api -d`, container `compras_api` up e saudável):

```
GET /api/v1/orgaos            → 200, dado real (187 órgãos em marts.dim_orgaos)
GET /api/v1/escalada-custo    → 200, dado real (76.041 linhas em marts.mart_escalada_custo)
GET /api/v1/concentracao-fornecedor?top_n=5  → 200, dado real
GET /docs                     → 200
```

Mascaramento conferido visualmente (`cod_unidade_gestora=310002`, órgão com fornecedores pessoa física): 59 de 200 linhas retornadas com `id_contratado` no formato `***.NNN.NNN-**` (ex.: `***.476.371-**`), exatamente como chega da mart — nenhuma transformação adicional aplicada, confirma o achado de Design.

## Ver também

- [[007-marts-e-metricas]]
- [[009-automacao-da-ingestao]]
- [[011-parametros-manifest]]

# Adendo — Endpoints e Requirements da spec 012

Colar nas seções **Design** (linha nova na tabela + subseção de endpoints) e **Requirements** de `docs/specs/012-eixo-frontend-biblioteca-grafico/spec.md`.

---

## Design (adendo — mapeamento de endpoints)

Cada mart da spec 007 vira um endpoint FastAPI, servindo dado bruto em JSON (não pré-moldado pro `option` do ECharts) — decisão já registrada no Design original desta spec, reforçada aqui: mantém a API reaproveitável por qualquer consumidor futuro, não só o frontend deste projeto.

| Mart (spec 007) | Endpoint | Filtros aceitos | Implementado em |
|---|---|---|---|
| `mart_escalada_custo` | `GET /api/v1/escalada-custo` | `cod_unidade_gestora`, `nm_modalidade`, `ano` | `api/app/routers/escalada_custo.py` |
| `mart_diversidade_vencedores` | `GET /api/v1/diversidade-vencedores` | `cod_unidade_gestora` (sem `ano` — mart não tem coluna de ano, grão é processo, confirmado 2026-08-20) | `api/app/routers/diversidade_vencedores.py` |
| `mart_contratos_temporal` | `GET /api/v1/contratos-temporal` | `cod_unidade_gestora`, `nm_modalidade`, `ano_inicio`, `ano_fim` | `api/app/routers/contratos_temporal.py` |
| `mart_concentracao_fornecedor` | `GET /api/v1/concentracao-fornecedor` | `cod_unidade_gestora`, `top_n` (default: 10) | `api/app/routers/concentracao_fornecedor.py` |

Nomes de query param corrigidos pra `snake_case` (`cod_unidade_gestora`, `nm_modalidade`) na implementação — os nomes originais desta tabela (`cdunidadegestora`, `nmmodalidade`) eram placeholder informal, não bateram com a convenção de coluna real das marts (confirmada via `\d` no Postgres de dev, 2026-08-20).

Endpoints auxiliares (metadata, pra popular filtro no frontend — não são mart, são leitura direta de dimensão):

| Fonte | Endpoint | Uso | Implementado em |
|---|---|---|---|
| `dim_orgaos` | `GET /api/v1/orgaos` | Popular dropdown de órgão nos filtros | `api/app/routers/orgaos.py` |
| `dim_modalidades` | `GET /api/v1/modalidades` | Popular dropdown de modalidade, incluindo categoria "Não informado" (spec 007, tratamento de nulo) | `api/app/routers/modalidades.py` |

### Mascaramento de CPF — cautela extra, não exigência legal

**Achado na implementação (2026-08-20), corrige a premissa original abaixo:** a premissa de que `id_contratado` chegaria como dígitos crus (11 ou 14) estava errada. Confirmado via `psql` direto em `marts.mart_concentracao_fornecedor` (27.849 linhas):

```
                  categoria                  |  qt   | distintos
---------------------------------------------+-------+-----------
 CNPJ formatado (18 chars, com pontuação)    | 27117 |     10731
 CPF pré-mascarado (14 chars, com pontuação) |   700 |       651
 outro/malformado                            |    32 |        24
```

- CNPJ chega formatado com pontuação (`00.000.000/0001-91`, 18 caracteres), **sem máscara** — igual ao que a decisão original já previa (exibir por completo).
- CPF chega **já mascarado na própria fonte** (portal de transparência), no formato `***.006.069-**` (14 caracteres, com pontuação) — extremos ocultos, bloco do meio visível. O padrão é o **oposto** do desenhado originalmente (`123.***.**-45`, extremos visíveis) e os dígitos reais das pontas não estão disponíveis: é impossível remontar o formato original a partir do que a fonte entrega.
- 32 linhas (24 valores distintos) não batem com nenhum dos dois formatos — ids curtos (`6`, `505`, `9876544`) que não são CPF nem CNPJ; ver Casos de borda.

Decisão tomada em resposta a este achado: **`masking.py` não reaplica máscara** — CPF já chega mascarado da fonte, CNPJ já chega completo por decisão já registrada aqui. A função vira uma identificação/normalização (reconhece o formato pelo padrão de pontuação, não por contagem de dígitos crus) para uso futuro (ex.: filtrar/agrupar por tipo de pessoa), sem transformar o valor exibido. Regra efetiva, aplicada na serialização Pydantic do endpoint `concentracao-fornecedor`:
- CNPJ (`NN.NNN.NNN/NNNN-NN`): exibido como veio da mart, sem alteração.
- CPF (`***.NNN.NNN-**`): exibido como veio da mart — já mascarado pela fonte, nenhuma máscara adicional aplicada.
- Formato não reconhecido (nem CPF nem CNPJ): exibido como veio da mart, sem tratamento especial (ver Casos de borda).

~~Premissa original (não confirmada contra o dado real, mantida riscada para histórico):~~ ~~`idcontratado` (spec 007) mistura CNPJ (14 dígitos, pessoa jurídica) e CPF (11 dígitos, pessoa física)... 11 dígitos (CPF): mascarado, mostrando só os 3 primeiros e 2 últimos dígitos (ex.: `123.***.**-45`), resto oculto.~~ O dado já é público na fonte oficial do governo (portal de transparência) — não há obrigação legal identificada de ocultar; a intenção de cautela extra do usuário permanece válida, só que já satisfeita pela própria fonte para CPF.

## Requirements

### Funcionais

1. O sistema DEVE expor um endpoint FastAPI por mart definida na spec 007: `/api/v1/escalada-custo`, `/api/v1/diversidade-vencedores`, `/api/v1/contratos-temporal`, `/api/v1/concentracao-fornecedor`.

2. Cada endpoint DEVE aceitar os filtros opcionais listados na tabela de Design acima via query parameters, retornando o conjunto completo (sem filtro) quando nenhum parâmetro for informado.

3. Os endpoints DEVEM retornar dado bruto em formato JSON genérico (registros, não estrutura pré-moldada pro ECharts) — a transformação pro formato `option` do ECharts é responsabilidade do código TypeScript no frontend, não do backend.

4. ~~QUANDO o endpoint `concentracao-fornecedor` retornar um `idcontratado` de 11 dígitos (CPF), O sistema DEVE mascarar o valor conforme a regra definida no Design (3 primeiros + 2 últimos dígitos visíveis)... QUANDO o valor tiver 14 dígitos (CNPJ), O sistema NÃO DEVE aplicar máscara.~~ **Corrigido (achado 2026-08-20, ver Design):** QUANDO o endpoint `concentracao-fornecedor` retornar um `id_contratado` no formato CPF pré-mascarado pela fonte (`***.NNN.NNN-**`), O sistema NÃO DEVE reaplicar máscara — o valor já vem oculto da origem. QUANDO o valor estiver no formato CNPJ (`NN.NNN.NNN/NNNN-NN`), O sistema NÃO DEVE aplicar máscara — exibido por completo, como já prescrito. QUANDO o valor não corresponder a nenhum dos dois formatos, O sistema DEVE expor o valor como veio da mart, sem tratamento especial (ver Casos de borda).

5. O sistema DEVE expor os endpoints auxiliares `/api/v1/orgaos` e `/api/v1/modalidades` para popular filtros no frontend, refletindo os valores reais das dimensões (incluindo a categoria "não informado" de `nmmodalidade`, definida na spec 007).

6. Todo endpoint DEVE ter response schema definido via Pydantic, com `description` preenchida — usado tanto para a documentação automática (`/docs`) quanto como fonte para geração de tipos TypeScript (decisão já registrada no Design original desta spec).

### Não-funcionais

1. A regra de mascaramento de CPF DEVE ser implementada num único ponto reaproveitável (função/serializer), não duplicada em cada endpoint que expuser `idcontratado` — se outro endpoint futuro também expuser fornecedor, deve reusar a mesma função.

2. O contrato de resposta de cada endpoint (schema Pydantic) DEVE permanecer estável o suficiente para gerar tipos TypeScript sem quebra frequente — mudança de schema é decisão registrada (spec nova ou adendo), não edição silenciosa.

## Casos de borda

- Filtro combinando `cdunidadegestora` + `nmmodalidade` que não retorna nenhuma linha (combinação real mas rara) — endpoint deve retornar lista vazia com `200 OK`, não erro.
- `top_n` do endpoint de concentração maior que o número real de fornecedores do órgão filtrado — retornar todos os disponíveis, sem erro.
- `id_contratado` que não bate com o formato CPF pré-mascarado nem com o formato CNPJ (32 linhas / 24 valores distintos confirmados em `mart_concentracao_fornecedor`, achado 2026-08-20 — ver Design): valores curtos e não identificados (`6`, `505`, `9876544`), provável sinal de qualidade de dado na fonte, não CPF/CNPJ real. Decisão: API expõe como está, sem filtrar ou corrigir — camada de serving não trata dado da mart. Se for necessário investigar a origem desses valores, é pendência de levantamento na camada dbt (spec própria), não desta API.