# 🛒 Compras Públicas SC — Pipeline Analytics

Pipeline Analytics completo para análise de compras públicas do estado de Santa Catarina.

Objetivo: Analisar padrões de contratação pública em SC — evolução de gastos, concentração de fornecedores e comportamento dos órgãos ao longo do tempo.

**Fonte:** [Transparência SC](https://www.transparencia.sc.gov.br/)

---

## 🏗️ Arquitetura

```
CSV (Transparência SC)
       ↓
  dbt seed → PostgreSQL (raw)
       ↓
  dbt build
  ├── staging      → padronização e limpeza
  ├── intermediate → regras de negócio
  └── marts        → métricas analíticas
       ↓
    Evidence → GitHub Pages
```

## 🧱 Stack

| Camada | Tecnologia |
|---|---|
| Banco de dados | PostgreSQL 17 |
| Transformação | dbt-core 1.9 |
| Visualização | Evidence.dev |
| Orquestração local | Docker Compose |
| CI/CD | GitHub Actions |
| Publicação | GitHub Pages |

---

## 🎯 Métricas Analíticas

- Valor licitado vs contratado (economia/sobrepreço)
- Competitividade (nº de fornecedores por compra)
- Modalidades mais utilizadas
- Tempo médio entre abertura e contratação
- Ranking de órgãos por volume de compras
- Ranking de fornecedores por participação

---

## 🚀 Como rodar localmente

### Pré-requisitos
- Docker Desktop instalado e rodando
- Git

### Setup

```bash
# 1. Clone o repositório
git clone https://github.com/jeysel/compras-publicas.git
cd compras-publicas

# 2. Configure as variáveis de ambiente
cp .env.example .env

# 3. Sobe o PostgreSQL
docker compose up postgres -d

# 4. Roda o dbt (seed + build)
docker compose run --rm dbt dbt seed
docker compose run --rm dbt dbt build

# 5. Sobe o Evidence
docker compose --profile evidence up evidence
# Acesse: http://localhost:3000
```

---

## 📁 Estrutura do Projeto

```
compras-publicas/
├── .github/workflows/   # CI/CD — GitHub Actions
├── postgres/
│   └── init/            # Scripts SQL de inicialização
├── dbt/
│   ├── models/
│   │   ├── staging/     # Padronização dos dados brutos
│   │   ├── intermediate/# Regras de negócio
│   │   └── marts/       # Tabelas analíticas finais
│   └── seeds/           # CSVs dos contratos SC
├── evidence/
│   └── pages/           # Dashboards interativos
├── docs/                # Arquitetura e decisões
├── docker-compose.yml
└── .env.example
```

---

## 📊 Dashboard

Acesse o dashboard publicado: **[GitHub Pages](https://jeysel.github.io/compras-publicas)**

---

## 👤 Autor

Desenvolvido por [Jeysel](https://github.com/jeysel) como projeto de portfólio em Analytics Engineering.

Portfólio completo: [github.com/jeysel/Analytics-Engineer](https://github.com/jeysel/Analytics-Engineer)
