# Spec 027 — Cache-busting real dos assets estáticos (Vite + FastAPI/Jinja2)

## Tipo

Correção de comportamento (bug de cache do browser) — mudança pequena de arquitetura no build do frontend e na forma como a API resolve/serve os assets estáticos.

## Status

Implementado, validado localmente, em staging e em produção em 2026-08-24 (REQ-1 a REQ-8) — commit `20a66a2` (código), `f50edc4` (promoção staging), `2c75849` (promoção produção).

### Validação (local, `docker compose --profile api up api -d --build`)

`web/vite.config.ts`: remoção de `entryFileNames`/`assetFileNames` fixos + `build.manifest: true`. Build confirma hash de conteúdo real, não timestamp — 2 rebuilds sucessivos comparados:

```
# build 1 (código inalterado)
../api/app/static/assets/main-BIW6ngjM.css
../api/app/static/assets/main-CSZ12GDS.js

# build 2, após 1 regra CSS nova de teste em src/style.css (revertida depois)
../api/app/static/assets/main-BnyHGHA5.css   ← hash mudou (conteúdo mudou)
../api/app/static/assets/main-D7zaxCzx.js    ← hash mudou também (JS referencia o nome do chunk CSS)

# build 3, mudança revertida (comentário-only, sem alterar bytes minificados)
../api/app/static/assets/main-BIW6ngjM.css   ← hash igual ao build 1 (minificador remove comentário, bytes finais idênticos)
```

`api/app/main.py`: helper `_load_main_entry()` lê `.vite/manifest.json` no import do módulo, expõe `main_js`/`main_css` como globals do Jinja2; middleware `cache_control_hashed_assets` aplica `Cache-Control` só em `/static/assets/*`.

```
$ curl -sI http://localhost:8000/static/assets/main-CSZ12GDS.js | grep -i cache-control
cache-control: public, max-age=31536000, immutable

$ curl -sI http://localhost:8000/static/favicon.svg | grep -i cache-control
(sem header — comportamento padrão do StaticFiles, ETag/Last-Modified)
```

REQ-3 (HTML referencia nome real, não hardcoded):

```
$ curl -s http://localhost:8000/ | grep -E "main-|link rel"
    <link rel="stylesheet" href="/static/assets/main-BIW6ngjM.css" />
    <script type="module" src="/static/assets/main-CSZ12GDS.js"></script>
```

REQ-4 (falha explícita, sem fallback silencioso) — `manifest.json` renomeado, container reiniciado:

```
RuntimeError: manifest do Vite não encontrado em /usr/app/api/app/static/.vite/manifest.json —
rode `npm run build` em web/ antes de iniciar a API (spec 027)
```

Restaurado o manifest, container voltou a subir normalmente (`Application startup complete`, `home: 200`).

Smoke test de 4 páginas (todas herdam `layout.html`):

```
/                              -> 200
/metodologia                   -> 200
/graficos/serie-temporal       -> 200
/relatorios/perfil-orgaos      -> 200
```

`grep -rn "static/main\." api/app/templates/` → nenhum resultado (nenhuma referência hardcoded remanescente).

### Validação (staging e produção, REQ-8)

Fluxo de promoção confirmado (spec 022, mecanismo já em uso): push → CI (`build-and-push.yml`, run 32741933330) publica `ghcr.io/.../compras-publicas-api:20a66a2` → `newTag` do overlay atualizado → commit/push → sync manual do Argo CD (`sudo -n kubectl patch application ... sync`) → pod `Running`/`Healthy` na tag nova, confirmado por `kubectl get pod`/`get application` via SSH.

Staging (via `kubectl port-forward` direto ao `Service`, sem passar pelo Ingress):

```
--- home HTML refs ---
<link rel="stylesheet" href="/static/assets/main-BIW6ngjM.css" />
<script type="module" src="/static/assets/main-CSZ12GDS.js"></script>
--- hashed asset headers ---
cache-control: public, max-age=31536000, immutable
--- favicon headers (no hash) ---
(sem cache-control, esperado)
--- smoke pages ---
/                          -> 200
/metodologia               -> 200
/relatorios/perfil-orgaos  -> 200
```

Produção (`https://contratos-sc.jeysel.dev`, domínio público real, atravessando Nginx/Traefik):

```
<link rel="stylesheet" href="/static/assets/main-BIW6ngjM.css" />
<script type="module" src="/static/assets/main-CSZ12GDS.js"></script>

Cache-Control: public, max-age=31536000, immutable          ← asset com hash
Cache-Control: max-age=14400                                ← favicon.svg (sem hash)

/                          -> 200
/metodologia               -> 200
/relatorios/perfil-orgaos  -> 200
```

O `max-age=14400` do `favicon.svg` em produção (ausente no teste local/staging via port-forward) vem da camada Nginx na frente do cluster, não da API — comportamento pré-existente, fora do escopo desta spec (ver Fora do escopo), e não é uma regressão: 4h é uma janela muito menor que o problema original (cache indefinido até hard-refresh manual) e esse arquivo não muda de conteúdo com frequência.

## Resumo

`main.js`/`main.css` são publicados sempre com o mesmo nome de arquivo a cada deploy. Sem hash de conteúdo no nome, o browser pode continuar servindo a versão em cache depois de um deploy novo — sintoma real reportado hoje: cards de KPI na home e relatórios novos (spec 026) aparecendo com placeholder "—" até múltiplos F5 forçarem o download do bundle novo. Esta spec formaliza a correção: nome de arquivo com hash de conteúdo (`build.manifest` do Vite), resolução do nome real via `manifest.json` no momento de servir o HTML (Jinja2 + FastAPI), e `Cache-Control` de longa duração só nos arquivos com hash — eliminando a necessidade de hard-refresh manual em todo deploy futuro.

## Contexto

- O frontend (`web/`, spec 012) é buildado em stage Node do Dockerfile multi-stage e copiado para `api/app/static/` (spec 022, Requirement 1) — `api/app/static/` é gitignored, só existe dentro da imagem.
- `api/app/main.py:61` monta `StaticFiles(directory=APP_DIR / "static")` em `/static`, sem nenhuma configuração de `Cache-Control` própria — Starlette usa validação por `Last-Modified`/`ETag` (HTTP 304), não `max-age` longo. Isso não é a causa do bug relatado (revalidação por `ETag` deveria pegar conteúdo novo), mas hoje não há proteção nenhuma contra um proxy/CDN intermediário ou cache de browser mais agressivo que ignore a revalidação.
- `api/app/templates/layout.html:7,65` referenciam `/static/main.css` e `/static/main.js` com nome fixo, hardcoded.

## Investigação

**1. Causa raiz confirmada em `web/vite.config.ts`:**

```ts
export default defineConfig({
  build: {
    outDir: "../api/app/static",
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(import.meta.dirname, "src/main.ts"),
      output: {
        entryFileNames: "main.js",
        assetFileNames: "[name][extname]",
      },
    },
  },
});
```

`entryFileNames`/`assetFileNames` sobrescrevem explicitamente o default do Vite (que já inclui hash de conteúdo, ex. `main-a1b2c3d4.js`) para nome fixo — decisão que hoje não está documentada em nenhuma spec anterior (não aparece em 012 nem 022). Efeito: toda imagem nova publica um `main.js` com o **mesmo nome** e conteúdo diferente, dependendo só de `ETag`/`Last-Modified` para invalidar cache — insuficiente pro sintoma relatado (proxy/browser que trata `same-name` como "não mudou" sem revalidar).

**2. `api/app/main.py` não define `Cache-Control` algum no mount de `/static`** — confirmado por leitura direta (`app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")`, sem `Response` customizado, sem middleware). Não há nenhum outro lugar do repo (`grep -rn "Cache-Control\|cache" api/ web/ deploy/`) configurando cache HTTP.

**3. `layout.html` referencia os 2 arquivos do bundle com path fixo** (`/static/main.css`, `/static/main.js`) — não há hoje nenhum mecanismo de leitura de `manifest.json`; `build.manifest` nem está habilitado no `vite.config.ts` atual.

**4. Assets de `web/public/` (`favicon.svg`, `icons.svg`) são copiados por padrão do Vite pro `outDir` sem hash** — comportamento normal e esperado do Vite (`publicDir`), não afetado por esta correção; ver Fora do escopo.

## Requirements

### Funcionais

- REQ-1: O build do frontend (`vite build`) DEVE gerar `main.<hash>.js`/`main.<hash>.css` com hash de conteúdo no nome — removendo a sobrescrita atual de `entryFileNames`/`assetFileNames` em `web/vite.config.ts` (ou ajustando para usar `[name].[hash][extname]`/`[hash]` explicitamente, já que o comportamento sem `output` customizado é o default do Vite).
- REQ-2: O build DEVE habilitar `build.manifest: true`, gerando `api/app/static/.vite/manifest.json` com o mapeamento de entrypoint (`src/main.ts`) para o nome real do arquivo (`file`) e seus assets CSS associados (`css`).
- REQ-3: QUANDO uma página for renderizada (qualquer uma das rotas em `_PAGES`, `api/app/main.py`), o sistema DEVE resolver o nome real de `main.js`/`main.css` lendo `manifest.json` (função helper única, não duplicada por template) — `layout.html` NÃO DEVE ter `/static/main.js`/`/static/main.css` hardcoded.
- REQ-4: SE `manifest.json` não existir ou não tiver a entrada esperada (`src/main.ts`) QUANDO a API tentar servir uma página, ENTÃO o sistema DEVE falhar de forma explícita (erro no startup ou 500 com log claro) — nunca cair silenciosamente para um nome fixo/hardcoded que reintroduziria o bug desta spec.
- REQ-5: Os arquivos com hash de conteúdo servidos por `/static` DEVEM receber `Cache-Control: public, max-age=31536000, immutable` — seguro porque qualquer mudança de conteúdo gera nome de arquivo novo (REQ-1).
- REQ-6: Arquivos estáticos sem hash no nome (`favicon.svg`, `icons.svg`, de `web/public/`) NÃO DEVEM receber o `Cache-Control` de longa duração do REQ-5 — mantêm o comportamento de validação padrão do `StaticFiles` (`ETag`/`Last-Modified`), já que uma mudança de conteúdo nesses arquivos não muda o nome.

### Não-funcionais

- REQ-7: A correção DEVE ser validada localmente antes do deploy simulando "browser com cache antigo" (DevTools Network: cache habilitado, sem hard-refresh) contra dois builds sucessivos com conteúdo diferente — confirmando que um F5 simples já mostra o bundle novo (constitution: validação real, não presumida).
- REQ-8: O deploy em staging DEVE ser validado com o mesmo critério do REQ-7 contra o ambiente real (não só local) antes de promover para produção.

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| Nome de arquivo do bundle | Hash de conteúdo (`[name]-[hash][extname]`, default do Vite) | Remove a sobrescrita atual (`entryFileNames: "main.js"`) que é a causa raiz do bug — nome muda só quando conteúdo muda |
| Resolução do nome real no HTML | `build.manifest: true` + função helper Python lida no startup/por request, usada em `layout.html` via Jinja2 | Mecanismo padrão do próprio Vite pra esse problema — evita reinventar convenção de nome ou regex sobre `static/` |
| Cache-Control | `immutable`/`max-age` longo só nos arquivos com hash; comportamento padrão (`ETag`) nos demais | Seguro só porque o nome muda a cada conteúdo novo (REQ-1) — aplicar o mesmo cache longo em `favicon.svg`/`icons.svg` (sem hash) reintroduziria o mesmo bug pra esses arquivos |
| Falha quando manifest ausente/incompleto | Erro explícito, não fallback silencioso pra nome fixo | Constitution (regra 4): correção "parece certa" não é suficiente; um fallback silencioso esconderia build quebrado em produção |

### Componentes afetados

- `web/vite.config.ts` — remove `entryFileNames`/`assetFileNames` fixos, adiciona `build.manifest: true`.
- `api/app/main.py` — função helper de leitura do manifest, exposta ao Jinja2 (`templates.env.globals` ou contexto por request).
- `api/app/templates/layout.html` — troca `/static/main.css`/`/static/main.js` hardcoded pela chamada ao helper.
- `api/app/main.py` — ajuste no mount de `/static` (ou middleware/subclasse de `StaticFiles`) para `Cache-Control` condicional (REQ-5/REQ-6).

## Casos de borda

- Build local (`npm run dev`, sem `vite build`) não gera `manifest.json` — helper precisa de um caminho de dev viável (ex.: dev server do Vite servindo os arquivos direto, se for o modo de desenvolvimento já usado) ou instrução clara de rodar `npm run build` antes de testar via FastAPI local; a confirmar durante a implementação, não presumido aqui.
- CSS: o manifest do Vite associa CSS ao entrypoint JS via campo `css` (array), não um `file` único — o helper precisa tratar isso (pode haver 0, 1 ou mais arquivos CSS por entrypoint), não assumir 1:1 com `main.css`.
- Deploy em k3s com `syncPolicy: {}` manual (spec 022): a imagem nova (com manifest novo) só entra em produção depois de promoção manual da tag — comportamento já existente, não alterado por esta spec, mas relevante pra validação do REQ-8 (staging e produção compartilham o mesmo Postgres, mas não a mesma imagem até a promoção).

## Fora do escopo

- Hash/versionamento de `favicon.svg`/`icons.svg` (`web/public/`) — comportamento padrão do Vite (cópia direta, sem hash) mantido como está; esses arquivos não fazem parte do sintoma relatado.
- Cache em camada de CDN/edge (Cloudflare, se houver, à frente do domínio público) — fora do escopo desta spec, que trata só do `Cache-Control` de origem (API/StaticFiles); investigar separadamente se o sintoma persistir mesmo depois desta correção.
- Service Worker / cache offline — o frontend não usa nenhum hoje; não é introduzido por esta spec.

## Referências de código

- `web/vite.config.ts` — configuração a corrigir (REQ-1/REQ-2).
- `api/app/main.py:61` — mount de `/static`, ponto de ajuste do `Cache-Control` (REQ-5/REQ-6) e registro do helper de manifest (REQ-3).
- `api/app/templates/layout.html:7,65` — referências hardcoded a substituir (REQ-3).
- `docs/specs/022-deploy-fastapi-frontend-k3s/spec.md` — build multi-stage que gera `api/app/static/` (Requirement 1), contexto de como a imagem é montada.

## Ver também

- [[022-deploy-fastapi-frontend-k3s]] (build multi-stage, `api/app/static/` gitignored)
- [[025-navbar-paginas-relatorios]] (`layout.html`, estrutura de página compartilhada)
- [[026-kpis-classificacoes-rankings]] (sintoma relatado: KPIs/relatórios novos com placeholder até hard-refresh)
