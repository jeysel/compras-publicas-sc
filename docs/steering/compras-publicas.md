# Steering — Compras Públicas SC

Documentação técnica interna do processo SDD para este repositório: o que
`compras-publicas-sc` precisa/espera logicamente do restante do ambiente
(camadas de dado, fluxo de ingestão, arquitetura da API/frontend). Não
descreve detalhe operacional físico (IP, hostname, nome de identity/
credential, nome de outros projetos no cluster, nome de arquivo de script
de infra) — essa fronteira é deliberada e vale mesmo em spec local não
pushada, ver `docs/memory/constitution.md` (regra 1) e a seção "Fronteira
de infra" do `CLAUDE.md` na raiz. Para decisões, incidentes e o estado real
de cada deploy, `CLAUDE.md` é a fonte de verdade; este documento descreve a
arquitetura em regime, não o histórico de como ela chegou lá.

## Fluxo de dados

```
 ┌───────────────────────────────────────────┐
 │  Portal Transparência SC (dados.sc.gov.br) │  CSV estático, publicação mensal
 └──────────────────┬──────────────────────────┘
                    │  download manual (spec 030 — fonte CKAN
                    │  original está congelada desde set/2025)
                    ▼
 ┌──────────────────────────────────────────────────────┐
 │  dbt/scripts/ingest.sh + process_csv.py               │
 │  Valida schema (tolerante, spec 017) → upsert por     │
 │  (cdunidadegestora, nucontrato) em raw.contratos        │
 │  (spec 030) — não é truncate/reload                  │
 └──────────────────┬───────────────────────────────────┘
                    │
                    ▼
            ┌──────────────────────────────┐
            │  Postgres — schema raw        │
            │  contratos (seed dbt)         │
            └──────────────┬────────────────┘
                           │  dbt run/build
                           ▼
            ┌──────────────────────────────────────────┐
            │  Postgres — schemas                       │
            │  staging.*       (views)                 │
            │  intermediate.*  (views)                 │
            │  marts.*         (tabelas)               │
            │                                          │
            │  dim_datas, dim_fornecedores,             │
            │  dim_modalidades, dim_orgaos, dim_ramos   │
            │  fct_contratos, fct_aditivos,              │
            │  fct_contratos_ramo                        │
            │  mart_contratos_temporal,                  │
            │  mart_concentracao_fornecedor,             │
            │  mart_diversidade_vencedores,              │
            │  mart_escalada_custo                       │
            └──────────────┬───────────────────────────┘
                           │  psycopg (api/app/db.py)
                           ▼
            ┌──────────────────────────────────────────┐
            │  API FastAPI (api/) + frontend (web/)      │
            │  rotas /api/v1/* (JSON) + páginas servidas │
            │  por Jinja2/ECharts                        │
            └──────────────────────────────────────────┘
```

`raw.contratos` guarda o histórico completo recebido até hoje (não é janela
recente) — o upsert por `(cdunidadegestora, nucontrato)` é o que permite
reprocessar o CSV inteiro a cada carga sem duplicar linha nem perder
histórico que não está mais no arquivo publicado. Ver
[[030-ingestao-manual-upsert]] para o motivo de ter abandonado o fluxo
automatizado via CKAN que a spec [[009-automacao-da-ingestao]] desenhou
originalmente.

### Fronteira temporal: 2016 é piso, não é o dado real completo

`stg_contratos` corta `ano_assinatura < 2016` antes de qualquer mart
consumir o dado; `GET /api/v1/anos-disponiveis` aplica
`GREATEST(MIN(ano_assinatura), 2016)` como piso adicional no próprio SQL,
redundante com o corte do staging mas deliberado (defesa em profundidade).
O intervalo 1994–2015 existe no `raw.contratos`/seed, mas é cauda
documentada — nunca aparece em KPI, série temporal ou export. Motivo e
decisão completos em [[034-fronteira-cobertura-temporal-2016]].

## Lineage dbt

```
raw.contratos ──► stg_contratos (view, corta ano_assinatura < 2016)
                         │
      ┌──────────────────┼──────────────────────────────────┐
      │                  │                                  │
      ▼                  ▼                                  ▼
int_processos   int_contratos_por_{orgao,fornecedor,modalidade,ramo}   (intermediate, views)
      │                  │
      │     int_concentracao_fornecedor_{estado,por_orgao}
      │     int_contratos_evolucao_{anual,por_modalidade,por_orgao}
      │
      ▼
dim_datas / dim_fornecedores / dim_modalidades / dim_orgaos / dim_ramos
      │
      ▼
fct_contratos ──► fct_aditivos
      │
      └─► fct_contratos_ramo
                │
                ▼
mart_contratos_temporal · mart_concentracao_fornecedor ·
mart_diversidade_vencedores · mart_escalada_custo
```

`dim_datas` é gerada por `dbt_utils.date_spine` em `stg_dim_datas`
(2015-01-01 a 2030-12-31) — não vem de fonte externa, é um model dbt desde
[[020-dim_datas-como-model-dbt-nao-fonte-externa]]. O período da dimensão
calendário começa antes do piso de 2016 de propósito (spec 020 não é a
mesma decisão que a spec 034 — a dimensão cobre o range, o corte de dado
real é feito em `stg_contratos`).

## Schemas Postgres em produção

| Schema | Origem | Conteúdo |
|--------|--------|----------|
| `raw` | seed dbt + upsert manual (`ingest.sh`) | `contratos` — histórico completo recebido até hoje, incluindo a cauda pré-2016 não exposta |
| `staging` | dbt (view) | `stg_contratos` (corta `ano_assinatura < 2016`), `stg_dim_datas` |
| `intermediate` | dbt (view) | agregações por órgão/fornecedor/modalidade/ramo, concentração de fornecedor, evolução anual — base para as marts, não consumido direto pela API |
| `marts` | dbt (table) | dimensões (`dim_*`), fatos (`fct_*`) e as 4 marts analíticas finais que a API consulta |

## Ingestão — manual, sem cron automático

Não há `CronJob` k3s nem crontab de host disparando a ingestão hoje. O
cron diário que existia (linha de cron do pipeline, `run` do serviço no
compose do repo `infra`) foi
**removido deliberadamente** na spec 030 (data divergente entre repositorios; ver nota na spec 030): a fonte CKAN automatizável que o
cron dependia está congelada desde set/2025, e um disparo automático
baseado em `ETag`/`Last-Modified` do link antigo arriscava sobrescrever
silenciosamente o histórico 2011–2020 que só existe porque foi trazido
manualmente. Hoje o fluxo é:

1. Download manual do CSV publicado em dados.sc.gov.br.
2. `dbt/scripts/ingest.sh` (valida schema tolerante, spec
   [[017-validacao-schema-tolerante]]) sobrescreve
   `dbt/seeds/contratos.csv` e roda `dbt seed` + upsert em `raw.contratos`.
3. `dbt build` recalcula staging → marts.

`dbt/scripts/ingest.sh`, a imagem Docker do pipeline e o workflow de build
continuam existindo no repo (não foram apagados), mas nada os dispara
automaticamente — rodar é decisão manual. Ver [[009-automacao-da-ingestao]]
(spec superada, mantida como histórico do que foi avaliado e descartado) e
[[030-ingestao-manual-upsert]] (decisão vigente).

## Deploy

Imagem Docker (`compras-publicas-api`, API + frontend juntos desde a spec
[[022-deploy-fastapi-frontend-k3s]]) publicada no GHCR via
`.github/workflows/build-and-push.yml`, disparado em push para `main` que
toque `dbt/`, `api/` ou `web/`. O job roda a suíte de testes (Postgres real
como serviço, [[033-suite-testes-automatizada]]) antes de publicar.

- **Staging**: Argo CD com `automated`/`selfHeal` — o próprio CI atualiza
  `deploy/k8s/overlays/staging/kustomization.yaml` (`newTag`) a cada push
  em `main` e o Argo CD sincroniza sozinho. Não editar esse `newTag` manualmente
  em condição normal.
- **Produção**: promoção manual — editar
  `deploy/k8s/overlays/production/kustomization.yaml` (`newTag` = um SHA já
  validado em staging) e disparar o sync do Argo CD. GitHub Actions nunca
  decide o que roda em produção; CLAUDE.md > "Status da migração" tem o
  histórico recente de promoções reais.
- 2 réplicas em produção (gap de connection pool do Postgres compartilhado
  durante restart de liveness, decisão registrada no `kustomization.yaml`
  de produção); staging roda com o default do `base` (1 réplica). App é
  stateless — API de leitura, sem sessão local, então múltiplas réplicas
  não exigem coordenação.
- `/health` testa `SELECT 1` via o pool real de `api/app/db.py` — não é
  rota estática. `readinessProbe`/`livenessProbe` apontam pra lá; ver
  nota de incidente no `kustomization.yaml` de produção para o teste real
  de falha controlada que validou esse comportamento.
- Fronteira de quem é dono de qual manifest: `Deployment`/`Service` deste
  app vivem neste repo; `Ingress`/`NetworkPolicy` e o recurso `Application`
  do Argo CD vivem no mono-repo `infra` — ver [[010-fronteira-deploy-argocd]]
  e a seção "Fronteira de infra" do `CLAUDE.md`.

## Mascaramento de dado pessoal

`api/app/masking.py` classifica `id_contratado` como veio da mart
(`cpf_mascarado_na_fonte`, `cnpj` ou `nao_identificado`) mas **não
reformata** — achado da spec 012 confirmou que a fonte (portal de
transparência) já entrega CPF pré-mascarado (`***.NNN.NNN-**`) e CNPJ
formatado sem máscara, então não existe dígito cru pra mascarar neste
ponto da pipeline. O ponto existe para ser reaproveitável caso uma fonte
futura entregue CPF/CNPJ cru, não porque há mascaramento ativo hoje.

## Detalhes técnicos importantes

### Rotas da API são todas `/api/v1/*`, servidas junto com o frontend
Um único `Deployment`/imagem serve as rotas JSON (`api/app/routers/*.py`,
uma por relatório/mart) e as páginas Jinja2/ECharts (`web/`) — não são dois
serviços separados. Rotas atuais: `anos-disponiveis`, `kpis-resumo`,
`contratos-temporal`, `concentracao-fornecedor`, `diversidade-vencedores`,
`escalada-custo`, `fornecedor-por-segmento`, `modalidades`, `orgaos`,
`perfil-fornecedores`, `qualidade-dado-orgao`, `top-aditivos`,
`variacao-custo-modalidade`, `variacao-prazo-modalidade` (esta última
ainda responde 200 mas foi retirada do menu/home, ver histórico no
`kustomization.yaml` de produção).

### Filtros de ano sempre passam pelo piso de `anos-disponiveis`
Qualquer página/rota que aceite filtro de ano (`ano_inicio`/`ano_fim`,
`dt_inicio_de`) deve respeitar o piso de 2016 vindo de
`/api/v1/anos-disponiveis` — nunca aceitar ano abaixo disso vindo de input
do usuário sem validar contra esse piso, senão a UI pode pedir dado que o
staging já cortou e receber resultado vazio silenciosamente.

### `web/` é Vite + ECharts, build versionado por hash de conteúdo
Cache-busting via nome de arquivo com hash ([[027-cache-busting-vite-static]])
— ao validar um deploy em staging/produção, confirmar o hash do bundle
servido (`main-<hash>.js`/`.css`) contra o hash esperado do commit, não só
assumir que o container novo está servindo o build novo (bind-mount local
pode servir build obsoleto, já aconteceu — ver memória de sessão sobre
docker-compose local).

## Ver também
- `CLAUDE.md` (raiz) — regras não-negociáveis, fronteira de infra, status
  de migração e histórico de incidentes/deploys reais.
- `docs/memory/constitution.md` — regra de fronteira entre este documento
  e o repositório `infra` (nunca dado operacional físico aqui).
- [[010-fronteira-deploy-argocd]] — decisão formal da fronteira de deploy.
- [[030-ingestao-manual-upsert]] — decisão vigente de ingestão.
- [[034-fronteira-cobertura-temporal-2016]] — decisão do piso de 2016.
