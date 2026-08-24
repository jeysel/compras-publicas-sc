from fastapi import APIRouter, Query

from app.db import get_connection
from app.schemas.escalada_custo import EscaladaCusto

router = APIRouter(tags=["top-aditivos"])


@router.get(
    "/top-aditivos",
    response_model=list[EscaladaCusto],
    description=(
        "Top-N contratos com maior aditivo de acréscimo (spec 026), sobre marts.mart_escalada_custo. "
        "Filtra vl_variacao > 0 (aditivo real de acréscimo) e exclui fl_aditivo_inconsistente/"
        "fl_valor_suspeito, mesmo critério já usado em variacao-custo-modalidade (spec 025)."
    ),
)
async def get_top_aditivos(
    top_n: int = Query(20, ge=1, le=100, description="Quantidade máxima de contratos retornados"),
) -> list[dict]:
    sql = """
        SELECT * FROM marts.mart_escalada_custo
        WHERE vl_variacao > 0
          AND fl_aditivo_inconsistente IS NOT TRUE
          AND fl_valor_suspeito IS NOT TRUE
        ORDER BY vl_variacao DESC
        LIMIT %(top_n)s
    """

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, {"top_n": top_n})
            return await cur.fetchall()
