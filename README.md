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
    (frontend em transição — ver nota abaixo)
```

> **Frontend em transição:** o dashboard anterior (Evidence.dev, publicado via GitHub Pages) foi removido deste repositório. O novo frontend (FastAPI + ECharts, spec 012) ainda não foi implementado — o projeto está temporariamente sem apresentação pública além do pipeline dbt/PostgreSQL. Ver `docs/specs/012-eixo-frontend-biblioteca-grafico/spec.md` e `docs/specs/013-levantamento-dbt-legado/spec.md` (Caso de borda 3) para o histórico da decisão.

## 🧱 Stack

| Camada | Tecnologia |
|---|---|
| Banco de dados | PostgreSQL 17 |
| Transformação | dbt-core 1.9 |
| Visualização | *(em transição — spec 012, não implementado)* |
| Orquestração local | Docker Compose |
| CI/CD | GitHub Actions |

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

# 2. Ative o pre-commit hook local (bloqueia commit de IP/ARN/chave privada
#    em arquivos de documentação — precisa rodar uma vez por clone, não se
#    propaga sozinho; ver .githooks/pre-commit)
git config core.hooksPath .githooks

# 3. Configure as variáveis de ambiente
cp .env.example .env

# 4. Compila as imagens docker
docker compose build

# 5. Sobe o PostgreSQL
docker compose up postgres -d

# Visualizar logs
docker logs compras_postgres

# Configurar PgAdmin (opcional)
# Host:     localhost
# Port:     5432
# Database: compras_publicas
# Username: cp_user
# Password: cp_pass

# 6. Instala dependências do dbt
docker compose run --rm dbt deps

# 7. Carrega os dados (seed)
docker compose run --rm dbt seed

# Validar no PgAdmin:
# SELECT count(*) FROM raw.contratos;
# Esperado: ~76.000 linhas

# 8. Executa e valida o staging
docker compose run --rm dbt build --select stg_contratos

# Validar no PgAdmin:
# SELECT table_name
#   FROM information_schema.tables
#   WHERE table_schema = 'staging'
#   ORDER BY table_name;

# 9. Executa e valida o intermediate
docker compose run --rm dbt build --select tag:int

# Validar no PgAdmin:
# SELECT table_name
#   FROM information_schema.tables
#   WHERE table_schema = 'intermediate'
#   ORDER BY table_name;

# 10. Executa os marts
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

# 11. Documentação do DBT (opcional)
# Gera a documentação com lineage graph e descrições dos modelos
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
│   └── entrypoint.sh    # Inicialização do cluster
├── dbt/
│   ├── models/
│   │   ├── staging/     # Padronização dos dados brutos + dim_datas (date_spine)
│   │   ├── intermediate/# Regras de negócio
│   │   └── marts/       # Tabelas analíticas finais
│   ├── seeds/           # CSV dos contratos SC
│   ├── macros/          # generate_schema_name
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── Dockerfile
├── docs/                # Arquitetura e decisões
├── docker-compose.yml
└── .env.example
```

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