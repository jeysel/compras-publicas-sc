import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db import close_pool, open_pool
from app.routers import (
    anos_disponiveis,
    concentracao_fornecedor,
    contratos_temporal,
    diversidade_vencedores,
    escalada_custo,
    fornecedor_por_segmento,
    kpis_resumo,
    modalidades,
    orgaos,
    perfil_fornecedores,
    qualidade_dado_orgao,
    variacao_custo_modalidade,
    variacao_prazo_modalidade,
)

# top_aditivos NÃO é registrado (spec 026): achado durante a spec — 13
# contratos com |vl_variacao| > R$100mi não são cobertos por fl_valor_suspeito,
# então um ranking "top aditivos" exporia esses outliers como se fossem
# aditivos reais. Router implementado e funcional, aguardando investigação de
# detecção (spec própria, nos moldes da 021) antes de ser exposto.

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"


def _load_main_entry() -> dict:
    """Lê o manifest do Vite (spec 027) e resolve o nome real, com hash de
    conteúdo, do entrypoint `src/main.ts` — falha explícita se o build do
    frontend não rodou, em vez de cair pra um nome fixo (reintroduziria o bug
    de cache que esta spec corrige)."""
    manifest_path = STATIC_DIR / ".vite" / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(
            f"manifest do Vite não encontrado em {manifest_path} — rode "
            "`npm run build` em web/ antes de iniciar a API (spec 027)"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = manifest.get("src/main.ts")
    if entry is None or "file" not in entry:
        raise RuntimeError(
            f"manifest do Vite ({manifest_path}) não tem entrada válida para "
            "src/main.ts (spec 027)"
        )
    return entry


_main_entry = _load_main_entry()
STATIC_MAIN_JS = f"/static/{_main_entry['file']}"
STATIC_MAIN_CSS = [f"/static/{css}" for css in _main_entry.get("css", [])]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await open_pool()
    yield
    await close_pool()


app = FastAPI(
    title="Compras Públicas SC — API",
    description="Serving layer para as marts do pipeline dbt (spec 007/012).",
    version="0.1.0",
    lifespan=lifespan,
)

for router in (
    anos_disponiveis.router,
    escalada_custo.router,
    diversidade_vencedores.router,
    contratos_temporal.router,
    concentracao_fornecedor.router,
    fornecedor_por_segmento.router,
    orgaos.router,
    modalidades.router,
    qualidade_dado_orgao.router,
    variacao_custo_modalidade.router,
    variacao_prazo_modalidade.router,
    kpis_resumo.router,
    perfil_fornecedores.router,
):
    app.include_router(router, prefix="/api/v1")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=APP_DIR / "templates")
templates.env.globals["main_js"] = STATIC_MAIN_JS
templates.env.globals["main_css"] = STATIC_MAIN_CSS


@app.middleware("http")
async def cache_control_hashed_assets(request: Request, call_next):
    """Cache-Control de longa duração só nos arquivos com hash de conteúdo no
    nome (`/static/assets/...`, gerados pelo Vite) — seguro porque qualquer
    mudança de conteúdo muda o nome do arquivo (spec 027). Assets sem hash
    (ex.: favicon.svg/icons.svg, copiados de web/public/) NÃO recebem esse
    cache: mantêm a validação padrão do StaticFiles (ETag/Last-Modified)."""
    response = await call_next(request)
    if request.url.path.startswith("/static/assets/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response

# (rota, template, data-page) — cada página é servida por um template Jinja2
# próprio; `page` vira `document.body.dataset.page` e dirige o dispatch de
# renderização em web/src/main.ts (spec 025).
_PAGES = (
    ("/", "home.html", "home"),
    ("/graficos/escalada-custo", "grafico_escalada_custo.html", "grafico-escalada-custo"),
    ("/graficos/diversidade-vencedores", "grafico_diversidade_vencedores.html", "grafico-diversidade-vencedores"),
    ("/graficos/serie-temporal", "grafico_serie_temporal.html", "grafico-serie-temporal"),
    ("/graficos/concentracao-fornecedor", "grafico_concentracao_fornecedor.html", "grafico-concentracao-fornecedor"),
    ("/graficos/fornecedor-por-segmento", "grafico_fornecedor_por_segmento.html", "grafico-fornecedor-por-segmento"),
    ("/relatorios/qualidade-dado-orgao", "relatorio_qualidade_orgao.html", "relatorio-qualidade-orgao"),
    ("/relatorios/variacao-custo-modalidade", "relatorio_variacao_custo.html", "relatorio-variacao-custo"),
    ("/relatorios/variacao-prazo-modalidade", "relatorio_variacao_prazo.html", "relatorio-variacao-prazo"),
    ("/relatorios/perfil-fornecedores", "relatorio_perfil_fornecedores.html", "relatorio-perfil-fornecedores"),
    ("/relatorios/perfil-orgaos", "relatorio_perfil_orgaos.html", "relatorio-perfil-orgaos"),
    ("/relatorios/fornecedor-por-segmento", "relatorio_fornecedor_por_segmento.html", "relatorio-fornecedor-por-segmento"),
    ("/metodologia", "metodologia.html", "metodologia"),
)

for path, template_name, page in _PAGES:

    def _make_page_view(template_name: str = template_name, page: str = page):
        async def _view(request: Request):
            return templates.TemplateResponse(request, template_name, {"page": page})

        return _view

    app.add_api_route(path, _make_page_view(), methods=["GET"], include_in_schema=False)
