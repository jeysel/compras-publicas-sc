# Spec 002 — Estado atual da infra k3s (Fase 1: levantamento)

Status: rascunho, aguardando revisão humana antes de virar tarefa executável.

Esta fase é somente leitura. Nenhum comando executado abaixo criou, alterou ou apagou nada no repo, no cluster ou na AWS. Nenhum valor de segredo foi solicitado ou colado — só nomes, metadata e existência.

**Nota (2026-08-19):** esta spec foi reescrita para remover dado operacional físico (IP de servidor, nome de identity IAM, nomes literais de outros projetos no mesmo cluster, nomes de arquivo de script de sync) que não deveria estar num repo público — ver regra em `docs/memory/constitution.md`. O output literal completo da investigação original (com esses dados) foi movido para a spec equivalente no mono-repo de infra privado (`docs/specs/078-compras-publicas-estado-infra-k3s/spec.md`), acessível só a quem tem acesso àquele repo. Aqui ficam só os achados arquiteturais/de padrão que informam decisões deste projeto.

## Investigação

### 1. Repo `compras-publicas-sc` (a aplicação)

Não existe `package.json`/`requirements.txt`/`pyproject.toml`/`go.mod` na raiz do repo — a raiz é um projeto dbt + Evidence + Postgres via docker-compose, sem um único "stack" de linguagem no sentido tradicional.

```
--- docker-compose.yml ---
version: "3.9"

services:
  postgres:
    build:
      context: ./postgres
      dockerfile: Dockerfile
    container_name: compras_postgres
    restart: unless-stopped
    env_file: .env
    environment:
      POSTGRES_DB:       ${POSTGRES_DB:-compras_publicas}
      POSTGRES_USER:     ${POSTGRES_USER:-cp_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-cp_pass}
      TZ: America/Sao_Paulo
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - pgdata:/var/lib/postgresql/17/main
      - pglog:/var/log/postgresql
    networks:
      - compras_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d ${POSTGRES_DB:-compras_publicas}"]
      interval: 10s
      timeout: 5s
      retries: 5

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: compras_pgadmin
    restart: unless-stopped
    env_file: .env
    environment:
      PGADMIN_DEFAULT_EMAIL:    ${PGADMIN_EMAIL:-admin@compras.local}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD:-admin}
      TZ: America/Sao_Paulo
    ports:
      - "${PGADMIN_PORT:-8080}:80"
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - compras_network

  dbt:
    build:
      context: ./dbt
      dockerfile: Dockerfile
    container_name: compras_dbt
    env_file: .env
    environment:
      DBT_PROFILES_DIR: /usr/app/dbt
      POSTGRES_HOST:     postgres
      POSTGRES_PORT:     ${POSTGRES_PORT:-5432}
      POSTGRES_DB:       ${POSTGRES_DB:-compras_publicas}
      POSTGRES_USER:     ${POSTGRES_USER:-cp_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-cp_pass}
    volumes:
      - ./dbt:/usr/app/dbt
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - compras_network
    profiles: ["dbt"]

networks:
  compras_network:
    driver: bridge

volumes:
  pgdata:
  pglog:
  pgadmin_data:
  evidence_node_modules:
```

```
--- find . -iname "Dockerfile*" -o -iname "docker-compose*.yml" ---
./dbt/Dockerfile
./docker-compose.yml
./evidence/Dockerfile
./postgres/Dockerfile
```

```
--- .github/workflows/compras-publicas.yml ---
name: Pipeline Compras Publicas

on:
  push:
    branches: [main]
    paths:
      - 'compras-publicas/**'
      - '.github/workflows/compras-publicas.yml'
  workflow_dispatch:

jobs:
  pipeline:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_DB:       compras_publicas
          POSTGRES_USER:     cp_user
          POSTGRES_PASSWORD: cp_pass
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Inicializa schemas
        env:
          PGPASSWORD: cp_pass
        run: |
          psql -h localhost -U cp_user -d compras_publicas \
            -f compras-publicas/postgres/init/01_init.sql

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Instala dbt
        run: pip install dbt-core==1.9.* dbt-postgres==1.9.*

      - name: dbt deps
        working-directory: compras-publicas/dbt
        run: dbt deps
        env:
          DBT_PROFILES_DIR: .
          POSTGRES_HOST:     localhost
          POSTGRES_PORT:     "5432"
          POSTGRES_DB:       compras_publicas
          POSTGRES_USER:     cp_user
          POSTGRES_PASSWORD: cp_pass

      - name: dbt seed
        working-directory: compras-publicas/dbt
        run: dbt seed
        env:
          DBT_PROFILES_DIR: .
          POSTGRES_HOST:     localhost
          POSTGRES_PORT:     "5432"
          POSTGRES_DB:       compras_publicas
          POSTGRES_USER:     cp_user
          POSTGRES_PASSWORD: cp_pass

      - name: dbt build
        working-directory: compras-publicas/dbt
        run: dbt build
        env:
          DBT_PROFILES_DIR: .
          POSTGRES_HOST:     localhost
          POSTGRES_PORT:     "5432"
          POSTGRES_DB:       compras_publicas
          POSTGRES_USER:     cp_user
          POSTGRES_PASSWORD: cp_pass

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Instala dependencias Evidence
        working-directory: compras-publicas/evidence
        run: npm install

      - name: Sources Evidence
        working-directory: compras-publicas/evidence
        run: npm run sources
        env:
          EVIDENCE_SOURCE__COMPRAS__host:     localhost
          EVIDENCE_SOURCE__COMPRAS__port:     "5432"
          EVIDENCE_SOURCE__COMPRAS__database: compras_publicas
          EVIDENCE_SOURCE__COMPRAS__user:     cp_user
          EVIDENCE_SOURCE__COMPRAS__password: cp_pass
          EVIDENCE_SOURCE__COMPRAS__schema:   marts

      - name: Build Evidence
        working-directory: compras-publicas/evidence
        run: npm run build
        env:
          EVIDENCE_SOURCE__COMPRAS__host:     localhost
          EVIDENCE_SOURCE__COMPRAS__port:     "5432"
          EVIDENCE_SOURCE__COMPRAS__database: compras_publicas
          EVIDENCE_SOURCE__COMPRAS__user:     cp_user
          EVIDENCE_SOURCE__COMPRAS__password: cp_pass
          EVIDENCE_SOURCE__COMPRAS__schema:   marts

      - name: Publica no GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir:  ./compras-publicas/evidence/build
          destination_dir: compras-publicas
```

```
--- grep -ril "cron\|worker\|celery\|sidekiq\|queue" ---
(nenhum resultado — sem sinal de cron/worker/queue no código da aplicação)
```

**Observação:** o workflow do Actions builda e publica um site estático (Evidence → GitHub Pages) a partir de um pipeline dbt rodado dentro do próprio job de CI, contra um Postgres efêmero (`services: postgres` do Actions), não contra um banco persistente. Não há imagem de container publicada em nenhum registry (GHCR ou outro) hoje — os `Dockerfile`s existentes (`dbt/`, `postgres/`, `evidence/`) só são usados pelo `docker-compose.yml` local, não pelo workflow.

---

### 2. Mono-repo de infra k3s (privado — detalhe completo em repo de infra)

Existem outros dois projetos já migrados para k3s antes deste, seguindo um padrão já estabelecido. Nomes literais, URLs de repo e nomes de arquivo de script ficam no repo de infra privado (spec 078) — não são reproduzidos aqui.

**Achado arquitetural (o que importa para o design deste projeto):**

- Cada aplicação é deployada via Argo CD (push → CI → build de imagem → registry → Argo CD sync), lendo manifests do próprio repo da aplicação (`deploy/k8s/overlays/<production|staging>`) — **não** de um diretório central no mono-repo de infra.
- O mono-repo de infra guarda só os manifests da `Application` do Argo CD e do `Ingress`/`NetworkPolicy` — confirma a fronteira já descrita na seção "Fronteira de infra" deste `CLAUDE.md`.
- Os scripts de deploy mais antigos do mono-repo de infra (fluxo `docker-compose` legado de outros projetos) não tocam k3s — são um fluxo separado, não aplicável a este projeto.

---

### 3. Cluster k3s (detalhe completo — endereços, nomes de recurso — em repo de infra privado)

**Achado arquitetural:**

- Namespaces do cluster seguem o padrão `production`/`staging` por ambiente, mais os namespaces de sistema (`argocd`, `kube-system`, etc.) — nenhum namespace dedicado a este projeto ainda existe.
- Argo CD está instalado e operacional no cluster (CRDs `applications.argoproj.io`, `applicationsets.argoproj.io`, `appprojects.argoproj.io` presentes).
- Ingress controller default do cluster é **Traefik** (`IngressClass` default).
- **Não há External Secrets Operator nem Sealed Secrets instalado** — confirmado via ausência dos CRDs correspondentes (`externalsecrets`, `sealedsecrets`). Os Secrets Kubernetes dos projetos já migrados são `Opaque` simples, aplicados via `kubectl create secret generic` por scripts de sync do mono-repo de infra, que por sua vez leem de AWS Secrets Manager. **Não é GitOps de secret** (não versionado no Git) — é sync manual/scriptado fora do Argo CD. Esse é o padrão que as specs 002/003 deste projeto decidiram replicar (ver seção "Segredos e stack de deploy" do `CLAUDE.md`).
- Os dois projetos já migrados não declaram `env` diretamente no manifest do `Deployment` na maior parte dos casos (usam `envFrom`/`secretRef` para o segredo sincronizado) — um deles expõe uma única env var de configuração de UI, não-sensível.

---

### 4. AWS Secrets Manager (detalhe completo — ARN, nome de identity — em repo de infra privado)

**Achado arquitetural:** a identity IAM usada hoje pelo `aws` CLI no servidor tem escopo **restritivo**, a ponto de bloquear até `secretsmanager:ListSecrets`/`DescribeSecret`/`GetResourcePolicy` — não é possível, a partir dessa identidade, listar o inventário completo de secrets na conta nem confirmar metadata (data de rotação, descrição) dos secrets dos projetos já migrados. O nome/escopo original da identity sugere que foi criada para outro projeto e reaproveitada — ver `CLAUDE.md`, seção "Segredos e stack de deploy": **se este projeto precisar de um secret novo, confirmar se essa identity tem permissão pro nome específico antes de assumir que o script de sync vai funcionar.**

## Fora do escopo desta fase

Decisões de design para o deploy do `compras-publicas-sc` no k3s (nova Application Argo CD, namespace, secret, ingress, cron/job para o pipeline dbt) ficam para a Fase 2, só depois desta investigação revisada.
