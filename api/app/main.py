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
):
    app.include_router(router, prefix="/api/v1")

app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=APP_DIR / "templates")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request, "base.html", {})
