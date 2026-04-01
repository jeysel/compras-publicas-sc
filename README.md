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

# 3. Compila as imagens docker
docker compose build

# 4. Sobe o PostgreSQL e PgAdmin
docker compose up postgres -d
- Visualizar logs: docker logs compras_postgres
- Configuração PGAdmin
Host:     localhost
Port:     5432
Database: compras_publicas
Username: cp_user
Password: cp_pass

- SELECT count(dd.dt_data) FROM "raw".dim_datas dd # Deve retornar 5.844 linhas

# 5. Instala dependências do dbt
docker compose run --rm dbt deps 

# 6. Carrega os dados (seed)
docker compose run --rm dbt seed
# Valide no PgAdmin: raw.contratos (~78.000 linhas)
- SELECT count(*) FROM raw.contratos; # Esperado: 76.041

# 7. Executa e valida o staging
docker compose run --rm dbt dbt build --select stg_contratos
# Valide no PgAdmin: staging.stg_contratos

# 8. Executa e valida o intermediate
docker compose run --rm dbt dbt build --select tag:int
# Valide no PgAdmin: intermediate.*

# 9. Executa os marts
docker compose run --rm dbt dbt build --select tag:marts
# Valide no PgAdmin: marts.dim_*, marts.fct_*

# 10. Sobe o Evidence
docker compose --profile evidence up evidence -d
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
