# 038 — Rede de segurança contra overflow horizontal em mobile (input de data)

## Tipo

Correção de bug reportado pelo usuário — investigação sem causa raiz fechada, correção
defensiva aplicada no lugar.

## Status

**Implementado — pendente deploy. Causa raiz NÃO confirmada** (ver Investigação e
"Não validado"). Diferente das specs 036/037, esta correção não reproduziu o bug
relatado em nenhum engine disponível localmente — é uma rede de segurança, não um fix
dirigido à causa.

## Resumo

Usuário reportou, após validar a spec 037 (fix do combobox "Órgão") em produção no
iPhone: "o componente de data da página Fornecedor por segmento está com o mesmo
problema" (vazando da tela) e pediu verificação em toda página com componente de data.
Só existem 2 páginas com `input[type="date"]`:
`grafico_fornecedor_por_segmento.html` e `relatorio_fornecedor_por_segmento.html` —
ambas usam o mesmo `#filtro-periodo-de` / `#filtro-periodo-ate`, mesmo
`.filter-field input[type="date"]` do CSS, já coberto pela correção da spec 037
(`width: 100%`, `max-width: 100%`, `box-sizing: border-box`, `min-width: 0` em mobile).

Não foi possível reproduzir overflow nessas páginas em Chromium nem em WebKit desktop
(engine Playwright), com ou sem valor selecionado no campo, antes desta correção — ao
contrário do combobox da spec 037, que reproduziu de forma determinística em Chromium.
Isto sugere (não confirma) que o problema é específico do WebKit móvel/iOS real, que
nenhum engine disponível localmente replica fielmente pra controles de formulário
nativos (o picker de data no iOS é renderizado por UIKit, não só CSS/layout engine).

Aplicada uma correção defensiva: `overflow-x: hidden` no `body`, que contém qualquer
vazamento horizontal futuro (deste ou de outro controle) sem depender de prever o
mecanismo exato.

## Contexto

- Terceiro achado de mobile na mesma sequência de validação real em iPhone
  (specs 036 → 037 → esta). Specs 036/037 foram fechadas com causa confirmada e
  reprodução real; esta não — registrado honestamente como tal (constitution, item 5:
  "119/120 passou" não é validação completa até se saber o que é o 1; aqui o "1" é esta
  spec).

## Investigação

Tentativas de reprodução, todas sem overflow detectado:

1. Chromium headless, `/relatorios/fornecedor-por-segmento`, viewport 375×800, campo
   vazio: `document.documentElement.scrollWidth` = `clientWidth` = 375.
2. Mesma página, produção já com o fix da spec 037 no ar
   (`https://contratos-sc.jeysel.dev`), mesma medição: sem overflow.
3. WebKit desktop (engine Playwright, não é iOS Safari real — compartilha motor de
   layout CSS mas não o UIKit que renderiza o picker nativo de data em iOS), antes e
   depois de preencher `#filtro-periodo-de` via `page.fill(..., "2020-05-15")`: sem
   overflow nos dois momentos.
4. Testado também `#filtro-ramo` (select) e `#filtro-nome-fornecedor` (busca de texto) na
   mesma página — nenhum excede 343px (largura do container, `main` com 16px de padding
   de cada lado em 375px de viewport).

**Hipótese não confirmada**: o picker nativo de data do iOS Safari (a UI que abre ao
tocar o campo) pode ter comportamento de dimensionamento que nenhum engine disponível
localmente reproduz — é renderizado pelo sistema operacional (UIKit), não só pelo motor
de CSS/layout do WebKit que o Playwright consegue emular em Linux. Sem acesso a um
iPhone real ou simulador iOS, não há como confirmar isto nesta sessão.

## Requirements

### Funcionais

1. O `body` DEVE ter `overflow-x: hidden` — nenhuma página do site tem conteúdo que
   legitimamente precise de scroll horizontal no nível do documento (`main` já tem
   `max-width`; `.table-card` já trata sua própria largura com `overflow-x: auto`
   localmente, contexto de scroll independente do `body`).

### Não-funcionais

1. A correção NÃO DEVE alterar a aparência ou o comportamento de nenhum controle de
   formulário em motores testáveis localmente (Chromium, WebKit desktop) — só contém
   overflow, não muda layout dentro dos limites normais.
2. `position: sticky` da navbar DEVE continuar funcionando com `overflow-x: hidden` no
   `body` — verificado (ver Validação); `overflow-x` sozinho não quebra sticky vertical
   (só overflow no eixo relevante ao sticky, aqui vertical, quebraria).

## Design

| Decisão | Alternativa | Motivo |
|---|---|---|
| `overflow-x: hidden` no `body`, sem tentar corrigir o `input[type="date"]` diretamente | `-webkit-appearance: none` no input de data (tentado e revertido nesta mesma sessão) | Tentativa de reset de aparência nativa **quebrou visualmente o campo em WebKit** (ícone de calendário e placeholder "dd/mm/aaaa" somem completamente, ver screenshot da tentativa) — regressão pior que o problema original, sem nenhuma evidência de que resolvia o bug relatado (que nem reproduziu). Reverida antes de commitar. |
| Rede de segurança genérica (`overflow-x: hidden`) em vez de investigação mais profunda (ex.: Playwright com `--emulate-ios`, BrowserStack, dispositivo real) | Insistir em reproduzir com mais ferramentas antes de corrigir | Ferramentas de emulação iOS real não estão disponíveis neste ambiente; `overflow-x: hidden` é uma correção de baixo risco, bem estabelecida, que resolve o **sintoma relatado** (vazamento visível/scroll horizontal) independente da causa exata — aceitável como primeira resposta dado o padrão já visto nesta sessão (3 bugs mobile seguidos todos de "controle nativo ignora layout CSS"). |
| `overflow-x: hidden` no `body`, não no `html` | `html { overflow-x: hidden }` ou nos dois | `body` já é o elemento com `margin: 0` existente (ponto natural de adicionar); testado e suficiente nos dois engines disponíveis. Se a causa real for algo que escapa até do `body` (improvável, mas não descartável sem iPhone real), pode precisar de ajuste futuro — registrado como risco residual, não como certeza. |

### Componentes afetados

- `web/src/style.css` — regra `body` (adiciona `overflow-x: hidden`).

## Validação

Constitution (item 4/5/6): esta seção documenta o que foi **e o que não foi** validado,
sem disfarçar uma correção especulativa como corrigida.

**Validado (reprodutível, confirmado por teste real):**
1. `-webkit-appearance: none` no `input[type="date"]` foi implementado, testado via
   screenshot em WebKit desktop, e **rejeitado** por quebrar visualmente o campo (ícone e
   placeholder desaparecem) — decisão tomada com evidência, não por hipótese.
2. Com `overflow-x: hidden` no `body`: sem overflow em Chromium nem WebKit desktop, nas
   mesmas páginas e campos (`scrollWidth` = `clientWidth` = 375 em ambos).
3. `position: sticky` da navbar continua grudando no topo após rolar a página 800px —
   testado nos dois engines (`getBoundingClientRect().top === 0` após scroll).
4. Nenhuma mudança visual aos campos de formulário nos dois engines (screenshot
   comparado antes/depois da adição de `overflow-x: hidden`, sem diferença).

**NÃO validado (honesto, não presumido):**
- O bug relatado pelo usuário ("componente de data vazando da tela" no iPhone real) não
  foi reproduzido em nenhum ambiente de teste disponível nesta sessão. A correção
  aplicada (`overflow-x: hidden`) deve conter o sintoma, mas isso não foi confirmado
  contra o bug real — só contra a ausência de overflow nos engines testáveis.
- Pendência explícita: o usuário precisa validar de novo em iPhone real depois do
  deploy. Se o campo de data ainda aparentar vazar (mesmo contido por
  `overflow-x: hidden`, o CAMPO em si pode ficar cortado visualmente em vez de
  "vazar" — sintoma diferente, não resolvido), a investigação precisa continuar com mais
  informação do usuário (modelo do iPhone, versão do iOS, se o vazamento acontece com o
  campo vazio ou só depois de abrir o picker).

## Casos de borda

- **Elemento legitimamente mais largo que a viewport por engano futuro** (regressão de
  CSS não relacionada) → antes causaria scroll horizontal visível (sintoma óbvio, fácil
  de notar); com `overflow-x: hidden`, o conteúdo é cortado silenciosamente em vez de
  rolável — troca "vaza e pode ler" por "não vaza mas pode cortar". Aceito como trade-off
  consciente: cortar é menos ruim que vazar pra fora do card observável no site de
  produção, não há conteúdo que precise genuinamente de scroll horizontal no `body` hoje.
- **`.table-card` com `overflow-x: auto`** → contexto de scroll independente, não afetado
  pelo `overflow-x: hidden` do `body` (scroll aninhado continua funcionando).

## Fora do escopo

- Resolver a causa raiz exata do comportamento do `input[type="date"]` em iOS Safari
  real — sem acesso a device/simulador, fica como pendência explícita.
- Qualquer mudança visual ou de comportamento nos campos de formulário além da contenção
  de overflow.

## Referências de código

- `web/src/style.css` — regra `body`.
- `api/app/templates/grafico_fornecedor_por_segmento.html`,
  `relatorio_fornecedor_por_segmento.html` — únicas páginas com `input[type="date"]`.

## Ver também

- [[037-mobile-combobox-overflow]] — bug irmão (combobox), mesma origem de relato
  (validação em iPhone real), mas com causa confirmada e reprodução real — contraste
  direto com esta spec, que não teve a mesma sorte de reprodução.
