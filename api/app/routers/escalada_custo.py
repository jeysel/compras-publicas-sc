from fastapi import APIRouter, Query

from app.db import get_connection
from app.schemas.escalada_custo import EscaladaCusto

router = APIRouter(tags=["escalada-custo"])


@router.get(
    "/escalada-custo",
    response_model=list[EscaladaCusto],
    description="Escalada de custo por contrato (mart_escalada_custo, spec 007/013/014).",
)
async def get_escalada_custo(
    cod_unidade_gestora: str | None = Query(None, description="Código da unidade gestora"),
    nm_modalidade: str | None = Query(None, description="Modalidade de licitação"),
    ano: int | None = Query(None, description="Ano de assinatura do contrato"),
) -> list[dict]:
    conditions = []
    params: dict = {}
    if cod_unidade_gestora is not None:
        conditions.append("cod_unidade_gestora = %(cod_unidade_gestora)s")
        params["cod_unidade_gestora"] = cod_unidade_gestora
    if nm_modalidade is not None:
        conditions.append("nm_modalidade = %(nm_modalidade)s")
        params["nm_modalidade"] = nm_modalidade
    if ano is not None:
        conditions.append("ano_assinatura = %(ano)s")
        params["ano"] = ano

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM marts.mart_escalada_custo {where} ORDER BY cod_unidade_gestora, nu_contrato"

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()
