# Backlog arquivado (2026-08-19)

Este backlog (épicos, features, stories escritos em 2026-04-28) foi arquivado porque descreve um **desenho pré-pivot** de ingestão multi-fonte via scraping/API — incluindo uma fonte **Betha Transparência** que nunca chegou a ser implementada — superado pelas decisões reais registradas nas specs 004-006 (`docs/specs/`): ingestão via arquivo CSV único, só do portal do Estado de SC (`dados.sc.gov.br`), sem Betha.

Confirmado antes do arquivamento que nenhum requisito de negócio (normalização de data/valor, regra de entidade) estava misturado no desenho de ingestão descartado — ver investigação na conversa que resultou neste arquivamento.

**O que foi migrado para specs ativas (rascunho):**
- Entidades (Órgão, Compra, Contrato) e métricas (licitado vs. contratado, competitividade, séries temporais) — stories 07-11 e 15-16 → [`docs/specs/007-marts-e-metricas/spec.md`](../specs/007-marts-e-metricas/spec.md).
- Dicionário de dados e testes de ingestão/transformação — stories 12-14 → [`docs/specs/008-qualidade-e-documentacao/spec.md`](../specs/008-qualidade-e-documentacao/spec.md).

**O que permanece só aqui, arquivado, não migrado:**
- Desenho de ingestão descartado (`base_source.py`, extração via scraping/API, Betha Transparência) — features 1.1-1.3, stories 01-04.
- Normalização de datas/valores monetários — feature 2.1, stories 05-06 (decisão consciente: fora do escopo desta rodada de migração).

Histórico completo recuperável via `git log --follow` sobre estes arquivos (a pasta já existia em `docs/backlog/` antes de ser movida para cá).
