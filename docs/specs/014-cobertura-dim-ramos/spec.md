# Spec 014 — Cobertura de `dim_ramos`

## Tipo

Decisão de arquitetura (a partir de levantamento prévio).

## Status

Decidida: mantida como está, com limite documentado.

## Resumo

A spec 013 registrou que `dim_ramos`/`fct_contratos_ramo`/`int_contratos_por_ramo` (classificação de contratos em ~18-19 categorias de "ramo de atividade" por palavra-chave em `ds_objeto`) é uma feature do pipeline legado sem cobertura em nenhuma spec 002-012. Esta spec traz o dado empírico de cobertura real, pedido antes de decidir se a feature é mantida, revisada ou descartada.

## Contexto

`int_contratos_por_ramo.sql` classifica cada contrato via `CASE WHEN lower(ds_objeto) LIKE '%palavra-chave%'` em 18 categorias nomeadas + `'Outros'` como fallback. Ver [[013-levantamento-dbt-legado]] para a cronologia de como essa feature chegou ao repo sem spec própria.

## Investigação

Query rodada contra `marts.dim_ramos` (materializado via `docker compose run --rm dbt build`, 76.041 contratos):

```
            ramo_atividade             | qt_contratos | perc_sobre_total_qt 
----------------------------------------+--------------+---------------------
 Outros                                 |        20289 |               26.68
 Alimentação                            |        10116 |               13.30
 Combustíveis e Energia                 |         8276 |               10.88
 Veículos e Manutenção                  |         8137 |               10.70
 Limpeza e Higiene                      |         6139 |                8.07
 Água e Saneamento                      |         3684 |                4.84
 Educação e Capacitação                 |         3623 |                4.76
 Material de Escritório e Equipamentos  |         3212 |                4.22
 Obras e Construção                     |         3105 |                4.08
 TI - Geral                             |         2150 |                2.83
 Locação de Imóveis                     |         1989 |                2.62
 Saúde e Medicamentos                   |         1589 |                2.09
 Segurança Pública                      |         1285 |                1.69
 Agropecuária                           |         1197 |                1.57
 TI - Licenciamento de Software         |          396 |                0.52
 Transporte e Logística                 |          342 |                0.45
 TI - Manutenção e Suporte              |          331 |                0.44
 Meio Ambiente e Recursos Hídricos      |          147 |                0.19
 TI - Desenvolvimento de Software       |           34 |                0.04
```

(19 linhas, soma = 76.041)

### Leitura

- **`Outros` = 26,68% do total** (20.289 de 76.041 contratos) — acima do limiar informal de 15-20% usado como sinal de "cobertura insuficiente pra confiar na classificação sem mais trabalho". Mais de 1 em cada 4 contratos não bate em nenhuma palavra-chave das 18 categorias.
- **Categorias com menor `qt_contratos`**: `TI - Desenvolvimento de Software` (34, 0,04%), `Meio Ambiente e Recursos Hídricos` (147, 0,19%), `TI - Manutenção e Suporte` (331, 0,44%). Não investigado nesta sessão se são raras de verdade (poucos contratos desse tipo existem) ou se a regra de `LIKE` é estreita demais (overfit) — as três têm listas de palavra-chave mais específicas que as categorias maiores (ex.: exige "desenvolvimento de software" ou "desenvolvimento de sistema" completos, não uma palavra solta).
- A sub-divisão de TI em 4 categorias (`TI - Geral`, `TI - Licenciamento`, `TI - Manutenção e Suporte`, `TI - Desenvolvimento de Software`) soma 2.911 contratos (3,83% do total) — desproporcional ao número de categorias dedicadas (4 de 18) frente a outras áreas de gasto maiores (ex.: Obras e Construção, uma só categoria, 3.105 contratos) que ficam menos detalhadas.

## Requirements

Não aplicável — decisão é de manter o comportamento existente, não de construir algo novo.

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| O que fazer com a cobertura de `dim_ramos` (26,68% em "Outros") | Manter como está — nenhuma mudança no `CASE WHEN` de `int_contratos_por_ramo.sql` | Custo de manutenção de uma lista de palavras-chave crescente não se paga frente ao valor marginal de reduzir "Outros" — não há fonte estruturada (CNAE ou equivalente) que tornaria a classificação confiável além de heurística de texto; expandir regras só empurra o problema, não resolve a causa (ausência de dado cadastral). |
| Como comunicar o limite | `description` explícita em `dim_ramos` no `schema.yml`, citando o percentual real e classificando a feature como heurística, não dado oficial | Consumidor da mart (dashboard, análise) precisa saber que "Outros" é limite conhecido, não erro nem lacuna a esconder |
| Descartar a feature | Rejeitada | A classificação já cobre 73% dos contratos com sinal útil (ex. Alimentação 13,3%, Combustíveis 10,9%) — descartar perderia valor real pra evitar um limite já documentável |

### Componentes afetados

- `dbt/models/marts/schema/marts_ramos.yml` — `description` de `dim_ramos` atualizada com o percentual real e a ressalva de heurística (feito nesta sessão).
- Nenhuma mudança em `.sql` — decisão é de não alterar o `CASE WHEN`.

## Casos de borda

- Contratos com `ds_objeto` nulo ou vazio — não verificado nesta sessão se caem em `Outros` por ausência de match ou se são excluídos antes.
- Sobreposição de palavras-chave entre categorias (ex.: "manutenção" aparece tanto em `Veículos e Manutenção` quanto poderia in principle casar com `TI - Manutenção e Suporte` dependendo da ordem do `CASE WHEN`) — a ordem das cláusulas do `CASE` determina o resultado em textos ambíguos; não auditado.

## Fora do escopo

- Qualquer mudança no `CASE WHEN` de `int_contratos_por_ramo.sql` — decisão explícita desta spec é não alterar.
- Fonte de dado estruturada (CNAE ou equivalente) para substituir a heurística por texto — não avaliada nesta sessão; reabrir só se houver fonte concreta identificada.

## Referências de código

- `dbt/models/intermediate/int_contratos_por_ramo.sql`
- `dbt/models/marts/dim_ramos.sql`
- `dbt/models/marts/fct_contratos_ramo.sql`

## Ver também

- [[013-levantamento-dbt-legado]]
- [[007-marts-e-metricas]]
