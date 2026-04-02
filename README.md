# 🛒 Compras Públicas SC — Pipeline Analytics

Pipeline de dados analíticos sobre contratos públicos do estado de Santa Catarina.

**Fonte:** [Portal de Transparência do Estado de Santa Catarina](https://www.transparencia.sc.gov.br/) | **Período:** 2016 a 2026

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

## 🚀 Como rodar localmente

### Pré-requisitos
- Docker Desktop instalado e rodando
- Node.js 20+
- Git

---

### Setup

```bash
# 1. Clone o repositório
git clone https://github.com/jeysel/Analytics-Engineer.git
cd Analytics-Engineer/compras-publicas

# 2. Configure as variáveis de ambiente
cp .env.example .env

# 3. Compila as imagens docker
docker compose build

# 4. Sobe o PostgreSQL
docker compose up postgres -d

# Visualizar logs
docker logs compras_postgres

# Configurar PgAdmin (opcional)
# Host:     localhost
# Port:     5432
# Database: compras_publicas
# Username: cp_user
# Password: cp_pass

# Validar dim_datas (deve retornar 5.844 linhas)
# SELECT count(*) FROM raw.dim_datas;

# 5. Instala dependências do dbt
docker compose run --rm dbt deps

# 6. Carrega os dados (seed)
docker compose run --rm dbt seed

# Validar no PgAdmin:
# SELECT count(*) FROM raw.contratos;
# Esperado: ~76.000 linhas

# 7. Executa e valida o staging
docker compose run --rm dbt build --select stg_contratos

# Validar no PgAdmin:
# SELECT table_name
#   FROM information_schema.tables
#   WHERE table_schema = 'staging'
#   ORDER BY table_name;

# 8. Executa e valida o intermediate
docker compose run --rm dbt build --select tag:int

# Validar no PgAdmin:
# SELECT table_name
#   FROM information_schema.tables
#   WHERE table_schema = 'intermediate'
#   ORDER BY table_name;

# 9. Executa os marts
docker compose run --rm dbt build --select tag:marts

# Validar no PgAdmin:
# SELECT table_name
#   FROM information_schema.tables
#   WHERE table_schema = 'marts'
#   ORDER BY table_name;

# Conferir campos descritivos na fct_contratos:
# SELECT
#     ds_situacao_aditivo,
#     ds_situacao_prazo,
#     porte_fornecedor,
#     count(*) as qt
# FROM marts.fct_contratos
# GROUP BY 1, 2, 3
# ORDER BY 4 DESC
# LIMIT 10;

# 10. Sobe o Evidence (desenvolvimento local)
cd evidence
npm install
npm run sources
npm run dev
# Acesse: http://localhost:3000

# Para buildar antes de publicar no GitHub Pages:
npm run build

# 11. Documentação do DBT (opcional)
# Gera a documentação com lineage graph e descrições dos modelos
cd ..
docker compose run --rm dbt docs generate

# Sobe o servidor de documentação
docker compose run --rm -p 8080:8080 dbt docs serve --host 0.0.0.0 --port 8080
# Acesse: http://localhost:8080
```

---

## 📁 Estrutura do Projeto

```
compras-publicas/
├── .github/workflows/   # CI/CD — GitHub Actions
├── postgres/
│   ├── Dockerfile       # Ubuntu 24.04 + PostgreSQL 17
│   ├── entrypoint.sh    # Inicialização do cluster
│   └── init/
│       └── 01_init.sql  # Schemas + dim_datas (2015-2030)
├── dbt/
│   ├── models/
│   │   ├── sources.yml
│   │   ├── staging/     # Padronização dos dados brutos
│   │   ├── intermediate/# Regras de negócio
│   │   └── marts/       # Tabelas analíticas finais
│   ├── seeds/           # CSV dos contratos SC
│   ├── macros/          # generate_schema_name
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── Dockerfile
├── evidence/
│   ├── pages/           # Dashboards (index, orgaos, fornecedores...)
│   └── sources/         # Conexão com PostgreSQL
├── docs/                # Arquitetura e decisões
├── docker-compose.yml
└── .env.example
```

---

## 📊 Dashboard

Acesse o dashboard publicado: **[GitHub Pages](https://jeysel.github.io/Analytics-Engineer/compras-publicas)**

### Páginas disponíveis

| Página | Conteúdo |
|---|---|
| Home | KPIs gerais, evolução anual, top 10 |
| Órgãos Públicos | Ranking por valor e quantidade |
| Fornecedores | Ranking, porte, concentração |
| Modalidades | Distribuição e taxa de aditivos |
| Evolução Temporal | Série temporal mensal e anual |
| Aditivos Contratuais | Tipos, faixas e maiores aditivos |
| Ramos de Atividade | Classificação por setor econômico |
| Fornecedores por Ramo | Análise cruzada com filtro dinâmico |
| Tecnologia da Informação | Análise detalhada do setor de TI |
| Contratos Não Classificados | Contratos de nicho e atípicos |

---

## 🎯 Métricas Analíticas

- Volume de contratos por órgão e período
- Ranking de fornecedores por valor e quantidade
- Distribuição por modalidade de licitação
- Evolução anual de gastos (2016-2026)
- Contratos com aditivo — acréscimo e supressão
- Perfil de contratação dos órgãos
- Classificação por ramo de atividade (16 categorias)
- Análise completa do setor de TI por subcategoria

---

## 👤 Autor

Desenvolvido por [Jeysel](https://github.com/jeysel) como projeto de portfólio em Analytics Engineering.

Portfólio completo: [github.com/jeysel/Analytics-Engineer](https://github.com/jeysel/Analytics-Engineer)