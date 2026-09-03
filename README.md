# 🛒 Compras Públicas SC

Painel de transparência sobre contratos públicos do Estado de Santa Catarina — do pipeline
de dados (dbt + PostgreSQL) à apresentação pública (FastAPI + ECharts).

- **No ar:** [contratos-sc.jeysel.dev](https://contratos-sc.jeysel.dev)
- **Fonte:** [Portal de Transparência de SC](https://www.transparencia.sc.gov.br/) — dados abertos em [dados.sc.gov.br](https://dados.sc.gov.br/dataset/contratos)
- **Cobertura:** contratos assinados a partir de 2016 ([spec 034](docs/specs/034-fronteira-cobertura-temporal-2016/spec.md))

---

## 🏗️ Arquitetura

```
Portal de Transparência SC (CSV)
        │   ingest.sh (gated por ETag)  +  upsert manual (spec 030)
        ▼
PostgreSQL  ──  raw.contratos
        │   dbt build
        ├── staging       padronização, tipagem, flags de qualidade, corte 2016+
        ├── intermediate  regras de negócio
        └── marts         tabelas e métricas analíticas
        │
        ▼
FastAPI  ──  páginas (Jinja2)  +  API de leitura  /api/v1/*
        │        ▲
        │        └──  web/  (Vite + TypeScript + ECharts) → build embutido em api/app/static
        ▼
k3s + Argo CD (GitOps)  ──►  contratos-sc.jeysel.dev
```

O frontend estático anterior (Evidence.dev via GitHub Pages) foi removido em 2026-08 e
substituído por este serving layer FastAPI + ECharts (specs 012 / 022). Histórico da decisão
em [`docs/specs/012`](docs/specs/012-eixo-frontend-biblioteca-grafico/spec.md) e
[`docs/specs/013`](docs/specs/013-levantamento-dbt-legado/spec.md).

## 🧱 Stack

| Camada | Tecnologia |
|---|---|
| Banco de dados | PostgreSQL 17 |
| Transformação | dbt-core 1.9 (`dbt-postgres`) |
| Serving / API | FastAPI · Jinja2 · `psycopg` 3 (pool) — Python 3.12 |
| Frontend | Vite · TypeScript · ECharts 6 |
| Empacotamento | Docker (multi-stage: Node builda o `web/`, imagem final serve a API) |
| Deploy | k3s (VPS) + Argo CD — manifests em [`deploy/k8s`](deploy/k8s); `Ingress`/`Application` no repo de infra |
| CI | GitHub Actions — suíte de testes (spec 033) + build/push das imagens no GHCR |
| Orquestração local | Docker Compose |

---

## 🚀 Rodar localmente

### Pré-requisitos

- Docker (Desktop ou Engine) rodando
- Node.js 22+ (só para iterar no frontend com `npm run dev`)
- Git

### Setup

```bash
# 1. Clone
git clone https://github.com/jeysel/compras-publicas-sc.git
cd compras-publicas-sc

# 2. Pre-commit hook local (bloqueia commit de IP/ARN/identity/chave privada em
#    docs — precisa rodar uma vez por clone, não se propaga; ver .githooks/pre-commit)
git config core.hooksPath .githooks

# 3. Variáveis de ambiente
cp .env.example .env

# 4. Sobe o PostgreSQL
docker compose up postgres -d

# 5. Pipeline dbt (deps → seed → build completo com testes)
docker compose run --rm dbt deps
docker compose run --rm dbt seed --select contratos --full-refresh
docker compose run --rm dbt build

# 6. Sobe a API + frontend (buildado dentro da imagem)
docker compose --profile api up api -d --build
#    → http://localhost:8000        (páginas)
#    → http://localhost:8000/docs   (OpenAPI)
```

### Iterar no frontend

```bash
cd web
npm install
npm run dev        # Vite dev server; consome a API em localhost:8000
npm run build      # tsc + vite build → api/app/static (o que a imagem serve)
```

### Documentação do dbt (opcional)

```bash
docker compose run --rm dbt docs generate
docker compose run --rm -p 8080:8080 dbt docs serve --host 0.0.0.0 --port 8080
# → http://localhost:8080
```

### PgAdmin (opcional)

```bash
docker compose up pgadmin -d          # → http://localhost:8080
# Host: postgres · Port: 5432 · Database/User/Password: ver .env
```

---

## 📁 Estrutura

```
compras-publicas-sc/
├── .github/workflows/       # CI — testes + build/push das imagens
├── postgres/                # imagem do Postgres local (Ubuntu 24.04 + PG 17)
├── dbt/
│   ├── models/
│   │   ├── staging/         # padronização, flags de qualidade, corte 2016+, dim_datas (date_spine)
│   │   ├── intermediate/    # regras de negócio
│   │   └── marts/           # tabelas e métricas analíticas
│   ├── seeds/               # CSV base dos contratos
│   ├── tests/               # asserts SQL (relações, invariantes)
│   ├── macros/              # generate_schema_name
│   ├── scripts/             # ingest.sh · process_csv.py
│   └── Dockerfile, Dockerfile.pipeline
├── api/
│   ├── app/
│   │   ├── routers/         # endpoints /api/v1/*
│   │   ├── schemas/         # modelos Pydantic
│   │   └── templates/       # páginas Jinja2 (layout, home, gráficos, relatórios, metodologia)
│   ├── tests/               # suíte pytest (integração contra Postgres real + testes rápidos)
│   └── Dockerfile
├── web/                     # frontend Vite/TS/ECharts (buildado para api/app/static)
├── deploy/k8s/              # Deployment/Service/NetworkPolicy + overlays staging/production
├── docs/
│   ├── specs/               # SDD — uma spec por decisão/mudança de comportamento
│   ├── memory/constitution.md
│   └── backlog-archived/    # backlog antigo (histórico)
├── docker-compose.yml
└── .env.example
```

---

## 📊 O que o painel mostra

- **Série temporal** de valor contratado (mês a mês, variação ano a ano, média móvel)
- **Escalada de custo** — variação de valor por aditivo, por ano de assinatura
- **Concentração de fornecedores** — top 10 por gasto, no estado e por órgão
- **Diversidade de vencedores** — concorrência efetiva por processo licitatório
- **Fornecedor por segmento** — ranking por ramo de atividade
- **Perfil de órgãos** e **perfil de fornecedores** (por porte, volume e valor)
- **Ranking de qualidade de dado** por órgão · **variação de custo/prazo** por modalidade

### Metodologia de dados

Decisões de tratamento ficam registradas como spec e resumidas em
[`/metodologia`](https://contratos-sc.jeysel.dev/metodologia):

- **Cobertura a partir de 2016** — registros anteriores existem na origem mas sem cobertura
  contínua nem auditoria; excluídos de todas as visualizações ([spec 034](docs/specs/034-fronteira-cobertura-temporal-2016/spec.md)).
- **`fl_valor_suspeito`** — valores implausíveis (erro da fonte) sinalizados e excluídos das
  agregações ([spec 021](docs/specs/021-levantamento-outliers-valor-extremo/spec.md)).
- **`fl_aditivo_inconsistente`** — divergência entre `vl_aditado` e a variação calculada
  ([spec 008](docs/specs/008-qualidade-e-documentacao/spec.md) / 013 / 014).
- Normalização de modalidade (mesmo instituto sob leis diferentes vira uma categoria).

---

## 🧭 Como este repositório trabalha

Metodologia SDD (spec-driven): toda decisão de arquitetura, requirement ou mudança de
comportamento relevante vira uma spec em [`docs/specs/`](docs/specs/) **antes** de virar
código. Regras não-negociáveis (segredos, push, validação real) em
[`docs/memory/constitution.md`](docs/memory/constitution.md). Orientação para agentes em
[`CLAUDE.md`](CLAUDE.md).

Deploy: `push` em `main` → CI roda a suíte e publica as imagens → staging sincroniza
automático via Argo CD → produção é promoção manual (bump de tag no overlay + sync).

---

## 👤 Autor

Desenvolvido por [Jeysel](https://github.com/jeysel) como projeto de portfólio em
Analytics / Data Engineering.

Outros projetos: [repositórios pessoais](https://github.com/jeysel?tab=repositories) ·
[organização jeysel-dev](https://github.com/orgs/jeysel-dev/repositories)

---

## 📄 Licença

Código, modelos dbt, specs e documentação deste repositório: **[MIT](LICENSE)** —
livre para baixar, estudar, modificar e redistribuir.

Os dados de contratos são do [Portal de Transparência do Estado de Santa Catarina](https://dados.sc.gov.br/),
publicados como dados abertos sob os termos do próprio portal; este repositório apenas os
processa e não os relicencia.
