from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db import close_pool, open_pool
from app.routers import (
    concentracao_fornecedor,
    contratos_temporal,
    diversidade_vencedores,
    escalada_custo,
    modalidades,
    orgaos,
    qualidade_dado_orgao,
    variacao_custo_modalidade,
    variacao_prazo_modalidade,
)

APP_DIR = Path(__file__).resolve().parent


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
    escalada_custo.router,
    diversidade_vencedores.router,
    contratos_temporal.router,
    concentracao_fornecedor.router,
    orgaos.router,
    modalidades.router,
    qualidade_dado_orgao.router,
    variacao_custo_modalidade.router,
    variacao_prazo_modalidade.router,
):
    app.include_router(router, prefix="/api/v1")

app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=APP_DIR / "templates")

# (rota, template, data-page) — cada página é servida por um template Jinja2
# próprio; `page` vira `document.body.dataset.page` e dirige o dispatch de
# renderização em web/src/main.ts (spec 025).
_PAGES = (
    ("/", "home.html", "home"),
    ("/graficos/escalada-custo", "grafico_escalada_custo.html", "grafico-escalada-custo"),
    ("/graficos/diversidade-vencedores", "grafico_diversidade_vencedores.html", "grafico-diversidade-vencedores"),
    ("/graficos/serie-temporal", "grafico_serie_temporal.html", "grafico-serie-temporal"),
    ("/graficos/concentracao-fornecedor", "grafico_concentracao_fornecedor.html", "grafico-concentracao-fornecedor"),
    ("/relatorios/qualidade-dado-orgao", "relatorio_qualidade_orgao.html", "relatorio-qualidade-orgao"),
    ("/relatorios/variacao-custo-modalidade", "relatorio_variacao_custo.html", "relatorio-variacao-custo"),
    ("/relatorios/variacao-prazo-modalidade", "relatorio_variacao_prazo.html", "relatorio-variacao-prazo"),
    ("/metodologia", "metodologia.html", "metodologia"),
)

for path, template_name, page in _PAGES:

    def _make_page_view(template_name: str = template_name, page: str = page):
        async def _view(request: Request):
            return templates.TemplateResponse(request, template_name, {"page": page})

        return _view

    app.add_api_route(path, _make_page_view(), methods=["GET"], include_in_schema=False)
