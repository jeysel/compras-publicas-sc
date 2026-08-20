from fastapi import APIRouter, Query

from app.db import get_connection
from app.schemas.diversidade_vencedores import DiversidadeVencedores

router = APIRouter(tags=["diversidade-vencedores"])


@router.get(
    "/diversidade-vencedores",
    response_model=list[DiversidadeVencedores],
    description=(
        "Diversidade de vencedores por processo licitatório (mart_diversidade_vencedores, spec 007). "
        "Sem filtro de ano: o grão da mart é processo, não período — não existe coluna de ano nesta mart "
        "(achado confirmado em 2026-08-20)."
    ),
)
async def get_diversidade_vencedores(
    cod_unidade_gestora: str | None = Query(None, description="Código da unidade gestora"),
) -> list[dict]:
    conditions = []
    params: dict = {}
    if cod_unidade_gestora is not None:
        conditions.append("cod_unidade_gestora = %(cod_unidade_gestora)s")
        params["cod_unidade_gestora"] = cod_unidade_gestora

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM marts.mart_diversidade_vencedores {where} ORDER BY cod_unidade_gestora, nu_processo"

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()
