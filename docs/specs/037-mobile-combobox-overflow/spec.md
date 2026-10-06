# 037 — Combobox/input de filtro vazando da tela em mobile

## Tipo

Correção de bug (achado reportado pelo usuário, confirmado em dispositivo real).

## Status

**Implementado e validado — pendente deploy.**

## Resumo

O combobox "Órgão" (e, pelo mesmo motivo, todo `<select>`/`<input>` dentro de
`.filter-bar` em todas as páginas de gráfico/relatório) vazava horizontalmente da tela em
mobile. Reportado pelo usuário após validar a spec 036 em iPhone real: "os dois estão
funcionando, apenas o combobox Órgão está vazando da tela". Corrigido em
`web/src/style.css` — dois ajustes de CSS, sem mudança de HTML/TS.

## Contexto

- Spec 036 (tratamento mobile de gráfico com eixo monetário/pizza) foi validada pelo
  usuário em produção, em iPhone real — os dois gráficos corrigidos (escalada de custo,
  série temporal) funcionaram. No mesmo teste, o usuário encontrou este bug separado, não
  coberto pela spec 036 (que tratava só o canvas do ECharts, não os controles de filtro
  ao redor).
- Pedido do usuário: corrigir não só o combobox "Órgão", mas generalizar pra "todos os
  componentes combobox do projeto" — resolvido na raiz porque a regra CSS
  (`.filter-field select` / `.filter-field input[...]`) já é compartilhada por todo
  `filter-bar` de toda página (`grafico_*.html`, `relatorio_*.html`), não por combobox
  individual.

## Investigação

Causa raiz, confirmada por reprodução real (não suposição):

- `.filter-field select` tinha só `min-width: 220px`, sem `width`/`max-width`. Um
  `<select>` nativo sem largura explícita se dimensiona pelo conteúdo — a `<option>` mais
  longa — em vez de respeitar o espaço disponível no container.
- `.filter-field` é filho de `.filter-bar` (`display: flex`). Item de flex tem
  `min-width: auto` por padrão (não `0`), ou seja, por definição do próprio flexbox não
  encolhe abaixo do tamanho intrínseco do conteúdo — o select "puxa" a linha inteira pra
  fora da viewport, e a página inteira ganha scroll horizontal.
- "Órgão" estourava especificamente porque nome de unidade gestora é o texto mais longo
  do app — confirmado real: a opção mais longa no seed local é "Administração do Porto de
  São Francisco do Sul" (37 caracteres visíveis, mas o `<option>` tinha espaço em branco
  de padding do lado do servidor totalizando 90 caracteres brutos). "Modalidade" e os dois
  campos de ano têm opções mais curtas, mas o mesmo bug os afetaria com dado longo o
  suficiente — por isso a correção é na regra compartilhada, não num seletor específico de
  "Órgão".
- Reproduzido em Chromium headless (não é bug exclusivo de WebKit/Safari): antes da
  correção, `document.documentElement.scrollWidth` = 626px contra `clientWidth` = 375px
  (viewport), com o select de Órgão medindo 610px de largura e a borda direita em 626px —
  251px vazando da tela. Screenshot capturado (ver Validação).

## Requirements

### Funcionais

1. Em viewport ≤ 720px, todo `<select>`/`input[type="search"]`/`input[type="date"]`
   dentro de `.filter-field` DEVE respeitar a largura do container
   (`.filter-bar`/`main`), independente do comprimento do texto da opção selecionada.
2. `.filter-field` DEVE ocupar 100% da largura disponível em mobile (campos empilham um
   por linha — já era o comportamento visual de fato, graças ao `min-width: 220px`
   anterior forçar o wrap, mas agora é explícito e não depende de um efeito colateral de
   outro valor).
3. Nenhuma mudança de comportamento em desktop (viewport > 720px) — `min-width: 220px`
   nos campos e o layout em linha de `.filter-bar` continuam como estavam.

### Não-funcionais

1. Correção só em `web/src/style.css` — sem tocar HTML (`api/app/templates/*.html`) nem
   TS, já que o problema é inteiramente de CSS (dimensionamento de elemento nativo).
2. Validação real, não presumida: reproduzir o bug antes da correção (não só confirmar
   que o código "parece certo" depois) — ver Validação.

## Design

| Decisão | Alternativa | Motivo |
|---|---|---|
| Fix em duas partes: `.filter-field { min-width: 0 }` (sempre) + `width: 100%` nos campos (só dentro do `@media max-width: 720px`) | Só `max-width: 100%` nos campos, sem mexer em `.filter-field` | Sem `min-width: 0` no item de flex, o `max-width: 100%` no filho não tem efeito — o item pai já recusa encolher abaixo do conteúdo antes de o filho sequer aplicar seu próprio `max-width`. As duas partes são necessárias juntas. |
| `width: 100%` só em mobile (dentro do media query), não globalmente | Aplicar `width: 100%` sempre, substituindo `min-width: 220px` | Em desktop, os campos ficam lado a lado em `.filter-bar` (`flex-wrap: wrap`, sem largura forçada) — `width: 100%` sempre faria cada campo ocupar a `.filter-bar` inteira, quebrando o layout horizontal atual de desktop, que não tem esse bug (tela larga o suficiente pro texto da opção). |
| `min-width: 0` em `.filter-field` fica fora do media query (sempre ativo) | Também condicionar a 720px | Não tem efeito colateral em desktop — só passa a permitir encolher, não força encolhimento. Mais simples manter uma única declaração sempre ativa do que duplicá-la dentro e fora do media query. |

### Componentes afetados

- `web/src/style.css` — `.filter-field` (regra base) e bloco
  `@media (max-width: 720px)` (nova regra pra `.filter-field` e seus
  `select`/`input[type="search"]`/`input[type="date"]`).

## Validação

Constitution (item 4): bug forçado a reproduzir de verdade antes de aceitar a correção
como resolvida, não só lido o código e presumido correto.

1. **Reprodução do bug** (antes da correção, `git stash` temporário no CSS): rebuild do
   frontend, servido via `docker compose` local com Postgres real (mesmo seed de 76.041
   linhas usado nas specs 035/036) → Playwright/Chromium, viewport 375×800:
   `scrollWidth` 626px vs `clientWidth` 375px, select de Órgão com 610px de largura,
   borda direita em 626px. Screenshot confirma visualmente o corte (seta do select some
   da tela).
2. **Correção restaurada** (`git stash pop`), rebuild, mesmo teste: `scrollWidth` volta a
   375px = `clientWidth`, select de Órgão com 343px (cabe dentro do `main` com padding de
   16px cada lado), sem scroll horizontal.
3. **Caso extremo**: opção mais longa do combobox real (`Administração do Porto de São
   Francisco do Sul`, 90 caracteres brutos com padding) selecionada via
   `page.evaluate` + `dispatchEvent("change")` — ainda sem overflow
   (`scrollWidth` = `clientWidth` = 375), texto exibido inteiro dentro do select sem
   cortar a seta.
4. Testado nas páginas `grafico-escalada-custo`, `grafico-serie-temporal` (ambas com
   `#filtro-orgao`) e `relatorio-perfil-orgaos` (sem `#filtro-orgao`, só filtro de ano —
   controle de não-regressão).

## Casos de borda

- **Campo de busca por texto** (`input[type="search"]`, usado em
  `/relatorios/fornecedor-por-segmento`) → mesma regra, mesma correção; não testado
  isoladamente nesta sessão (mesmo seletor CSS dos já testados, risco residual baixo).
- **`input[type="date"]`** (filtro de período em `fornecedor-por-segmento`) → mesma regra
  compartilhada; o widget nativo de data do iOS não tem o problema de "option longa" (não
  há opções de texto variável), mas ganha `width: 100%` do mesmo jeito, sem efeito
  colateral esperado.
- **Desktop com nome de órgão extremamente longo** → fora do escopo desta correção (sem
  bug relatado); `min-width: 220px` desktop permanece, sem `max-width`, mas a tela larga
  dá folga suficiente na prática.

## Fora do escopo

- Qualquer mudança visual em desktop.
- Estilização customizada do combobox nativo (ex.: dropdown customizado em vez do
  `<select>` do sistema) — fora do pedido do usuário, que foi só "corrigir o vazamento".

## Referências de código

- `web/src/style.css` — `.filter-field`, `.filter-field select` / `input[...]`,
  bloco `@media (max-width: 720px)`.
- `api/app/templates/grafico_escalada_custo.html`,
  `grafico_serie_temporal.html` — markup do `.filter-bar` com `#filtro-orgao` usado na
  validação.

## Ver também

- [[036-mobile-graficos-eixo-monetario]] — validação em iPhone real que encontrou este
  bug como item separado.
