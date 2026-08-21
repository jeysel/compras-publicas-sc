# Spec 021 — Levantamento: outliers de valor extremo em `vl_original`/`vl_atual`

## Tipo

Investigação (levantamento) + Design (fechado em 2026-08-20, Caso de borda 7 revisto em 2026-08-21 — ver seção Requirements/Design abaixo). A investigação original (itens 1-10) rodou só leitura contra `staging.stg_contratos` e as marts já materializadas. O tratamento (item 11 em diante) alterou `stg_contratos.sql`, `mart_escalada_custo.sql`, os três `int_contratos_evolucao_*.sql`, e os gráficos `escalada-custo.ts`/`contratos-temporal.ts`/`concentracao-fornecedor.ts` da spec 012. O adendo de 2026-08-21 (REQ-11/REQ-12) alterou também `int_concentracao_fornecedor_por_orgao.sql`/`int_concentracao_fornecedor_estado.sql` e a legenda de `concentracao-fornecedor.ts`.

## Status

Levantamento concluído, Design fechado, implementado e validado (2026-08-20; Caso de borda 7 revisto e fechado em 2026-08-21). Confirma que `CT-00269/2022` (achado original, R$ 23,6 bi de `vl_original` contra R$ 5,39 milhões de `vl_atual`) **não é um caso isolado** — é o maior de um grupo de **146 linhas** com valor implausível, distribuído em **três padrões distintos** de corrupção, nenhum deles coberto por `fl_aditivo_inconsistente`. Sozinhas, **8 dessas linhas somam 52,3% de todo o `vl_original` do dataset** (76.041 linhas).

`fl_valor_suspeito` implementada em `stg_contratos` (146/76.041 linhas, contagem confirmada pós-build). `mart_escalada_custo` expõe a coluna; `mart_contratos_temporal` exclui as 146 linhas do `SUM()` nos três `int_contratos_evolucao_*` (grão agregado não permite filtro depois). `mart_concentracao_fornecedor` inicialmente **não recebeu tratamento** (pendência registrada no Caso de borda 7) — decisão revista em 2026-08-21: investigação confirmou que não havia bloqueio técnico (mesma técnica já validada em `mart_contratos_temporal`, só não implementada por decisão de escopo da spec de levantamento) e que o impacto era material (ranking #1 estadual sustentado por uma única linha corrompida); ver Design e REQ-11/REQ-12.

## Contexto

Achado original, durante implementação do frontend (spec 012): `CT-00269/2022` responde por ~97% de um pico de -R$ 25 bi na agregação de `vl_variacao` em outubro/2022, e não é pego pelo filtro `fl_aditivo_inconsistente` (é `NULL` nessa linha — o filtro cobre inconsistência de *aditivo*, não de valor absurdo em si). Antes de decidir qualquer tratamento no frontend, esta spec quantifica a extensão real do problema no dataset inteiro.

## Investigação

### 1. Distribuição geral de `vl_original`

```sql
select
    percentile_cont(0.5) within group (order by vl_original) as mediana,
    percentile_cont(0.99) within group (order by vl_original) as p99,
    max(vl_original) as maximo,
    avg(vl_original) as media,
    count(*) as total_linhas
from staging.stg_contratos
where vl_original is not null;
```

```
 mediana  |        p99         |     maximo     |        media         | total_linhas
----------+--------------------+----------------+----------------------+--------------
 21717.36 | 10918349.124000136 | 23602153155.36 | 1319016.785619862969 |        76041
```

Mediana R$ 21,7 mil, p99 R$ 10,9 milhões — mas a **média** já é R$ 1,3 milhão, 60x a mediana, puxada por outliers. O máximo (R$ 23,6 bi) é `CT-00269/2022`, mais de 2.000x o p99.

### 2. Candidatos a outlier: valor absoluto extremo ou razão `vl_original`/`vl_atual` extrema

```sql
select nu_contrato, cod_unidade_gestora, nm_contratado, vl_original, vl_atual,
       vl_original / nullif(vl_atual, 0) as razao_original_sobre_atual
from staging.stg_contratos
where vl_original > 1000000000
   or vl_original / nullif(vl_atual, 0) > 100
order by vl_original desc
limit 50;
```

50 linhas retornadas (limite da query), amostra do topo:

```
      nu_contrato      | cod_unidade_gestora |                nm_contratado                | vl_original    |    vl_atual    | razao
-----------------------+---------------------+----------------------------------------------+----------------+----------------+---------
 CT-00269/2022         | 530001              | Fraga Construções e Engenharia LTDA           | 23602153155.36 |     5390370.02 |   4378.58
 2024CT010186          | 540091              | PIATA COMERCIO DE PECAS LTDA                  | 10495768960.16 | 10495768960.16 |      1.00
 2022CT005403          | 540096              | VS - VIDA SAUDAVEL SOLUCOES EM REFEICOES COL. |  6476368432.60 |  6476368432.60 |      1.00
 2020CT004866          | 530001              | CLARO S A                                     |  6270672958.20 |  6270672958.20 |      1.00
 2025CT003501          | 160085              | FUNCIONAL TECHNOLOGICAL GARMENT LTDA          |  4466572036.67 |  4466169772.55 |      1.00
 2016CT006428          | 530023              | WF5 SOLUCOES LTDA                             |  1172160000.00 |      566102.86 |   2070.58
 2021CT002172          | 450001              | EDINO VENDRAMI                                |   352252209.59 |      276818.16 |   1272.50
 ... (mais 43 linhas, razão de 100x a 1573x, valores de R$ 1,16 bi a R$ 349 mil)
```

Contagem exata por critério (a query acima tem `limit 50`, então não basta contar as linhas retornadas):

```sql
select
    count(*) filter (where vl_original > 1000000000) as acima_1bi,
    count(*) filter (where vl_original / nullif(vl_atual, 0) > 100) as razao_acima_100,
    count(*) filter (where vl_original > 1000000000
                        or vl_original / nullif(vl_atual, 0) > 100) as uniao,
    count(*) filter (where vl_original > 1000000000
                        and abs(vl_original / nullif(vl_atual,0) - 1) < 0.01) as acima_1bi_com_atual_tambem_alto
from staging.stg_contratos
where vl_original is not null;
```

```
 acima_1bi | razao_acima_100 | uniao | acima_1bi_com_atual_tambem_alto
-----------+-----------------+-------+---------------------------------
         6 |             140 |   144 |                               4
```

**144 linhas** (0,19% de 76.041) cruzam pelo menos um dos dois limiares. Dos 6 acima de R$ 1 bi, **4 têm `vl_atual` igual ao `vl_original`** (razão ≈ 1 — os dois campos "explodiram" juntos, não é o mesmo padrão de `CT-00269/2022`, onde só `vl_original` é absurdo).

### 3. `vl_atual` também tem outliers — critério separado, dois casos novos

```sql
select percentile_cont(0.5) within group (order by vl_atual) as mediana,
       percentile_cont(0.99) within group (order by vl_atual) as p99,
       max(vl_atual) as maximo
from staging.stg_contratos where vl_atual is not null;
```

```
 mediana |        p99         |     maximo
---------+--------------------+----------------
 14455.2 | 10698549.976000458 | 10495768960.16
```

```sql
select nu_contrato, cod_unidade_gestora, nm_contratado, vl_original, vl_atual
from staging.stg_contratos
where vl_atual > 500000000
order by vl_atual desc limit 20;
```

```
 nu_contrato  | cod_unidade_gestora |                nm_contratado                | vl_original |    vl_atual
--------------+---------------------+----------------------------------------------+-------------+----------------
 2024CT010186 | 540091              | PIATA COMERCIO DE PECAS LTDA                  | 10495768960.16 | 10495768960.16  (já contado acima)
 2022CT005403 | 540096              | VS - VIDA SAUDAVEL SOLUCOES...                |  6476368432.60 |  6476368432.60  (já contado acima)
 2020CT004866 | 530001              | CLARO S A                                     |  6270672958.20 |  6270672958.20  (já contado acima)
 2025CT003501 | 160085              | FUNCIONAL TECHNOLOGICAL GARMENT LTDA          |  4466572036.67 |  4466169772.55  (já contado acima)
 2024CT009399 | 160084              | LOCALIZA VEICULOS ESPECIAIS S A               |     1808987.62 |  3759480538.23  (NOVO)
 2022CT000743 | 160020              | TECPRINTERS TECNOLOGIA DE IMPRESSAO LTDA      |     2557104.29 |  1014331960.06  (NOVO)
```

Só 6 linhas cruzam este limiar; 4 já estavam no grupo do item 2. **2 linhas novas** (`2024CT009399`, `2022CT000743`) têm `vl_original` normal e `vl_atual` absurdo — padrão inverso do original. Esse padrão não aparece no item 2 porque a razão ali é `original/atual` (fica pequena, não grande, quando é `atual` que explode) — critério unidirecional não pega os dois sentidos.

**Total de linhas distintas cruzando qualquer um dos três critérios: 146** (144 do item 2 + 2 novas do item 3).

### 4. Três padrões distintos, confirmados por inspeção dos casos extremos

| Padrão | Descrição | Exemplos confirmados |
|---|---|---|
| A — só `vl_original` explode | `vl_original` >> `vl_atual`, razão de 100x a 4.378x | `CT-00269/2022` (4.378x), `2016CT006428`/WF5 (2.070x), e mais 138 linhas menores (razão 100x–1.573x) |
| B — os dois campos explodem juntos | `vl_original` ≈ `vl_atual`, ambos na casa de bilhões | `2024CT010186`/Piata (R$ 10,50 bi), `2022CT005403`/VS (R$ 6,48 bi), `2020CT004866`/Claro (R$ 6,27 bi), `2025CT003501`/Functional (R$ 4,47 bi) |
| C — só `vl_atual` explode | `vl_atual` >> `vl_original`, inverso do padrão A | `2024CT009399`/Localiza (R$ 3,76 bi), `2022CT000743`/Tecprinters (R$ 1,01 bi) |

São mecanismos de corrupção diferentes — um tratamento que só olhe `vl_original` (como o achado original sugeria) deixaria passar os padrões B e C inteiros.

### 5. `fl_aditivo_inconsistente` não cobre nenhuma das 146 linhas

```sql
select fl_aditivo_inconsistente, count(*) as n
from staging.stg_contratos
where vl_original > 1000000000
   or vl_original / nullif(vl_atual, 0) > 100
   or vl_atual > 500000000
group by fl_aditivo_inconsistente order by n desc;
```

```
 fl_aditivo_inconsistente |  n
--------------------------+-----
   (NULL)                 | 146
```

**100% das 146 linhas têm o flag `NULL`.** Confirma o achado original: não é que o flag falhe em detectar — ele é estruturalmente cego a este problema (é calculado a partir de comparação com aditivos, e essas linhas não necessariamente têm aditivo problemático). Para contexto, o flag na tabela inteira:

```sql
select fl_aditivo_inconsistente, count(*) from staging.stg_contratos group by 1;
```

```
 fl_aditivo_inconsistente | count
--------------------------+-------
 f                        |   976
 t                        |   975
   (NULL)                 | 74090
```

### 6. Impacto em `mart_escalada_custo` — outliers dominam os dois extremos do ranking

```sql
select nu_contrato, cod_unidade_gestora, nm_contratado, vl_original, vl_atual, vl_variacao, perc_variacao,
       rank() over (order by vl_variacao asc) as rank_queda,
       rank() over (order by vl_variacao desc) as rank_alta
from marts.mart_escalada_custo
where nu_contrato in ('CT-00269/2022','2024CT010186','2022CT005403','2020CT004866',
                       '2025CT003501','2016CT006428','2024CT009399','2022CT000743');
```

```
  nu_contrato  |                nm_contratado           |   vl_variacao    | rank_queda | rank_alta
---------------+------------------------------------------+------------------+------------+-----------
 CT-00269/2022 | Fraga Construções e Engenharia LTDA       | -23596762785.34 |          1 |         8
 2016CT006428  | WF5 SOLUCOES LTDA                         |  -1171593897.14 |          2 |         7
 2025CT003501  | FUNCIONAL TECHNOLOGICAL GARMENT LTDA      |      -402264.12 |          3 |         6
 2022CT005403  | VS - VIDA SAUDAVEL...                     |             0.00 |          4 |         3
 2020CT004866  | CLARO S A                                  |             0.00 |          4 |         3
 2024CT010186  | PIATA COMERCIO DE PECAS LTDA               |             0.00 |          4 |         3
 2022CT000743  | TECPRINTERS TECNOLOGIA DE IMPRESSAO LTDA   |   1011774855.77 |          7 |         2
 2024CT009399  | LOCALIZA VEICULOS ESPECIAIS S A            |   3757671550.61 |          8 |         1
```

Os **8 primeiros lugares em ambos os extremos** (maior queda e maior alta de `vl_variacao`) do dataset inteiro são as 8 linhas outlier identificadas — não sobra nenhum contrato real no topo do ranking hoje.

### 7. Impacto em `mart_contratos_temporal` — dominância mês a mês

Cada uma das 8 linhas outlier cai em um mês/ano diferente. Comparando o total mensal (`tp_recorte='Geral'`) com o valor da própria linha:

```sql
select ano_assinatura, mes_assinatura, qt_contratos, vl_total_original, vl_total_atual, vl_total_variacao
from marts.mart_contratos_temporal
where tp_recorte = 'Geral'
  and (ano_assinatura,mes_assinatura) in
      ((2016,3),(2020,7),(2020,10),(2022,9),(2022,10),(2024,9),(2024,10),(2025,5));
```

```
 ano  | mes | qt_contratos | vl_total_original | vl_total_atual  | vl_total_variacao
------+-----+--------------+--------------------+-----------------+-------------------
 2016 |   3 |          468 |     1508117790.04 |    440779300.98 |    -1067338489.06
 2020 |   7 |          343 |      189907575.26 |   1214486364.40 |     1024578789.14
 2020 |  10 |          680 |     6771593108.37 |   6564736296.85 |     -206856811.52
 2022 |   9 |          889 |     7409223626.78 |   7446597358.16 |       37373731.38
 2022 |  10 |          508 |    24446455680.21 |    850838536.03 |   -23595617144.18
 2024 |   9 |          638 |      496554364.98 |   4295931507.37 |     3799377142.39
 2024 |  10 |          679 |    11153739483.95 |  11175100670.92 |       21361186.97
 2025 |   5 |         1272 |     4914289344.99 |   4926799657.15 |       12510312.16
```

% do total mensal que é uma única linha outlier: 2016/03 = 77,7% (WF5, sobre `vl_original`); 2020/07 = 83,5% (Tecprinters, sobre `vl_atual`); 2020/10 = 92,6% (Claro, `vl_original`); 2022/09 = 87,4% (VS, ambos campos); 2022/10 = 96,5% (`CT-00269/2022`, `vl_original`); 2024/09 = 87,5% (Localiza, `vl_atual`); 2024/10 = 94,1% (Piata, ambos campos); 2025/05 = 90,9% (Functional, `vl_original`).

Caso mais grave, **2022/10**: removendo `CT-00269/2022` do total do mês, `vl_total_original` cai para R$ 844.302.524,85 e `vl_total_atual` para R$ 845.448.166,01 — `vl_total_variacao` real seria **+R$ 1.145.641,16 (positivo)**, não os -R$ 23,6 bi mostrados hoje. Uma única linha inverte o sinal do mês inteiro.

### 8. Impacto em `mart_concentracao_fornecedor` — 6 dos 10 maiores fornecedores do estado são artefato

```sql
select distinct nm_contratado, vl_total_fornecedor_estado, rank_estado, perc_sobre_total_estado
from marts.mart_concentracao_fornecedor
where rank_estado <= 10 order by rank_estado;
```

```
                nm_contratado                    | vl_total_fornecedor_estado | rank_estado | perc_estado
--------------------------------------------------+----------------------------+--------------+-------------
 PIATA COMERCIO DE PECAS LTDA                     |             10498765947.45 |            1 |       13.17
 VS - VIDA SAUDAVEL SOLUCOES EM REFEICOES COL.    |              6478097012.72 |            2 |        8.13
 CLARO S A                                        |              6313609487.92 |            3 |        7.92
 FUNCIONAL TECHNOLOGICAL GARMENT LTDA             |              4523420622.68 |            4 |        5.68
 LOCALIZA VEICULOS ESPECIAIS S A                  |              3770500698.19 |            5 |        4.73
 CENTRO DE INFORMATICA E AUTOMACAO DO ESTADO SC   |              2139529129.79 |            6 |        2.68
 PLANATERRA - TERRAPLENAGEM E PAVIMENTAÇÃO LTDA   |              1370194701.86 |            7 |        1.72
 TECPRINTERS TECNOLOGIA DE IMPRESSAO LTDA         |              1152483989.89 |            8 |        1.45
 SEPAT MULTI SERVICE LTDA                         |              1080638248.01 |            9 |        1.36
 ORBENK ADMINISTRACAO E SERVICOS LTDA             |              1076776753.46 |           10 |        1.35
```

Posições **1, 2, 3, 4, 5 e 8** do ranking estadual de fornecedores são exatamente as 6 empresas com contrato outlier identificado acima. Inspecionando `PIATA COMERCIO DE PECAS LTDA` por órgão (`rank_no_orgao`), a empresa é irrelevante em quase todos os órgãos onde de fato contrata (`rank_no_orgao` 33, 138, 34, 183, 1049, 226...) — o rank #1 estadual existe *inteiramente* por causa de uma linha em um único órgão (`540091`).

### 9. Achado colateral: limiares usados são conservadores — há outliers abaixo deles

Investigando por que `CENTRO DE INFORMATICA E AUTOMACAO DO ESTADO DE SC S A` (rank #6, R$ 2,14 bi) não apareceu em nenhuma das listas acima:

```sql
select nu_contrato, cod_unidade_gestora, vl_original, vl_atual
from staging.stg_contratos
where nm_contratado ilike '%CENTRO DE INFORMATICA E AUTOMACAO%'
order by vl_original desc limit 5;
```

```
 nu_contrato  | cod_unidade_gestora | vl_original  |   vl_atual
--------------+---------------------+--------------+--------------
 2020CT003997 | 470022              | 398608678.40 | 398608678.40
 2022CT002080 | 440022              | 307934520.00 |         0.00
 ...
```

`2020CT003997` (R$ 398,6 milhões, razão original/atual = 1 — mesmo padrão B) fica **abaixo dos dois limiares usados** (R$ 1 bi absoluto, R$ 500 milhões para `vl_atual`), mas ainda é ~18.000x a mediana de `vl_original`. **As 146 linhas do item 3 são um piso, não a extensão completa do problema** — o limiar de R$ 1 bi / R$ 500 milhões foi escolhido para isolar os casos mais extremos rapidamente, não para capturar toda a causa raiz.

### 10. Magnitude agregada: 8 linhas = 52% do dataset inteiro

```sql
select sum(vl_original) as soma_total,
       sum(vl_original) filter (where nu_contrato in
           ('CT-00269/2022','2024CT010186','2022CT005403','2020CT004866',
            '2025CT003501','2016CT006428','2024CT009399','2022CT000743')) as soma_8_outliers,
       round(100.0 * sum(vl_original) filter (where nu_contrato in (...)) / sum(vl_original), 2) as pct
from staging.stg_contratos where vl_original is not null;
```

```
     soma_total       |   soma_8_outliers   | pct
-----------------------+----------------------+-------
     100299355395.32   |      52488061634.90 | 52.33
```

**8 linhas em 76.041 (0,01% das linhas) somam 52,33% do `vl_original` de todo o dataset.** Qualquer métrica agregada que some `vl_original`/`vl_atual` sem tratar esses casos está, na prática, reportando o ruído de 8 linhas como se fosse o total de contratos públicos de SC.

### 11. Inspeção manual do padrão B (decisão de tratamento)

Os 4 contratos do padrão B (item 4) — `vl_original` ≈ `vl_atual`, ambos na casa de bilhões — não são pegos por nenhum teste de razão (razão ≈ 1). Inspecionados linha a linha contra `nu_contrato`, `nm_unidade_gestora`, `nm_contratado`, `ds_objeto`, `dt_assinatura`/`dt_fim`, `nm_modalidade`:

```sql
select nu_contrato, cod_unidade_gestora, nm_unidade_gestora, nm_contratado,
       ds_objeto, dt_assinatura, dt_inicio, dt_fim, vl_original, vl_atual,
       nm_modalidade
from staging.stg_contratos
where nu_contrato in ('2024CT010186','2022CT005403','2020CT004866','2025CT003501');
```

| `nu_contrato` | Fornecedor | Valor | Objeto | Decisão | Razão |
|---|---|---|---|---|---|
| `2020CT004866` | Claro S A | R$ 6,27 bi | Serviço móvel pessoal (SMP) pós-pago + comodato de aparelhos, para a Secretaria de Infraestrutura e Mobilidade | **Suspeito** | Contrato de telefonia móvel institucional, por maior que seja, não chega à casa de bilhões — mesmo contratos estaduais de telecom de grande porte ficam em dezenas/centenas de milhões |
| `2024CT010186` | Piata Comercio de Pecas | R$ 10,50 bi | Registro de preços (aquisição futura e eventual) de materiais de construção civil para unidades prisionais de uma única regional (Regional Norte) | **Suspeito** | R$10,5 bi para material de construção de uma única regional prisional seria um dos maiores contratos públicos do Brasil; é "eventual", não firme, incompatível com o valor |
| `2022CT005403` | VS Vida Saudavel Solucoes | R$ 6,48 bi | Alimentação/nutrição para um único presídio (Presídio Regional de Rio do Sul), 3 anos | **Suspeito** | R$6,48 bi em 3 anos para alimentar um único presídio implicaria um custo per capita absurdo — ordem de grandeza incompatível com o objeto |
| `2025CT003501` | Functional Technological Garment | R$ 4,47 bi | Registro de preços de uniformes para Bombeiros Comunitários, 1 ano | **Suspeito** | R$4,47 bi para uniformes de uma corporação comunitária é incompatível em qualquer ordem de grandeza razoável |

**Decisão: as 4 linhas são suspeitas.** Nenhuma tem objeto/órgão/modalidade compatível com um contrato genuíno na casa de bilhões (obra de infraestrutura real, PPP) — todas são serviços/bens rotineiros (telecom, material de construção, alimentação, uniforme) para um único órgão ou regional, incompatíveis em ordem de grandeza com o valor registrado. Diferente do padrão A/C (testável por limiar), o padrão B fica como lista fechada desses 4 `nu_contrato` — não generalizável sem mais uma spec de levantamento (ver Caso de borda 5, ainda não resolvido).

## Requirements

### Funcionais

- REQ-1: O sistema DEVE sinalizar `fl_valor_suspeito = true` em `stg_contratos` quando `vl_original / vl_atual > 100` (padrão A).
- REQ-2: O sistema DEVE sinalizar `fl_valor_suspeito = true` quando `vl_atual > R$ 500.000.000` e `|vl_original / vl_atual - 1| >= 0.01` (padrão C — exclui o padrão B, que também tem `vl_atual` alto mas razão ≈ 1).
- REQ-3: O sistema DEVE sinalizar `fl_valor_suspeito = true` para os 4 `nu_contrato` do padrão B confirmados na inspeção manual do item 11 (`2024CT010186`, `2022CT005403`, `2020CT004866`, `2025CT003501`).
- REQ-4: O sistema DEVE retornar `fl_valor_suspeito = null` quando `vl_original` ou `vl_atual` for nulo (sem base pra julgar).
- REQ-5: `mart_escalada_custo` DEVE expor `fl_valor_suspeito` como coluna de contexto (grão de contrato permite), sem filtrar internamente — decisão de uso fica com quem consome.
- REQ-6: `mart_contratos_temporal` DEVE excluir linhas com `fl_valor_suspeito = true` do `SUM()` dentro dos três `int_contratos_evolucao_*` (grão já agregado ali, filtro depois é impossível).
- REQ-7: O gráfico `escalada-custo` (spec 012) DEVE excluir contratos com `fl_valor_suspeito = true` da agregação exibida, combinando a contagem de exclusão com a já existente de `fl_aditivo_inconsistente` numa única mensagem de legenda.
- REQ-8: O gráfico `contratos-temporal` (spec 012) DEVE atualizar sua legenda para refletir que a exclusão por valor implausível já ocorre na camada de dado (REQ-6), distinguindo-a da exclusão por aditivo (ainda pendente, achado do adendo da spec 012).
- REQ-9: Todo valor monetário exibido nos gráficos da spec 012 (eixos, tooltip, texto) DEVE usar formatação brasileira (`Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })` ou equivalente).
- REQ-11 *(adicionado 2026-08-21, fecha o Caso de borda 7)*: `int_concentracao_fornecedor_por_orgao` e `int_concentracao_fornecedor_estado` DEVEM excluir linhas com `fl_valor_suspeito = true` do `SUM(vl_atual)`, mesmo padrão de REQ-6 (grão já agregado por fornecedor, filtro depois é impossível).
- REQ-12 *(adicionado 2026-08-21)*: O gráfico `concentracao-fornecedor` (spec 012) DEVE ter legenda informando que a exclusão por valor implausível (REQ-11) já ocorre na camada de dado, mesmo padrão de REQ-8.

### Não-funcionais

- REQ-10: A documentação (`schema.yml`) de `fl_valor_suspeito` DEVE registrar os critérios exatos e a lista fechada do padrão B, no mesmo padrão de documentação já usado para `fl_aditivo_inconsistente`.

## Design

| Decisão | Racional |
|---|---|
| Padrão A/C via limiar (razão > 100x / `vl_atual` > R$500mi com razão distante de 1) | Generalizável, sem falso positivo identificado nas 142 linhas confirmadas |
| Padrão B via lista fechada de 4 `nu_contrato` | Razão ≈ 1 não é testável por limiar sem generalizar demais (contratos plurianuais genuínos também têm razão ≈ 1); inspeção manual por linha é a única forma segura de decidir sem falso positivo |
| Sinalizar, não corrigir o valor | Caso de borda 3 (não resolvido): não há heurística de casa decimal confiável para o padrão A (`CT-00269/2022`: razão 4.378x, não é 10x/100x/1000x limpo) — corrigir arriscaria trocar um valor errado por outro |
| `mart_escalada_custo`: coluna de contexto, sem filtro interno | Grão de contrato — mesmo padrão já usado para `fl_aditivo_inconsistente`, decisão de uso fica com o consumidor |
| `mart_contratos_temporal`: exclusão dentro do `SUM()` | Grão já agregado (ano/mês) nos `int_contratos_evolucao_*` — filtro client-side é estruturalmente impossível depois da agregação, mesma limitação já documentada pra `fl_aditivo_inconsistente` nesta mart |
| `mart_concentracao_fornecedor`: exclusão dentro do `SUM()` nos dois `int_concentracao_fornecedor_*` — **decisão revista em 2026-08-21** | Grão também já agregado (`SUM(vl_atual)` por fornecedor nos `int_concentracao_fornecedor_*`, antes da mart) — mesmo problema estrutural de `mart_contratos_temporal`, mesma técnica (REQ-6/REQ-11). Decisão original (2026-08-20) foi não implementar sem spec de Design própria (Caso de borda 7) — mas essa razão era de **escopo da spec de levantamento**, não bloqueio técnico: os dois `int_concentracao_fornecedor_*` leem `stg_contratos` direto (mesma estrutura de um nível só que `int_contratos_evolucao_*`), sem intermediário adicional perdendo granularidade antes. Investigação de 2026-08-21 mediu o impacto de manter a pendência: ranking estadual tinha `PIATA COMERCIO DE PECAS LTDA` em #1 (R$10,5 bi) sustentado por uma única linha `fl_valor_suspeito=true` (R$10.495.768.960,16 dos R$10.498.765.947,45 do total do fornecedor) — não havia justificativa pra manter dado corrompido determinando o #1 exibido publicamente. Aplicada a exclusão; `CENTRO DE INFORMATICA E AUTOMACAO DO ESTADO DE SC S A` assume #1 (R$2,14 bi), Piatã sai do top 15 |

### Componentes afetados

- `dbt/models/staging/stg_contratos.sql` — `fl_valor_suspeito` calculada (com. inline documentando os 3 padrões).
- `dbt/models/staging/schema/stg_contratos.yml` — documentação da coluna.
- `dbt/models/marts/mart_escalada_custo.sql` + `schema/marts_escalada_custo.yml` — coluna exposta.
- `dbt/models/intermediate/int_contratos_evolucao_anual.sql`, `int_contratos_evolucao_por_orgao.sql`, `int_contratos_evolucao_por_modalidade.sql` + `schema/int_contratos.yml` — exclusão antes do `SUM()`.
- `dbt/models/marts/schema/marts_temporal.yml` — nota sobre a exclusão upstream.
- `api/app/schemas/escalada_custo.py` — campo `fl_valor_suspeito` adicionado ao schema Pydantic (endpoint usa `SELECT *`, propaga automaticamente).
- `web/src/api-types.ts` — regenerado via `npm run generate-types` após restart da API.
- `web/src/charts/escalada-custo.ts` — filtro combinado (`fl_aditivo_inconsistente` + `fl_valor_suspeito`), legenda atualizada, formatação de moeda.
- `web/src/charts/contratos-temporal.ts` — legenda atualizada (exclusão já ocorre na camada de dado), formatação de moeda.
- `web/src/charts/concentracao-fornecedor.ts` — só formatação de moeda (rótulos do eixo rotacionados 30° pra não colidir — o formato completo pt-BR é mais longo que o padrão americano anterior).
- `web/src/charts/format.ts` (novo) — `formatarMoedaBRL()`, compartilhado pelos 3 gráficos com valor monetário (`diversidade-vencedores` não tem valor monetário, não foi alterado).
- `dbt/models/intermediate/int_concentracao_fornecedor_por_orgao.sql`, `int_concentracao_fornecedor_estado.sql` — exclusão pré-`SUM()` (REQ-11, adicionado 2026-08-21).
- `web/src/charts/concentracao-fornecedor.ts`, `web/index.html`, `web/src/main.ts` — legenda de exclusão adicionada (REQ-12, adicionado 2026-08-21).

## Casos de borda

Status atualizado em 2026-08-21 — 5 resolvidos por decisão de Design nesta spec (item 7 revisto em 2026-08-21), 2 seguem em aberto (registrados como pendência real, não como problema resolvido):

1. ~~Flag nova computada no dbt, no mesmo padrão de `fl_aditivo_inconsistente`, ou os três padrões exigem lógica diferente cada um?~~ **Resolvido:** `fl_valor_suspeito`, padrões A/C por limiar + padrão B por lista fechada (ver item 11, Requirements REQ-1 a REQ-4).
2. ~~Limiar estatístico ou lista de exclusão manual?~~ **Resolvido, híbrido:** limiar pros padrões A/C (generalizável, sem falso positivo nas 142 linhas confirmadas), lista fechada de 4 `nu_contrato` pro padrão B (razão ≈ 1 não é testável por limiar sem capturar contratos plurianuais genuínos).
3. ~~Corrigir o valor via heurística de casa decimal, ou só sinalizar?~~ **Resolvido: só sinalizar.** Nenhuma heurística de casa decimal confiável foi encontrada pro padrão A — risco de trocar um valor errado por outro. `fl_valor_suspeito` não altera `vl_original`/`vl_atual`.
4. ~~Filtro na mart ou em staging?~~ **Resolvido, por mart:** `mart_escalada_custo` expõe a coluna (grão de contrato permite filtro no consumidor); `mart_contratos_temporal` e (desde 2026-08-21) `mart_concentracao_fornecedor` excluem antes do `SUM()` (grão agregado não permite depois) — ver item 7.
5. **Ainda em aberto.** Extensão completa do problema abaixo dos limiares usados (item 9, ex. `2020CT003997`, R$398,6 milhões) não foi mapeada — segue exigindo uma spec de levantamento própria, não coberta por esta implementação.
6. **Ainda em aberto.** Causa raiz na fonte (portal/SICOP) não foi investigada — `fl_valor_suspeito` sinaliza o sintoma no dataset já processado, não a causa no sistema de origem.
7. ~~`mart_concentracao_fornecedor` não recebeu tratamento — implementar sem spec de Design própria, ou manter como pendência de escopo?~~ **Resolvido em 2026-08-21** (registrado como pendência aberta em 2026-08-20, texto de investigação original abaixo mantido como histórico): investigação dedicada confirmou que a razão original para não implementar era de **escopo** (esta spec era de levantamento), não bloqueio técnico — `int_concentracao_fornecedor_por_orgao`/`_estado` leem `stg_contratos` direto e agregam num único nível, estrutura idêntica à já corrigida em `int_contratos_evolucao_*`. Impacto medido antes de decidir: o #1 do ranking estadual (`PIATA COMERCIO DE PECAS LTDA`, R$10,5 bi, achado do item 8) era sustentado por uma única linha `fl_valor_suspeito=true` de R$10.495.768.960,16. Decisão: aplicar a mesma exclusão (REQ-11) — Piatã sai do top 15, `CENTRO DE INFORMATICA E AUTOMACAO DO ESTADO DE SC S A` assume #1 com R$2,14 bi. Legenda do gráfico `concentracao-fornecedor` atualizada (REQ-12).

## Fora do escopo

- Corrigir o valor de `vl_original`/`vl_atual` das linhas sinalizadas (caso de borda 3).
- Determinar a causa raiz exata de cada padrão (A/B/C) no sistema de origem (caso de borda 6).
- Varredura sistemática abaixo dos limiares usados (caso de borda 5).
- ~~Tratamento de `mart_concentracao_fornecedor` — pendência registrada, não resolvida (caso de borda 7).~~ Implementado em 2026-08-21 (REQ-11/REQ-12) — deixa de ser "fora do escopo", ver Design e Caso de borda 7.
- Qualquer alteração em `fl_aditivo_inconsistente` ou no tratamento que ele já recebe (permanece como estava).

## Referências de código

- `dbt/models/staging/stg_contratos.sql` — `fl_aditivo_inconsistente` e `fl_valor_suspeito` (esta spec), lado a lado.
- `dbt/models/staging/schema/stg_contratos.yml` — documentação de `fl_valor_suspeito`.
- `dbt/models/marts/mart_escalada_custo.sql` + `schema/marts_escalada_custo.yml` — coluna exposta.
- `dbt/models/intermediate/int_contratos_evolucao_anual.sql`, `int_contratos_evolucao_por_orgao.sql`, `int_contratos_evolucao_por_modalidade.sql` + `schema/int_contratos.yml` — exclusão pré-`SUM()`.
- `dbt/models/marts/mart_contratos_temporal.sql` + `schema/marts_temporal.yml` — item 7, agregação mensal corrigida (sinal de 2022/10 confirmado revertido: -R$23,6bi → +R$1,15mi).
- `dbt/models/marts/mart_concentracao_fornecedor.sql`, `dbt/models/intermediate/int_concentracao_fornecedor_por_orgao.sql`, `int_concentracao_fornecedor_estado.sql` — item 8, ranking de fornecedores estava distorcido; corrigido em 2026-08-21 (REQ-11, caso de borda 7 resolvido).
- `web/src/charts/escalada-custo.ts`, `contratos-temporal.ts`, `concentracao-fornecedor.ts`, `format.ts` — frontend spec 012.
- `api/app/schemas/escalada_custo.py` — schema Pydantic com `fl_valor_suspeito`.

## Ver também

- [[012-eixo-frontend-biblioteca-grafico]] (contexto original do achado — pico de -R$ 25 bi na agregação de `vl_variacao`)
- [[007-marts-e-metricas]] (spec original das marts afetadas)
- [[008-qualidade-e-documentacao]] (spec original de `fl_aditivo_inconsistente`)
