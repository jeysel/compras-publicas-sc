# 036 — Tratamento mobile consistente em gráficos com eixo monetário e pizza

## Tipo

Correção de UI (consistência de padrão já existente, não padrão novo).

## Status

**No ar em produção — pendente deploy.** Implementado e validado localmente (ver
Validação). Falta build/push da imagem e promoção via Argo CD (fora do escopo desta
sessão — ver pendência no final).

## Resumo

Avaliação mobile do frontend (sessão de 2026-10-06) encontrou que o tratamento
responsivo de gráfico — já presente e correto em 5 dos 8 módulos ECharts
(`concentracao-fornecedor.ts`, `fornecedor-por-segmento.ts`, `variacao-custo-modalidade.ts`,
`variacao-prazo-modalidade.ts`, `perfil-orgaos.ts`) — não tinha sido replicado em
`escalada-custo.ts`, `contratos-temporal.ts` (série principal + sazonalidade mensal) e
`diversidade-vencedores.ts` (pizza). Esta spec aplica o mesmo padrão a esses três
arquivos.

## Contexto

- Avaliação solicitada pelo usuário (2026-10-06): "avalie a versão mobile deste projeto,
  sugira correções e emita um parecer". Entregue como parecer em texto (sem código),
  depois aprovado para execução ("Aprovado. Realize todas as suas recomendações").
- O padrão mobile já estabelecido (breakpoint único 720px espelhado em CSS e TS via
  `isMobileViewport()`, `grid.left`/`containLabel` ajustado, notação monetária compacta
  via `formatarMoedaCompactaBRL`, nome de eixo omitido em mobile) existe desde specs
  anteriores não documentadas isoladamente como "spec de mobile" — foi introduzido junto
  com cada gráfico de ranking. Esta spec é a primeira a tratar "consistência mobile entre
  gráficos" como problema próprio.
- Os 5 arquivos corrigidos aqui tinham o comentário idêntico "Fix especulativo (spec
  pendente) para gráfico encolhido observado em iPhone real — causa não confirmada em
  código" — uma correção (`requestAnimationFrame(() => chart.resize())`) aplicada sem
  investigação fechada, sem spec correspondente. Esta spec não resolve essa investigação
  (nenhum teste em iPhone real foi feito aqui — ver **Fora do escopo**), mas documenta o
  que existe e corrige a referência cruzada nos comentários.

## Investigação

Achados do parecer (não repetidos aqui em detalhe, só o que motivou a correção):

- `escalada-custo.ts` e `contratos-temporal.ts`: eixo de valor em BRL completo
  (`formatarMoedaBRL`, ex. "R$ 1.234.567,89") sem `grid.left`/`containLabel` ajustado e
  sem nome de eixo condicional — grid fixo por padrão do ECharts (não
  `containLabel`-aware) corta o rótulo em tela estreita.
- `diversidade-vencedores.ts` (pizza): rótulo externo com linha de chamada trunca em "…"
  mesmo com só 2 categorias possíveis (`Fornecedor único` / `Múltiplos fornecedores`,
  `mart_diversidade_vencedores.sql:36-38` — confirmado só essas 2, sem fallback nulo no
  banco apesar do `?? "Não classificado"` defensivo no TS) — **confirmado visualmente**
  via screenshot em 375px antes da correção (ver Validação), não só suposição do parecer.

## Requirements

### Funcionais

1. `escalada-custo.ts` e `contratos-temporal.ts` (ambos os gráficos: série principal e
   sazonalidade mensal) DEVEM calcular `const mobile = isMobileViewport()` e aplicar:
   - `grid: { left: mobile ? 8 : <valor desktop>, right/bottom, containLabel: true }`;
   - `xAxis.name` / `yAxis.name` omitidos (`undefined`) em mobile;
   - `yAxis.axisLabel.formatter` usando `formatarMoedaCompactaBRL` em mobile (só nos dois
     primeiros — `renderSazonalidadeMensal` usa contagem, não BRL, não precisa de
     notação compacta, só da folga de `grid`/`containLabel`).
2. `diversidade-vencedores.ts` DEVE, em mobile: ocultar o rótulo externo da fatia
   (`label.show = false`), mostrar `legend` na base (`bottom: 0, left: "center"`) com o
   nome completo de cada categoria, e recentralizar o pie (`center`, `radius` reduzido)
   para não colidir com o título de 2 linhas acima nem a legenda abaixo.
3. Nenhuma mudança de comportamento em desktop (viewport > 720px) — todo ajuste é
   condicional a `mobile`.

### Não-funcionais

1. Mesmo padrão (nomes de variável, estrutura condicional `mobile ? x : y`) dos 5 módulos
   já corrigidos — não introduzir uma abordagem nova.
2. Validação funcional real antes de considerar concluído (constitution, item 4) — ver
   Validação.

## Design

| Decisão | Alternativa | Motivo |
|---|---|---|
| Legenda na base do pizza em mobile, rótulo externo oculto | Truncar o rótulo externo com `truncarTexto` (como nas barras) | Rótulo de pizza com linha de chamada depende de espaço lateral que não existe em 375px; truncar o texto não resolve a colisão da linha de chamada com a borda do card. Legenda embaixo é o padrão ECharts para esse caso e não exige geometria por categoria. |
| `renderSazonalidadeMensal` ganha `grid`/`containLabel` mas NÃO ganha notação compacta | Aplicar `formatarMoedaCompactaBRL` também lá | A série é contagem de contratos (`qt_contratos`), não valor monetário — não há BRL nesse eixo, `formatarMoedaCompactaBRL` não se aplica. |
| Pie `radius` reduzido de 60% pra 50% em mobile | Manter 60% e só mexer no `center` | Com legenda ocupando a base do card (320px de altura fixa em mobile), 60% de raio ainda colide com o título de 2 linhas acima; 50% + `center` em 48% da altura resolve sem precisar aumentar a altura do card pra essa página específica. |

### Componentes afetados

- `web/src/charts/escalada-custo.ts`
- `web/src/charts/contratos-temporal.ts` (duas funções: `renderContratosTemporal` e
  `renderSazonalidadeMensal`)
- `web/src/charts/diversidade-vencedores.ts`

## Validação

Constitution (item 4): "editei o código" não é "corrigido" — teste funcional real.
Realizado nesta sessão, não presumido:

1. Subida local completa (não mockada): `docker compose up postgres -d` →
   `dbt deps && dbt seed --select contratos --full-refresh && dbt build` (134/134 PASS,
   76.041 linhas de seed real, `dbt/seeds/contratos.csv`) → `npm run build` (host, por
   causa do bind mount `./api:/usr/app/api` que sobrepõe o `app/static` da imagem —
   **achado colateral**, ver nota abaixo) → `docker compose --profile api restart api`.
2. **Achado colateral de infra local (não é bug de produção):** a primeira tentativa de
   validar via `docker compose --profile api up api -d --build` serviu um bundle JS
   antigo mesmo após rebuild — o bind mount `./api:/usr/app/api` do `docker-compose.yml`
   sobrepõe `app/static/` da imagem com o conteúdo do host, e `STATIC_MAIN_JS` em
   `api/app/main.py:60` é lido do `manifest.json` uma vez no import do módulo, não por
   request — um restart sem rebuild do `web/` local serve o hash antigo em silêncio, sem
   erro. Em produção isso não se aplica (sem bind mount, a imagem já traz o build do CI).
   Registrado aqui porque quase invalidou a validação sem dar nenhum sinal de erro.
3. Com o bundle correto confirmado servido (`curl` + grep do hash no HTML, bate com
   `.vite/manifest.json`), screenshot real via Playwright/Chromium headless, viewport
   375×800 (iPhone SE — o mais estreito comum), das 3 páginas corrigidas +
   `concentracao-fornecedor` como controle de não-regressão:
   - `escalada-custo`: eixo Y em "R$ 600 mi" / "R$ 400 mi" etc. (antes: "R$
     600.000.000,00" cortado), sem nome de eixo sobrepondo.
   - `serie-temporal`: mesmo padrão no gráfico principal; sazonalidade mensal sem nome de
     eixo longo estourando a largura.
   - `diversidade-vencedores`: ANTES da correção, rótulo confirmado truncado
     ("Múltiplos f…", "Fornecedo…") mesmo com só 2 categorias — screenshot capturado.
     DEPOIS: legenda na base com "Fornecedor único" / "Múltiplos fornecedores" por
     extenso, sem sobreposição com o título de 2 linhas.
   - `concentracao-fornecedor` (não tocado nesta spec): segue idêntico, sem regressão.
4. `npx tsc --noEmit` limpo em todas as edições.

**Não validado** (fora do alcance desta sessão, honesto por constitution item 5/6): teste
em dispositivo iOS real (Safari) — o "gráfico encolhido" original foi reportado em iPhone
real, e o ambiente aqui é Chromium headless. O `requestAnimationFrame` especulativo
permanece no código (não removido), mas o comentário foi atualizado pra apontar pra esta
spec em vez de "spec pendente" genérico — a investigação Safari-específica continua em
aberto, registrada como pendência, não como resolvida.

## Casos de borda

- **`ds_diversidade` nulo** (`"Não classificado"`, fallback defensivo em
  `diversidade-vencedores.ts:12`) → hoje não ocorre no dado real (confirmado: schema do
  banco só produz as 2 categorias, `mart_diversidade_vencedores.sql:36-38`), mas se
  ocorrer, legenda mobile mostra uma 3ª entrada normalmente — sem tratamento especial
  necessário.
- **Filtro reduz pizza a 1 categoria só** → legenda mostra 1 item, pie vira círculo
  inteiro de uma cor; comportamento padrão do ECharts, sem necessidade de caso especial.
- **Tela exatamente 720px** (limite do breakpoint) → `isMobileViewport()` usa `<=`, cai no
  ramo mobile; consistente com `@media (max-width: 720px)` do CSS (mesmo limite).

## Fora do escopo

- Investigação fechada do "gráfico encolhido em iPhone real" (causa raiz, teste em
  device/emulador iOS) — seguia pendente antes desta spec, segue pendente depois.
- Qualquer mudança nos 5 módulos que já tinham o padrão mobile correto
  (`concentracao-fornecedor.ts` etc.) — só confirmados como não regredidos.
- Deploy em staging/produção — fica para o fluxo normal de CI → Argo CD; esta spec cobre
  só a implementação e a validação local.

## Referências de código

- `web/src/charts/theme.ts` — `isMobileViewport()`, `tituloResponsivo()` (padrão-base,
  não alterado aqui).
- `web/src/charts/format.ts` — `formatarMoedaCompactaBRL`, `truncarTexto`.
- `web/src/charts/escalada-custo.ts`, `contratos-temporal.ts`,
  `diversidade-vencedores.ts` — arquivos corrigidos.
- `api/app/main.py:35-61` — resolução do manifest do Vite (`STATIC_MAIN_JS`), achado
  colateral da validação local.
- `docker-compose.yml:143-144` — bind mount `./api:/usr/app/api` do serviço `api`.

## Ver também

- [[035-footer-tres-colunas]] — última mudança de UI compartilhada antes desta.
- [[027-cache-busting-vite-static]] — build do frontend e o manifest do Vite que esta
  spec esbarrou na validação.
