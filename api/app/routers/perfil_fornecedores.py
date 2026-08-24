from fastapi import APIRouter

from app.db import get_connection
from app.schemas.perfil_fornecedores import PerfilFornecedores

router = APIRouter(tags=["perfil-fornecedores"])


@router.get(
    "/perfil-fornecedores",
    response_model=list[PerfilFornecedores],
    description=(
        "Distribuição de fornecedores por porte (spec 026) — GROUP BY porte_fornecedor sobre "
        "marts.dim_fornecedores; a classificação já vem pronta da mart (dim_fornecedores.sql), "
        "este endpoint só agrega o que já existe, não reclassifica nada."
    ),
)
async def get_perfil_fornecedores() -> list[dict]:
    sql = """
        SELECT
            porte_fornecedor,
            count(*) AS qt_fornecedores,
            sum(vl_total_atual) AS valor_total
        FROM marts.dim_fornecedores
        GROUP BY porte_fornecedor
        ORDER BY sum(vl_total_atual) DESC
    """

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            return await cur.fetchall()
