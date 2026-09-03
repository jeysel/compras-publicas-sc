# 035 — Footer de 3 colunas em todas as páginas

## Tipo

Melhoria de UI (layout compartilhado). Replica o padrão já implementado no projeto
weather-analytics (spec 019 de lá), adaptado ao conteúdo e ao stack deste repo.

## Status

**No ar em produção (2026-09-03).** `layout.html` + `web/src/style.css` com o footer de 3
colunas. Validado local (Postgres real, screenshots light/dark/estreito) e em staging;
deploy da API via CI→Argo (staging automático, produção promovida manualmente, commit
`23cc99f`). Sem toque em dbt.

## Resumo

O footer atual (`layout.html`) é uma linha única: a frase de atribuição da fonte +
link "Metodologia →". Esta spec troca por um footer de 3 colunas — marca / Navegação /
Contato — seguido de uma barra de rodapé com copyright, nota de licença e os links
Privacidade / Termos de Uso. Aparece em todas as páginas (está em `layout.html`, nenhuma
página tem footer próprio).

## Contexto

- Decisão de 2026-09-03: alinhar visualmente com weather-analytics, que já rodou a mesma
  mudança (spec 019 daquele repo — footer `.site-footer__*` de 3 colunas + barra inferior).
- O footer atual perde só a frase "Fonte: sistemas de gestão do Estado…". Num projeto de
  transparência a procedência do dado pesa — ela é **dobrada na coluna de marca** (na
  `desc`), não descartada (weather descartou a atribuição Open-Meteo dele; aqui não).
- `web/src/cobertura.ts` já popula todo `.ano-cobertura` com o `ano_min` real de
  `/api/v1/anos-disponiveis` (spec 034). O footer novo mantém o `<span class="ano-cobertura">`
  na `desc`, então o "2016" continua vindo do dado, não hardcoded.
- Não há arquivo `LICENSE` no repo hoje. A nota "Código e dados sob licença aberta" é a
  redação escolhida pelo usuário; adicionar um `LICENSE` de fato é **fora do escopo** desta
  spec, registrado como pendência.

## Requirements

### Funcionais

1. O `layout.html` DEVE renderizar `<footer class="site-footer">` com `.site-footer__grid`
   contendo 3 blocos:
   - **Marca**: `.site-footer__title` "Compras Públicas SC" + `.site-footer__desc` com o
     texto: *"Painel de transparência de contratos públicos do Estado de Santa Catarina, a
     partir de `<span class="ano-cobertura">2016</span>`. Dados abertos do Portal de
     Transparência oficial, a partir dos sistemas de gestão do Estado."*
   - **Navegação**: `.site-footer__title--caps` "Navegação" + `.site-footer__links` com,
     nesta ordem: Início (`/`), Série temporal (`/graficos/serie-temporal`), Escalada de
     custo (`/graficos/escalada-custo`), Concentração de fornecedores
     (`/graficos/concentracao-fornecedor`), Perfil de órgãos (`/relatorios/perfil-orgaos`),
     Metodologia (`/metodologia`).
   - **Contato**: `.site-footer__title--caps` "Contato" + `.site-footer__links` com
     `mailto:contato@jeysel.dev` e `https://jeysel.dev` ("Desenvolvido por jeysel.dev").

2. O `layout.html` DEVE renderizar `.site-footer__bottom` com:
   - `© 2026 Compras Públicas SC · Código e dados sob licença aberta.`
   - links `Privacidade` e `Termos de Uso`, ambos `href="#"` (páginas não existem).

3. O footer DEVE aparecer em todas as páginas — consequência de estar em `layout.html`.

4. O `<span class="ano-cobertura">` dentro da `desc` DEVE continuar sendo atualizado por
   `web/src/cobertura.ts` (nenhuma mudança nesse arquivo; ele já faz `querySelectorAll`).

### Não-funcionais

1. `.site-footer` e filhos DEVEM usar só os tokens de `:root` já existentes (`--border`,
   `--bg`, `--text`, `--text-h`, `--accent`), sem regra nova dentro de
   `@media (prefers-color-scheme: dark)` — o dark mode herda automático (os cinco tokens já
   têm variante dark em `web/src/style.css`).

2. `.site-footer__grid` DEVE ser `repeat(auto-fit, minmax(280px, 1fr))` — colapsa para 1
   coluna em tela estreita sem media query dedicada.

3. `.site-footer__grid` e `.site-footer__bottom` DEVEM alinhar com o conteúdo
   (`max-width: 1126px; margin: 0 auto`), mesmo valor de `main` e `.navbar-inner`.

4. As regras `.footer` / `.footer-inner` (incl. a variante em `@media (max-width: 720px)`)
   DEVEM ser removidas de `web/src/style.css` — nada mais as usa após esta spec.

## Design

| Decisão | Alternativa | Motivo |
|---|---|---|
| "Navegação" = lista curada de 6 entradas, markup estático | Gerar do `_PAGES` de `main.py` | Footer é lista curada, não espelho da navbar. Os 5 gráficos + 6 relatórios não cabem; escolhidas as portas de entrada de maior valor. Estático = bate exatamente com a spec. |
| Atribuição da fonte dobrada na `desc` da coluna de marca | Descartar (como weather fez com Open-Meteo) / manter linha separada | Projeto de transparência — procedência importa. Cabe na `desc` sem poluir. |
| "Código e dados sob licença aberta" no lugar de "Todos os direitos reservados" | Manter a frase padrão do weather | Painel sobre dados abertos — "direitos reservados" contradiz. Redação escolhida pelo usuário. |
| `Privacidade` / `Termos` como `href="#"` | Omitir até existirem / linkar as de jeysel.dev | Placeholder visível, mesmo padrão do weather. Sem auth/form/sessão neste app, uma página de privacidade seria quase vazia. Criar as páginas é fora do escopo. |
| Sem `LICENSE` nesta spec | Adicionar `LICENSE` junto | Escolha de licença é decisão à parte; a nota do footer fica como declaração de intenção até lá. Pendência registrada. |
| CSS portado quase verbatim do weather (`.site-footer__*`) | Reescrever do zero | Tokens idênticos entre os dois repos; `max-width: 1126px` idêntico. Só muda `margin-top` (24px, como o `.footer` atual daqui). |

### Componentes afetados

- `api/app/templates/layout.html` — bloco `<footer class="footer">…</footer>` inteiro
  substituído por `<footer class="site-footer">…`.
- `web/src/style.css` — regras `.footer` / `.footer-inner` / `.footer-inner a` e a variante
  `.footer-inner` em `@media (max-width: 720px)` removidas; adicionado o bloco
  `.site-footer` + `__grid` / `__title` / `__title--caps` / `__desc` / `__links` /
  `__bottom` (portado da spec 019 do weather-analytics).
- `web/src/cobertura.ts` — **sem mudança** (o `querySelectorAll(".ano-cobertura")` já cobre
  o novo span).

## Casos de borda

- **Tela < ~600px** → `auto-fit` + `minmax(280px, 1fr)` colapsa as 3 colunas em 1;
  `.site-footer__bottom` já é `text-align: center`.
- **Dark mode** → sem regra própria; os 5 tokens usados já têm variante dark em `:root`.
- **`/api/v1/anos-disponiveis` fora do ar** → `cobertura.ts` faz `return` no `!resposta.ok`;
  o `<span>` mantém o "2016" do HTML. Mesmo comportamento de hoje.
- **`Privacidade` / `Termos`** → `href="#"`; clicar rola pro topo. Placeholder esperado.
- **`web/index.html`** (scaffold de dev, não servido) → não tem footer, não muda.

## Fora do escopo

- Criar as páginas de Privacidade e Termos de Uso.
- Adicionar um arquivo `LICENSE` ao repo (pendência registrada, decisão à parte).
- Gerar a coluna "Navegação" a partir de `_PAGES`.
- Qualquer mudança no hero da home (`home.html`) ou na metodologia.

## Referências de código

- `api/app/templates/layout.html` — `<footer class="site-footer">`.
- `web/src/style.css` — bloco "Footer (compartilhado em layout.html)"; tokens em `:root` /
  `@media (prefers-color-scheme: dark)`.
- `web/src/cobertura.ts` — popula `.ano-cobertura` (spec 034).
- weather-analytics `docs/specs/019-footer-tres-colunas/spec.md` — origem do padrão.

## Ver também

- [[034-fronteira-cobertura-temporal-2016]] — o `.ano-cobertura` que o footer carrega.
- [[025-navbar-paginas-relatorios]] — a navbar compartilhada em `layout.html`.
- [[027-cache-busting-vite-static]] — o build do frontend (`web/`) que precisa rodar pro CSS novo entrar.
