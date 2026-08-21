# Spec 023 — Levantamento: fragilidade de `ipBlock` fixo nas NetworkPolicy de egress do Postgres compartilhado

## Tipo

Investigação (levantamento) — dívida técnica conhecida, registrada como backlog. Nenhuma investigação de código nova foi rodada nesta spec além da conferência dos manifests já versionados no repo `infra`; nenhum YAML foi criado ou alterado, nenhuma `NetworkPolicy` existente foi tocada. A pergunta central (ver Investigação) fica formulada, não respondida — resposta e decisão de migração ficam para uma spec de Design futura.

## Status

Backlog / Proposto, baixa urgência — mesma categoria de outras pendências de backlog não urgente já registradas no projeto. **Não é spec de Design:** não há decisão de solução aqui, só o registro do problema e da pergunta que uma investigação futura precisa responder antes de decidir se vale migrar.

## Contexto

O cluster k3s roda `NetworkPolicy` de egress restrito (`default-deny-egress` por namespace + policy própria por app) para os apps que precisam alcançar o Postgres compartilhado, que roda fora do k3s (container Docker no host, rede bridge própria — não é um `Service` nativo do cluster). Hoje, **duas** dessas policies fixam o IP do Postgres via `ipBlock` de `/32` (valores exatos de IP são detalhe operacional físico — não repetidos aqui, ver "Fronteira de infra" neste `CLAUDE.md`; conferir literal em `infra` spec 080):

- `jeysel-egress-restrict` (namespaces `staging`/`production`) — regra de Postgres com `ipBlock` fixo, confirmado **desatualizado** em relação ao IP real do container (reconfirmado ao vivo via `docker inspect postgres` em 2026-08-21) — ver `infra` spec 080, Contexto e Casos de borda.
- `compras-publicas-api-egress-restrict` (namespace `staging`) — criada em 2026-08-21 (`infra` spec 080) para destravar um `CrashLoopBackOff` do pod `compras-publicas-api` (erro real: `psycopg_pool.PoolTimeout: pool initialization incomplete after 30.0 sec`, causado por egress bloqueado). Criada já com o IP correto, reconfirmado ao vivo na mesma sessão — **não** copiado do vizinho desatualizado, exatamente para não repetir o bug já conhecido.

**`weather-analytics-egress-restrict` fica de fora deste levantamento** — checagem do manifest real (`infra`, `docs/specs/072-weather-analytics-k3s-migracao/networkpolicy-weather-analytics-egress-restrict-{staging,production}.yaml`) confirma que suas únicas regras de egress são DNS (53/UDP+TCP → `kube-system`) e HTTPS irrestrito (443/TCP, sem `to:`) — **sem nenhuma regra de Postgres/`ipBlock`**, porque o app lê/escreve BigQuery, não o Postgres compartilhado. A hipótese original de que as três policies do cluster compartilhavam essa fragilidade não se confirmou; só as duas listadas acima.

O IP do container Postgres já mudou pelo menos uma vez, conforme documentado em `infra` spec 080, Caso de borda ("já aconteceu duas vezes entre os vizinhos"), e a versão de `jeysel-egress-restrict` versionada no repo `infra` continua com o valor antigo — correção registrada como pendência explícita em `infra` spec 080 ("Fora do escopo": *"Corrigir o IP desatualizado em `jeysel-egress-restrict`... Registrado para avaliação futura"*), ainda não fechada até a data desta spec.

Achado relevante para a pergunta de investigação abaixo: `compras-publicas-sc` já versiona, neste próprio repo, uma ponte `Service`+`Endpoints` pro Postgres (`deploy/k8s/base/postgres-service.yaml`, spec 022) — um `Service` `ClusterIP` chamado `postgres` com um `Endpoints` manual apontando pro mesmo IP externo fixo. Isso dá um nome DNS estável dentro do cluster (`postgres.<namespace>.svc.cluster.local`), mas **não** elimina o IP fixo — o `Endpoints` ainda aponta pra um IP de bridge Docker que muda, e seria preciso confirmar se `NetworkPolicy` consegue mesmo selecionar egress por um `Service` sem back-end de pods reais (`podSelector`/`namespaceSelector` selecionam por label de pod, não por nome de `Service`) antes de assumir que essa ponte já resolve o problema. Além disso, cada projeto mantém sua própria cópia do `Service`+`Endpoints` (comentário no próprio manifest: "cada projeto mantém sua própria cópia, não compartilhada") — não há hoje um `Service` único e compartilhado entre os projetos que uma `NetworkPolicy` pudesse referenciar de forma unificada.

## Investigação

**Pergunta a investigar (não respondida nesta spec):**

Existe (ou vale criar) um mecanismo dentro do cluster — `Service` `ClusterIP` compartilhado, ou outro — que permita que as `NetworkPolicy` de egress do Postgres compartilhado usem `podSelector`/`namespaceSelector` em vez de `ipBlock` fixo? Especificamente:

1. `NetworkPolicy` do k3s/kube-router consegue de fato restringir egress por destino `Service` (via `podSelector` apontando pro `Endpoints` do `Service`, ou algum outro mecanismo), dado que o Postgres roda fora do cluster (não é um pod) e o `Endpoints` é preenchido manualmente, não por seleção automática de pod? Ou a limitação estrutural do k3s/kube-router para egress só permite `ipBlock` quando o destino não é um pod nativo do cluster?
2. Se existir um caminho técnico viável, qual o esforço de consolidar as duas policies afetadas (`jeysel-egress-restrict`, `compras-publicas-api-egress-restrict`) para usá-lo de uma vez — e vale estender esse mesmo trabalho pra também corrigir o IP desatualizado de `jeysel-egress-restrict`, já registrado como pendência separada em `infra` spec 080?
3. Existe alternativa mais simples que resolva a fragilidade sem depender de `Service`/`Endpoints` (ex.: IP estático real pro container Postgres via configuração de rede Docker, em vez de deixar o Docker atribuir IP de bridge dinamicamente)? Essa opção evitaria o problema na raiz, sem depender de capacidade do `NetworkPolicy` controller.

## Requirements

Não fechado nesta spec — é levantamento em backlog, sem investigação técnica ainda rodada para as perguntas acima. Nenhum requirement formal até a pergunta ser respondida.

## Design

Não se aplica nesta etapa. Nenhuma decisão de arquitetura tomada — esta spec só registra o problema e a pergunta.

### Componentes afetados

Nenhum alterado nesta spec. Se a migração for decidida numa spec futura, os componentes prováveis seriam:

- `infra`: `docs/specs/072-weather-analytics-k3s-migracao/networkpolicy-*.yaml` (só como referência de padrão, não afetado), manifests de `jeysel-egress-restrict` (localização a confirmar) e `docs/specs/080-egress-compras-publicas-api/networkpolicy-compras-publicas-api-egress-restrict.yaml`.
- `compras-publicas-sc`: `deploy/k8s/base/postgres-service.yaml` (ponte já existente, possível ponto de partida).

## Casos de borda

Perguntas em aberto, formuladas aqui, não respondidas — ficam para a spec de levantamento/Design subsequente:

1. Se `NetworkPolicy` não conseguir de fato selecionar por `Service`/`Endpoints` (limitação estrutural do kube-router pra destino fora do cluster), a única correção viável pode ser fora do k8s inteiramente (IP Docker estático) — nesse caso, esta spec vira, na prática, uma investigação de rede Docker, não de `NetworkPolicy`.
2. `weather-analytics-egress-restrict` não tem hoje regra de Postgres, mas se o projeto `weather-analytics` algum dia precisar de acesso direto ao Postgres compartilhado (hoje usa só BigQuery), herdaria a mesma fragilidade ao copiar o padrão das duas policies existentes — vale registrar isso como motivo a mais pra resolver a causa raiz antes que apareça um quarto caso.
3. Correção do IP desatualizado em `jeysel-egress-restrict` (pendência já registrada em `infra` spec 080, "Fora do escopo") é uma correção pontual independente desta spec — pode (e talvez deva) ser resolvida antes, sem esperar a decisão de migração de mecanismo.

## Fora do escopo

- Implementar qualquer migração de `ipBlock` para `podSelector`/`namespaceSelector` — só investigar e decidir se vale a pena.
- Aplicar ou alterar qualquer `NetworkPolicy` existente (`jeysel-egress-restrict`, `weather-analytics-egress-restrict`, `compras-publicas-api-egress-restrict`).
- Corrigir o IP desatualizado de `jeysel-egress-restrict` (pendência já registrada separadamente em `infra` spec 080).
- Decidir se a correção fica neste repo, no `infra`, ou em ambos — depende da resposta técnica da pergunta de investigação, que não foi respondida aqui.

## Referências de código

- `deploy/k8s/base/postgres-service.yaml` (este repo) — ponte `Service`+`Endpoints` própria pro Postgres, spec 022, achado relevante pra pergunta de investigação.
- `infra`, `docs/specs/080-egress-compras-publicas-api/spec.md` — incidente real do `CrashLoopBackOff` de `compras-publicas-api`, confirmação do IP desatualizado em `jeysel-egress-restrict`, e criação da policy com o `ipBlock` correto (valor literal só no `infra`, repo privado).
- `infra`, `docs/specs/080-egress-compras-publicas-api/networkpolicy-compras-publicas-api-egress-restrict.yaml` — manifest real com `ipBlock` fixo.
- `infra`, `docs/specs/072-weather-analytics-k3s-migracao/networkpolicy-weather-analytics-egress-restrict-{staging,production}.yaml` — confirma ausência de regra de Postgres/`ipBlock` neste projeto (achado que reduziu o escopo de 3 para 2 policies).

## Ver também

- [[010-fronteira-deploy-argocd]] (decisão original de que `NetworkPolicy` pertence ao mono-repo `infra`, não a este repo — motivo pelo qual esta spec só registra o problema, sem propor YAML)
- [[022-deploy-fastapi-frontend-k3s]] (Requirement 6 e Design — criação da ponte `Service`+`Endpoints` pro Postgres neste repo, com a mesma fragilidade de IP já documentada como risco conhecido na época)
