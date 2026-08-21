# 022 — Deploy do FastAPI+frontend em k3s (produção)

## Tipo

Decisão de arquitetura — concretiza as specs 010/011 (fronteira e parâmetros de manifest, já decididas mas nunca implementadas) com as convenções reais dos dois projetos vizinhos, confirmadas por investigação nesta sessão.

## Status

Design definido. Requirements em EARS formalizados. Implementação ainda não feita.

## Resumo

`compras-publicas-sc` (API FastAPI + frontend Jinja2/TS/ECharts) está pronto e testado localmente, mas nunca foi implantado — o site público (`https://contratos-sc.jeysel.dev`) não existe ainda. Esta spec registra as decisões de deploy real, baseadas em investigação direta dos dois projetos já em produção no mesmo cluster (`jeysel-auth`, `weather-analytics`), não em suposição.

## Contexto

- Specs 010/011 já tinham decidido a fronteira (Deployment/Service no repo do app; Application/Ingress/NetworkPolicy no `infra`) e os parâmetros de recurso (`requests`/`limits`), mas nunca foram implementadas em manifest real.
- Investigação desta sessão (repos `compras-publicas-sc` e `infra`) confirmou 5 convenções que não estavam documentadas antes: mecanismo de TLS, ausência de wildcard DNS, estado real (e fragilidade) da ponte Postgres, padrão de role de banco por schema, e estrutura real de `Application` do Argo CD.
- Achado colateral urgente desta mesma investigação: a ponte Postgres→k8s de `jeysel-auth`/`weather-analytics` estava quebrada em produção (IP desatualizado) — mitigada ao vivo, mas o manifest versionado continua desatualizado (pendência separada, fora do escopo desta spec).

## Requirements

### Funcionais

1. A imagem da API/frontend DEVE ser construída via Dockerfile multi-stage: um stage Node (`npm ci && npm run build` em `web/`) gerando os assets estáticos, copiados pra dentro do stage Python final (`api/app/static/`) — `api/app/static/` NÃO é commitado (gitignored), então a imagem SÓ funciona corretamente se o build multi-stage rodar; um Dockerfile single-stage produziria imagem sem frontend, silenciosamente.
2. O workflow de build/push (spec 015) DEVE ganhar um job novo, com `paths` próprios (`api/**`, `web/**`), publicando uma imagem separada da de ingestão (spec 009) — mudança em `dbt/` não deve disparar rebuild desnecessário desta imagem, e vice-versa.
3. A API DEVE se conectar ao Postgres usando uma role dedicada de leitura (`compras_publicas_api` ou nome equivalente), com `GRANT SELECT` só no schema `marts` — não DEVE reaproveitar `compras_publicas_app` (que tem CRUD completo em todos os schemas, usada pela ingestão). Mesmo padrão já confirmado em uso real por `transparencia_app`/`transparencia_dbt` (GRANT escopado por schema, não por app).
4. O `Deployment` DEVE seguir os `requests`/`limits` já decididos na spec 011 (`cpu: 100m/memory: 128Mi` requests; `cpu: 250-500m/memory: 256Mi` limits), no namespace `production` e `staging` compartilhados (não dedicado).
5. O `Ingress` DEVE usar host sintético `<app>-<ambiente>.internal` (ex.: `compras-publicas-production.internal`), seguindo a convenção real confirmada — o domínio público (`contratos-sc.jeysel.dev`) é resolvido por uma camada fora do k3s (Nginx no host, ver Requirement 7), não pelo `Ingress` diretamente.
6. A ponte `Service`+`Endpoints` pro Postgres compartilhado DEVE ser criada no repo `compras-publicas-sc` (mesmo padrão dos vizinhos — cada projeto mantém sua própria cópia, não compartilhada), com o IP real confirmado no momento da implementação (não presumir o valor documentado em spec anterior, que já mudou uma vez).
7. A configuração de TLS/domínio público (vhost Nginx + certificado Let's Encrypt via certbot pra `contratos-sc.jeysel.dev`, proxy para o `kubectl port-forward` persistente do Traefik) DEVE ser feita no host do servidor — fora do k3s, fora de qualquer repo Git versionado por padrão (confirmar se há algum lugar que versiona config de Nginx antes de decidir se isso fica só como passo manual documentado ou se entra em algum repo).
8. DUAS `Application` do Argo CD DEVEM ser criadas (uma por ambiente, `compras-publicas-staging` e `compras-publicas-production`), `syncPolicy: {}` (manual, sem auto-sync), `path` apontando pro overlay Kustomize do próprio repo `compras-publicas-sc`.
9. O registro DNS individual de `contratos-sc.jeysel.dev` na Cloudflare (não há wildcard) é pré-requisito manual do usuário, fora de qualquer prompt de implementação — bloqueia a emissão do certificado TLS até ser feito.

### Não-funcionais

1. A fragilidade da ponte `Service`+`Endpoints` (IP não-estático do container Postgres) é um risco já materializado uma vez nesta sessão (jeysel-auth/weather-analytics) — o Requirement 6 desta spec NÃO resolve a causa raiz (só replica o padrão existente), mas deve ser implementado com essa fragilidade já documentada, não descoberta de surpresa depois.

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| TLS/domínio público | Nginx no host + certbot, proxy pra `kubectl port-forward` do Traefik via systemd | Mecanismo real já em uso pelos dois projetos vizinhos — não existe `cert-manager` no cluster, replicar em vez de introduzir mecanismo novo |
| Host do `Ingress` | Sintético `<app>-<ambiente>.internal` | Convenção real confirmada — o `Ingress` do k3s nunca vê o domínio público diretamente |
| DNS | Registro individual manual na Cloudflare (sem wildcard) | Confirmado empiricamente (`NXDOMAIN` em subdomínio de teste) — não há atalho, é passo manual sempre |
| Ponte Postgres | `Service`+`Endpoints` própria no repo do app, mesmo padrão dos vizinhos | Consistência com o que já existe; risco de IP dinâmico já documentado e, agora, já vivido |
| Role de banco pra API | Nova role `compras_publicas_api`, `SELECT` só em `marts` | Least privilege — API pública não deveria ter a mesma credencial de escrita da ingestão. Padrão confirmado em uso real (`transparencia_app`/`_dbt`) |
| Build da imagem | Multi-stage (Node → Python) | `api/app/static/` não é commitado; single-stage produziria imagem quebrada silenciosamente |
| Argo CD | 2 `Application`, `syncPolicy: {}` manual | Mesmo padrão confirmado nos dois projetos vizinhos |

### Componentes afetados

- `compras-publicas-sc`: `api/Dockerfile` (multi-stage), `.github/workflows/build-and-push.yml` (job novo), `deploy/k8s/base/` + `deploy/k8s/overlays/{staging,production}/` (Deployment, Service, Service+Endpoints da ponte Postgres).
- `infra`: 2 `Application` (Argo CD), `Ingress` x2 (staging/production), config de Nginx/certbot no host (fora de repo, ou registrada onde a investigação de implementação confirmar).
- Postgres compartilhado: nova role `compras_publicas_api`.
- AWS Secrets Manager: novo secret pras credenciais da API (distinto do `compras-publicas/prod` da ingestão, já que a role é diferente).

## Casos de borda

- Container Postgres recriado de novo (já aconteceu uma vez) quebra a ponte desta spec do mesmo jeito que quebrou a dos vizinhos — não resolvido aqui, é o mesmo risco herdado conscientemente.
- Cloudflare/DNS não registrado antes da tentativa de emitir certificado — certbot falha, precisa checar isso antes de tentar.
- `syncPolicy: {}` manual significa que um `git push` no repo do app NÃO implanta sozinho — precisa de sync manual do Argo CD depois, sempre.

## Fora do escopo

- Corrigir o manifest versionado desatualizado de jeysel-auth/weather-analytics (repo `jeysel.dev`) — pendência separada, já registrada.
- Resolver a causa raiz da fragilidade de IP do Postgres (ex.: IP estático, mecanismo de sync automático) — herdado como risco conhecido, não corrigido nesta spec.
- Migrar o Postgres compartilhado pra dentro do k3s (eliminaria a ponte de vez) — mudança de arquitetura maior, não avaliada aqui.

## Referências de código

_A preencher conforme a implementação._

## Ver também

- [[003-storage-e-chave-unica]] (ponte Postgres, adendo original)
- [[009-automacao-da-ingestao]]
- [[010-fronteira-deploy-argocd]]
- [[011-parametros-manifest]]
- [[012-eixo-frontend-biblioteca-grafico]]
- [[015-convencao-build-imagem]]
