# 011 — Parâmetros do manifest: namespace, domínio e resource limits

## Tipo

Decisão de implementação — concretiza a fronteira já formalizada em [[010-fronteira-deploy-argocd]].

## Status

Design e Requirements (EARS) definidos em 2026-08-19 — pendente de aprovação/fechamento pelo usuário.

## Resumo

A spec 010 decidiu *onde* os manifests vivem. Esta spec decide os valores concretos: namespace de `compras-publicas`, domínio/host do Ingress, e `requests`/`limits` de CPU/memória pro `Deployment` (app) e pro `CronJob` (spec 009). Parte do levantamento já foi feito na spec 002 (Bloco 3 — `kubectl get ingress -A`, namespaces existentes) mas os valores reais podem não ter sido capturados de forma reutilizável ali — confirmar antes de decidir, não presumir que o placeholder genérico daquela investigação virou dado real.

## Contexto

- Spec 002: levantou namespaces e Ingress dos dois projetos existentes, mas o roteiro original usava `<namespace-projeto-1>`/`<namespace-projeto-2>` como placeholder — precisa confirmar se os valores reais ficaram registrados na spec ou só no output bruto que foi pro repo de infra privado.
- Spec 009: confirmou headroom real do cluster (CPU 7%, memória 49% em uso) — base pra propor `requests`/`limits` sem repetir o susto de recurso apertado da leitura inicial da spec 003.
- Spec 003: Postgres já tem schema/banco dedicado pra `compras-publicas` — não afeta namespace do workload em si, mas é referência de que o padrão aqui é "recurso compartilhado com isolamento lógico", não físico.

## Investigação

### Bloco 1 — confirmar namespace e domínio reais dos projetos existentes

```
$ kubectl get namespaces
NAME              STATUS   AGE
argocd            Active   6d21h
default           Active   6d21h
kube-node-lease   Active   6d21h
kube-public       Active   6d21h
kube-system       Active   6d21h
production        Active   6d21h
staging           Active   6d21h
```

`kubectl get ingress -A` também foi rodado, mas o output cru contém nome e host dos dois projetos vizinhos já em produção no cluster — dado operacional de infra de terceiros compartilhando o cluster. Pela mesma regra que gerou a remediação das specs 002/003 (commit `e901493` — "remediar dado operacional exposto nas specs 002/003, mover para repo de infra"), esse output não é colado aqui; fica registrado no repo de infra privado.

**Achado (generalizado, sem nomes de projeto):** não existe namespace por projeto — os dois projetos existentes **compartilham** os namespaces `production` e `staging` (um Ingress por projeto, por ambiente, dentro do mesmo namespace). Os hosts seguem o padrão `<nome-do-projeto>-<ambiente>.internal` — sufixo `.internal`, ou seja, não é o domínio público diretamente no `spec.rules.host` do Ingress; deve existir outra camada resolvendo o hostname público real (proxy, túnel, ou DNS externo) — confirmar qual foge do escopo desta spec, é pergunta pro repo de infra.

Isso **contradiz** a hipótese registrada no Contexto/Design original ("Tendência: dedicado, mesmo padrão de isolamento lógico do Postgres") — o padrão real observado é namespace por **ambiente**, compartilhado entre projetos, não namespace por projeto.

### Bloco 2 — requests/limits já declarados nos projetos existentes (ou ausência deles)

```
$ kubectl get deployment -A -o jsonpath='...'
argocd/argocd-applicationset-controller
  requests: {"cpu":"50m","memory":"64Mi"}  limits: {"cpu":"200m","memory":"256Mi"}
argocd/argocd-redis
  requests: {"cpu":"50m","memory":"32Mi"}  limits: {"cpu":"200m","memory":"128Mi"}
argocd/argocd-repo-server
  requests: {"cpu":"100m","memory":"128Mi"}  limits: {"cpu":"500m","memory":"512Mi"}
argocd/argocd-server
  requests: {"cpu":"100m","memory":"128Mi"}  limits: {"cpu":"300m","memory":"256Mi"}
kube-system/coredns
  requests: {"cpu":"100m","memory":"70Mi"}  limits: {"memory":"170Mi"}
kube-system/local-path-provisioner
  requests:   limits: 
kube-system/metrics-server
  requests: {"cpu":"100m","memory":"70Mi"}  limits: 
kube-system/traefik
  requests:   limits: 
production/<projeto-1>
  requests: {"cpu":"100m","memory":"128Mi"}  limits: {"cpu":"500m","memory":"256Mi"}
production/<projeto-2>
  requests: {"cpu":"100m","memory":"128Mi"}  limits: {"cpu":"250m","memory":"256Mi"}
staging/<projeto-1>
  requests: {"cpu":"100m","memory":"128Mi"}  limits: {"cpu":"500m","memory":"256Mi"}
staging/<projeto-2>
  requests: {"cpu":"100m","memory":"128Mi"}  limits: {"cpu":"250m","memory":"256Mi"}
```

Nomes reais dos dois projetos existentes substituídos por `<projeto-1>`/`<projeto-2>` — mesma razão do Bloco 1 (dado operacional de terceiros, fica no repo de infra privado).

**Achado:** os dois projetos existentes **declaram** `requests`/`limits` — não rodam sem limite (diferente de `local-path-provisioner`/`traefik`, que rodam sem declarar). Padrão real: `requests` idêntico entre os dois (`cpu: 100m`, `memory: 128Mi`); `limits` varia um pouco (`cpu: 500m` vs `250m`, `memory: 256Mi` igual nos dois). Mesma faixa de valores nos dois ambientes (`production` e `staging`). Isso dá um padrão concreto e replicável pra propor pro `compras-publicas`, na mesma ordem de grandeza, coerente com o headroom confirmado na spec 009 (CPU 7%, memória 49% em uso hoje no nó).

### Bloco 3 — domínio disponível pra novo subdomínio

Não é um comando de cluster — confirmado diretamente pelo usuário (2026-08-19). Existe um domínio próprio já usado pelos outros projetos, disponível pra criar um subdomínio novo pra `compras-publicas`. Valor literal do domínio **não registrado neste repo público** — mesma razão dos Blocos 1 e 2 (dado operacional, fica no mono-repo de infra privado, junto com o recurso `Ingress` que vai usá-lo, conforme [[010-fronteira-deploy-argocd]]).

**Achado:** convenção de subdomínio confirmada como viável: `compras-publicas.<domínio-existente>`, seguindo o mesmo domínio-base já usado pelos outros dois projetos (que hoje resolvem via host `.internal` no Ingress — ver Bloco 1 — então o mapeamento `compras-publicas.<domínio>` → Ingress real fica a cargo da mesma camada externa que já faz isso pros outros dois, não é decisão nova desta spec).

## Requirements

### Funcionais

1. O manifest `Deployment` de `compras-publicas` DEVE ser implantado nos namespaces `production` e `staging` já existentes no cluster — não DEVE criar um namespace dedicado só pra este projeto, seguindo o padrão real (namespace por ambiente, compartilhado entre projetos), não a hipótese original de namespace dedicado.
2. O manifest do `CronJob` (spec 009) DEVE rodar no mesmo namespace do `Deployment` do ambiente correspondente (`production` ou `staging`) — sem namespace próprio pra ingestão.
3. O `Deployment` DEVE declarar `requests` de `cpu: 100m` / `memory: 128Mi`, seguindo o valor idêntico observado nos dois projetos existentes (Bloco 2).
4. O `Deployment` DEVE declarar `limits` na mesma ordem de grandeza observada (`cpu` entre `250m` e `500m`, `memory: 256Mi`) — valor exato a fechar na implementação, sem exceder o teto que causaria pressão de CPU dado o headroom atual (spec 009: 7% de uso).
5. O `CronJob` DEVE declarar `requests`/`limits` próprios, distintos dos do `Deployment` — o pico de uso do `dbt run` é maior e mais curto que o uso contínuo do `Deployment`, então não DEVE herdar o mesmo perfil de recurso sem ajuste.
6. O host do `Ingress` de `compras-publicas` DEVE seguir a convenção `compras-publicas.<domínio-existente>`, consistente com o domínio-base já usado pelos outros dois projetos do cluster. Valor literal do domínio fica registrado só no mono-repo de infra privado.

### Não-funcionais

1. Nenhum nome de projeto vizinho, host `.internal`, ou valor literal de domínio DEVE ser registrado neste repo público (`compras-publicas`) — consistente com a remediação das specs 002/003 e com o CLAUDE.md ("Nunca detalhe operacional físico aqui").
2. Os valores de `requests`/`limits` propostos DEVEM permanecer dentro do headroom confirmado na spec 009 (CPU 7%, memória 49% em uso) somados aos dos dois projetos existentes — não é uma verificação nova desta spec, mas os valores não DEVEM ser fechados na implementação sem checar `kubectl top nodes` de novo se o tempo entre a decisão e a implementação for grande.

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| Namespace | `production`/`staging` já existentes (compartilhado, não dedicado) | Padrão real confirmado no Bloco 1 — os dois projetos existentes compartilham namespace por ambiente; a hipótese original de namespace dedicado por projeto não correspondia à prática real do cluster |
| Domínio/host | `compras-publicas.<domínio-existente>` | Mesmo domínio-base dos outros dois projetos (confirmado pelo usuário, Bloco 3); resolução real (proxy/DNS externo → Ingress) segue a mesma camada já usada pelos outros dois, sem mudança de arquitetura de rede |
| `requests`/`limits` do `Deployment` | `requests: cpu 100m / memory 128Mi`; `limits: cpu 250-500m / memory 256Mi` (valor exato a fechar na implementação) | Replica a proporção real observada nos dois projetos existentes (Bloco 2) — não é valor inventado, é o padrão já validado em produção no mesmo cluster |
| `requests`/`limits` do `CronJob` | Perfil próprio, distinto do `Deployment` (a definir na implementação da spec 009) | Job de ingestão tem pico de uso maior e mais curto (download + `dbt run`) que o `Deployment` contínuo — herdar o mesmo perfil de recurso seria ou insuficiente no pico ou desperdício no resto do tempo |

### Componentes afetados

- Manifest `Deployment` de `compras-publicas`: `namespace: production`/`staging`, `requests`/`limits` conforme acima.
- Manifest `CronJob` (spec 009): mesmo namespace do `Deployment` correspondente, `requests`/`limits` próprios.
- Recurso `Ingress` (mono-repo infra, fora deste repo por [[010-fronteira-deploy-argocd]]): host `compras-publicas.<domínio-existente>`.

## Casos de borda

- `CronJob` e `Deployment` competindo por recurso se rodarem ao mesmo tempo (ex.: ingestão rodando durante pico de acesso ao site) — mitigado por `requests`/`limits` declarados separadamente (Kubernetes agenda com base neles), mas não eliminado; se virar problema real, considerar horário de execução do `CronJob` fora do pico de acesso esperado.
- Headroom do cluster mudar entre a decisão desta spec e a implementação (ex.: um terceiro projeto entrar no cluster) — valores de `requests`/`limits` propostos aqui devem ser reconferidos contra `kubectl top nodes` antes de aplicar, não presumidos como ainda válidos indefinidamente.

## Fora do escopo

- Decisão de frontend (framework, lib de gráfico) — eixo próprio, ainda não aberto.
- Mudança de decisões já fechadas nas specs 002-010.

## Referências de código

_A preencher conforme a implementação._

## Ver também

- [[002-estado-atual-infra-k3s]]
- [[009-automacao-da-ingestao]]
- [[010-fronteira-deploy-argocd]]
