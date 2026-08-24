# Spec 031 — Fornecedor por segmento (gráfico + relatório)

## Tipo

Nova funcionalidade — gráfico "Fornecedor por segmento" e relatório "Fornecedor por segmento", reaproveitando a classificação heurística de ramo de atividade já existente (`fct_contratos_ramo`, spec 013/014), sem criar uma segunda fonte de classificação.

## Status

Implementado em 2026-08-24 (dbt + API + frontend), com dois achados reais adicionais durante a implementação, ambos corrigidos e documentados antes do commit: `dt_inicio` nullable (ver Investigação, REQ-8) e ausência de `fl_valor_suspeito` na mart (ver Investigação, REQ-16). Testado localmente (visual via Playwright/screenshots, `pytest` sem regressão, teste de carga real repetido contra a implementação final — ver Validação). Volume de produção (93.978 linhas) segue não reproduzível no ambiente de dev local (achado de ambiente documentado na Investigação, não resolvido por este trabalho).

## Resumo

Dois pontos de entrada sobre o mesmo dado (`marts.fct_contratos_ramo`, grão = contrato):

- **Gráfico**: agregado por (ramo, fornecedor) — top fornecedores dentro de um segmento.
- **Relatório**: listagem em grão de contrato, com filtro de segmento e busca por nome de fornecedor.

## Contexto

- Reaproveita `fct_contratos_ramo` (classificação por palavras-chave em `ds_objeto`, 18 ramos + "Outros", spec 013/014) — decisão consciente de não criar segunda classificação.
- **Nota de população (medida em 2026-08-24, banco `compras_publicas` do host, via `docker exec postgres psql`)**:

  | | linhas | "Outros" |
  |---|---|---|
  | `marts.fct_contratos_ramo` (grão contrato, filtra teste + `vl_original ≤ R$1.000`) | 93.978 | 28,47% |
  | `marts.dim_ramos` (agregado de `int_contratos_por_ramo`, sem esse filtro) | soma `qt_contratos` = 104.574 | 26,20% |

  Diferença real de **10.596 contratos (10,1%)** entre as duas fontes — maior que a estimativa do brief original ("26,68%" para Outros, população não quantificada). Esta nota de exclusão deve aparecer na UI do gráfico/relatório, mesmo padrão já usado para `fl_valor_suspeito` em outras páginas.
- **Primeira exposição de `fct_contratos_ramo`/ramo de atividade via API e frontend** — hoje nenhum router, schema Pydantic ou chart TS referencia "ramo". Não há precedente direto a copiar 1:1; o Design abaixo generaliza os padrões mais próximos (`qualidade_dado_orgao.py` para GROUP BY sem mart nova, `diversidade_vencedores.py`/`contratos_temporal.py` para grão-contrato em volume alto).

## Investigação

### Schema real de `fct_contratos_ramo` (dbt/models/marts/fct_contratos_ramo.sql + schema/marts_ramos.yml)

Colunas disponíveis — **divergem dos nomes assumidos no brief original**:

| Assumido no brief | Coluna real | Observação |
|---|---|---|
| `nucontrato` | `nu_contrato` | |
| `vlatual` | `vl_atual` | também há `vl_original`, `vl_aditado` |
| `dtinicio` | **não existe na mart** | existe em `stg_contratos.dt_inicio`, não selecionado |
| `dtfimatual` | **não existe na mart** | existe em `stg_contratos.dt_fim_atual`, não selecionado |
| `ano_assinatura` | `ano_assinatura` | confirmado, igual ao padrão do projeto |
| — | `id_contratado`, `nm_contratado`, `cod_unidade_gestora`, `nm_unidade_gestora`, `nm_modalidade`, `ds_objeto`, `dt_assinatura`, `ds_situacao`, `ramo_atividade` | já disponíveis |

**Implicação de Design**: o requirement do relatório ("período: início – fim atualizado") não é servível hoje. `fct_contratos_ramo.sql` precisa de 2 colunas novas (passthrough, sem mudar grão nem classificação): `dt_inicio` e `dt_fim_atual`, ambas já existentes em `stg_contratos`. Não é criação de segunda fonte — é completar a mart existente com colunas que faltam para este uso. Requer doc `schema/marts_ramos.yml` atualizado.

**Achado na implementação (2026-08-24, após adicionar as colunas)**: a premissa inicial de que ambas as colunas ganhariam teste `not_null` (como as demais colunas obrigatórias da mart) não se sustentou. `dt_inicio` tem NULLs reais na fonte — 80 de 67.656 linhas no ambiente local (0,12%), anos de assinatura variados (2014–2025, não concentrado em import recente), confirmado por amostra que são contratos legítimos, não lixo de import. Decisão: tratar `dt_inicio` como nullable, mesmo padrão já previsto para `dt_fim_atual` (ver Casos de borda) — nenhuma das duas colunas tem teste `not_null` na mart.

**Achado na implementação (2026-08-24, ao testar o endpoint de gráfico contra dado real)**: `fct_contratos_ramo` não tem a coluna `fl_valor_suspeito` (spec 021) — a mart foi criada em spec 013/014, antes de `fl_valor_suspeito` existir, e nunca herdou o filtro. Sem ele, o top 3 do endpoint agregado (`GROUP BY ramo_atividade, id_contratado, nm_contratado`, `ORDER BY vl_total DESC`) era dominado por 3 dos 4 contratos da lista fechada de corrupção de dado confirmada por inspeção manual (`stg_contratos.sql:134-139`): Piata Comercio de Pecas (R$10,50 bi), VS Vida Saudavel Solucoes (R$6,48 bi), Claro S A (R$6,31 bi) — não gasto real. Não coberto pelo requirement original (REQ-1 só previa somar `vl_atual`, sem menção a `fl_valor_suspeito`); só apareceu ao rodar contra dado real, não seria pego por revisão de código. Decisão: `fl_valor_suspeito` também vira passthrough na mart (mesmo padrão de `dt_inicio`/`dt_fim_atual`), com filtro `WHERE fl_valor_suspeito IS NOT TRUE` obrigatório nos dois endpoints — ver REQ-16.

### Volume (decide client-side vs server-side pagination)

```
SELECT COUNT(*) FROM marts.fct_contratos_ramo;                        -- 93978
SELECT COUNT(DISTINCT id_contratado) FROM marts.fct_contratos_ramo;   -- 15132
```
Maior segmento único ("Outros") = 26.758 linhas.

**Precedente no projeto** para volume nessa ordem de grandeza em grão-contrato, servido inteiro ao client:
- `diversidade_vencedores.py`: teto de segurança 200.000, volume real medido ~51.812 linhas. `Response`/`TypeAdapter`, sem OOM.
- `contratos_temporal.py`: teto 100.000, volume real ~10.810 linhas. `Response`/`TypeAdapter`, sem OOM.
- **`escalada_custo.py` — achado só na revisão do usuário, não na investigação inicial**: mesmo padrão `Response`/`TypeAdapter` **falhou** com `OOMKilled` sob container limitado a 512Mi (mesmo teto do pod em produção) na faixa de 76.041–95.508 linhas, com `SELECT *` sobre `mart_escalada_custo` (~19 colunas: strings, decimais, datas, booleanos). Precisou virar `StreamingResponse` com cursor nomeado server-side (`fetchmany` em lotes de 2.000), documentado no próprio código como fix do incidente de OOM em produção de 2026-08-21.
- Isso muda a conclusão inicial: **93.978 linhas (volume deste relatório) está acima da faixa que já quebrou** (76.041–95.508) usando `Response`/`TypeAdapter` simples — não dava para decidir por analogia com `diversidade_vencedores`/`contratos_temporal` sem medir.

**Decisão, após medição real (ver Validação abaixo)**: `Response`/`TypeAdapter` sem streaming, com `SELECT` explícito e estreito (as 5 colunas de REQ-3, não `SELECT *`), sobrevive a 93.978 linhas sob 512Mi — payload de 11,55MB, pico de 127MiB (24,84% do limite), sem OOM em 1 requisição nem em 50 sequenciais. A causa do OOM em `escalada_custo` parece ser mais o peso por linha (`SELECT *`, ~19 colunas) do que a contagem de linhas isolada. Mesmo assim, **REQ-7 abaixo exige o `SELECT` estreito como parte do requirement**, não como detalhe de implementação livre — se o escopo crescer (mais colunas), o teto de 512Mi precisa ser revalidado antes do merge. Paginação de exibição continua client-side via `criarPaginador` (15 linhas, "Ver mais"). **Não** introduzir `LIMIT`/`OFFSET` real no backend.

### Padrão de agregação sem mart nova

`api/app/routers/qualidade_dado_orgao.py` agrega direto via SQL (`GROUP BY`/`FILTER`) em cima de uma mart de grão-contrato já existente, sem model dbt intermediário dedicado. Mesmo padrão se aplica aqui: o endpoint de gráfico agrega `fct_contratos_ramo` por `(ramo_atividade, id_contratado, nm_contratado)` direto no router — **sem novo model dbt**.

### Busca por nome — padrão novo no frontend

Nenhuma página hoje tem campo de busca por texto livre — todos os filtros existentes são `<select>` (`web/src/charts/filtros.ts`, evento `change`). O campo de busca por fornecedor é o **primeiro input de texto livre do projeto**; precisa de debounce (ex. 300ms) antes de disparar novo fetch, para não bater a API a cada tecla. Novo helper a criar em `filtros.ts` ou arquivo próprio — decisão de nome/local fica para a implementação.

## Requirements

### Funcionais

- REQ-1: Quando o usuário acessar `/graficos/fornecedor-por-segmento`, o sistema DEVE agregar `marts.fct_contratos_ramo` por `(ramo_atividade, id_contratado, nm_contratado)`, somando `vl_atual`, ordenado por valor decrescente — mesmo padrão visual de `concentracao-fornecedor` (barra horizontal, top N).
- REQ-2: O gráfico DEVE aceitar filtro de segmento via dropdown (18 ramos + "Outros"); ao selecionar um segmento, o gráfico DEVE mostrar o top N fornecedores daquele segmento.
- REQ-3: Quando o usuário acessar `/relatorios/fornecedor-por-segmento`, o sistema DEVE listar contratos individuais (grão = contrato) com colunas: nome do fornecedor, número do contrato (`nu_contrato`), valor atual (`vl_atual`), período (`dt_inicio` – `dt_fim_atual`).
- REQ-4: O relatório DEVE aceitar filtro de segmento (dropdown) e busca por nome de fornecedor (texto livre, case-insensitive, correspondência parcial via `ILIKE`), aplicáveis em conjunto ou isoladamente.
- REQ-5: O relatório DEVE paginar a exibição em 15 linhas por página com botão "Ver mais", igual ao padrão já estabelecido (`criarPaginador`).
- REQ-6: Tanto o gráfico quanto o relatório DEVEM exibir a nota de população — `fct_contratos_ramo` exclui contratos de teste e valor original ≤ R$1.000 — mesmo padrão de nota já usado para `fl_valor_suspeito`.

### Não-funcionais

- REQ-7: O endpoint de listagem (relatório) DEVE usar `Response` + `TypeAdapter(...).dump_json(...)` em vez de `response_model=list[...]`, seguindo o padrão de `diversidade_vencedores.py`/`contratos_temporal.py`, para evitar repetição do incidente de OOM de 2026-08-21. O `SELECT` DEVE ser explícito e limitado às colunas de REQ-3 (não `SELECT *`) — a validação de volume (ver Validação) só cobre esse conjunto estreito de colunas; qualquer coluna adicional exige repetir o teste de carga sob 512Mi antes do merge, dado que `escalada_custo.py` já quebrou com esse mesmo padrão não-streaming em volume comparável usando `SELECT *`.
- REQ-8: `fct_contratos_ramo.sql` DEVE ganhar as colunas `dt_inicio` e `dt_fim_atual` (passthrough de `stg_contratos`, sem alterar grão nem a lógica de classificação existente), documentadas em `schema/marts_ramos.yml`. Nenhuma das duas colunas leva teste `not_null` — ambas podem ser nulas na fonte (achado real para `dt_inicio`, ver Investigação; já previsto para `dt_fim_atual`); tratamento de UI é "período em aberto" (ver Casos de borda), não erro.
- REQ-16: `fct_contratos_ramo.sql` DEVE ganhar a coluna `fl_valor_suspeito` (passthrough de `stg_contratos`, spec 021), documentada em `schema/marts_ramos.yml`. Os dois endpoints de `fornecedor_por_segmento.py` (gráfico e listagem) DEVEM filtrar `fl_valor_suspeito IS NOT TRUE` — achado real (ver Investigação): sem o filtro, o top do endpoint de gráfico era dominado por contratos com corrupção de dado confirmada (lista fechada de 4 casos, spec 021), não gasto real. Mesmo critério de exclusão de `concentracao_fornecedor.py`, e mesma nota de UI (ver REQ-6): "já exclui contratos com valor implausível... antes da agregação".

## Validação

Teste de carga real, executado em 2026-08-24 no ambiente de dev local (`docker compose`), replicando o protocolo usado para diagnosticar o OOM de `escalada_custo` em 2026-08-21 (container limitado a 512Mi — mesmo teto do pod em produção).

**Setup**: endpoint de teste temporário (`GET /api/v1/_teste-carga/fornecedor-por-segmento`), `SELECT nu_contrato, vl_atual, dt_assinatura, nm_contratado, ramo_atividade FROM marts.fct_contratos_ramo` sem filtro (93.978 linhas, pior caso), `Response` + `TypeAdapter(...).dump_json(...)` — exatamente o padrão então proposto para REQ-7, sem streaming. `dt_assinatura` usado como placeholder de `dt_inicio`/`dt_fim_atual` (REQ-8 ainda não implementado); mesmo número de colunas (5) e mesmo perfil de tipos (string, decimal, date) do conjunto real de REQ-3. Removido após o teste — não faz parte da feature.

**1 requisição, pior caso (dataset completo, sem filtro):**
```
$ docker update --memory=512m --memory-swap=512m compras_api && docker restart compras_api
$ curl -sv http://localhost:8000/api/v1/_teste-carga/fornecedor-por-segmento -o resp.json
< HTTP/1.1 200 OK
< content-length: 11551578
real  0m0.392s

$ docker inspect compras_api --format 'Status={{.State.Status}} OOMKilled={{.State.OOMKilled}} ExitCode={{.State.ExitCode}}'
Status=running OOMKilled=false ExitCode=0
```
Payload: 11.551.578 bytes (~11,55MB). HTTP 200, sem OOM.

**50 requisições sequenciais:**
```
$ for i in $(seq 1 50); do
    code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/_teste-carga/fornecedor-por-segmento)
    [ "$code" != "200" ] && echo "FALHOU na requisição $i: HTTP $code"
  done
loop concluído
$ docker inspect compras_api --format 'Status={{.State.Status}} OOMKilled={{.State.OOMKilled}} ExitCode={{.State.ExitCode}}'
Status=running OOMKilled=false ExitCode=0
$ docker stats compras_api --no-stream --format "{{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"
compras_api   127.2MiB / 512MiB   24.84%
```
Todas as 50 requisições retornaram HTTP 200. Memória estável em 127,2MiB (24,84% do limite de 512Mi) — sem crescimento progressivo entre requisições sequenciais.

**Conclusão**: `Response`/`TypeAdapter` sem streaming sobrevive a 93.978 linhas sob o mesmo teto de memória que matou `escalada_custo` — desde que o `SELECT` fique estreito (5 colunas testadas vs. `SELECT *` em `escalada_custo`, ~19 colunas). REQ-7 foi ajustado para tornar isso explícito (SELECT restrito, revalidação obrigatória se o conjunto de colunas crescer).

**Limitação conhecida do teste**: as 50 requisições foram sequenciais (uma por vez), não concorrentes. Não há medição de comportamento sob requisições simultâneas — se isso for uma preocupação real de produção (tráfego concorrente no relatório), fica como risco residual não coberto por esta validação, não como algo decidido.

**Efeito colateral operacional**: `compras_postgres` (banco local) estava parado no início desta sessão — achado, não causado por este trabalho — parado em decorrência de um teste de import da spec 030 (erros de CSV: quebra de linha não citada, valor não-numérico em `stg_contratos_import`). Reiniciado com autorização do usuário antes deste teste (`docker start compras_postgres`, operação não-destrutiva, dado em volume nomeado). `compras_api` precisou de um restart adicional para descartar conexões antigas (`psycopg.OperationalError: consuming input failed`). Limite de memória revertido ao final via `docker compose up -d --force-recreate api` (o `docker update --memory=0` não removeu o limite de forma confiável nesta versão do engine — precisou recriar o container a partir da definição do compose para restaurar `Memory=0 MemorySwap=0` original).

### Repetição com a implementação real (2026-08-24, após REQ-16)

O `SELECT` real de `GET /api/v1/fornecedor-por-segmento/contratos` ficou com **6 colunas** (`nu_contrato, nm_contratado, vl_atual, dt_inicio, dt_fim_atual, ramo_atividade`), uma a mais que as 5 testadas acima — `ramo_atividade` acabou incluído no retorno (Casos de borda: "cada linha do relatório mantém o ramo do seu próprio contrato"), não só como filtro. REQ-7 exige revalidação nesse caso; repetido com o endpoint real (mesmo protocolo: 512Mi, 1 requisição + 50 sequenciais), sem filtro (pior caso):

```
$ docker update --memory=512m --memory-swap=512m compras_api && docker restart compras_api
$ curl -sv http://localhost:8000/api/v1/fornecedor-por-segmento/contratos -o resp.json
< HTTP/1.1 200 OK
< content-length: 13146296
real  0m0.500s
$ docker inspect compras_api --format 'Status={{.State.Status}} OOMKilled={{.State.OOMKilled}} ExitCode={{.State.ExitCode}}'
Status=running OOMKilled=false ExitCode=0
```
Payload: 13.146.296 bytes (~13,15MB) — maior que os 11,55MB testados (coluna extra), 67.510 linhas (volume real do ambiente local pós-filtro `fl_valor_suspeito`, menor que os 93.978 do ambiente de produção — mismatch de ambiente já documentado, não coberto por este teste).

```
$ for i in $(seq 1 50); do curl -s -o /dev/null -w "%{http_code}" ...; done
loop concluído (50/50 HTTP 200)
$ docker stats compras_api --no-stream --format "{{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"
compras_api   106.9MiB / 512MiB   20.87%
```
Sem OOM em 1 requisição nem em 50 sequenciais; memória proporcionalmente menor que o teste anterior (esperado — volume local é ~72% do volume testado antes). **Limitação**: por rodar sob volume local (67.510), não repete literalmente o pior caso de 93.978 linhas de produção — mesma limitação de ambiente já registrada na Investigação, não resolvida por este teste. Memória revertida ao final (`docker compose up -d --force-recreate api`).

## Design

| Decisão | Escolha | Alternativa descartada | Por quê |
|---|---|---|---|
| Fonte de dado | `marts.fct_contratos_ramo` direto | Novo model `int_fornecedores_por_ramo` | Grão certo já existe; GROUP BY no router é o padrão já usado (`qualidade_dado_orgao.py`) e evita mart intermediária para um agregado simples |
| Colunas de período | Adicionar `dt_inicio`/`dt_fim_atual` na mart existente | Nova mart só para o relatório | São passthrough de `stg_contratos`, sem risco de mudar classificação/grão; menor superfície de mudança |
| Paginação do relatório | Client-side (`criarPaginador`, fetch completo com teto de segurança) | `LIMIT`/`OFFSET` real no backend | Medido sob carga real (ver Validação): 93.978 linhas × 5 colunas sobrevive a 512Mi sem OOM, 1 e 50 requisições; manter padrão único do projeto |
| Serialização do endpoint de listagem | `Response` + `TypeAdapter`, `SELECT` estreito (não `SELECT *`) | `response_model=list[...]` / `StreamingResponse` com cursor (padrão de `escalada_custo.py`) | `TypeAdapter` simples validado sob carga real para o conjunto de colunas de REQ-3; `escalada_custo` só quebrou com `SELECT *` (~19 colunas) no mesmo volume — streaming fica reservado para se o escopo de colunas crescer e a revalidação (exigida por REQ-7) falhar |
| Busca por nome | Novo input de texto com debounce | — (primeiro do tipo no projeto) | Não há padrão equivalente a reaproveitar; precisa ser desenhado |

### Componentes afetados

- `dbt/models/marts/fct_contratos_ramo.sql` — adicionar `dt_inicio`, `dt_fim_atual`, `fl_valor_suspeito`.
- `dbt/models/marts/schema/marts_ramos.yml` — documentar as 3 colunas novas (nenhuma com teste `not_null` — ver REQ-8/REQ-16 e Investigação).
- `api/app/routers/fornecedor_por_segmento.py` (novo) — 2 endpoints: agregado (gráfico) e listagem (relatório).
- `api/app/schemas/fornecedor_por_segmento.py` (novo).
- `api/app/main.py` — registrar as 2 rotas de página (`/graficos/fornecedor-por-segmento`, `/relatorios/fornecedor-por-segmento`) na lista existente (~linha 114-122).
- `api/app/templates/grafico_fornecedor_por_segmento.html`, `relatorio_fornecedor_por_segmento.html` (novos).
- `api/app/templates/layout.html`, `home.html` — links de navegação.
- `web/src/charts/fornecedor-por-segmento.ts` (novo) — render do gráfico e da tabela do relatório.
- `web/src/charts/filtros.ts` — novo helper de busca por texto com debounce (ou arquivo próprio).
- `web/src/main.ts` — wiring das 2 páginas novas.

## Casos de borda

- Segmento "Outros" (maior fatia, 28,47% em `fct_contratos_ramo`) aparece como opção normal no dropdown, não escondida.
- Busca por nome sem resultado — retorna lista vazia, não erro.
- Fornecedor presente em mais de um ramo (contratos diferentes, classificados por objeto de cada contrato) — cada linha do relatório mantém o ramo do seu próprio contrato; nenhuma tentativa de forçar um único ramo por fornecedor.
- `dt_inicio` ou `dt_fim_atual` nulo (contrato sem a data registrada na fonte — qualquer um dos dois lados pode faltar, ver achado na seção Investigação) — exibir período com o campo em aberto (ex. "dd/mm/aaaa – —", "— – dd/mm/aaaa" ou "— – —" se ambos faltarem), não erro nem linha descartada.

## Fora do escopo

- Reclassificação ou melhoria da heurística de ramo (decisão já fechada na spec 014).
- CNAE ou qualquer fonte estruturada de classificação de fornecedor.
- Paginação server-side real (`LIMIT`/`OFFSET`) — fora de escopo enquanto o volume permanecer na ordem de grandeza validada acima; se um filtro futuro sem segmento nem busca precisar do relatório completo (93.978 linhas) e isso se mostrar pesado demais no client, vira spec própria.

## Referências de código

- `dbt/models/marts/fct_contratos_ramo.sql`, `dbt/models/marts/schema/marts_ramos.yml` — mart e schema a estender (REQ-8).
- `dbt/models/staging/stg_contratos.sql:40-43` — origem de `dt_inicio`/`dt_fim_atual`.
- `dbt/models/marts/dim_ramos.sql`, `dbt/models/intermediate/int_contratos_por_ramo.sql` — fonte da nota de população (dado sem o filtro de teste/valor).
- `api/app/routers/qualidade_dado_orgao.py` — padrão de GROUP BY/FILTER sem mart nova (REQ-1).
- `api/app/routers/diversidade_vencedores.py`, `api/app/routers/contratos_temporal.py` — padrão de `Response`/`TypeAdapter` para grão-contrato em volume alto, e o comentário sobre o OOM de 2026-08-21 (REQ-7).
- `api/app/routers/escalada_custo.py` — caso em que `Response`/`TypeAdapter` sem streaming **falhou** (76.041–95.508 linhas, `SELECT *`, 512Mi); padrão de `StreamingResponse` com cursor nomeado a copiar se REQ-7 precisar de revalidação futura (ver Validação).
- `api/app/routers/concentracao_fornecedor.py` — padrão visual/estrutural do gráfico "barra horizontal, top N" (REQ-1) e padrão de exclusão de `fl_valor_suspeito` + nota de legenda (REQ-16).
- `dbt/models/staging/stg_contratos.sql:109-141` — origem de `fl_valor_suspeito`, incluindo a lista fechada dos 4 contratos confirmados por inspeção manual (REQ-16).
- `web/src/charts/pagination.ts` (`criarPaginador`) — paginação client-side 15 linhas (REQ-5).
- `web/src/charts/filtros.ts` — padrão de dropdown (`initFiltrosGrafico`) a estender para o filtro de segmento; ausência de padrão de busca por texto (REQ-4).
- `api/app/main.py:114-122` — lista de rotas de página a estender.

## Ver também

- [[013-levantamento-dbt-legado]], [[014-cobertura-dim-ramos]] — origem da classificação heurística de ramo por palavras-chave.
