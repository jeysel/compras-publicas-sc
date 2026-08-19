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
