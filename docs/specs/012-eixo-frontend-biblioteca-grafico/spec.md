# 012 — Eixo frontend: biblioteca de gráfico e arquitetura de serving

## Tipo

Decisão de arquitetura — abre o eixo frontend (último dos três definidos no início do planejamento: storage → pipeline → frontend).

## Status

Design principal fechado: biblioteca de gráfico (ECharts), backend (FastAPI), estratégia de renderização (Jinja2 + TypeScript sem framework, tipos gerados via OpenAPI). Requirements (EARS) formalizados no adendo abaixo.

**API FastAPI implementada e validada (2026-08-20)** — os 6 endpoints (`escalada-custo`, `diversidade-vencedores`, `contratos-temporal`, `concentracao-fornecedor`, `orgaos`, `modalidades`) existem em `api/`, testados contra o Postgres de dev real (curl + teste unitário de mascaramento, ver Referências de código).

**Camada de renderização implementada e validada (2026-08-20)** — Jinja2 (esqueleto) + TypeScript vanilla + ECharts, os 4 gráficos das marts existem e renderizam com dado real (Playwright headless, sem erro de console). Loop provado ponta a ponta primeiro com `escalada-custo` isolado, depois replicado pros outros 3, conforme decisão de validação incremental desta spec. Ver Referências de código.

**Achado de outlier (`CT-00269/2022`, registrado abaixo) corrigido (2026-08-20) — ver [[021-levantamento-outliers-valor-extremo]].** A pendência estava registrada como "não corrigida" nesta spec; spec 021 levantou a extensão real (146 linhas, 3 padrões), implementou `fl_valor_suspeito` em `stg_contratos`, e o pico de -R$25bi em `escalada-custo`/`contratos-temporal` foi confirmado revertido. Formatação de moeda também corrigida (pt-BR) nos 4 gráficos. `mart_concentracao_fornecedor` **não foi corrigida** — pendência nova, ver spec 021 caso de borda 7.

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
- `web/` (novo) — implementado 2026-08-20, ver Referências de código.

### Design (adendo — exclusão de `fl_aditivo_inconsistente`, 2026-08-20)

Decisão tomada fora de spec, aplicada nesta sessão: gráficos que agregam **valor de contrato** excluem por padrão, no TypeScript do frontend (não no backend — a API continua expondo dado bruto, decisão original já registrada acima), linhas com `fl_aditivo_inconsistente = true`. `null`/`false` permanecem incluídos — `null` significa "sem aditivo", não "inconsistente".

| Gráfico | Endpoint | Tratamento | Razão |
|---|---|---|---|
| `escalada-custo` | `/api/v1/escalada-custo` | Filtra `fl_aditivo_inconsistente === true` antes de agregar `vl_variacao` por ano; legenda visível com contagem de excluídos (975 de 76.041 no dado real de dev, 2026-08-20) | Grão do endpoint é o contrato — o flag existe por linha, filtro é possível e direto |
| `contratos-temporal` | `/api/v1/contratos-temporal` | **Não filtra** — legenda visível avisa que a exclusão não foi aplicada | Investigado 2026-08-20 (ver abaixo): `fl_aditivo_inconsistente` não existe nesta mart nem nos modelos intermediários que a alimentam — a informação já foi perdida na agregação antes de chegar à API. Filtro client-side é impossível neste grão; pendência fica registrada, correção exigiria mudar os modelos dbt `int_contratos_evolucao_*` (spec própria) |
| `diversidade-vencedores` | `/api/v1/diversidade-vencedores` | Não se aplica | O gráfico implementado classifica processos por `ds_diversidade` (contagem), não agrega `vl_total_variacao` — nenhum campo de valor é somado |
| `concentracao-fornecedor` | `/api/v1/concentracao-fornecedor` | Não se aplica, confirmado | Agrega `vl_atual` (valor corrente do contrato), não `vl_variacao`. `fl_aditivo_inconsistente` sinaliza divergência entre `vl_aditado` e `vl_variacao` (`vl_atual - vl_original`) — não questiona `vl_atual` em si. Excluir essas linhas subestimaria o gasto real do fornecedor sem motivo, então a decisão é não filtrar |

**Investigação — `mart_contratos_temporal` (2026-08-20):**

```
docker compose exec postgres psql -U postgres -d compras_publicas -c "\d marts.mart_contratos_temporal"
```

Confirmado: a tabela não tem coluna `fl_aditivo_inconsistente` nem equivalente. Rastreado até a origem: `mart_contratos_temporal.sql` lê de `int_contratos_evolucao_anual`/`_por_orgao`/`_por_modalidade`, e essas três leem de `stg_contratos` (`sum(vl_atual)`, `sum(vl_variacao)`, `group by ano/mês[/órgão|modalidade]`) **sem filtrar nem expor o flag**. Ou seja: o problema de agregação inflada por aditivo inconsistente **também existe** em `contratos-temporal` (mesma fonte, mesmo `vl_variacao`), mas não há como saber, a partir do dado que a API expõe hoje, quanto de cada célula agregada vem de linhas inconsistentes. Não presumido — confirmado lendo os 4 arquivos `.sql` envolvidos.

**Achado não solicitado, fora do escopo desta sessão (2026-08-20) — outlier em `mart_escalada_custo`:**

A expectativa de que excluir `fl_aditivo_inconsistente = true` faria desaparecer o pico visual de ~-R$25bi em `ano_assinatura = 2022` **não se confirmou**. Validação real:

```sql
select fl_aditivo_inconsistente, count(*), sum(vl_variacao)
from marts.mart_escalada_custo where ano_assinatura = 2022 group by 1;
--  f | 107  |     13820446.39
--  t | 303  |    328727193.61   (exclusão aplicada não é a causa do pico)
--    | 7285 | -24367495078.02   (NULL = "sem aditivo", não "inconsistente")
```

Isolando a maior linha do grupo `NULL`:

```
nu_contrato: CT-00269/2022 — Fraga Construções e Engenharia LTDA
vl_original: 23.602.153.155,36   vl_atual: 5.390.370,02   vl_variacao: -23.596.762.785,34
```

Removendo só essa linha, a soma de 2022 cai de -R$24,35bi pra -R$757 milhões (confirmado via `sum(...) filter (...)`) — uma única linha responde por ~97% do pico. `vl_original` de R$23,6 bilhões é implausível pra um contrato público estadual (maior que o orçamento anual de SC inteiro); o padrão (~3 ordens de grandeza acima de um valor plausível) sugere erro de parsing de casa decimal na fonte, não decisão de negócio. **Corrigido em [[021-levantamento-outliers-valor-extremo]] (2026-08-20)** — levantamento ampliou o achado (146 linhas, 3 padrões distintos), `fl_valor_suspeito` implementada em `stg_contratos`, ver adendo abaixo.

### Design (adendo — exclusão de `fl_valor_suspeito`, spec 021, 2026-08-20)

Mesmo padrão de decisão do adendo anterior (`fl_aditivo_inconsistente`), critério independente: gráficos que agregam **valor de contrato** também excluem, no TypeScript do frontend (ou na camada dbt quando o grão da mart não permitir), linhas com `fl_valor_suspeito = true` (spec 021 — três padrões de valor implausível em `vl_original`/`vl_atual`, nenhum deles é inconsistência de aditivo).

| Gráfico | Endpoint | Tratamento | Razão |
|---|---|---|---|
| `escalada-custo` | `/api/v1/escalada-custo` | Filtra `fl_valor_suspeito === true` (combinado com `fl_aditivo_inconsistente === true`, mesma exclusão) antes de agregar `vl_variacao` por ano; legenda única com as duas contagens separadas (146 por valor implausível, 975 por aditivo, no dado real de dev, 2026-08-20) | Grão do endpoint é o contrato — o flag existe por linha, filtro é possível e direto, mesmo caso de `fl_aditivo_inconsistente` |
| `contratos-temporal` | `/api/v1/contratos-temporal` | **Exclusão aplicada na camada dbt** (não no cliente) — os `int_contratos_evolucao_*` que alimentam a mart excluem as 146 linhas do `SUM()` antes da mart existir; legenda atualizada pra refletir que a exclusão por valor implausível já ocorre, distinta da exclusão por aditivo (essa ainda não, ver linha acima da tabela original) | Mesmo grão pré-agregado que impede filtro client-side de `fl_aditivo_inconsistente` — só que aqui a correção foi implementada na origem (spec 021), não deixada como pendência |
| `diversidade-vencedores` | `/api/v1/diversidade-vencedores` | Não se aplica | Mesmo motivo já registrado acima — não agrega valor monetário |
| `concentracao-fornecedor` | `/api/v1/concentracao-fornecedor` | **Não aplicado — pendência registrada** (spec 021, caso de borda 7) | `int_concentracao_fornecedor_por_orgao`/`_estado` também somam `vl_atual` por fornecedor antes da mart, mesmo problema de `contratos-temporal` — mas essa correção **não foi implementada** nesta sessão, por decisão explícita de não estender o escopo do tratamento de `mart_concentracao_fornecedor` sem uma spec de Design própria. Ranking estadual de fornecedores continua distorcido pelos outliers (`PIATA COMERCIO DE PECAS LTDA` segue #1, R$10,5 bi) |

### Design (adendo — formatação de moeda pt-BR, spec 021, 2026-08-20)

Achado durante a validação da spec 021: os 4 gráficos exibiam valor monetário em formatação americana padrão do ECharts (`$9,999,999,999.99` implícito, sem `Intl.NumberFormat` nenhum aplicado). Corrigido: `web/src/charts/format.ts` (novo) exporta `formatarMoedaBRL()` via `Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })`, aplicado a eixo e tooltip de `escalada-custo`, `contratos-temporal` e `concentracao-fornecedor` (`diversidade-vencedores` não tem valor monetário, não alterado). Achado de regressão durante a validação com Playwright: o formato completo pt-BR é mais longo que o formato numérico cru anterior, o que causou colisão visual nos rótulos do eixo X de `concentracao-fornecedor` (valores na casa de bilhões); corrigido com `axisLabel: { rotate: 30 }` + `grid.bottom` maior — confirmado via Playwright (hook em `fillText` do canvas) que os rótulos ficaram legíveis e sem sobreposição.

## Casos de borda

- Alternativas consideradas e descartadas pra renderização: framework de componente completo (React/Vue/Svelte) — descartado por peso de engenharia desproporcional ao que uma vaga de analytics engineer avalia, e por preferência explícita do usuário de evitar JavaScript "pesado"; Alpine.js — descartado por não ter tipagem (perderia o benefício de contrato tipado ponta a ponta); htmx puro — descartado por reintroduzir acoplamento servidor/fragmento HTML que anula parte do valor de ter uma API JSON separada e reaproveitável.
- Se o número de gráficos/páginas crescer muito e o TypeScript sem framework começar a repetir bastante boilerplate de inicialização, reavaliar (não decidir agora) se vale introduzir alguma coisa leve de organização — mas essa reavaliação é uma spec própria, não uma correção silenciosa no meio da implementação.
- `openapi-typescript@7.13.0` exige peer `typescript@^5.x`; o template `vanilla-ts` do Vite instala TypeScript 6.0.2 — conflito real de peer dependency, resolvido com `--legacy-peer-deps` (só afeta devDependency de geração de tipo, não entra no bundle de produção).
- Grão de `mart_concentracao_fornecedor` é (`cod_unidade_gestora`, `id_contratado`): sem filtro de órgão, um mesmo fornecedor aparece uma vez por órgão com que contratou (até 126+ linhas pro mesmo fornecedor, confirmado via `group by rank_estado` em dev). `ORDER BY rank_estado LIMIT top_n` no backend não garante `top_n` fornecedores distintos — o dedup por `id_contratado`, mantendo o maior `vl_total_fornecedor_estado`, é feito no TypeScript (`concentracao-fornecedor.ts`), buscando a mart inteira (`top_n=30000`) pra garantir cobertura.
- Achado de qualidade de dado em `mart_escalada_custo` não relacionado a `fl_aditivo_inconsistente`: contrato `CT-00269/2022` (Fraga Construções e Engenharia LTDA) com `vl_original` de ~R$23,6 bilhões, provável erro de parsing na fonte — ver Design (adendo) acima. **Corrigido** em [[021-levantamento-outliers-valor-extremo]] (2026-08-20) — não é mais pendência desta spec.
- `mart_concentracao_fornecedor` não recebeu o tratamento de `fl_valor_suspeito` — pendência nova (spec 021, caso de borda 7), diferente da anterior: aqui a causa raiz (mesmo grão pré-agregado de `mart_contratos_temporal`) já foi diagnosticada, só a correção não foi implementada, por decisão consciente de não estender escopo sem spec de Design própria.

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

Camada de renderização, implementada e validada 2026-08-20:

- `web/vite.config.ts` — `build.outDir: "../api/app/static"`, entry direto em `src/main.ts` (não em `index.html`), nomes de saída fixos (`main.js`/`main.css`, sem hash) — evita ter que ler manifest no lado Python.
- `web/src/api-types.ts` — gerado via `npm run generate-types` (`openapi-typescript`), regenerar sempre que o schema da API mudar (script já registrado em `web/package.json`).
- `web/src/charts/legend.ts` — helper reaproveitado por `escalada-custo.ts` e `contratos-temporal.ts` pra escrever a legenda de exclusão num elemento `<p>` fora do canvas do ECharts (decisão: `title`/`subtitle` do ECharts pode passar despercebido).
- `web/src/charts/escalada-custo.ts` — filtra `fl_aditivo_inconsistente === true` antes de agregar `vl_variacao` por `ano_assinatura`; legenda com contagem de excluídos.
- `web/src/charts/contratos-temporal.ts` — série `vl_total_atual` por ano-mês, recorte `tp_recorte === 'Geral'`; **não filtra** por aditivo inconsistente (ver Design/adendo — grão da mart não permite); legenda avisa a pendência.
- `web/src/charts/diversidade-vencedores.ts` — contagem de processos por `ds_diversidade` ('Fornecedor único' / 'Múltiplos fornecedores').
- `web/src/charts/concentracao-fornecedor.ts` — top 10 fornecedores por `vl_total_fornecedor_estado`, com dedup client-side por `id_contratado` (ver Casos de borda — grão órgão×fornecedor).
- `web/src/main.ts` — inicializa os 4 gráficos quando `document.body.dataset.page === "home"`.
- `api/app/main.py` — `StaticFiles` em `/static` (serve o build do Vite), `Jinja2Templates`, rota `GET /`.
- `api/app/templates/base.html` — esqueleto único (`home`), 4 containers de gráfico, 2 legendas de exclusão, seção `#metodologia` com o texto de contexto do link "metodologia".
- `api/requirements.txt` — `jinja2` adicionado (exigiu rebuild de imagem Docker, não só restart, já que dependência Python não vem do bind mount).
- `.gitignore` — `api/app/static/` (build output do Vite, artefato gerado, não versionado).

Validação real (`docker compose --profile api up api -d --build`, depois `npm run build` + `docker compose --profile api restart api` nas iterações seguintes):

```
GET /                                → 200, 4 containers de gráfico presentes no HTML
GET /static/main.js, /static/main.css → 200
```

Confirmação visual via Playwright headless (Chromium, instalado à parte pra validação, fora do projeto): 4 `<canvas>` renderizados, sem erro de console, screenshot conferido manualmente. Legenda de `escalada-custo` (dado real, dev): "975 de 76041 contratos excluídos". Legenda de `contratos-temporal`: aviso de pendência exibido corretamente.

**Achado durante a validação, não presumido:** a expectativa de que a exclusão de `fl_aditivo_inconsistente = true` eliminaria o pico visual de 2022 em `escalada-custo` não se confirmou — o pico é causado por outlier não relacionado (ver Design/adendo acima, `CT-00269/2022`). Filtro implementado e funcionando exatamente como decidido; pico é achado novo, registrado, corrigido depois em [[021-levantamento-outliers-valor-extremo]] (ver abaixo).

### Tratamento de `fl_valor_suspeito` e formatação de moeda (spec 021, implementado e validado 2026-08-20)

- `web/src/charts/format.ts` (novo) — `formatarMoedaBRL()`, `Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })`, compartilhado por `escalada-custo.ts`, `contratos-temporal.ts`, `concentracao-fornecedor.ts`.
- `web/src/charts/escalada-custo.ts` — filtro combinado `fl_aditivo_inconsistente === true` + `fl_valor_suspeito === true`, legenda com as duas contagens separadas, eixo/tooltip em moeda BRL.
- `web/src/charts/contratos-temporal.ts` — legenda atualizada (exclusão de `fl_valor_suspeito` já ocorre na camada dbt, distinta da pendência de `fl_aditivo_inconsistente`), eixo/tooltip em moeda BRL.
- `web/src/charts/concentracao-fornecedor.ts` — eixo/tooltip em moeda BRL; `axisLabel.rotate: 30` + `grid.bottom: 70` pra evitar colisão de rótulo (achado de regressão da formatação mais longa, corrigido e validado via Playwright); dado (ranking de fornecedores) **não corrigido** — pendência spec 021 caso de borda 7.
- `api/app/schemas/escalada_custo.py` — campo `fl_valor_suspeito: bool | None` adicionado.
- `web/src/api-types.ts` — regenerado (`npm run generate-types`) após restart do container `api` com o schema novo.
- `dbt/models/staging/stg_contratos.sql`, `mart_escalada_custo.sql`, `int_contratos_evolucao_anual/_por_orgao/_por_modalidade.sql` — ver [[021-levantamento-outliers-valor-extremo]] Referências de código, não duplicado aqui.

Validação real (Playwright headless, 2026-08-20, container `compras_api` reiniciado após `npm run build`):

```
Y-axis escalada-custo:      "R$ 600.000.000,00" ... "-R$ 800.000.000,00"  (pt-BR confirmado)
Tooltip escalada-custo 2022: -R$ 716.866.820,69                          (era -R$ ~25 bi antes da correção)
Y-axis contratos-temporal:  "R$ 1.800.000.000,00" ... "R$ 0,00"
Legenda escalada-custo:     "1121 de 76041 contratos excluídos ... (975 por aditivo, 146 por valor implausível)"
Legenda contratos-temporal: "Este agregado já exclui 146 contratos com valor implausível ... antes da soma"
X-axis concentracao-fornecedor: "R$ 0,00" .. "R$ 12.000.000.000,00", rotacionados 30°, sem sobreposição (confirmado via hook em fillText do canvas)
Top fornecedor concentracao-fornecedor: PIATA COMERCIO DE PECAS LTDA, R$ 10.498.765.947,45 (inalterado — pendência, não bug)
Console/erros de página: nenhum
```

## Ver também

- [[007-marts-e-metricas]]
- [[009-automacao-da-ingestao]]
- [[011-parametros-manifest]]
- [[021-levantamento-outliers-valor-extremo]] (levantamento + correção do outlier `CT-00269/2022` e formatação de moeda)

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

7. QUANDO um gráfico do frontend agregar `vl_variacao` (ou derivado) a partir de dado no grão de contrato individual, O sistema DEVE excluir por padrão as linhas com `fl_aditivo_inconsistente = true` antes de agregar.

8. QUANDO um gráfico excluir linhas por `fl_aditivo_inconsistente = true`, O sistema DEVE exibir, num elemento visível da página (não apenas `title`/`subtitle` do gráfico), a quantidade de linhas excluídas e um link pra uma seção de metodologia que explique o critério.

9. QUANDO a mart consumida por um gráfico já vier agregada num grão que não preserva `fl_aditivo_inconsistente` por linha (achado 2026-08-20: `mart_contratos_temporal`), O sistema NÃO DEVE tentar aplicar o filtro — DEVE exibir aviso visível de que a exclusão não foi aplicada, em vez de omitir o aviso ou aplicar um filtro incorreto.

10. QUANDO um gráfico do frontend agregar `vl_variacao`/`vl_atual`/`vl_original` (ou derivado) a partir de dado no grão de contrato individual, O sistema DEVE excluir por padrão as linhas com `fl_valor_suspeito = true` (spec 021), reportando a contagem de exclusão combinada com a de `fl_aditivo_inconsistente` numa única legenda (não duas separadas).

11. QUANDO a mart consumida por um gráfico já vier agregada num grão que não preserva `fl_valor_suspeito` por linha (achado spec 021: `mart_contratos_temporal`, `mart_concentracao_fornecedor`), a exclusão DEVE acontecer na camada dbt (dentro do `SUM()`), não no cliente — diferente do requirement 9 (`fl_aditivo_inconsistente`), que registra a exclusão como pendência quando isso ocorre; para `fl_valor_suspeito`, a mesma limitação de grão NÃO justifica deixar a mart sem tratamento (`mart_contratos_temporal` já corrigida; `mart_concentracao_fornecedor` é pendência explícita registrada em spec 021, não satisfaz este requirement ainda).

12. Todo valor monetário exibido nos gráficos (eixo, tooltip, texto) DEVE usar formatação brasileira (`Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })` ou equivalente) — não o formato numérico padrão do ECharts nem formatação americana.

### Não-funcionais

1. A regra de mascaramento de CPF DEVE ser implementada num único ponto reaproveitável (função/serializer), não duplicada em cada endpoint que expuser `idcontratado` — se outro endpoint futuro também expuser fornecedor, deve reusar a mesma função.

2. O contrato de resposta de cada endpoint (schema Pydantic) DEVE permanecer estável o suficiente para gerar tipos TypeScript sem quebra frequente — mudança de schema é decisão registrada (spec nova ou adendo), não edição silenciosa.

3. Todo módulo TypeScript de gráfico (`web/src/charts/*.ts`) DEVE usar os tipos gerados via OpenAPI (`api-types.ts`) pro retorno do `fetch` — não usar `any`.

## Casos de borda

- Filtro combinando `cdunidadegestora` + `nmmodalidade` que não retorna nenhuma linha (combinação real mas rara) — endpoint deve retornar lista vazia com `200 OK`, não erro.
- `top_n` do endpoint de concentração maior que o número real de fornecedores do órgão filtrado — retornar todos os disponíveis, sem erro.
- `id_contratado` que não bate com o formato CPF pré-mascarado nem com o formato CNPJ (32 linhas / 24 valores distintos confirmados em `mart_concentracao_fornecedor`, achado 2026-08-20 — ver Design): valores curtos e não identificados (`6`, `505`, `9876544`), provável sinal de qualidade de dado na fonte, não CPF/CNPJ real. Decisão: API expõe como está, sem filtrar ou corrigir — camada de serving não trata dado da mart. Se for necessário investigar a origem desses valores, é pendência de levantamento na camada dbt (spec própria), não desta API.