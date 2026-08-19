# 007 — Marts e métricas (escopo real: só dados de contratos)

## Tipo

Decisão de arquitetura — substitui a versão anterior (rascunho extraído do backlog), que assumia um dataset de licitações que não existe de forma utilizável.

## Status

Design definido. Requirements (EARS) a formalizar.

## Resumo

A versão anterior desta spec (extraída do backlog arquivado) assumia uma entidade "Compra"/licitação com dado próprio de valor licitado, permitindo a métrica "licitado vs. contratado" (Story 10, descrita como "central do projeto" no backlog original). Investigação nesta sessão confirmou que **isso não existe como dataset utilizável**: o Portal de Dados Abertos SC tem um grupo "Licitações e contratos" com 5 conjuntos, mas os três relacionados a licitação (`Licitações - Editais`, `Licitações - Pregão Eletrônico`, `Licitações - DEINFRA`) são apenas links para sistemas de consulta externos (`portaldecompras.sc.gov.br`, `e-lic.sc.gov.br`), sem arquivo baixável, parados desde dezembro de 2019. Scraping desses sistemas está fora de escopo por decisão já tomada (spec 004).

**Decisão desta spec**: escopo recortado para o que é honestamente construível só com `contratos.csv`/`seeds/contratos.csv` (specs 003-006). Isso ainda permite bastante análise útil — só não permite comparar licitado vs. contratado, porque esse dado não existe em lugar acessível.

## Contexto

- Achado desta sessão (busca + fetch em `dados.sc.gov.br/group/licitacoes-e-contratos` e nos 2 datasets de licitação verificados): sem dataset estruturado de licitação estadual, atualizado, cobrindo todos os órgãos.
- Achado da spec 003 (reaproveitado aqui): `nuprocesso` tem menos valores únicos que `nucontrato` na amostra (`contrato-demo.csv`: 1600 únicos de 2368 linhas) — evidência de que múltiplos contratos podem compartilhar o mesmo processo licitatório. Isso é a base real pra uma entidade "Processo", derivada do próprio `contratos.csv`, sem precisar de fonte externa.
- Grão e chave já fechados nas specs 003/005: 1 registro = 1 contrato, chave `(cdunidadegestora, nucontrato)`. Esta spec não redefine isso — as entidades abaixo são construídas em cima desse fato já modelado, não o substituem.

## Investigação

_Itens a confirmar antes de implementar (não bloqueiam o Design, mas bloqueiam Requirements definitivos):_

- Confirmar se `(cdunidadegestora, nuprocesso)` é chave estável pra agrupar contratos do mesmo processo — mesmo cuidado que levou à composição `(cdunidadegestora, nucontrato)` na spec 003 (não presumir que `nuprocesso` sozinho não colide entre unidades gestoras diferentes, sem testar).
- Confirmar o nome exato da coluna de fornecedor/contratado em `contratos.csv` (`contratado`? `idcontratado`? — mencionado informalmente em investigações anteriores, nunca formalmente listado nesta spec) e se existe um identificador estável (CNPJ) além do nome.
- Confirmar existência e valores de `nmmodalidade` (modalidade de licitação) em `contratos.csv` — necessário pras métricas agrupadas por modalidade.

## Requirements

_A formalizar em EARS após a Investigação acima. Rascunho funcional, por entidade/métrica:_

### Entidades (dbt core/dimensões e fatos)

- **Órgão** (dimensão): de `(cdunidadegestora, nmunidadegestora)` — `cdunidadegestora` como chave estável (spec 003/006), `nmunidadegestora` como atributo descritivo da carga mais recente (nunca chave — regra já registrada nas specs 003/005/006).
- **Contrato** (fato, já modelado): grão e chave herdados das specs 003/005 — nenhuma mudança aqui, esta spec só consome.
- **Processo** (dimensão/agrupamento derivado, NOVO nesta spec): agrupamento de contratos por `(cdunidadegestora, nuprocesso)` — não é uma entidade com dado próprio, é uma visão agregada sobre `Contrato`. Substitui a "Compra" do backlog original, com escopo menor e honesto (não tem valor licitado, só o que os contratos vinculados a ela somam).
- **Fornecedor** (dimensão): extraída do campo de contratado em `contratos.csv` — nome exato de coluna a confirmar na Investigação.

### Métricas

- **Escalada de custo por aditivo** (substitui a Story 10 "licitado vs. contratado"): `vlatual - vloriginal` (e equivalente em dias: `diasatuais - diasoriginais`) por contrato, agregável por órgão/modalidade/período. Mede o quanto um contrato cresceu do valor original pro atual — proxy honesto de "sobrepreço via aditivo", com o dado que realmente existe (ao contrário de "economia vs. licitado", que exigiria dado inexistente).
- **Diversidade de vencedores por processo** (substitui a Story 11 "competitividade"): contagem de fornecedores distintos vinculados a contratos do mesmo `(cdunidadegestora, nuprocesso)`. Renomeada deliberadamente — mede quantos fornecedores diferentes **venceram** itens/lotes de um processo, não quantos **participaram/concorreram** (esse dado não existe). Nome antigo ("competitividade") seria enganoso.
- **Séries temporais de valor contratado** (Stories 15/16, adaptadas): evolução do valor contratado (não licitado) por ano/modalidade/órgão, com window functions (`SUM() OVER`, `LAG()` pra variação ano a ano, média móvel) — tecnicamente idêntico ao que o backlog original propunha, só ancorado em `vlatual`/`vloriginal` em vez de um "valor licitado" inexistente.
- **Concentração de gasto por fornecedor** (aprovada nesta sessão — não estava no backlog original): quanto do gasto total de um órgão (ou do estado) se concentra nos top N fornecedores. Totalmente construível só com `contratos.csv`.

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| Fonte de dado | Só `contratos.csv`/`seeds/contratos.csv` (specs 003-006) | Nenhum dataset de licitação estruturado existe de forma utilizável — confirmado nesta sessão, não presumido |
| Entidade "Compra"/licitação | Descartada como entidade com dado próprio; substituída por "Processo" (agrupamento derivado de `Contrato` por `nuprocesso`) | Sem fonte de valor licitado, não há como ter uma entidade "Compra" com atributos próprios além do que os contratos vinculados já têm |
| Métrica "licitado vs. contratado" | Descartada | Dado de valor licitado não existe em fonte utilizável (achado desta sessão) |
| Métrica substituta de sobrepreço | Escalada de custo via aditivo (`vlatual - vloriginal`) | Mede o mesmo fenômeno de interesse (ineficiência/sobrepreço) com dado real disponível |
| Métrica "competitividade" | Renomeada para "diversidade de vencedores por processo", com semântica ajustada | Mede vencedores, não participantes — nome precisa refletir a limitação real do dado |
| Séries temporais | Mantidas, ancoradas em valor contratado | Window functions continuam plenamente aplicáveis; só a base de valor muda |
| Concentração de gasto por fornecedor | Aprovada como métrica nova (não estava no backlog original) | Construível só com dado já disponível; complementa a leitura de competitividade/diversidade de vencedores com outro ângulo (concentração de mercado) |

### Componentes afetados

- Models dbt de camada `core`: `dim_orgao`, `dim_processo` (ou `int_processo` se ficar como intermediate), `dim_fornecedor`.
- Models dbt de camada `marts`: `mart_escalada_custo`, `mart_diversidade_vencedores`, `mart_contratos_temporal`, `mart_concentracao_fornecedor`.

## Casos de borda

- Contrato sem `nuprocesso` preenchido (dispensa/inexigibilidade pode não ter processo licitatório formal) — a entidade "Processo" precisa lidar com isso sem quebrar (grupo de tamanho 1, ou uma categoria "sem processo formal").
- `vloriginal` ausente ou zero em algum contrato — a métrica de escalada de custo precisa de regra explícita pra esse caso (excluir do cálculo? tratar como 0% de escalada?), a decidir na formalização dos Requirements.

## Fora do escopo

- Métrica "licitado vs. contratado" em qualquer forma — dado não existe em fonte utilizável; não reabrir sem uma fonte de dado nova e confirmada.
- Scraping de `portaldecompras.sc.gov.br` ou `e-lic.sc.gov.br` — decisão já tomada (spec 004), reforçada aqui.
- Normalização de data/valor monetário (feature 2.1, stories 05-06 do backlog original) — permanece fora, como já registrado na versão anterior desta spec.

## Referências de código

_A preencher conforme a implementação._

## Ver também

- [[003-storage-e-chave-unica]]
- [[004-origem-dados-api-vs-arquivo]]
- [[005-grao-do-dado-contrato-vs-aditivo]]
- [[006-backfill-historico]]
- [[008-qualidade-e-documentacao]]