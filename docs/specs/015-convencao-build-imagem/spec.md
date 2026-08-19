# 015 — Convenção de build e publicação de imagem

## Tipo

Decisão de arquitetura — adoção de convenção já existente e validada em produção pelos outros dois projetos do cluster.

## Status

Decidida — adoção direta do padrão real, sem investigação adicional necessária (já levantado na sessão que revisou a spec 009).

## Resumo

`compras-publicas-sc` precisa publicar pelo menos uma imagem (a da rotina de ingestão, spec 009) e, no futuro, a do FastAPI (spec 012). Em vez de desenhar um mecanismo novo, esta spec adota o padrão já usado e comprovado pelos dois projetos vizinhos no mesmo cluster.

## Contexto

Achado da investigação de deploy (sessão que revisou a spec 009): os dois projetos existentes têm workflow próprio (`.github/workflows/build-and-push.yml`) no repo do próprio app, publicando no GHCR, com promoção de produção manual via `kustomize`.

## Requirements

### Funcionais

1. O workflow de build DEVE viver no repo do próprio app (`compras-publicas-sc`), não no `infra` — consistente com a fronteira já estabelecida (spec 010: cada repo cuida do que é seu).
2. A imagem DEVE ser publicada no GHCR (`ghcr.io/<repo>`), autenticado via `secrets.GITHUB_TOKEN` do próprio workflow — sem PAT externo.
3. Cada build DEVE gerar duas tags: SHA curto do commit (`${GITHUB_SHA::7}`) e `latest`.
4. QUANDO o projeto tiver múltiplas imagens (ex.: ingestão e FastAPI, futuramente), cada uma DEVE ter seu próprio Dockerfile e job de build separado no mesmo workflow — mesmo padrão do projeto vizinho que builda imagem de serviço principal e imagem de pipeline separadamente.
5. A promoção pra staging PODE ser automática (o job de build já atualiza o overlay de staging via `kustomize edit set image` + commit `[skip ci]`, se este projeto adotar overlays kustomize — a decidir junto com a spec 011 quando o `Deployment` for implementado).
6. A promoção pra produção DEVE ser manual — sem bump automático de imagem em produção via CI, mesmo padrão dos dois projetos vizinhos.

### Não-funcionais

1. O instalador do `kustomize` no workflow DEVE baixar o binário direto do tarball de release (não usar o script `install_kustomize.sh` dinâmico) — achado da investigação: esse script já falhou por instabilidade de rede do runner nos projetos vizinhos.

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| Registry | GHCR | Já em uso pelos dois projetos vizinhos, sem custo adicional, integrado ao GITHUB_TOKEN |
| Tags | SHA curto + `latest` | Rastreabilidade (SHA) e conveniência (latest) — padrão já validado |
| Local do workflow | Repo do app, não infra | Consistente com a fronteira spec 010 |
| Promoção produção | Manual | Mesmo padrão dos vizinhos — evita deploy acidental de produção via commit em staging |

## Casos de borda

- Se o número de imagens deste projeto crescer além de ingestão + FastAPI (ex.: um worker adicional), cada uma segue o mesmo padrão de job separado — não há limite arquitetural conhecido.

## Fora do escopo

- Overlays `kustomize` específicos deste projeto (staging/production) — a detalhar quando o primeiro deploy real (ingestão, spec 009 revisada) for implementado.

## Referências de código

_A preencher conforme a implementação._

## Ver também

- [[009-automacao-da-ingestao]]
- [[010-fronteira-deploy-argocd]]
- [[011-parametros-manifest]]
