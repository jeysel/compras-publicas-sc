# 010 — Fronteira de deploy: manifests do app vs. mono-repo de infra (Argo CD)

## Tipo

Decisão de arquitetura — formalização de decisão já tomada e aplicada informalmente (no CLAUDE.md), nunca registrada como spec.

## Status

Decidida. Sem investigação nova nesta spec — a investigação de origem já foi feita na spec 002 (Bloco 2, levantamento do mono-repo de infra k3s). Esta spec só formaliza o que já foi confirmado e está em uso, pra deixar de ser conhecimento implícito só no CLAUDE.md.

## Resumo

O padrão real observado nos dois projetos já em produção no cluster (spec 002) é: `Deployment`/`Service` no repo de cada app, `Application` do Argo CD + `Ingress`/`NetworkPolicy` no mono-repo de infra privado, deploy via GitOps (Argo CD observando o repo do app). Esta spec fixa essa fronteira formalmente para `compras-publicas`, corrigindo a suposição inicial (registrada informalmente antes da spec 002) de que tudo ficaria centralizado no mono-repo de infra.

## Contexto

- Achado da spec 002: os dois projetos existentes (`jeysel-auth`, `weather-analytics`) seguem esse padrão híbrido — não é decisão nova, é confirmação de precedente real.
- A decisão já foi aplicada informalmente no `CLAUDE.md` do repo `compras-publicas` (seção "Fronteira de infra"), como orientação de trabalho — mas nunca virou spec, o que violava a própria disciplina de "decisão de arquitetura = spec antes de virar prática".
- Esta spec fecha essa lacuna retroativamente.

## Requirements

### Funcionais

1. O sistema DEVE manter os manifests `Deployment` e `Service` de `compras-publicas` no repositório `compras-publicas` (público), versionados junto com o código da aplicação.
2. O sistema DEVE manter o recurso `Application` do Argo CD, `Ingress` e `NetworkPolicy` referentes a `compras-publicas` no mono-repo de infra privado, não no repo público.
3. O deploy DEVE ocorrer via Argo CD observando o repo `compras-publicas` (GitOps) — não via `kubectl apply` manual nem push de imagem acionando deploy diretamente.
4. QUANDO uma tarefa envolver `kubectl` direto no cluster fora de leitura/debug, ou qualquer ação que não passe pelo fluxo do Argo CD, O sistema (ou quem estiver operando) DEVE tratar isso como exceção a justificar, não como caminho padrão.

### Não-funcionais

1. Esta spec DEVE ser referenciada (`[[010-fronteira-deploy-argocd]]`) pelo CLAUDE.md do repo `compras-publicas`, substituindo a seção "Fronteira de infra" atual por uma referência a esta spec em vez de regra solta sem origem documentada.
2. Nenhum dado físico de infra (IP, identity, nomes de projetos vizinhos) DEVE ser registrado nesta spec, consistente com a regra adicionada em `docs/memory/constitution.md` após a remediação de segurança (specs 002/003).

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| Local do `Deployment`/`Service` | Repo `compras-publicas` | Padrão real observado em `jeysel-auth`/`weather-analytics` (spec 002); mantém o ciclo de vida do workload junto com o código que ele roda |
| Local da `Application`/`Ingress`/`NetworkPolicy` | Mono-repo de infra privado | Mesma razão; além disso, evita expor decisão de borda de rede (domínio, política de rede) num repo público de portfólio |
| Mecanismo de deploy | Argo CD (GitOps) | Já em uso pelos dois projetos existentes; sem motivo para introduzir um segundo mecanismo só para este projeto |

### Componentes afetados

- `CLAUDE.md` do repo `compras-publicas`: seção "Fronteira de infra" passa a referenciar esta spec.
- Nenhuma mudança de infra nova — esta spec documenta prática já em vigor desde que o CLAUDE.md foi escrito.

## Casos de borda

- Se o padrão dos outros dois projetos mudar no futuro (ex.: centralizarem manifests), esta spec precisa ser revisada explicitamente — não seguir mudança de padrão alheio silenciosamente.

## Fora do escopo

- Valores concretos do manifest (namespace, domínio/host do Ingress, requests/limits de recurso) — ainda não decididos, ficam para uma spec de implementação própria (ou para quando a spec 009 — CronJob — e o eixo frontend definirem o que precisa ser exposto).
- Mudança no padrão de segredos (já tratado nas specs 002/003, mono-repo infra).

## Referências de código

_A preencher conforme a implementação._

## Ver também

- [[002-estado-atual-infra-k3s]]
- [[009-automacao-da-ingestao]]
