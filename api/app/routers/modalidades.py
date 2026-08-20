from fastapi import APIRouter

from app.db import get_connection
from app.schemas.modalidades import Modalidade

router = APIRouter(tags=["modalidades"])


@router.get(
    "/modalidades",
    response_model=list[Modalidade],
    description=(
        "Lista de modalidades de licitação (dim_modalidades, spec 007) — usada para popular filtro de "
        "modalidade no frontend, incluindo a categoria 'Não informado'."
    ),
)
async def get_modalidades() -> list[dict]:
    sql = "SELECT * FROM marts.dim_modalidades ORDER BY nm_modalidade"

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            return await cur.fetchall()
