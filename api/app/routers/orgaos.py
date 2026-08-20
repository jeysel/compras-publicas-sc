from fastapi import APIRouter

from app.db import get_connection
from app.schemas.orgaos import Orgao

router = APIRouter(tags=["orgaos"])


@router.get(
    "/orgaos",
    response_model=list[Orgao],
    description="Lista de órgãos (dim_orgaos, spec 007) — usada para popular filtro de órgão no frontend.",
)
async def get_orgaos() -> list[dict]:
    sql = "SELECT * FROM marts.dim_orgaos ORDER BY nm_unidade_gestora"

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            return await cur.fetchall()
