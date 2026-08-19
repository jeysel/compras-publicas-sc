# Spec 013 — Levantamento: pipeline dbt legado vs. spec 007

## Tipo

Investigação (levantamento). Somente leitura — nenhum model dbt foi criado, alterado ou apagado nesta sessão.

## Status

Levantamento concluído. Itens 1 e 2 dos Casos de borda resolvidos nesta mesma sessão (ver specs 007/014). Item 3 permanece aberto, com decisão operacional registrada abaixo (não é decisão de arquitetura fechada, é uma diretriz temporária até o cutover).

## Resumo

Uma sessão pediu para iniciar a implementação dos models dbt do fluxo corrente (specs 002-012, todas fechadas), sob a premissa de "início da implementação de código, depois do planejamento completo". A Etapa 0 (levantamento obrigatório antes de criar qualquer model) encontrou um pipeline dbt **completo, funcional e anterior a todo o ciclo de specs** — não um scaffold vazio. Esse pipeline diverge da spec 007 em pontos estruturais (entidades e marts nomeados de forma diferente, uma métrica ausente, uma feature inteira não coberta por nenhuma spec). Por instrução explícita do prompt e da constitution (nunca ajustar spec retroativamente sem revisão), a sessão parou antes de escrever qualquer model novo.

## Contexto

Cronologia reconstruída via `git log` (datas reais, não presumidas):

- **2026-04-01 a 2026-04-02**: pipeline dbt + Evidence.dev construído e declarado concluído — commits `15037ee` até `4847cef`, mensagens incluindo *"Modelagem, transformação e carga concluídos... Versão beta 0.1"*, *"Projeto concluído, versão pré-produção"*, *"Documentação revisada, projeto finalizado"*. `README.md` (não alterado desde então) descreve isso como projeto de portfólio já publicado via GitHub Pages/GitHub Actions.
- **2026-04-28**: backlog (épicos/features/stories) escrito em `docs/backlog-archived/`, descrevendo uma arquitetura nova (ingestão multi-fonte incluindo Betha Transparência, camada `core` com entidades Órgão/Compra/Contrato, métricas "licitado vs. contratado" e "competitividade"). Este backlog não faz nenhuma referência ao pipeline já existente desde abril — nem para reaproveitá-lo, nem para descartá-lo explicitamente.
- **2026-08-19 (hoje)**: backlog arquivado (`docs/backlog-archived/README.md`) por estar "pré-pivot de ingestão" (a fonte Betha nunca foi implementada; decisão real foi CSV único do portal SC). Stories 07-11 e 15-16 do backlog migraram para a spec 007; stories 12-14 migraram para a spec 008. A spec 007 foi formalizada, recortando a métrica "licitado vs. contratado" (dado não existe) e redesenhando as entidades em cima do que `contratos.csv` de fato permite.
- Em nenhum momento desse processo (backlog → arquivamento → spec 007) o pipeline dbt de abril foi mencionado, auditado ou formalmente descartado. `dbt/models/` não sofreu nenhum commit entre `4847cef` (02/04) e o HEAD atual (`aee683d`) — ou seja, ele está parado, mas ainda é o único código dbt que existe no repo.

## Investigação

### Estrutura real de `dbt/models/` (comando: `find dbt/models -type f`)

```
dbt/models/intermediate/int_contratos_evolucao_anual.sql
dbt/models/intermediate/int_contratos_por_fornecedor.sql
dbt/models/intermediate/int_contratos_por_modalidade.sql
dbt/models/intermediate/int_contratos_por_orgao.sql
dbt/models/intermediate/int_contratos_por_ramo.sql
dbt/models/intermediate/schema/int_contratos.yml
dbt/models/intermediate/schema/int_ramo.yml
dbt/models/marts/dim_datas.sql
dbt/models/marts/dim_fornecedores.sql
dbt/models/marts/dim_modalidades.sql
dbt/models/marts/dim_orgaos.sql
dbt/models/marts/dim_ramos.sql
dbt/models/marts/fct_aditivos.sql
dbt/models/marts/fct_contratos.sql
dbt/models/marts/fct_contratos_ramo.sql
dbt/models/marts/schema/marts_contratos.yml
dbt/models/marts/schema/marts_ramos.yml
dbt/models/sources.yml
dbt/models/staging/schema/stg_contratos.yml
dbt/models/staging/stg_contratos.sql
```

Convenção de camadas (`dbt_project.yml`): `staging` (view) → `intermediate` (view) → `marts` (table). Não existe camada `core` — dimensões e fatos convivem em `marts/`.

### Divergências pontuais vs. spec 007

| Spec 007 (`Requirements`/`Design`) | Estado real em `dbt/models/` |
|---|---|
| `dim_processo`: agrupamento `(cdunidadegestora, nuprocesso)`, excluindo placeholders (`-`, `.`, `0`, `SED`, `S/N`) | **Não existe.** Nenhum model agrupa por processo; a entidade "Processo" não está implementada. |
| `stg_contratos` marca `nuprocesso` placeholder numa coluna auxiliar (sem descartar a linha) | **Não existe.** `stg_contratos.sql` não tem essa lógica — nenhuma coluna equivalente a `fl_processo_placeholder`. |
| `dim_orgao` (chave `cdunidadegestora`, `nmunidadegestora` como atributo descritivo) | Existe como `dim_orgaos.sql`, mesma lógica de chave/atributo (compatível em espírito, nome no plural). |
| `dim_fornecedor` (chave `idcontratado`, `contratado` como atributo descritivo) | Existe como `dim_fornecedores.sql`, mesma lógica (compatível em espírito, nome no plural). |
| `mart_escalada_custo` (`vlatual - vloriginal` por contrato, agregável) | Métrica existe como coluna `vl_variacao`/`perc_variacao`/`tp_variacao` dentro de `fct_contratos.sql` e `fct_aditivos.sql` — não como mart dedicado. |
| `mart_diversidade_vencedores` (fornecedores distintos por `(cdunidadegestora, nuprocesso)`) | **Não existe** — depende de `dim_processo`, que não existe. |
| `mart_contratos_temporal` (série anual/modalidade/órgão com `SUM() OVER`, `LAG()`, média móvel) | Parcialmente coberto por `int_contratos_evolucao_anual.sql` (soma acumulada mensal via `SUM() OVER`), mas sem `LAG()` nem média móvel, e sem recorte por modalidade/órgão na mesma tabela. |
| `mart_concentracao_fornecedor` (gasto por fornecedor, % sobre total do órgão/estado) | Parcialmente coberto por `perc_concentracao` em `dim_fornecedores.sql` — mas essa coluna é "% do maior contrato sobre o total do próprio fornecedor", não "% do fornecedor sobre o total do órgão/estado" como a spec 007 define. Semântica diferente, não é a mesma métrica. |
| `nmmodalidade` nulo → categoria "Não informado" | **Já implementado**, compatível: `int_contratos_por_modalidade.sql` usa `coalesce(nm_modalidade, 'Não informado')`. |

### Feature fora de qualquer spec

`dim_ramos` / `fct_contratos_ramo` / `int_contratos_por_ramo`: classificação de cada contrato em ~18 categorias de "ramo de atividade" via `LIKE` sobre palavras-chave de `ds_objeto` (TI, Combustíveis, Alimentação, Obras, Saúde, etc.). É uma feature inteira, com regra de negócio própria, presente no README (*"Classificação por ramo de atividade (16 categorias)"*, página "Ramos de Atividade" e "Fornecedores por Ramo") e não mencionada em nenhuma spec 002-012 nem no backlog arquivado.

### Stack declarada no README (não confirmado se ainda vigente)

`README.md` descreve Evidence.dev + GitHub Pages + GitHub Actions como camada de apresentação/deploy — potencialmente conflitante com a seção "Status da migração" do `CLAUDE.md` (GitHub Actions como fonte de verdade operacional até a migração k3s estar documentada em spec própria) e com a spec 010 (fronteira Argo CD/k3s), que não menciona Evidence em nenhum momento.

### Adendo (2026-08-19) — `.gitignore` nunca versionado + encoding misto

Achado de higiene de repositório, sem relação com o pipeline dbt — registrado aqui por decisão explícita da sessão, não porque pertença ao tema desta spec.

- `git log --all --oneline -- .gitignore` e `git ls-files -- .gitignore` retornaram vazio: **o `.gitignore` nunca foi commitado neste repositório em nenhum momento do histórico.** O arquivo existia só como untracked em disco, e continha uma linha `.gitignore` que se auto-excluía — o que explica por que `git add .gitignore` falhava silenciosamente em sessão anterior.
- O corpo do arquivo (separadores `# ── ... ──`) é UTF-8 correto (bytes `e2 94 80` = U+2500); a exibição corrompida (`â”€â”€`) era só o console decodificando como cp1252/Latin-1, não um defeito no arquivo.
- A linha `dbt/.user.yml`, adicionada em sessão anterior, estava genuinamente corrompida: bytes `64 00 62 00 74 00 2f 00...` = UTF-16LE (cada caractere seguido de byte nulo), misturado num arquivo que é UTF-8 no resto — provavelmente resultado de `Add-Content`/`Out-File` do PowerShell (que usa UTF-16LE por padrão) anexando a uma edição que era UTF-8.
- Correção aplicada: arquivo reescrito em UTF-8 limpo, sem bytes nulos, com a linha `.gitignore` removida (não deve haver uma entrada se auto-excluindo) e `dbt/.user.yml` reescrita como texto plano. Commitado em `75a5235` como `new file` (78 linhas) — consistente com o achado de que nunca existira no histórico.

## Requirements

Resolvido nas specs [[007-marts-e-metricas]] e [[014-cobertura-dim-ramos]] — esta spec (013) permanece só como levantamento histórico. As decisões de arquitetura vivem lá, não aqui.

## Design

Resolvido nas specs [[007-marts-e-metricas]] e [[014-cobertura-dim-ramos]] — mesmo motivo do Requirements acima. Esta seção fica só com o registro de quais arquivos esta sessão tocou (abaixo); o *porquê* de cada decisão está nas specs que a tomaram.

### Componentes afetados

**Tocados nesta sessão** (implementação das decisões da spec 007, ver lá para a decisão em si):
- `dbt/models/staging/stg_contratos.sql` e `.yml` — coluna `fl_aditivo_inconsistente`.
- `dbt/models/intermediate/int_contratos_por_modalidade.sql` — correção do bug de consolidação (hífen).
- `dbt/models/intermediate/int_concentracao_fornecedor_por_orgao.sql`, `int_concentracao_fornecedor_estado.sql` (novos).
- `dbt/models/marts/mart_concentracao_fornecedor.sql` (novo) + `dbt/models/marts/schema/marts_concentracao.yml` (novo).
- `dbt/models/marts/schema/marts_contratos.yml` — documentação de `perc_concentracao` vs. `mart_concentracao_fornecedor`.
- `dbt/models/marts/schema/marts_ramos.yml` — documentação do limite de `dim_ramos` (spec 014).

**Intocados, pendentes**:
- `README.md` — aguardando o cutover do item 3 dos Casos de borda (decisão operacional, não decidida agora).
- Os demais 4 models de `intermediate/` (`int_contratos_por_orgao`, `int_contratos_por_fornecedor`, `int_contratos_por_ramo`, `int_contratos_evolucao_anual`) e os 8 models de `marts/` que não são os listados acima (`dim_orgaos`, `dim_fornecedores`, `dim_modalidades`, `dim_ramos`, `dim_datas`, `fct_contratos`, `fct_aditivos`, `fct_contratos_ramo`) — não precisaram de mudança para as decisões desta sessão; permanecem como estavam.

## Casos de borda

1. **O que fazer com os 8 models de `marts/` e 5 de `intermediate/` que já existem e rodam?** — **Resolvido.** Nem (a) refatoração completa nem (b) duplicação ao lado: adotada uma via pragmática — a convenção real do projeto (`staging → intermediate → marts`, sem camada `core`) foi reconhecida como a estrutura vigente (spec 007 atualizada); bugs reais encontrados foram corrigidos (consolidação de modalidade); métricas genuinamente ausentes foram implementadas como models novos seguindo essa convenção (`mart_concentracao_fornecedor`); métricas com nome parecido mas semântica diferente foram mantidas em paralelo, documentadas (`perc_concentracao` vs. `mart_concentracao_fornecedor`). Pendências reais que sobraram (`dim_processo`, `mart_diversidade_vencedores`, `mart_escalada_custo` como model dedicado, `mart_contratos_temporal` completo) estão registradas na spec 007, seção Componentes afetados — não são decisão em aberto, são trabalho futuro identificado.
2. **A feature `dim_ramos`/`fct_contratos_ramo` é mantida, descartada ou formalizada em spec própria?** — **Resolvido em [[014-cobertura-dim-ramos]]**: mantida como está (26,68% em "Outros" documentado como limite conhecido, não expandida, não descartada).
3. **A stack Evidence/GitHub Pages/GitHub Actions do README ainda é a intenção do projeto, ou foi substituída pelo eixo frontend da spec 012?** — **Parcialmente resolvido, decisão operacional (não arquitetural) registrada aqui pela primeira vez:** o site Evidence publicado via GitHub Pages continua no ar deliberadamente — é o portfólio público hoje, com link potencialmente já compartilhado (currículo, LinkedIn). Decisão: manter `evidence/`, a branch `gh-pages`, e o fluxo manual de build/publish do README **intocados** até o novo frontend (spec 012: FastAPI + Jinja2 + TS + ECharts) estar pronto e substituindo-o de fato. Isso não é reabertura da spec 012 (que já decidiu a stack nova) — é reconhecimento de que existem dois sites coexistindo por um período de transição, e o antigo não deve ser tocado, quebrado, ou removido até o corte deliberado. O "corte" (retirar Evidence, decidir destino da branch `gh-pages`, atualizar README) fica registrado aqui como **spec futura a abrir no momento do cutover**, não decidido agora.

## Fora do escopo

- Decisão sobre qual via seguir para o item 1 dos Casos de borda — **já resolvida**, ver Casos de borda item 1 e spec 007 atualizada. Não é mais uma pendência em aberto.
- Implementação de `dim_processo`, `mart_diversidade_vencedores`, `mart_escalada_custo` como model dedicado, `mart_contratos_temporal` completo — **continua fora do escopo desta spec 013 especificamente** (013 é levantamento, não implementação); pendência rastreada na spec 007, não aqui. `mart_concentracao_fornecedor`, que também estava nesta lista, já foi implementado — ver Componentes afetados acima.
- Etapas 1-5 do prompt original desta sessão (staging/core/marts/schema/validação) — não executadas dentro do escopo da investigação que gerou esta spec.

## Referências de código

- `dbt/models/staging/stg_contratos.sql`, `dbt/models/staging/schema/stg_contratos.yml`
- `dbt/models/intermediate/int_contratos_por_orgao.sql`, `int_contratos_por_fornecedor.sql`, `int_contratos_por_modalidade.sql`, `int_contratos_por_ramo.sql`, `int_contratos_evolucao_anual.sql`
- `dbt/models/marts/dim_orgaos.sql`, `dim_fornecedores.sql`, `dim_modalidades.sql`, `dim_ramos.sql`, `dim_datas.sql`, `fct_contratos.sql`, `fct_aditivos.sql`, `fct_contratos_ramo.sql`
- `README.md` (arquitetura e stack declaradas)
- `docs/backlog-archived/README.md` (nota de arquivamento, 2026-08-19)

## Ver também

- [[007-marts-e-metricas]]
- [[008-qualidade-e-documentacao]]
- [[010-fronteira-deploy-argocd]]
- [[012-eixo-frontend-biblioteca-grafico]]
