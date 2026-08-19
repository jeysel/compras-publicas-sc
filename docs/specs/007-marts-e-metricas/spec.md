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
- `nuprocesso` com placeholder não-numérico (`-`, `.`, `SED`, `S/N`, `00`, etc. — 4.478 de 76.041 linhas, achado no Bloco 1 da Investigação) além do caso vazio já previsto acima — a entidade "Processo" não pode tratar esses valores como processo real nem agrupá-los entre si (senão gera "processos" fantasma juntando contratos não relacionados de UGs diferentes, como aconteceu na checagem ingênua do Bloco 1).
- `nmmodalidade` ausente (5.507 de 76.041 linhas, achado no Bloco 3) — métricas agrupadas por modalidade precisam de categoria explícita "Não informado" ou exclusão deliberada, a decidir nos Requirements.
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