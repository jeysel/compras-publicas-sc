# 007 — Marts e métricas (escopo real: só dados de contratos)

## Tipo

Decisão de arquitetura — substitui a versão anterior (rascunho extraído do backlog), que assumia um dataset de licitações que não existe de forma utilizável.

## Status

Design definido. Requirements (EARS) a formalizar. Implementação completa (specs 013/014): `mart_concentracao_fornecedor`, `fl_aditivo_inconsistente`, a correção de consolidação de modalidade, `int_processos` (equivalente intermediate de "dim_processo"), `mart_diversidade_vencedores`, `mart_escalada_custo` e `mart_contratos_temporal` completo (com `LAG()`, média móvel de 3 anos e recorte por órgão/modalidade) — todos feitos e validados (build + test 100% verde, 128/128 e 104/104 respectivamente).

## Resumo

A versão anterior desta spec (extraída do backlog arquivado) assumia uma entidade "Compra"/licitação com dado próprio de valor licitado, permitindo a métrica "licitado vs. contratado" (Story 10, descrita como "central do projeto" no backlog original). Investigação nesta sessão confirmou que **isso não existe como dataset utilizável**: o Portal de Dados Abertos SC tem um grupo "Licitações e contratos" com 5 conjuntos, mas os três relacionados a licitação (`Licitações - Editais`, `Licitações - Pregão Eletrônico`, `Licitações - DEINFRA`) são apenas links para sistemas de consulta externos (`portaldecompras.sc.gov.br`, `e-lic.sc.gov.br`), sem arquivo baixável, parados desde dezembro de 2019. Scraping desses sistemas está fora de escopo por decisão já tomada (spec 004).

**Decisão desta spec**: escopo recortado para o que é honestamente construível só com `contratos.csv`/`seeds/contratos.csv` (specs 003-006). Isso ainda permite bastante análise útil — só não permite comparar licitado vs. contratado, porque esse dado não existe em lugar acessível.

## Contexto

- Achado desta sessão (busca + fetch em `dados.sc.gov.br/group/licitacoes-e-contratos` e nos 2 datasets de licitação verificados): sem dataset estruturado de licitação estadual, atualizado, cobrindo todos os órgãos.
- Achado da spec 003 (reaproveitado aqui): `nuprocesso` tem menos valores únicos que `nucontrato` na amostra (`contrato-demo.csv`: 1600 únicos de 2368 linhas) — evidência de que múltiplos contratos podem compartilhar o mesmo processo licitatório. Isso é a base real pra uma entidade "Processo", derivada do próprio `contratos.csv`, sem precisar de fonte externa.
- Grão e chave já fechados nas specs 003/005: 1 registro = 1 contrato, chave `(cdunidadegestora, nucontrato)`. Esta spec não redefine isso — as entidades abaixo são construídas em cima desse fato já modelado, não o substituem.

## Investigação

Rodado contra `dbt/seeds/contratos.csv` real (76.041 linhas), não amostra. Os 3 itens abaixo, antes listados como "a confirmar", estão fechados.

### Bloco 1 — `(cdunidadegestora, nuprocesso)` é chave estável pra agrupar contratos do mesmo processo?

**Confirma a hipótese do Design — mesma colisão que já existia para `nucontrato` na spec 003, e a mesma correção resolve.**

```
nuprocesso puro: 42348 únicos de 76041 (33692 duplicados)
(cdunidadegestora, nuprocesso): 44165 combinações únicas de 76041 linhas

Distribuição de contratos por processo (usando a chave composta):
1     35873
2      4101
3      1428
4       769
5       491
6       317
7       223
8       171
9       114
10       89

Maior número de contratos num único processo: 297
```

O `duplicated()` puro em `nuprocesso` mistura dois fenômenos diferentes: (a) processo real com múltiplos contratos vinculados — o comportamento esperado que justifica a entidade "Processo" — e (b) colisão de texto entre processos de unidades gestoras diferentes, que é o risco real que motivou o item. Rodei uma checagem adicional (não estava no bloco original, mas era necessária pra responder à pergunta feita no comentário do script) isolando (b): quantos valores de `nuprocesso` aparecem sob mais de uma `cdunidadegestora` distinta.

Primeira rodada, ingênua, deu um número alarmante (1198 de 42348, 10,5% das linhas) — mas o valor de `nuprocesso` que mais colidia era `' '` (um espaço em branco), não um número de processo real. Refinei o filtro pra excluir placeholders (vazio, sem nenhum dígito, ou só zeros — ex.: `-`, `.`, `0`, `SED`, `S/N`):

```
Placeholders (vazio/sem dígito significativo/só zero): 4478 de 76041

nuprocesso genuínos (com dígito, não-placeholder) usados por >1 UG: 1189 de 42283 únicos
Linhas afetadas: 5711 de 71563 (7.98%)

Amostra de nuprocesso genuíno colidindo entre UGs diferentes:
'0001': 3 UGs distintas -> [160097, 440023, 440023]
'0007/2017': 2 UGs distintas -> [410050, 410039]
'0008/2017': 2 UGs distintas -> [410050, 440023]
'001': 15 UGs distintas -> [160085, 160091, 160097, 410032, 410036, 410040, 410047, 410057, 440023, 440023, 450001, 540096, 540097, 610001, 730001]
'001/2016': 3 UGs distintas -> [230023, 410001, 840001]
```

Mesmo depois de tirar o ruído de placeholder, a colisão genuína é real e não desprezível: ~8% das linhas com `nuprocesso` válido compartilham o número com outra unidade gestora (numeração local reinicia por órgão a cada ano — `001/2016` é um processo diferente em cada UG que o abriu). **Conclusão: `(cdunidadegestora, nuprocesso)` é necessário, `nuprocesso` sozinho não serve — exatamente a mesma lógica já registrada pra `nucontrato` na spec 003.** Também vale registrar como caso de borda: `nuprocesso` tem placeholders não-numéricos (`-`, `.`, `SED`, `S/N`, etc., ~4.478 linhas) além do já conhecido "ausente" — a entidade "Processo" precisa tratar isso, não só o caso vazio.

### Bloco 2 — nome exato da coluna de fornecedor/contratado e identificador estável

```
Colunas candidatas a fornecedor: ['nucontrato', 'idcontratado', 'contratado', 'detipocontrato']

--- idcontratado ---
['27.087.458/0001-86', '18.490.362/0001-73', '16.572.041/0001-92', '13.366.571/0001-96', '13.366.571/0001-96']
Nulos: 0 de 76041
Únicos: 11406

--- contratado ---
['Guillherme Raineri de Souza', 'Atos Construtora Ltda', 'Leiber Silva Antonio', 'RML Administradora de Bens', 'RML Administradora de Bens']
Nulos: 0 de 76041
Únicos: 11317
```

`idcontratado` é o CNPJ/CPF (formato `NN.NNN.NNN/NNNN-NN`), sem nulos, é o identificador estável. `contratado` é o nome, também sem nulos, mas com menos valores únicos que `idcontratado` (11317 vs. 11406) — sinal de que o mesmo CNPJ pode aparecer com grafias de nome levemente diferentes (não investigado a fundo aqui; se a dimensão Fornecedor for chaveada por `idcontratado`, o `contratado` mais recente deve ser o atributo descritivo, mesmo padrão já usado pra `nmunidadegestora` em `cdunidadegestora`). **Fornecedor: chave = `idcontratado`, atributo descritivo = `contratado`.**

### Bloco 3 — existência e valores de `nmmodalidade`

```
--- nmmodalidade ---
Pregão Eletrônico - Lei 10.520                      28225
Pregão Presencial - Lei 10.520                      13025
Pregão Eletrônico Lei 14.133                          7982
Dispensa de Licitação - Lei 8.666                     7050
Dispensa de Licitação por Valor - Lei 8.666           4700
Não Aplicável                                         3330
Licitação Inexigível - Lei 8.666                      2269
Dispensa de Licitação - Lei 14.133                    1181
Licitação Inexigível - Lei 14.133                      773
Concorrência - Lei 8.666                               695
Dispensa de Licitação por Valor - Lei 14.133           675
Convite - Lei 8.666                                    213
Procedimento Licitatório (empresas) - Lei 13.303      125
Tomada de Preços - Lei 8.666                            70
Concorrência - Lei 14.133                               53
Nulos: 5507 de 76041
```

Coluna existe, com valores consistentes (nome da modalidade + lei de referência — útil pra distinguir Lei 8.666 de Lei 14.133 no mesmo agrupamento). 5.507 nulos (7,2% das linhas) — a decidir na formalização dos Requirements se entra como categoria "Não informado" ou é excluído das métricas por modalidade.

**Nota de correção (2026-08-19, sessão specs 013/014):** a tabela acima lista só as 15 maiores categorias, não o total — era uma amostra truncada do script de investigação original, não declarada como tal. Contagem real, confirmada por query direta: **25 categorias brutas não-nulas** em `nmmodalidade` (mais os 5.507 nulos). Após a consolidação por lei que `int_contratos_por_modalidade.sql` já implementa (funde pares Lei 8.666/Lei 14.133 da mesma modalidade): **22 categorias** (mais "Não informado" pros nulos e "Não Aplicável" como categoria própria da fonte — 23 se contadas separado, 22 se "Não informado"/"Não Aplicável" forem tratadas como não-modalidade). Nesta sessão também foi corrigido um bug de consolidação: o `CASE WHEN` buscava o literal `'Pregão Presencial Lei 14.133'` (sem hífen), mas o valor real na fonte é `'Pregão Presencial - Lei 14.133'` (com hífen) — 31 contratos escapavam da fusão por isso; corrigido em `dbt/models/intermediate/int_contratos_por_modalidade.sql`.

## Requirements

_A formalizar em EARS após a Investigação acima. Rascunho funcional, por entidade/métrica:_

### Entidades (dbt core/dimensões e fatos)

- **Órgão** (dimensão): de `(cdunidadegestora, nmunidadegestora)` — `cdunidadegestora` como chave estável (spec 003/006), `nmunidadegestora` como atributo descritivo da carga mais recente (nunca chave — regra já registrada nas specs 003/005/006).
- **Contrato** (fato, já modelado): grão e chave herdados das specs 003/005 — nenhuma mudança aqui, esta spec só consome.
- **Processo** (dimensão/agrupamento derivado, NOVO nesta spec): agrupamento de contratos por `(cdunidadegestora, nuprocesso)` — não é uma entidade com dado próprio, é uma visão agregada sobre `Contrato`. Substitui a "Compra" do backlog original, com escopo menor e honesto (não tem valor licitado, só o que os contratos vinculados a ela somam).
- **Fornecedor** (dimensão): extraída do campo de contratado em `contratos.csv` — nome exato de coluna a confirmar na Investigação.

### Métricas

- **Escalada de custo por aditivo** (substitui a Story 10 "licitado vs. contratado"): `vlatual - vloriginal` (e equivalente em dias: `diasatuais - diasoriginais`) por contrato, agregável por órgão/modalidade/período. Mede o quanto um contrato cresceu do valor original pro atual — proxy honesto de "sobrepreço via aditivo", com o dado que realmente existe (ao contrário de "economia vs. licitado", que exigiria dado inexistente). **Decisão adicional (sessão specs 013/014):** `vl_variacao` (`vl_atual - vl_original`, já materializado em `stg_contratos`) é a métrica oficial. O campo `vl_aditado` da fonte diverge dela em ~24% dos contratos com aditivo (976 de 1951, na medição original sem tolerância — 975/976 com tolerância de R$0,01, ver `stg_contratos.fl_aditivo_inconsistente`), por magnitude grande demais pra ser arredondamento — sinal de qualidade de dado da fonte. `vl_aditado` não foi descartado; virou sinal auxiliar de qualidade via a coluna booleana `fl_aditivo_inconsistente` em `stg_contratos`. **Implementada** como mart dedicada `mart_escalada_custo` (grão de contrato, agregável por órgão/modalidade/período pelo consumidor) — `fl_aditivo_inconsistente` exposta como coluna de contexto, não usada como filtro.
- **Diversidade de vencedores por processo** (substitui a Story 11 "competitividade"): contagem de fornecedores distintos vinculados a contratos do mesmo `(cdunidadegestora, nuprocesso)`. Renomeada deliberadamente — mede quantos fornecedores diferentes **venceram** itens/lotes de um processo, não quantos **participaram/concorreram** (esse dado não existe). Nome antigo ("competitividade") seria enganoso. **Implementada** como `mart_diversidade_vencedores`, sobre `int_processos` (equivalente intermediate da entidade Processo) — grão `(cod_unidade_gestora, nu_processo)`, 43.953 processos únicos após excluir 4.482 linhas de `nu_processo` placeholder (achado reconfirmado nesta sessão sobre os 76.041 registros reais). Validada por recomputação total contra `stg_contratos` (teste `assert_mart_diversidade_vencedores_correto`), não só amostra manual.
- **Séries temporais de valor contratado** (Stories 15/16, adaptadas): evolução do valor contratado (não licitado) por ano/modalidade/órgão, com window functions (`SUM() OVER`, `LAG()` pra variação ano a ano, média móvel) — tecnicamente idêntico ao que o backlog original propunha, só ancorado em `vlatual`/`vloriginal` em vez de um "valor licitado" inexistente. **Completa** como `mart_contratos_temporal`, que estende `int_contratos_evolucao_anual` (reaproveitado, não recriado) com: variação ano a ano via `LAG()` guardado contra buraco de ano (só aceita o valor do ano imediatamente anterior se ele existir de fato — sem isso, `LAG()` pularia silenciosamente pro ano disponível mais próximo em recortes esparsos, achado real validado no órgão 150001/mês 1, anos 2020 e 2022 ausentes), média móvel de 3 anos via janela `RANGE` (não `ROWS`, pelo mesmo motivo de robustez a buracos), e recorte por órgão/modalidade na mesma tabela (dimensão `tp_recorte`: 'Geral'/'Órgão'/'Modalidade').
- **Concentração de gasto por fornecedor** (aprovada nesta sessão — não estava no backlog original): quanto do gasto total de um órgão (ou do estado) se concentra nos top N fornecedores. Totalmente construível só com `contratos.csv`. **Implementada nesta sessão** como `mart_concentracao_fornecedor` (grão `cod_unidade_gestora` + `id_contratado`, com visão por órgão e por estado) — não existia nem parcialmente antes (achado da spec 013). Distinta de `dim_fornecedores.perc_concentracao`, que já existia no pipeline legado mas mede concentração *interna* do fornecedor (maior contrato dele / total dele), não concentração de mercado — as duas são mantidas em paralelo, com a diferença documentada nos respectivos `schema.yml`.

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
| `vl_variacao` vs. `vl_aditado` (achado spec 013/014) | `vl_variacao` é a métrica oficial de escalada de custo; `vl_aditado` mantido, não descartado, sinalizado via `fl_aditivo_inconsistente` | As duas colunas divergem em ~24% dos contratos com aditivo, em magnitude grande demais pra ser arredondamento — não são intercambiáveis, e a fonte (Transparência SC) não permite reconciliar sem mais investigação |
| Camada de implementação | Sem camada `core` — convenção real do projeto (achado spec 013) é `staging → intermediate → marts`, dimensões/fatos convivem em `marts/` | O pipeline dbt já existente (pré-spec, achado da spec 013) usa essa convenção; specs novas seguem o que já está em produção, não recriam uma camada `core` que não existe no projeto |

**Nota de correção (conclusão desta sessão):** a lista fixa de placeholder (`-`, `.`, `0`, `SED`, `S/N`) documentada na Investigação original subestimava casos reais. Reconfirmação direto em `stg_contratos` nesta sessão achou variedade maior (`xxx`, `CT`, `ESEJ`, entre outros). Regra final, implementada em `int_processos.sql`: qualquer `nu_processo` sem nenhum dígito, ou cujos dígitos (após remover caracteres não-numéricos) resultem todos zero — regra computada por regex, não lista fixa. Ver comentário completo no `.sql` para o raciocínio detalhado.

### Componentes afetados

Convenção real do projeto (achado spec 013): `staging → intermediate → marts`, sem camada `core` separada.

- **Implementado (specs 013/014)**: `int_concentracao_fornecedor_por_orgao`, `int_concentracao_fornecedor_estado` (intermediate) e `mart_concentracao_fornecedor` (marts); `stg_contratos.fl_aditivo_inconsistente` (staging).
- **Implementado (conclusão desta sessão)**:
  - `int_processos.sql` (intermediate) — equivalente intermediate de "dim_processo", grão `(cod_unidade_gestora, nu_processo)`, exclui placeholder de `nu_processo`.
  - `mart_diversidade_vencedores.sql` (marts) — sobre `int_processos`.
  - `mart_escalada_custo.sql` (marts) — mart dedicada, grão de contrato.
  - `int_contratos_evolucao_por_orgao.sql`, `int_contratos_evolucao_por_modalidade.sql` (intermediate, novos cortes) e `mart_contratos_temporal.sql` (marts) — estende `int_contratos_evolucao_anual.sql` (mantido como está) com `LAG()` ano-a-ano guardado contra buraco, média móvel de 3 anos via `RANGE`, e recorte por órgão/modalidade unificado via dimensão `tp_recorte`.
  - Testes de corretude (`dbt/tests/assert_*.sql`, recomputação total contra `stg_contratos`, não amostra): `assert_int_processos_grao_bate`, `assert_mart_diversidade_vencedores_correto`, `assert_mart_escalada_custo_variacao_correta`, `assert_mart_contratos_temporal_recorte_bate`, `assert_mart_contratos_temporal_lag_sem_buraco`.
  - `dbt build` e `dbt test` completos: 128/128 e 104/104, 0 erro, 0 skip.
- `dim_orgao`/`dim_fornecedor` da Investigação já existem no pipeline legado como `dim_orgaos`/`dim_fornecedores` (achado spec 013) — compatíveis em espírito, nome no plural; não foram renomeados nesta sessão.

## Casos de borda

- Contrato sem `nuprocesso` preenchido (dispensa/inexigibilidade pode não ter processo licitatório formal) — a entidade "Processo" precisa lidar com isso sem quebrar (grupo de tamanho 1, ou uma categoria "sem processo formal").
- `nuprocesso` com placeholder não-numérico (`-`, `.`, `SED`, `S/N`, `00`, etc. — 4.478 de 76.041 linhas, achado no Bloco 1 da Investigação) além do caso vazio já previsto acima — a entidade "Processo" não pode tratar esses valores como processo real nem agrupá-los entre si (senão gera "processos" fantasma juntando contratos não relacionados de UGs diferentes, como aconteceu na checagem ingênua do Bloco 1).
- `nmmodalidade` ausente (5.507 de 76.041 linhas, achado no Bloco 3) — métricas agrupadas por modalidade precisam de categoria explícita "Não informado" ou exclusão deliberada, a decidir nos Requirements.
- `vloriginal` ausente ou zero em algum contrato — a métrica de escalada de custo precisa de regra explícita pra esse caso (excluir do cálculo? tratar como 0% de escalada?), a decidir na formalização dos Requirements.

## Fora do escopo

- Métrica "licitado vs. contratado" em qualquer forma — dado não existe em fonte utilizável; não reabrir sem uma fonte de dado nova e confirmada.
- Scraping de `portaldecompras.sc.gov.br` ou `e-lic.sc.gov.br` — decisão já tomada (spec 004), reforçada aqui.
- Normalização de data/valor monetário (feature 2.1, stories 05-06 do backlog original) — permanece fora, como já registrado na versão anterior desta spec.

## Referências de código

- `dbt/models/staging/stg_contratos.sql` — coluna `fl_aditivo_inconsistente`.
- `dbt/models/intermediate/int_contratos_por_modalidade.sql` — bug de consolidação de "Pregão Presencial - Lei 14.133" corrigido.
- `dbt/models/intermediate/int_concentracao_fornecedor_por_orgao.sql`, `int_concentracao_fornecedor_estado.sql`.
- `dbt/models/marts/mart_concentracao_fornecedor.sql`.
- `dbt/models/intermediate/int_processos.sql` — entidade Processo, exclui `nu_processo` placeholder.
- `dbt/models/marts/mart_diversidade_vencedores.sql`.
- `dbt/models/marts/mart_escalada_custo.sql`.
- `dbt/models/intermediate/int_contratos_evolucao_por_orgao.sql`, `int_contratos_evolucao_por_modalidade.sql`, `dbt/models/marts/mart_contratos_temporal.sql`.
- `dbt/tests/assert_int_processos_grao_bate.sql`, `assert_mart_diversidade_vencedores_correto.sql`, `assert_mart_escalada_custo_variacao_correta.sql`, `assert_mart_contratos_temporal_recorte_bate.sql`, `assert_mart_contratos_temporal_lag_sem_buraco.sql`.

## Ver também

- [[003-storage-e-chave-unica]]
- [[004-origem-dados-api-vs-arquivo]]
- [[005-grao-do-dado-contrato-vs-aditivo]]
- [[006-backfill-historico]]
- [[008-qualidade-e-documentacao]]
- [[013-levantamento-dbt-legado]]
- [[014-cobertura-dim-ramos]] — feature `dim_ramos` fora do escopo original desta spec, mas relevante o suficiente pra linkar (decisão de manter, registrada lá)