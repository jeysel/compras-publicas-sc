# Spec 018 — Levantamento: bloqueios de `dbt seed` contra o CSV real do portal

## Tipo

Investigação (levantamento). Requirements e Design deliberadamente em aberto — nenhuma decisão de arquitetura tomada aqui, nenhum código alterado (`ingest.sh`, `stg_contratos.sql`, `dbt/seeds/schema/contratos.yml` intocados). O ambiente de dev (`dbt/seeds/contratos.csv`, tabela `raw.contratos`) foi restaurado ao estado original ao final da sessão — ver item 6 da Investigação.

## Status

Levantamento concluído. Aprofunda os dois "Casos de borda não resolvidos" registrados em [[017-validacao-schema-tolerante]] (itens 2 e 3) e encontra um **terceiro bloqueio**, não documentado antes, mais sério que os dois originais: a recriação de schema via `--full-refresh` não tem custo relevante de tempo, mas tem risco real de corromper silenciosamente os tipos de coluna da tabela `raw.contratos`.

## Resumo

Reproduzido contra Postgres real (mesmo container `compras_postgres`), com o CSV real do portal baixado nesta sessão (mesmo ETag `"1757412122.95-122184246"` da spec 016/017 — arquivo não mudou).

**Parte A — `dbt seed` / `--full-refresh`:** a sequência de erros documentada na spec 017 (primeiro "column does not exist", depois "Row 2687 has 63 values" só com `--full-refresh`) **não se repetiu** nesta sessão — rodando contra o arquivo real completo, o erro de compilação (linhas malformadas, Parte B) bloqueia **imediatamente, com ou sem `--full-refresh`**, antes de qualquer erro de schema conseguir se manifestar. Isolando esse bloqueio (rodando contra uma cópia sem as linhas malformadas), o custo em tempo do `--full-refresh` é **desprezível** (228,66s vs. 228,36s do seed incremental — diferença de 0,3s, dentro do ruído de medição, para ~95 mil linhas). A pergunta de custo (formulada no prompt original) tem resposta clara: **não é caro**. Mas apareceu uma pergunta mais séria que o prompt não antecipava — ver "Achado adicional" no item 4.

**Parte B — as 747 linhas malformadas:** confirmadas as 747 linhas (0,78% de 96.239 linhas lógicas), mas elas não são 747 incidentes independentes — são **69 incidentes reais** de "estilhaçamento" de linha, cada um gerando entre 1 e 54 fragmentos consecutivos até o parser CSV resincronizar. Causa identificada em amostra manual: o sistema de origem (SICOP/SIGEF) escapa aspas internas em campos de texto livre (`RESUMO`, `OBJETO`) com `\"` (estilo C/JSON) em vez do padrão RFC4180 (`""`) — um parser CSV padrão (Python `csv.reader`, e presumivelmente o parser do dbt/agate/Postgres `COPY`) não reconhece `\"` como aspas escapadas, fecha o campo ali, e todo o resto da linha (e das linhas físicas seguintes, se o campo tinha quebra de linha embutida) se desalinha em fragmentos. Pelo menos dois dos incidentes correspondem a contratos de valor alto (R$ 14–19 milhões e R$ 2,1–2,2 milhões) — não é um padrão restrito a registros de baixo valor.

## Investigação

### 1. Download do CSV real (mesmo arquivo da spec 016/017)

```
$ curl -sSI ".../download/contratos.csv" | grep -i etag
ETag: "1757412122.95-122184246"

$ wc -l contratos_portal_full.csv
141666

$ head -1 contratos_portal_full.csv | tr ';' '\n' | wc -l
59
```

Mesmo ETag da spec 017 — arquivo idêntico, não mudou desde então.

### 2. Parte A.1 — reproduzir o erro sem `--full-refresh`

CSV real completo (59 colunas) copiado para `dbt/seeds/contratos.csv`, tabela `raw.contratos` já existente com schema antigo (51 colunas, confirmado via `\d raw.contratos` antes do teste). Rodando `docker compose run --rm dbt seed --select contratos` (sem `--full-refresh`):

```
15:54:32  1 of 1 ERROR loading seed file raw.contratos ................................... [ERROR in 3.39s]
15:54:32
15:54:32    Compilation Error in seed contratos (seeds/contratos.csv)
  Row 2687 has 63 values, but Table only has 59 columns.

  > in macro materialization_seed_default (macros/materializations/seeds/seed.sql)
  > called by seed contratos (seeds/contratos.csv)
```

**Divergência em relação à spec 017:** lá, sem `--full-refresh`, o primeiro erro relatado foi `Database Error ... column "origem" does not exist` (achado 7.1) — o erro de linha malformada só apareceu depois, com `--full-refresh` (achado 7.2). Aqui, contra o mesmo arquivo, o erro de compilação (linha malformada) bloqueia **imediatamente**, antes de qualquer tentativa de insert, com ou sem `--full-refresh` (confirmado repetindo o comando com `--full-refresh` — erro idêntico, `real 0m9.933s`). Não foi investigado a fundo por que a sessão anterior viu a ordem inversa (hipótese não confirmada: `dbt seed` insere em lotes, e a linha problemática pode não ter estado no primeiro lote processado naquela execução) — registrado aqui como discrepância, não resolvida.

**Conclusão prática:** hoje, a Parte B (linhas malformadas) é o bloqueio que efetivamente impede qualquer teste isolado da Parte A contra o arquivo real — o erro de compilação sempre chega primeiro. Para medir a Parte A de forma isolada, foi necessário remover as 747 linhas malformadas primeiro (ver item 5).

### 3. Parte B.1 — isolar as linhas problemáticas

```python
import csv
with open(path, encoding='utf-8', errors='replace', newline='') as f:
    reader = csv.reader(f, delimiter=';')
    header = next(reader)
    esperado = len(header)  # 59
    problemas = [(i, len(row), row) for i, row in enumerate(reader, start=2) if len(row) != esperado]
```

```
Total de linhas de dado (logicas, csv.reader): 96239
Total de linhas com contagem de campo divergente: 747
Esperado: 59 campos
```

Mesmos números da spec 017 (747 de 96.239 = 0,78%).

### 4. Parte B.2 — distribuição da divergência

```
0 campos: 92 linhas       10 campos: 46 linhas      46 campos: 42 linhas
1 campos: 396 linhas      11 campos: 4 linhas       47 campos: 4 linhas
2 campos: 73 linhas       14 campos: 2 linhas       48 campos: 1 linhas
3 campos: 2 linhas        15 campos: 3 linhas       51 campos: 1 linhas
4 campos: 5 linhas        24 campos: 1 linhas       55 campos: 2 linhas
5 campos: 50 linhas       30 campos: 1 linhas       58 campos: 1 linhas
6 campos: 3 linhas                                  61 campos: 4 linhas
7 campos: 1 linhas                                  63 campos: 1 linhas
8 campos: 1 linhas                                  65 campos: 3 linhas
                                                     66 campos: 1 linhas
                                                     81 campos: 1 linhas
                                                     93 campos: 5 linhas
                                                     97 campos: 1 linhas
```

Padrão **bimodal**, não um único "sempre 1 campo a mais" — 563 de 747 linhas (75%) têm **poucos** campos (0–8, fragmentos "cauda" de um registro estilhaçado) e o restante tem **muitos** campos (46+, fragmentos "cabeça" que engoliram parte das linhas seguintes). Isso não bate com a hipótese simples de "aspas malformadas juntando dois campos" (que produziria só contagens levemente acima do esperado) — é consistente com um registro lógico inteiro sendo **estilhaçado em múltiplas linhas de saída**, não só um campo mal-juntado.

Agrupando linhas problemáticas consecutivas (mesmo incidente de estilhaçamento):

```python
# 747 linhas -> 69 clusters de linhas consecutivas
```

```
Total de linhas problematicas: 747
Total de clusters (incidentes de shredding, linhas consecutivas agrupadas): 69

Distribuicao de tamanho de cluster:
  1 linha(s) por incidente: 16 incidentes     13 linha(s): 2 incidentes
  2 linha(s) por incidente: 2 incidentes      15 linha(s): 1 incidente
  3 linha(s) por incidente: 19 incidentes     16 linha(s): 1 incidente
  5 linha(s) por incidente: 5 incidentes      17 linha(s): 4 incidentes
  7 linha(s) por incidente: 4 incidentes      19 linha(s): 1 incidente
  9 linha(s) por incidente: 2 incidentes      23 linha(s): 1 incidente
  11 linha(s) por incidente: 2 incidentes     35/41/43/45 linha(s): 1 incidente cada
                                               47 linha(s): 3 incidentes
                                               51/54 linha(s): 1 incidente cada
```

**Achado central da Parte B: são 69 registros originais malformados, não 747.** Cada um gera uma cascata de 1 a 54 linhas de saída até o parser CSV resincronizar com o próximo `;` "de sorte". Isso muda a magnitude real do problema para qualquer spec de Design subsequente — 69 registros afetados em ~96 mil (0,07% dos registros, não 0,78% das linhas de saída).

### 5. Parte B.3 — inspeção manual de casos (campo a campo)

Duas linhas com contagem **acima** do esperado (fragmento "cabeça"), inspecionadas por completo:

**Linha 2689 (63 campos, esperado 59)** — contrato SICOP, unidade `530001` (Secretaria de Estado da Infraestrutura), `CT-00006/2013/SIE`. O campo `OBJETO` contém:

```
...pelo Banco Nacional do Desenvolvimento Econômico e Social (BNDES): \Programa Caminhos do Desenvolvimento\", subprograma Novos Caminhos Catarinenses...
```

O padrão `\Programa Caminhos do Desenvolvimento\"` usa barra invertida (`\`) antes das aspas internas (`"Programa Caminhos do Desenvolvimento"`) em vez de aspas duplicadas (`""Programa Caminhos do Desenvolvimento""`, o escape correto em RFC4180). Um parser CSV padrão não reconhece `\"` como escape — interpreta o `"` como fechamento do campo, e o restante do texto (que ainda tem `;` internos de pontuação de frase) vira campos extras. `VLORIGINAL`/`VLATUAL` ainda são identificáveis no fragmento: `14444280.14` e `19774876.37` — **contrato de R$ 14,4 a 19,8 milhões**.

**Linha 4088 (61 campos, esperado 59)** — mesmo padrão, unidade `530025` (Departamento Estadual de Infraestrutura), `PJ-00152/2016`, campo `RESUMO` com `KM 132+300 ... 49° 12'40,66\" W` — mesma barra invertida antes de aspas internas (aqui, aspas de coordenada geográfica em segundos). `VLORIGINAL`/`VLATUAL`: `2141000` e `2181357.78` — **contrato de R$ 2,1 milhões**.

**Cluster 10163–10167 (5 fragmentos)** — caso mais severo: um único registro de licitação de produtos de limpeza (unidade `160084`, Fundo de Melhoria da Polícia Civil) tem o campo `OBJETO` com **múltiplos itens de lista** (`A)Pano de copa...`, `B)\Flanela peluciada...`, `C)Saco de tecido...`), cada um com sua própria aspas internas mal-escapadas (`\"`) e, adicionalmente, uma quebra de linha física (`\r\n`) real embutida no texto entre os itens. A combinação de aspas mal-fechadas + quebra de linha real faz o parser perder completamente a sincronia por 5 linhas de saída antes de encontrar um `;` que o realinhe. Mesmo padrão se repete no cluster 10182–10186 (registro irmão, mesmo órgão, mesmo tipo de licitação, provavelmente gerado pelo mesmo template de exportação).

**Conclusão da inspeção manual:** todos os casos inspecionados têm a mesma causa raiz aparente — **aspas internas escapadas com `\"` em vez de `""`** em campos de texto livre (`RESUMO`, `OBJETO`), presumivelmente porque o sistema de origem (SICOP/SIGEF) gera o CSV com uma rotina de escape estilo C/JSON em vez de RFC4180. Causa **não confirmada exaustivamente**: o arquivo inteiro tem 3.132 ocorrências da sequência `\"`, mas só 69 delas (uma fração) efetivamente produzem estilhaçamento — o que sugere que só uma combinação específica (ex.: `\"` perto do fim de um campo, ou combinado com quebra de linha real embutida) causa o problema; a maioria das ocorrências de `\"` deve estar em posições que não confundem o parser. Não investigado a fundo qual é exatamente essa combinação.

### 6. Parte B.4 — concentração por órgão

```python
orgaos_problema = Counter(row[1] for _, _, row in problemas)  # indice 1 = CDUNIDADEGESTORA (ORIGEM eh indice 0)
```

```
None: 488    (sem valor identificavel no fragmento — maioria dos fragmentos "cauda")
'': 40
'440022': 32
'   ': 24
'160091': 14
'160084': 5
'2021-09-27 00:00:00.0': 5   (valor de outra coluna vazado pro campo errado — evidencia do desalinhamento)
' ': 4
'160090': 3
'33.040.981/0001-50': 3      (CNPJ vazado pro campo errado — mesma evidencia)
```

488 de 747 linhas problemáticas (65%) não têm um `cdunidadegestora` identificável — são fragmentos "cauda" sem os campos iniciais da linha. Dos que têm valor identificável, há concentração real em `440022` (32 ocorrências) e `160091`/`160084`/`160090` (todos ligados a órgãos de segurança pública — Polícia Civil, pelos exemplos inspecionados manualmente). **Não é conclusivo** se isso significa que esses órgãos específicos usam um sistema de exportação diferente (mais propenso ao bug de escape) ou se é só volume — não normalizado pelo total de linhas de cada órgão nesta sessão.

### 7. Parte A.2 — custo do `dbt seed`/`--full-refresh`, isolado das linhas malformadas

Para medir o custo real, as 747 linhas malformadas foram removidas (CSV limpo, 95.492 linhas de dado, mesmas 59 colunas) — só para viabilizar a medição, arquivo não commitado.

**Sem `--full-refresh`** (tabela existente ainda com schema antigo de 51 colunas) — reproduz exatamente o achado 7.1 da spec 017:

```
16:14:18  1 of 1 ERROR loading seed file raw.contratos ................................... [ERROR in 30.47s]
16:14:18    Database Error in seed contratos (seeds/contratos.csv)
  column "origem" of relation "contratos" does not exist
  LINE 2: ...insert into "compras_publicas"."raw"."contratos" (ORIGEM, CD...
```

**Com `--full-refresh`** (mesmo arquivo limpo de 747 linhas, mas ainda com os valores extremos das colunas identificadas no item 8) — erro **diferente** do relatado na spec 017 (lá, item 7.2, era o erro de linha malformada; aqui, com as linhas malformadas já removidas, aparece um erro novo):

```
16:15:02  1 of 1 ERROR loading seed file raw.contratos ................................... [ERROR in 31.80s]
16:15:02    Database Error in seed contratos (seeds/contratos.csv)
  integer out of range

real    0m37.706s
```

Ver item 8 para a causa raiz deste erro — é um **terceiro bloqueio**, não documentado na spec 017.

### 8. Achado adicional — `--full-refresh` recria o schema via inferência de tipo, e a inferência erra

`dbt/seeds/schema/contratos.yml` só documenta 4 colunas (descrição, sem `column_types`):

```yaml
seeds:
  - name: contratos
    columns:
      - name: nucontrato
      - name: idcontratado
      - name: vloriginal
      - name: vlatual
```

Sem `column_types` fixado, `dbt seed --full-refresh` recria a tabela do zero usando o tipo que a biblioteca `agate` (usada internamente pelo dbt) infere a partir dos próprios dados do CSV — não usa os tipos da tabela existente. Isolando as colunas com valores fora do range de `integer` (`int4`, limite `2147483647`):

```
Coluna | preenchidas | fora do range int32 | maximo absoluto
  IDCONTRATADO: 95124 ocorrencias fora do range int32 (praticamente todas as linhas — CNPJ de 14 digitos)
  CDFISCAL: 14637 de 34446 preenchidas fora do range int32, max=4294216849
  NUDOCUMENTOLEGAL: 110 ocorrencias, max=52270860079201343
  OBJETO: 6 ocorrencias, max=19232159000160        (valor vazado de outra coluna — linha corrompida que passou pela checagem de contagem de campo por coincidencia)
  NMREPINTERVENIENTE: 2, NMREPUG: 3, NUPROCESSO: 21, NUPROCESSOFORMATADO: 21, NUEDITAL: 3, NMREPCREDOR: 4, NMBEMPUBLICO: 1
```

`IDCONTRATADO` (CNPJ/CPF, coluna já existente desde o schema antigo, hoje `character varying` na tabela real) é o caso mais grave: **praticamente toda linha** tem um CNPJ de 14 dígitos, que sempre excede `int32`. `agate` está inferindo `integer` para essa coluna porque olha só uma amostra/o formato aparente do valor, não o domínio de negócio (CNPJ não é um "número" no sentido aritmético). As outras colunas fora de `IDCONTRATADO`/`CDFISCAL` (`OBJETO`, `NUPROCESSO` etc., com poucas ocorrências) são texto livre — a presença de valores puramente numéricos nelas nessas poucas linhas provavelmente indica **linhas corrompidas que passaram pela checagem de contagem de campo por coincidência** (um campo perdeu um valor e outro ganhou um `;` a mais, contagem total bate com 59 por acaso) — não investigado a fundo, registrado como suspeita.

Para conseguir medir o `--full-refresh` até o fim (sucesso), os valores acima foram zerados só para teste (109.932 valores em branco, arquivo não commitado). Resultado:

```
16:27:09  1 of 1 OK loaded seed file raw.contratos ....... [CREATE 95492 in 228.66s]
16:27:09  Finished running 1 seed in 0 hours 3 minutes and 48.84 seconds (228.84s)
```

**Sucesso — mas o schema resultante diverge seriamente do schema atual em produção:**

```
$ docker compose exec postgres psql ... -c "\d raw.contratos"
 origem                | text              <- coluna nova, ok
 cdunidadegestora      | integer           <- ERA character varying (codigo de orgao, risco de perder zero a esquerda)
 cdgestao              | integer           <- ERA character varying
 idcontratado          | integer           <- ERA character varying (CNPJ! e so nao deu overflow aqui pq foi zerado pro teste)
 dtinicio               | text             <- ERA timestamp without time zone
 dtfim                  | text             <- ERA timestamp without time zone
 dtfimatual             | text             <- ERA timestamp without time zone
 dtassinatura           | text             <- ERA timestamp without time zone
 dtautorizacao          | text             <- ERA timestamp without time zone
 dtinclusao             | text             <- ERA timestamp without time zone
 dtlimiteproposta       | text             <- ERA timestamp without time zone
 dataproposta           | text             <- ERA timestamp without time zone
 vloriginal             | double precision <- ERA numeric
 vlatual                | double precision <- ERA numeric
 vlgarantia             | double precision <- ERA numeric
 vlpercgarantia         | double precision <- ERA numeric
 vlpercmulta            | double precision <- ERA numeric
 vladitado              | double precision <- ERA numeric
 nuprazo                | integer          <- ERA character varying
 nutitulo               | integer          <- ERA character varying
 cdcredor               | integer          (coluna nova)
 cdfiscal               | text             (coluna nova — so nao virou integer pq foi zerado pro teste)
```

**Todas as 8 colunas de data viraram `text`** (perda total de validação/tipo — qualquer filtro por data em SQL downstream quebraria silenciosamente ou exigiria cast). **Todas as 6 colunas monetárias viraram `double precision`** em vez de `numeric` (perda de precisão decimal exata em valores de contrato — problema real para soma agregada de milhões de registros). **`cdunidadegestora`, `cdgestao`, `nuprazo`, `nutitulo`, `idcontratado`** viraram `integer` (risco de perda de zero à esquerda em códigos, e `idcontratado` estava a um passo de dar overflow de novo — só não deu porque os valores foram zerados manualmente para viabilizar este teste).

**Isso significa que o schema "correto" (varchar/numeric/timestamp) que a tabela `raw.contratos` tem hoje não é protegido por nenhuma configuração** — ele existe porque, historicamente, ninguém rodou `--full-refresh` contra o schema completo real (ou rodou uma vez contra dado mais limpo/período menor, e nunca mais). Rodar `--full-refresh` hoje, mesmo resolvendo os bloqueios A e B, **regridiria os tipos da tabela inteira** a menos que `dbt/seeds/schema/contratos.yml` ganhe `column_types` explícitos antes.

### 9. Medição do seed incremental (schema já compatível, sem `--full-refresh`)

Depois do `--full-refresh` bem-sucedido do item 8 (schema de 59 colunas já criado), rodando `dbt seed --select contratos` de novo (mesmo arquivo, sem `--full-refresh`):

```
16:31:45  1 of 1 OK loaded seed file raw.contratos ....... [INSERT 95492 in 228.36s]
16:31:45  Finished running 1 seed in 0 hours 3 minutes and 48.56 seconds (228.56s)

real    3m54.155s
```

**228,36s incremental vs. 228,66s com `--full-refresh` — diferença de 0,3s, dentro do ruído de medição.** Para este volume (~95 mil linhas), o `TRUNCATE+INSERT` e o `DROP+CREATE+INSERT` custam essencialmente o mesmo — o tempo é dominado pelo `INSERT` em si, não pela DDL. **A pergunta de custo do prompt original tem resposta objetiva: não há custo relevante a evitar.** O que precisa de decisão de Design não é custo, é correção de tipo (item 8).

### 10. Restauração do ambiente

Ao final da sessão, `dbt/seeds/contratos.csv` foi restaurado do backup feito antes do primeiro teste (`git diff` confirma zero divergência do committed), e `dbt seed --select contratos --full-refresh` rodado contra o arquivo original restaurou `raw.contratos` para 51 colunas / 76.041 linhas, tipos originais (`character varying`/`numeric`/`timestamp`) confirmados via `\d raw.contratos` — mesmo estado de antes desta sessão.

## Requirements

Não fechado nesta spec — é levantamento puro. Ver Casos de borda para as decisões pendentes.

## Design

Não fechado nesta spec. Nenhuma mudança aplicada a `ingest.sh`, `stg_contratos.sql`, `dbt/seeds/schema/contratos.yml`, ou `dbt/seeds/contratos.csv`.

### Componentes afetados

Nenhum — investigação apenas.

## Casos de borda

Perguntas em aberto que uma spec de Design subsequente precisa decidir — formuladas aqui, não respondidas:

1. **`column_types` para `raw.contratos`.** Antes de qualquer `--full-refresh` real acontecer contra o schema de 59 colunas, `dbt/seeds/schema/contratos.yml` precisa declarar `column_types` explícitos para pelo menos as colunas de data (`timestamp`), valor (`numeric`), e código de órgão/CNPJ (`varchar`) — ou a inferência automática do `agate` regride o schema (item 8). Decisão de quais tipos exatos, e se vale declarar as 59 colunas ou só as que hoje têm tipo não-texto, fica para spec de Design.
2. **`IDCONTRATADO` como `integer` é um risco recorrente, não só de hoje.** Mesmo com `column_types` corrigido para o schema atual, qualquer coluna nova que pareça numérica (como `CDFISCAL` foi) é candidata a receber tipo errado da próxima vez que o portal adicionar uma coluna e `--full-refresh` rodar sem `column_types` atualizado junto. Vale decisão de processo: `column_types` sempre revisado manualmente quando uma coluna nova aparece, ou nunca usar `--full-refresh` sem checagem prévia.
3. **As 69 linhas malformadas do CSV real (0,07% dos registros — não 747/0,78%, ver item 4): descartar, reparar programaticamente, ou reportar para revisão manual?** Pelo menos 2 dos incidentes inspecionados (item 5) correspondem a contratos de valor alto (R$ 14–19 milhões e R$ 2,1–2,2 milhões) — não dá para assumir que são todos irrelevantes. A causa aparente (`\"` em vez de `""` para aspas internas em `RESUMO`/`OBJETO`, ver item 5) sugere que um pré-processamento específico (substituir esse padrão de escape antes do parse) poderia recuperar a maioria sem intervenção manual linha a linha — não testado nesta sessão.
4. **Por que a ordem dos erros divergiu entre a spec 017 e esta sessão (item 2)?** Não investigado a fundo. Se relevante para decidir a ordem de correção (Parte A vs. Parte B), vale entender antes de agir — hoje, na prática, a Parte B bloqueia primeiro de qualquer forma.
5. **Frequência esperada de mudança de schema do portal — pergunta original do prompt, ainda sem resposta.** O único dado histórico disponível é o achado da spec 016 (mudança publicada em 09/09/2025, detectada só ~11 meses depois porque o ETag não tinha mudado o suficiente para disparar reprocessamento, ou a rotina não rodava). Não há como saber, só com esta investigação, se mudanças de schema no portal são raras (uma a cada anos) ou mais frequentes do que o `Last-Modified` sugere. Como o custo de `--full-refresh` é desprezível (item 9), essa pergunta deixa de ser sobre "vale a pena pagar o custo toda vez" e passa a ser só sobre a cadência de revisão manual do `column_types` (caso de borda 2).
6. **Concentração por órgão (item 6) não normalizada pelo volume total de cada órgão.** Não dá para afirmar que `440022`/`160091`/`160084`/`160090` têm uma taxa de erro maior que a média sem esse denominador — só que, em termos absolutos, aparecem mais nos incidentes.

## Fora do escopo

- Qualquer alteração em `ingest.sh`, `stg_contratos.sql`, `dbt/seeds/schema/contratos.yml`, ou `dbt/seeds/contratos.csv` — fica para spec de Design subsequente.
- Implementar `column_types` no seed.
- Implementar qualquer estratégia de reparo/pré-processamento para as 69 linhas malformadas.
- Determinar exatamente qual combinação de `\"` produz estilhaçamento (vs. as ~3.063 ocorrências que não produzem) — registrado como não resolvido no item 5.
- Normalizar a concentração por órgão pelo volume total (caso de borda 6).

## Referências de código

- `dbt/seeds/schema/contratos.yml` — hoje só documenta 4 colunas, sem `column_types` (achado central do item 8).
- `dbt/seeds/contratos.csv` — seed versionado, restaurado ao schema antigo (51 colunas) ao final desta sessão.
- `dbt/scripts/ingest.sh:145-151` — chama `dbt seed --select contratos` sem `--full-refresh` (comportamento hoje, não alterado nesta spec).

## Ver também

- [[017-validacao-schema-tolerante]] (Casos de borda 2 e 3 — origem desta investigação)
- [[016-levantamento-schema-csv-portal]] (mapeamento original das 8 colunas novas, incluindo `CDFISCAL`)
- [[009-automacao-da-ingestao]] (spec original do `ingest.sh`)
