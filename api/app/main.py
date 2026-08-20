from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import close_pool, open_pool
from app.routers import (
    concentracao_fornecedor,
    contratos_temporal,
    diversidade_vencedores,
    escalada_custo,
    modalidades,
    orgaos,
)


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
