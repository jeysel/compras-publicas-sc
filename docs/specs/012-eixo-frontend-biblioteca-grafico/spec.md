# 012 — Eixo frontend: biblioteca de gráfico e arquitetura de serving

## Tipo

Decisão de arquitetura — abre o eixo frontend (último dos três definidos no início do planejamento: storage → pipeline → frontend).

## Status

Design principal fechado: biblioteca de gráfico (ECharts), backend (FastAPI), estratégia de renderização (Jinja2 + TypeScript sem framework, tipos gerados via OpenAPI). Requirements (EARS) ainda não formalizados. Bloqueado para fechamento completo até a spec 007 (marts/métricas) sair do rascunho — os endpoints concretos dependem do que ela definir.

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

- Nenhuma mudança de código ainda — spec de decisão, implementação fica para depois do fechamento da spec 007.

## Casos de borda

- Alternativas consideradas e descartadas pra renderização: framework de componente completo (React/Vue/Svelte) — descartado por peso de engenharia desproporcional ao que uma vaga de analytics engineer avalia, e por preferência explícita do usuário de evitar JavaScript "pesado"; Alpine.js — descartado por não ter tipagem (perderia o benefício de contrato tipado ponta a ponta); htmx puro — descartado por reintroduzir acoplamento servidor/fragmento HTML que anula parte do valor de ter uma API JSON separada e reaproveitável.
- Se o número de gráficos/páginas crescer muito e o TypeScript sem framework começar a repetir bastante boilerplate de inicialização, reavaliar (não decidir agora) se vale introduzir alguma coisa leve de organização — mas essa reavaliação é uma spec própria, não uma correção silenciosa no meio da implementação.

## Fora do escopo

- Reabrir a decisão de storage/pipeline (specs 003-009) — frontend consome o que já foi modelado, não redesenha a camada de dado.
- Autenticação/login — este é um portfólio público, sem necessidade de área logada identificada até o momento.

## Referências de código

_A preencher conforme a implementação._

## Ver também

- [[007-marts-e-metricas]]
- [[009-automacao-da-ingestao]]
- [[011-parametros-manifest]]

# Adendo — Endpoints e Requirements da spec 012

Colar nas seções **Design** (linha nova na tabela + subseção de endpoints) e **Requirements** de `docs/specs/012-eixo-frontend-biblioteca-grafico/spec.md`.

---

## Design (adendo — mapeamento de endpoints)

Cada mart da spec 007 vira um endpoint FastAPI, servindo dado bruto em JSON (não pré-moldado pro `option` do ECharts) — decisão já registrada no Design original desta spec, reforçada aqui: mantém a API reaproveitável por qualquer consumidor futuro, não só o frontend deste projeto.

| Mart (spec 007) | Endpoint | Filtros aceitos |
|---|---|---|
| `mart_escalada_custo` | `GET /api/v1/escalada-custo` | `cdunidadegestora`, `nmmodalidade`, `ano` |
| `mart_diversidade_vencedores` | `GET /api/v1/diversidade-vencedores` | `cdunidadegestora`, `ano` |
| `mart_contratos_temporal` | `GET /api/v1/contratos-temporal` | `cdunidadegestora`, `nmmodalidade`, `ano_inicio`, `ano_fim` |
| `mart_concentracao_fornecedor` | `GET /api/v1/concentracao-fornecedor` | `cdunidadegestora`, `top_n` (default: 10) |

Endpoints auxiliares (metadata, pra popular filtro no frontend — não são mart, são leitura direta de dimensão):

| Fonte | Endpoint | Uso |
|---|---|---|
| `dim_orgao` | `GET /api/v1/orgaos` | Popular dropdown de órgão nos filtros |
| `nmmodalidade` (distinct) | `GET /api/v1/modalidades` | Popular dropdown de modalidade, incluindo categoria "não informado" (spec 007, tratamento de nulo) |

### Mascaramento de CPF — cautela extra, não exigência legal

`idcontratado` (spec 007) mistura CNPJ (14 dígitos, pessoa jurídica) e CPF (11 dígitos, pessoa física). O dado já é público na fonte oficial do governo (portal de transparência) — não há obrigação legal identificada de ocultar. Decisão consciente do usuário: aplicar máscara mesmo assim, como camada extra de cautela, não como exigência de conformidade. Regra, aplicada na serialização Pydantic do endpoint `concentracao-fornecedor`:
- 14 dígitos (CNPJ): exibido por completo, sem máscara.
- 11 dígitos (CPF): mascarado, mostrando só os 3 primeiros e 2 últimos dígitos (ex.: `123.***.**-45`), resto oculto.

## Requirements

### Funcionais

1. O sistema DEVE expor um endpoint FastAPI por mart definida na spec 007: `/api/v1/escalada-custo`, `/api/v1/diversidade-vencedores`, `/api/v1/contratos-temporal`, `/api/v1/concentracao-fornecedor`.

2. Cada endpoint DEVE aceitar os filtros opcionais listados na tabela de Design acima via query parameters, retornando o conjunto completo (sem filtro) quando nenhum parâmetro for informado.

3. Os endpoints DEVEM retornar dado bruto em formato JSON genérico (registros, não estrutura pré-moldada pro ECharts) — a transformação pro formato `option` do ECharts é responsabilidade do código TypeScript no frontend, não do backend.

4. QUANDO o endpoint `concentracao-fornecedor` retornar um `idcontratado` de 11 dígitos (CPF), O sistema DEVE mascarar o valor conforme a regra definida no Design (3 primeiros + 2 últimos dígitos visíveis) — decisão de cautela extra do usuário, não exigência legal (o dado já é público na fonte oficial). QUANDO o valor tiver 14 dígitos (CNPJ), O sistema NÃO DEVE aplicar máscara.

5. O sistema DEVE expor os endpoints auxiliares `/api/v1/orgaos` e `/api/v1/modalidades` para popular filtros no frontend, refletindo os valores reais das dimensões (incluindo a categoria "não informado" de `nmmodalidade`, definida na spec 007).

6. Todo endpoint DEVE ter response schema definido via Pydantic, com `description` preenchida — usado tanto para a documentação automática (`/docs`) quanto como fonte para geração de tipos TypeScript (decisão já registrada no Design original desta spec).

### Não-funcionais

1. A regra de mascaramento de CPF DEVE ser implementada num único ponto reaproveitável (função/serializer), não duplicada em cada endpoint que expuser `idcontratado` — se outro endpoint futuro também expuser fornecedor, deve reusar a mesma função.

2. O contrato de resposta de cada endpoint (schema Pydantic) DEVE permanecer estável o suficiente para gerar tipos TypeScript sem quebra frequente — mudança de schema é decisão registrada (spec nova ou adendo), não edição silenciosa.

## Casos de borda

- Filtro combinando `cdunidadegestora` + `nmmodalidade` que não retorna nenhuma linha (combinação real mas rara) — endpoint deve retornar lista vazia com `200 OK`, não erro.
- `top_n` do endpoint de concentração maior que o número real de fornecedores do órgão filtrado — retornar todos os disponíveis, sem erro.