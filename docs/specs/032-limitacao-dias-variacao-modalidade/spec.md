# Spec 032 — Ocultar relatório de variação de prazo do menu (revisão de REQ-9a)

## Tipo

Decisão de arquitetura — revisão de decisão anterior ([[025-navbar-paginas-relatorios]], REQ-9a).

## Status

Decidida e implementada em 2026-08-25.

## Resumo

O relatório "Variação de prazo" (`/relatorios/variacao-prazo-modalidade`) é removido do dropdown "Relatórios ▾" do navbar e do card correspondente na home. Rota, template e endpoint (`/api/v1/variacao-prazo-modalidade`) permanecem intactos e funcionais — acessíveis via URL direta, com o aviso de baixa cobertura já existente na página (REQ-9a da spec 025) mantido. Reverte a parte de REQ-9a que mantinha o relatório promovido nos pontos de entrada da navegação; não reverte o aviso em si.

## Contexto

A spec 025 (2026-08-21), achado "4a" da Investigação, já havia identificado que `dias_originais`/`dias_atuais` estão preenchidos em só ~7% dos contratos da fonte (Portal de Transparência), e que esses poucos contratos preenchidos caem quase todos em `nm_modalidade_norm = 'Não informado'` — nenhuma modalidade nomeada (Pregão Eletrônico, Dispensa, etc.) tinha uma linha sequer com `dias_variacao <> 0`. A decisão tomada na época (REQ-9a, confirmada com o usuário) foi implementar e manter o relatório visível mesmo assim, com aviso explícito de baixa cobertura na página.

Em 2026-08-25, uma investigação independente (sem consulta prévia à spec 025 no momento) chegou aos mesmos números exatos, o que confirma que o achado é estável — a fonte não passou a preencher esses campos entre 21/08 e 25/08. Essa estabilidade é o gatilho para revisar REQ-9a: um relatório cujo resultado é, na prática, sempre uma única linha ("Não informado") não cumpre a promessa do próprio título ("variação de prazo **por modalidade**") nem justifica ocupar um item de menu — decisão de produto: tirar da navegação até a fonte publicar `diasoriginais`/`diasatuais` de forma utilizável para as modalidades classificadas, sem apagar nada do código (reativação deve ser trivial quando/se isso acontecer).

## Investigação

Evidência re-confirmada em 2026-08-25, via `docker exec compras_postgres psql` (mesmo ambiente da spec 025).

### 1. Endpoint retorna hoje 1 única linha

```
curl -s http://localhost:8000/api/v1/variacao-prazo-modalidade
```

```json
[{"nm_modalidade":"Não informado","qt_contratos_com_aditivo_prazo":707,"dias_variacao_media":"202.7"}]
```

Comparado com `variacao-custo-modalidade` (mesma mart, mesmo padrão de query, filtro em `vl_variacao <> 0` em vez de `dias_variacao <> 0`), que retorna 18 modalidades distintas e ~38 mil contratos.

### 2. `dias_originais`/`dias_atuais` nunca preenchidos para contratos com modalidade classificada

```sql
SELECT
  count(*) AS total,
  count(diasoriginais) AS dias_originais_preenchido,
  count(diasatuais) AS dias_atuais_preenchido,
  count(*) FILTER (WHERE diasoriginais IS NOT NULL AND diasatuais IS NOT NULL AND diasatuais = diasoriginais) AS iguais,
  count(*) FILTER (WHERE diasoriginais IS NOT NULL AND diasatuais IS NOT NULL AND diasatuais <> diasoriginais) AS diferentes
FROM raw.contratos
WHERE nmmodalidade IS NOT NULL AND nmmodalidade <> '';
```

```
 total | dias_originais_preenchido | dias_atuais_preenchido | iguais | diferentes
-------+---------------------------+-------------------------+--------+------------
 70534 |                         0 |                       0 |      0 |          0
```

Nenhum dos 70.534 contratos com modalidade classificada tem `diasoriginais`/`diasatuais` preenchidos.

### 3. Os campos só existem no bloco de contratos sem classificação nenhuma

```sql
SELECT
  count(*) AS total,
  count(diasoriginais) AS dias_originais_preenchido,
  count(diasatuais) AS dias_atuais_preenchido,
  count(*) FILTER (WHERE diasoriginais IS NOT NULL AND diasatuais IS NOT NULL AND diasatuais = diasoriginais) AS iguais,
  count(*) FILTER (WHERE diasoriginais IS NOT NULL AND diasatuais IS NOT NULL AND diasatuais <> diasoriginais) AS diferentes
FROM raw.contratos
WHERE nmmodalidade IS NULL OR nmmodalidade = '';
```

```
 total | dias_originais_preenchido | dias_atuais_preenchido | iguais | diferentes
-------+---------------------------+-------------------------+--------+------------
  5507 |                      2141 |                    5424 |   1263 |        877

```

Dos 5.507 contratos sem `nmmodalidade` (que também não têm `detipocontrato`/`detipodocumentolegal` preenchidos — bloco de registros sem classificação nenhuma, espalhado por várias unidades gestoras, não concentrado num único órgão), 877 têm `diasatuais <> diasoriginais`. São exatamente os 877 que, na mart (`mart_escalada_custo`), caem em `nm_modalidade_norm = 'Não informado'` via `coalesce(nm_modalidade, 'Não informado')`; após os filtros de qualidade (`fl_aditivo_inconsistente`, `fl_valor_suspeito`) da mart, sobram os 707 retornados pela API.

### Leitura

Confirma achado 4a da spec 025 sem alteração — a query, a mart e o router estão corretos; a limitação é inteiramente da fonte. Não há bug a corrigir neste código.

## Requirements

### Funcionais

- REQ-1: O sistema DEVE remover o link "Variação de prazo" do dropdown "Relatórios ▾" em `layout.html`.
- REQ-2: O sistema DEVE remover o card "Variação de prazo" da seção "Relatórios" em `home.html`.
- REQ-3: O sistema DEVE manter a rota `/relatorios/variacao-prazo-modalidade`, o template `relatorio_variacao_prazo.html` e o endpoint `/api/v1/variacao-prazo-modalidade` funcionais e inalterados, para acesso direto por URL e reativação futura sem retrabalho.
- REQ-4: A página, quando acessada diretamente, DEVE manter o aviso de baixa cobertura já existente (REQ-9a da spec 025) — a decisão de tirar do menu não elimina a necessidade do aviso para quem chegar via link direto ou favorito salvo.

### Não-funcionais

- REQ-5: Esta spec DEVE ser referenciada a partir da spec 025 (seção "Ver também" ou nota equivalente) para manter rastreável que REQ-9a foi revisado, não simplesmente descumprido.

## Design

| Decisão | Racional |
|---|---|
| Ocultar do menu (navbar + home), não remover código | Rota "órfã" (sem link, mas funcional via URL direta) é suficiente e reversível — menor custo que apagar e reimplementar depois se a fonte publicar o dado; evita quebrar link já salvo por algum usuário |
| Manter o `warning-box` na própria página | Já resolve a preocupação de "usuário chega via URL direta sem contexto" (REQ-9a da spec 025) — mais simples que qualquer mecanismo novo de bloqueio/redirecionamento na rota |
| Remover também o card da home, não só o dropdown | Deixar o card na home seria inconsistente — o relatório continuaria promovido num ponto de entrada mesmo tirado do menu; a intenção ("ocultar até a fonte publicar dado utilizável") vale para todos os pontos de entrada, não só o navbar |
| Nova spec em vez de editar REQ-9a direto na spec 025 | Spec 025 é sobre navbar+3 relatórios novos (tema mais amplo); a reversão pontual fica mais rastreável como spec própria que referencia e revê REQ-9a explicitamente, mesmo padrão usado na spec 021 ao rever sua própria decisão em adendo datado |

### Componentes afetados

- `api/app/templates/layout.html` — remove o `<li>` do link "Variação de prazo" no dropdown Relatórios (linha 46 antes desta mudança).
- `api/app/templates/home.html` — remove o `<a class="list-row">` do card "Variação de prazo" (linhas 93-99 antes desta mudança).
- `api/app/templates/relatorio_variacao_prazo.html` — sem alteração (aviso já existente, REQ-9a, mantido).
- `api/app/routers/variacao_prazo_modalidade.py`, `api/app/main.py` — sem alteração (rota/endpoint permanecem registrados).

## Casos de borda

- Usuário com link direto salvo (`/relatorios/variacao-prazo-modalidade`) continua acessando a página normalmente, com o aviso de baixa cobertura visível — não é tratado como erro 404 nem redirecionado.
- Se a fonte (Portal de Transparência) passar a preencher `diasoriginais`/`diasatuais` para contratos com modalidade classificada, reativar exige só devolver os dois `<a>`/`<li>` removidos aqui — nenhuma mudança de backend/dbt necessária.

## Fora do escopo

- Qualquer alteração em `dbt/models/staging/stg_contratos.sql`, `mart_escalada_custo.sql` ou no endpoint — a limitação é de dado de origem, não de código (confirmado na Investigação).
- Investigar a causa raiz na fonte (Portal de Transparência/SICOP) de por que `diasoriginais`/`diasatuais` não são preenchidos para contratos classificados — mesmo tipo de pendência já registrada como fora de escopo na spec 021 (caso de borda 6, causa raiz na fonte).
- Mecanismo de detecção automática (ex.: reativar o menu sozinho quando a cobertura melhorar) — reativação é manual, decisão consciente quando/se a fonte mudar.

## Referências de código

- `api/app/templates/layout.html` — dropdown Relatórios ▾.
- `api/app/templates/home.html` — seção "Relatórios", cards `link-list`.
- `api/app/templates/relatorio_variacao_prazo.html` — `warning-box` (REQ-9a, spec 025, inalterado).
- `api/app/routers/variacao_prazo_modalidade.py` — endpoint inalterado.
- `dbt/models/marts/mart_escalada_custo.sql` — `dias_variacao`, `nm_modalidade_norm` (confirmados corretos, sem alteração).

## Ver também

- [[025-navbar-paginas-relatorios]] — achado 4a e REQ-9a, decisão original sendo revisada aqui.
- [[021-levantamento-outliers-valor-extremo]] — padrão de spec que revê sua própria decisão em adendo datado, mesmo padrão seguido aqui como spec separada.
