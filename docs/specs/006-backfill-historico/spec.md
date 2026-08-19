# 006 — Backfill histórico (escopo 2011+)

## Tipo

Decisão de arquitetura — extensão deliberada do escopo temporal, separada do fluxo corrente (specs 003/004/005).

## Status

Design e Requirements (EARS) definidos em 2026-08-19 — pendente de aprovação/fechamento pelo usuário.

## Resumo

O fluxo corrente (specs 003–005) cobre o formato atual do portal (snapshot mensal, `contrato-demo.csv`, formato validado). Existe também um arquivo histórico já em disco (`dbt/seeds/contratos.csv`, 76.041 linhas, obtido em maio deste ano) e arquivos anuais publicados no portal (`Contratos - 2011-2021.csv`, `contratos-2022.csv`, etc.) que ainda não foram comparados entre si nem contra o formato atual. Esta spec decide se — e como — esse histórico entra no pipeline: como fonte única já consolidada, como múltiplos arquivos a normalizar, ou como escopo a não perseguir agora.

**Conclusão (Bloco 4, 2026-08-19): existe gap real de cobertura oficial.** O portal não publica nenhum arquivo anual específico para 2023 ou 2024 (confirmado via listagem de recursos do dataset — só existem os 7 recursos: dicionário, `Contratos - 2011-2021` [csv/xlsx], `contratos-2022` [csv/xlsx/json] e o `contratos.csv` corrente/vigente). Dentro do que os arquivos baixados cobrem: **2022 e 2023 estão bem representados** em `contratos-2022.csv` (confirmado por busca literal no arquivo bruto, contornando um bug de parsing do próprio CSV do portal); **2024 tem gap parcial real** (o arquivo do portal captura contratos `2024CT` só até a sequência ~7582, o seed tem até ~11459); **2025 tem gap total** (nenhum registro de 2025 existe em nenhum arquivo oficial baixado, e não há arquivo anual publicado pra esse ano). Ou seja, **`seeds/contratos.csv` é hoje a única fonte para o final de 2024 e todo o 2025** — não é redundância/conveniência, é dado que não existe em nenhum outro lugar verificado.

**Checagem complementar (Bloco 5, 2026-08-19): o snapshot atual (`contrato-demo.csv`, formato novo `CT-NNNNN/AAAA/SIGLA`) não reduz o gap.** Comparado contra o gap estritamente confirmado no Bloco 4 (2024 sequência >7582 + todo 2025, 12.234 linhas do seed), o overlap por chave exata é de apenas 5 linhas; por `nuprocesso` (mais tolerante à mudança de formato de `nucontrato`), 95 de 7.753 chaves comparáveis. **Gap real após a checagem: 12.229 de 12.234 linhas (99,96%) permanecem sem cobertura em nenhuma fonte verificada.** O tamanho do buraco documentado no Bloco 4 não muda de forma material — `seeds/contratos.csv` continua sendo, de fato, a única fonte pra esse período.

## Contexto

- Decisão já tomada (fora de spec, nesta sessão): separar backfill do fluxo corrente para não acoplar a complexidade de normalização de schema drift ao MVP (specs 003–005), que já está com Design fechado.
- `seeds/contratos.csv` (76.041 linhas) é a origem do achado de colisão de `nucontrato` resolvida pela spec 005 — mas não se sabe ainda se esse arquivo já é uma consolidação de múltiplos anos feita por terceiros (o portal? alguma ferramenta do usuário?), ou se corresponde a um recorte específico.
- O portal expõe arquivos separados por período: `Contratos - 2011-2021.csv`, `contratos-2022.csv`/`.json`, além do `contratos.csv` corrente (formato atual, validado nas specs anteriores).
- Não foi confirmado se as colunas, encoding, delimitador e nomenclatura de campos são consistentes entre esses arquivos anuais — schema drift é hipótese, não fato confirmado.

## Investigação

### Bloco 1 — o que `seeds/contratos.csv` realmente é

```python
import pandas as pd

df_hist = pd.read_csv('dbt/seeds/contratos.csv', sep=';', encoding='utf-8')
print('Colunas:', list(df_hist.columns))
print('Total linhas:', len(df_hist))

# Distribuição por ano - assumindo que exista uma coluna de data de assinatura/início
for col in ['dtassinatura', 'dtinicio']:
    if col in df_hist.columns:
        anos = pd.to_datetime(df_hist[col], errors='coerce').dt.year.value_counts().sort_index()
        print(f'\nDistribuição por ano ({col}):')
        print(anos)
```

Objetivo: confirmar se `seeds/contratos.csv` já cobre 2011-2025 de forma contínua, ou se tem lacunas/concentração em períodos específicos.

#### Resultado (executado 2026-08-19)

```
Colunas: ['cdunidadegestora', 'nmunidadegestora', 'cdgestao', 'nmgestao', 'nucontrato', 'idcontratado',
'contratado', 'resumo', 'objeto', 'dtinicio', 'dtfim', 'dtfimatual', 'dtassinatura', 'situacao',
'nuprocesso', 'vloriginal', 'vlatual', 'nmfiscal', 'nuedital', 'nmbempublico', 'nmregimeexecucao',
'detipocontrato', 'detipodocumentolegal', 'nudocumentolegal', 'demulta', 'nuautorizacaoorgao', 'nuprazo',
'nminterveniente', 'nmlocalexecucao', 'nmmodalidade', 'nmrepcredor', 'nmrepinterveniente', 'nmrepug',
'dtautorizacao', 'dtinclusao', 'dtlimiteproposta', 'vlgarantia', 'vlpercgarantia', 'vlpercmulta',
'nutitulo', 'vladitado', 'cdugfiscalizador', 'ugfiscalizador', 'cdgestaofiscalizador', 'gestaofiscalizador',
'bempublico', 'deesptitulo', 'dataproposta', 'diasoriginais', 'diasaditados', 'diasatuais']
Total linhas: 76041

Distribuição por ano (dtassinatura):
2013      35
2014     110
2015    1519
2016    7742
2017    9607
2018    8736
2019    6263
2020    5916
2021    6365
2022    7695
2023    6554
2024    6951
2025    8548
```

**Conclusão do Bloco 1:** `seeds/contratos.csv` cobre **2013-2025**, não 2011+. A hipótese de que já seria um consolidado completo desde 2011 está **descartada** — faltam 2011 e 2012 inteiros. Encoding do arquivo é UTF-8 real (bytes confirmados como `\xc3\xad` para "í" — qualquer mojibake visto em terminal foi artefato de exibição, não corrupção de dado).

### Bloco 2 — baixar e comparar os arquivos anuais do portal

```bash
curl -sL -o /tmp/contratos-2011-2021.csv "https://dados.sc.gov.br/dataset/93dab950-e805-4388-8418-cfb3b73f1623/resource/ac64ba57-bac8-4969-9248-cb9c9b76415d/download/contratos-2011-2021.csv"
curl -sL -o /tmp/contratos-2022.csv "https://dados.sc.gov.br/dataset/93dab950-e805-4388-8418-cfb3b73f1623/resource/54789bf5-ff35-4be3-af5a-f20a31424264/download/contratos-2022.csv"
```

```python
import pandas as pd

def inspecionar(path, **kwargs):
    try:
        df = pd.read_csv(path, **kwargs)
        return list(df.columns), len(df)
    except Exception as e:
        return f'ERRO: {e}', 0

for path, kwargs in [
    ('/tmp/contratos-2011-2021.csv', dict(sep=None, engine='python', encoding='ISO-8859-1')),
    ('/tmp/contratos-2022.csv', dict(sep=None, engine='python', encoding='ISO-8859-1')),
]:
    cols, n = inspecionar(path, **kwargs)
    print(f'\n{path}: {n} linhas')
    print(cols)
```

Comparar essa lista de colunas com as 51 colunas já conhecidas do formato atual (`contrato-demo.csv`) e do `seeds/contratos.csv` — anotar quais colunas existem em uns e não em outros, e se os nomes batem exatamente ou mudaram ao longo do tempo.

#### Resultado (executado 2026-08-19)

```
$ curl -sL -o contratos-2011-2021.csv "...download/contratos-2011-2021.csv" -w "HTTP:%{http_code} SIZE:%{size_download}"
HTTP:200 SIZE:82564102
$ curl -sL -o contratos-2022.csv "...download/contratos-2022.csv" -w "HTTP:%{http_code} SIZE:%{size_download}"
HTTP:200 SIZE:105045961
```

Delimitador real (não `;`): **vírgula**. Encoding real: **ISO-8859-1** (utf-8 falha ao parsear). Ambos diferentes do `seeds/contratos.csv` (`;`, UTF-8).

```
contratos-2011-2021.csv (54 colunas, 68752 linhas):
['ORIGEM', 'CDUNIDADEGESTORA', 'NMUNIDADEGESTORA', 'CDGESTAO', 'NMGESTAO', 'NUCONTRATO', 'IDCONTRATADO',
'CONTRATADO', 'RESUMO', 'OBJETO', 'DTINIBUSCA', 'DTINICIO', 'DTFIM', 'DTFIMATUAL', 'DTASSINATURA',
'SITUACAO', 'NUPROCESSO', 'NUPROCESSOFORMATADO', 'VLORIGINAL', 'VLATUAL', 'TAGS', 'NUEDITAL',
'NMBEMPUBLICO', 'NMREGIMEEXECUCAO', 'DETIPOCONTRATO', 'DETIPODOCUMENTOLEGAL', 'NUDOCUMENTOLEGAL',
'DEMULTA', 'NUAUTORIZACAOORGAO', 'NUPRAZO', 'NMINTERVENIENTE', 'NMLOCALEXECUCAO', 'NMMODALIDADE',
'NMREPCREDOR', 'NMREPINTERVENIENTE', 'NMREPUG', 'DTAUTORIZACAO', 'DTINCLUSAO', 'DTLIMITEPROPOSTA',
'VLGARANTIA', 'VLPERCGARANTIA', 'VLPERCMULTA', 'NUTITULO', 'VLADITADO', 'CDUGFISCALIZADOR',
'UGFISCALIZADOR', 'CDGESTAOFISCALIZADOR', 'GESTAOFISCALIZADOR', 'BEMPUBLICO', 'DEESPTITULO',
'DATAPROPOSTA', 'DIASORIGINAIS', 'DIASADITADOS', 'DIASATUAIS', 'INDICE']

contratos-2022.csv (56 colunas — todas as 54 acima + 2 novas):
[... mesmas 54 ...] + ['IDCONTRATADOMASCARADO', 'CDCREDOR']

Distribuição por ano (DTASSINATURA) em contratos-2011-2021.csv:
2005       2
2006      67
2007       7
2008      73
2009      50
2010     164
2011     408
2012     303
2013    1832
2014    6198
2015    3968
2016    4336
2017    4288
2018    4793
2019    3346
2020    2817
2021    2785
(DTASSINATURA nulos: 0)
```

**Conclusões do Bloco 2:**
1. **Schema drift confirmado, real e em três eixos**: (a) delimitador (`;` no seed vs `,` no portal), (b) encoding (UTF-8 no seed vs ISO-8859-1 no portal), (c) colunas — o portal tem 5 colunas extras que o seed não tem (`ORIGEM`, `DTINIBUSCA`, `NUPROCESSOFORMATADO`, `TAGS`, `INDICE`), e o próprio portal muda de schema **entre um ano e o outro** (2022 ganha `IDCONTRATADOMASCARADO` e `CDCREDOR` que 2011-2021 não tem).
2. **`contratos-2011-2021.csv` não começa em 2011**: tem registros de 2005 a 2021, incluindo 6 anos antes do range nominal do arquivo. O nome do arquivo é enganoso quanto à cobertura real.
3. **Os anos 2013-2021 aparecem em ambas as fontes** (seed e portal) — overlap a resolver (ver Bloco 3).

### Bloco 3 — estabilidade de `cdunidadegestora` entre anos

```python
# Unidades gestoras mudam de código, se fundem ou são renomeadas ao longo de 14 anos?
# Comparar o conjunto de (cdunidadegestora, nmunidadegestora) entre o histórico e o formato atual
hist_ugs = df_hist[['cdunidadegestora', 'nmunidadegestora']].drop_duplicates()
print(f'Unidades gestoras distintas no histórico: {len(hist_ugs)}')
# Repetir contra contrato-demo.csv e comparar overlap
```

Objetivo: confirmar que a chave `(cdunidadegestora, nucontrato)` validada nas specs 003/005 continua estável quando o histórico completo entra em jogo — não só dentro do arquivo já testado.

#### Resultado (executado 2026-08-19)

```
UGs distintas no seeds (2013-2025): 414
UGs distintas no portal 2011-2021: 292
CDs só no seeds: 29
CDs só no portal 2011-2021: 6
CDs em comum: 158
CDs com nome divergente entre fontes: 753

Exemplos (cdunidadegestora | nmunidadegestora no seeds | NMUNIDADEGESTORA no portal):
160084 | Fundo de Melhoria da Polícia Civil        | Fundo para Melhoria da Segurança Pública
160001 | Secretaria de Estado da Segurança Pública | Secretaria de Estado da Segurança Pública (variação de espaço/whitespace)
410001 | Casa Civil                                 | Secretaria Executiva de Assuntos Internacionais
410001 | Casa Civil                                 | Secretaria de Estado da Casa Civil
410001 | Secretaria de Estado da Casa Civil         | Casa Civil
```

Checagem adicional (não prevista no rascunho original, mas necessária pra fechar o caso de borda "mesmo contrato em duas fontes"): overlap da chave `(cdunidadegestora, nucontrato)` entre `seeds/contratos.csv` e `contratos-2011-2021.csv`, e consistência de valores no overlap.

```
Chaves (cdunidadegestora, nucontrato) só no seeds: 30595
Chaves só no portal 2011-2021: 23306
Chaves em ambos (overlap): 45446
Total seeds: 76041 | Total portal 2011-2021: 68752

Amostra do overlap (vloriginal, vlatual, situacao — seeds vs portal):
cd=160091 nu=2017CT013311 → seeds: [16758.0, 16758.0, 'Encerrado'] | portal: [16758.0, 16758.0, 'Encerrado']
cd=470092 nu=2020CT001404 → seeds: [1016.0, 0.0, 'Encerrado']      | portal: [1016.0, 0.0, 'Encerrado']
cd=160091 nu=2016CT007167 → seeds: [570.0, 570.0, 'Encerrado']     | portal: [570.0, 570.0, 'Encerrado']
cd=160091 nu=2020CT004291 → seeds: [2585.2, 2585.2, 'Encerrado']   | portal: [2585.2, 2585.2, 'Encerrado']
cd=160097 nu=2016CT006818 → seeds: [20600.0, 20600.0, 'Encerrado'] | portal: [20600.0, 20600.0, 'Encerrado']
```

**Conclusões do Bloco 3:**
1. A **chave `(cdunidadegestora, nucontrato)` em si é estável** — na amostra verificada, os mesmos pares de código aparecem nas duas fontes com valores idênticos (`vloriginal`, `vlatual`, `situacao`). Não confirma exaustivamente (amostra de 5 em 45446), mas não há indício de conflito.
2. **`nmunidadegestora` (o nome) NÃO é estável** — 753 códigos de UG têm nomes diferentes entre fontes, incluindo casos de um mesmo código associado a 2-3 nomes distintos (`410001`: "Casa Civil" / "Secretaria de Estado da Casa Civil" / "Secretaria Executiva de Assuntos Internacionais"). Isso é reorganização administrativa real ao longo de 14+ anos, não erro de dado. **A chave de junção deve ser sempre o código, nunca o nome.**
3. Há overlap massivo de linhas entre as duas fontes brutas (45446 de 76041 linhas do seed também aparecem no portal 2011-2021) — confirma que unificar as fontes exige deduplicação por `(cdunidadegestora, nucontrato)`, não uma simples concatenação.

### Bloco 4 — gap de cobertura 2022-2025 e checagem de recurso oficial

Motivação: os Blocos 1-3 mostraram overlap entre `seeds/contratos.csv` e `contratos-2011-2021.csv`, mas não respondiam se o intervalo 2022-2025 (fora do range desses dois arquivos nominal) tem alguma fonte oficial alternativa, ou se `seeds/contratos.csv` é a única fonte pra esse período.

#### Passo 1 — join ingênuo por chave `(cdunidadegestora, nucontrato)`

Script fornecido precisou de ajustes — documentados aqui, não só o resultado:
- Paths `/tmp/...` não resolvem no Python nativo do Windows usado nesta sessão; usados os arquivos já baixados no scratchpad da sessão.
- Colunas dos arquivos do portal são maiúsculas (`CDUNIDADEGESTORA`, `NUCONTRATO`), diferente do seed (minúsculas) — ajustado por arquivo.
- `sep=None, engine='python'` (autodetecção) falhou em `contratos-2022.csv` com `_csv.Error: ';' expected after '"'` — o arquivo tem aspas malformadas em pelo menos uma linha. Trocado por delimitador explícito por arquivo: `,` pra `contratos-2011-2021.csv` (confirmado no Bloco 2), `;` pra `contratos-2022.csv`.
- Mesmo com `;` explícito, `contratos-2022.csv` ainda falhou: `ParserError: Expected 57 fields in line 322, saw 58`. Inspeção da linha 322 mostrou aspas não fechadas e um campo (provavelmente `INDICE`, usado pra busca full-text) contendo os valores da própria linha novamente, concatenados por `|` — sujeira real do dado de origem, não erro nosso. Contornado com `on_bad_lines=<coletor>` pra quantificar, não descartar silenciosamente.

```
contratos-2022.csv: 976 linhas descartadas por malformação de 117.017 originais (116041 carregadas com sucesso)
contratos-2011-2021.csv: 0 linhas descartadas (carrega limpo com sep=',')
```

Resultado do join ingênuo:

```
df_seed: 76041 linhas
df_2011_2021: 68752 linhas
df_2022: 116041 linhas (976 descartadas por malformação)

Linhas do seed sem equivalente em nenhum arquivo oficial: 30595

Distribuição por ano (dtassinatura) das linhas exclusivas do seed:
2013       1
2014       2
2015       1
2016      11
2017      22
2018      73
2019      61
2020     271
2021     410
2022    7690
2023    6554
2024    6951
2025    8548
```

**Esse resultado bruto é enganoso e não foi aceito sem checagem adicional** — ver conclusão abaixo.

#### Verificação adicional (não estava no script original, mas necessária antes de aceitar o join como confiável)

Ao investigar por que praticamente 100% das linhas de 2022 do seed apareciam como "sem equivalente" — mesmo `contratos-2022.csv` tendo 116.041 linhas — foram encontrados dois problemas reais que invalidam o join ingênuo pra 2022-2024:

1. **`contratos-2022.csv` não é escopado a 2022**: cobre 2005-2024 (mesma distorção de nome de arquivo já vista no Bloco 2 pro arquivo 2011-2021). Distribuição real por `DTASSINATURA`:
   ```
   2005:2  2006:67  2007:7  2008:72  2009:48  2010:159  2011:397  2012:299
   2013:1788  2014:6005  2015:3847  2016:4171  2017:4086  2018:4356
   2019:2809  2020:2474  2021:2330  2022:3131  2023:2566  2024:680
   ```
2. **Corrupção de alinhamento de coluna**: mesmo em linhas "válidas" (não descartadas por `on_bad_lines`), valores vazam de campo pra campo — ex.: uma linha tem `NUCONTRATO = '2013-03-27 00:00:00.0'` (uma data, não um número de contrato), evidência de que aspas malformadas deslocam colunas sem necessariamente quebrar a contagem de campos.
3. **Formato de `nucontrato` mudou**: até ~2021, formato é `AAAACTnnnnnn` (ex.: `2017CT013311`); a partir de 2022 o portal passa a usar majoritariamente `CT-nnnnn/AAAA/SIGLA-ORGAO` (ex.: `CT-00023/2022/SIE`), mas o seed tem os DOIS formatos misturados pro mesmo período — mais um eixo de drift não previsto no rascunho original da spec.

Dado isso, o join por chave exata é não-confiável pra 2022+ por causa da corrupção do CSV, não necessariamente por ausência real do dado. Verificação por busca literal (`grep -F`, contorna o parser) numa amostra aleatória de `nucontrato` do seed por ano (seed=42/7, n=10 por ano):

```
Amostra 2022 (10 valores) → 9/10 encontrados no arquivo bruto contratos-2022.csv
Amostra 2023 (10 valores) → 10/10 encontrados
Amostra 2024 (10 valores) → 0/10 encontrados
Amostra 2025 (10 valores) → 0/10 encontrados
```

A amostra de 2024 zerada foi investigada à parte: os 10 valores sorteados eram todos formato antigo (`2024CTnnnnnn`). Esse formato existe no arquivo (3.312 ocorrências brutas de `2024CT\d+`), mas com range menor:

```
2024CT no arquivo contratos-2022.csv: min=1, max=7582, qtd=5288
2024CT no seed:                       min=1, max=11459, qtd=6506
```

Ou seja: o snapshot do portal capturou contratos `2024CT` só até a sequência ~7582 (embora a data de assinatura mais recente presente no arquivo pra 2024 seja `2024-12-04` — a captura parece truncada por algum outro critério, não estritamente por data). O seed tem contratos `2024CT` até 11459 que **não existem em nenhum arquivo do portal baixado**.

**Conclusão do Passo 1:** 2022 e 2023 — sem gap real (o "gap" do join ingênuo foi artefato de corrupção de CSV + mudança de formato de `nucontrato`, não ausência de dado). 2024 — gap parcial real e confirmado (contratos numerados acima de ~7582 no formato antigo, e o formato novo tem cobertura muito baixa: só 40 ocorrências de `CT-.../2024/` no arquivo do portal contra 207 no seed). 2025 — gap total confirmado (zero ocorrências).

#### Passo 2 — recurso oficial 2023/2024 no portal

```
$ curl -sL "https://dados.sc.gov.br/dataset/contratos" -o dataset-contratos.html -w "HTTP:%{http_code} SIZE:%{size_download}"
HTTP:200 SIZE:27037

$ grep -oE 'contratos[a-zA-Z0-9_.\-]*\.(csv|xlsx|json)' dataset-contratos.html | sort -u
contratos-2011-2021.csv
contratos-2011-2021.xlsx
contratos-2022.csv
contratos-2022.json
contratos-2022.xlsx
contratos-v1.0-1.xlsx
contratos.csv

$ grep -oiE '[^"'"'"']*20(23|24)[^"'"'"']*\.(csv|xlsx|json)' dataset-contratos.html | sort -u
(nenhuma saída — nenhum arquivo com "2023" ou "2024" no nome)

$ grep -oE 'resource/[a-f0-9-]+' dataset-contratos.html | sort -u | wc -l
7
```

**Conclusão do Passo 2 (ausência confirmada, não assumida):** a página do dataset (`https://dados.sc.gov.br/dataset/contratos`) lista exatamente 7 recursos: dicionário de dados, `Contratos - 2011-2021` (csv/xlsx), `contratos-2022` (csv/xlsx/json), e `contratos.csv` (snapshot vigente, atualizado 09/09/2025). **Não existe recurso anual específico para 2023 nem para 2024.** Checado direto no HTML bruto da página (não só via resumo de ferramenta), batendo com o resultado de uma leitura assistida da mesma página.

### Bloco 5 — o snapshot atual (`contrato-demo.csv`) já cobre parte do gap 2024/2025?

Motivação: `contrato-demo.csv` foi baixado manualmente nesta sessão (formato novo, `CT-NNNNN/AAAA/SIGLA`) — antes de aceitar o tamanho do gap documentado no Bloco 4 como definitivo, checar se esse snapshot mais recente já cobre parte do que o Bloco 4 marcou como não coberto. Arquivo fornecido pelo usuário fora do repo (`C:\temp\contrato-demo.csv`), não commitado.

Execução 1 — script conforme fornecido (`_ano >= 2024`, chave `(cdunidadegestora, nucontrato)` e `(cdunidadegestora, nuprocesso)`):

```
Linhas do seed em 2024+: 15499
Overlap por chave exata (cdunidadegestora, nucontrato): 5
Overlap por (cdunidadegestora, nuprocesso): 118

Tamanho real do gap nao coberto por nenhuma fonte (chave exata): 15494 de 15499
```

Verificação adicional antes de aceitar o número acima como confiável (mesmo padrão do Bloco 4: não aceitar join bruto sem checar se é artefato):

- **dtype das chaves**: `cdunidadegestora` é `int64` nas duas fontes, `nucontrato`/`nuprocesso` são `object` nas duas — overlap baixo não é artefato de tipo.
- **Formato de `nucontrato` realmente diverge** entre seed (`AS-00093/2020/SSP-FMPC`, formato antigo do período coberto) e `contrato-demo.csv` (`CT-00683/2025/...`, `MN-00046/2026/...`, formato novo) — confirma por amostra o schema drift já documentado no Bloco 4, overlap exato baixo é esperado e não indica bug de comparação.

Essa primeira execução usa `_ano >= 2024` como proxy do gap, mas o Bloco 4 confirmou que o gap real é mais estreito (só a partir da sequência `2024CT` > 7582, não 2024 inteiro). Reexecutado com o filtro estrito, pra não superestimar nem subestimar o gap:

```
Gap estrito (2024 seq>7582 + 2025 inteiro): 12234 linhas
  2024 seq>7582: 3686
  2025: 8548
Overlap exato (gap estrito x contrato-demo.csv): 5
Overlap por nuprocesso (gap estrito x contrato-demo.csv): 95

Gap estrito nao coberto (chave exata): 12229 de 12234
Gap estrito nao coberto (nuprocesso): 7658 de 7753
```

**Conclusão do Bloco 5:** o overlap entre `contrato-demo.csv` e o gap confirmado no Bloco 4 é marginal nos dois critérios de chave (5 por chave exata, 95 por `nuprocesso`, sobre um universo de 12.234 linhas). O snapshot atual **não reduz de forma material** o tamanho do gap documentado — é consistente com o esperado, já que `contrato-demo.csv` é um snapshot do estado *vigente* dos contratos (situação atual), não um arquivo histórico com todos os contratos já encerrados desse período. Contratos do gap que já foram encerrados/removidos da vitrine "vigente" do portal não apareceriam nesse snapshot mesmo que tivessem sido publicados em algum momento — isso não foi confirmado, é hipótese a registrar, não a decidir aqui.

## Requirements

### Funcionais

1. O sistema DEVE unificar as quatro fontes de dado (`contratos-2011-2021`, `contratos-2022`, `seeds/contratos.csv`, fluxo corrente) num único model, aplicando a ordem de precedência definida no Design (fonte mais recente/oficial vence sobre `seeds/contratos.csv`; fluxo corrente vence sobre todas).

2. QUANDO houver mais de um registro para a mesma chave `(cdunidadegestora, nucontrato)` em fontes diferentes, O sistema DEVE reter apenas o registro da fonte de maior precedência, descartando os demais — não concatenar.

3. O sistema DEVE armazenar `nucontrato` como texto literal, sem aplicar normalização, regex de conversão, ou tentativa de unificação entre o formato antigo (`AAAACTNNNNNN`) e o novo (`CT-NNNNN/AAAA/SIGLA`).

4. O sistema DEVE marcar, via `description`/`meta` do model dbt, os registros originados exclusivamente de `seeds/contratos.csv` para o intervalo sem cobertura oficial confirmada (2024, sequência `2024CT7583+`, e todo 2025) como "não auditados contra fonte oficial arquivada".

5. O sistema NÃO DEVE usar `nmunidadegestora` em nenhuma operação de join, filtro ou agrupamento — apenas `cdunidadegestora`, consistente com [[003-storage-e-chave-unica]] e [[005-grao-do-dado-contrato-vs-aditivo]].

6. SE um arquivo oficial "contratos-2024" ou "contratos-2025" for publicado futuramente pelo portal, ENTÃO a reconciliação da fatia não auditada DEVE ser tratada em spec própria, sem exigir redesenho do model de precedência desta spec.

### Não-funcionais

1. A nota de proveniência da fatia não auditada (item 4) DEVE permanecer visível em qualquer consumo posterior do dado — no mínimo no dbt docs; no frontend, quando a spec correspondente for aberta, a mesma nota DEVE ser propagada.

2. Esta spec NÃO DEVE redefinir decisão de chave ou grão já fechada — toda referência a `(cdunidadegestora, nucontrato)` ou ao grão "1 registro = 1 contrato" DEVE citar [[003-storage-e-chave-unica]] e [[005-grao-do-dado-contrato-vs-aditivo]] como fonte da decisão, não redeclarar.

## Design

### Ordem de precedência do merge

Fonte oficial mais recente vence onde há sobreposição; `seeds/contratos.csv` só contribui onde é a única fonte confirmada:

| Ordem | Fonte | Papel |
|---|---|---|
| 1 | `contratos-2011-2021.csv` | Fundação — cobre 2005–2021 |
| 2 | `contratos-2022.csv` | Cobre 2022 até meados de 2024 (`2024CT` até sequência ~7582) |
| 3 | `seeds/contratos.csv` | **Só entra pra preencher a cauda não coberta**: `2024CT` sequência 7583+ e todo 2025. Onde já existe registro nas fontes 1–2 para a mesma chave, a fonte oficial vence — o seed não sobrescreve |
| 4 | Snapshot atual (fluxo corrente, `contrato-demo.csv` em diante) | Mais recente, vence tudo — é o que o merge incremental do fluxo corrente (spec 003) já trata |

Implementação: cada fonte vira um `source`/model de staging próprio (com seu delimitador/encoding documentados no Bloco 2 da investigação), unidos num model de precedência que aplica essa ordem via `row_number() over (partition by cdunidadegestora, nucontrato order by prioridade_fonte)` ou equivalente — não concatenação simples, dado o overlap de 45.446 linhas já confirmado.

### `nucontrato`: dois formatos coexistem, sem normalização forçada

Confirmado que o formato mudou (`2017CT013311` → `CT-00023/2022/SIE`) numa transição real do sistema de origem, não um erro de dado. Tratamento:
- Campo armazenado como texto puro, sem regex de normalização entre formatos.
- Nenhuma tentativa de "unificar" os dois formatos numa chave sintética — a chave continua sendo o valor literal de `nucontrato` (dentro de `(cdunidadegestora, nucontrato)`), e os dois formatos convivem na mesma coluna, diferenciados naturalmente por período.
- Se algum consumo futuro precisar identificar o formato (ex.: para exibição), inferir por regex simples no momento do consumo, não na modelagem de origem.

### Limitação de cobertura — aceita e documentada, não escondida

- **2024 (sequência 2024CT7583+) e 2025 inteiro**: única fonte é `seeds/contratos.csv`, sem verificação cruzada contra arquivo oficial arquivado do portal (99,96% desse recorte — 12.229 de 12.234 linhas — sem cobertura em nenhuma outra fonte checada, incluindo o snapshot atual).
- Essa fatia do dado é tratada como **não auditada de forma independente** — documentar isso explicitamente onde o dado for consumido (ex.: nota no dbt docs do model, não só na spec), para que qualquer análise sobre 2024–2025 carregue esse alerta de proveniência.
- Se um arquivo oficial "contratos-2024" ou "contratos-2025" for publicado pelo portal no futuro, essa fatia deve ser reconciliada contra ele (nova spec, não retrabalho da 006).

### `nmunidadegestora` — reforço (já propagado pras specs 003/005)

Nunca usar em join, filtro ou agrupamento — só `cdunidadegestora`. O model de precedência desta spec deve seguir a mesma regra: ao escolher qual `nmunidadegestora` exibir por `cdunidadegestora`, usar sempre o valor da fonte mais recente na ordem de precedência acima, nunca uma lógica de "nome mais comum" ou similar.

### Componentes afetados

- 4 sources/staging models: `contratos_2011_2021`, `contratos_2022`, `contratos_seed_gap` (ou nome equivalente, já filtrado só pra fatia não coberta), `contratos_atual` (fluxo corrente, já existente da spec 003).
- 1 model de precedência/dedup unindo os 4 pela chave `(cdunidadegestora, nucontrato)`.
- Nota de proveniência (dbt `description` / `meta`) no model final, marcando a fatia 2024-cauda/2025 como não auditada.

## Casos de borda

- Contrato cuja chave aparece em mais de uma fonte com valores divergentes além do esperado (não só `nmunidadegestora`, mas `vlatual`/`situacao` diferentes): a ordem de precedência decide automaticamente, mas vale considerar um log/flag de quantos casos assim existem, pra dimensionar o quanto a divergência entre fontes é ruído normal vs. algo que merece investigação futura.
- Se a fatia "não auditada" (2024-cauda/2025) for citada em qualquer dashboard ou relatório do frontend (spec ainda não aberta), a nota de proveniência precisa estar visível lá também, não só no dbt docs.

## Fora do escopo

- Mudança no fluxo corrente (specs 003–005) — este backfill não deve reabrir o Design já fechado, só estender.
- Automação/orquestração da ingestão — tratada em spec própria do eixo pipeline.
- Reconciliação com arquivo oficial futuro para 2024/2025 — vira spec própria se e quando o portal publicar.

## Referências de código

_A preencher conforme a implementação._

## Ver também

- [[003-storage-e-chave-unica]]
- [[004-origem-dados-api-vs-arquivo]]
- [[005-grao-do-dado-contrato-vs-aditivo]]
