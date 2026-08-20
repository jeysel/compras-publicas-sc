from fastapi import APIRouter, Query

from app.db import get_connection
from app.schemas.concentracao_fornecedor import ConcentracaoFornecedor

router = APIRouter(tags=["concentracao-fornecedor"])


@router.get(
    "/concentracao-fornecedor",
    response_model=list[ConcentracaoFornecedor],
    description=(
        "Concentração de gasto por fornecedor (mart_concentracao_fornecedor, spec 007/013/014). "
        "Com cod_unidade_gestora informado, ordena e limita por rank_no_orgao (ranking dentro do órgão). "
        "Sem cod_unidade_gestora, ordena e limita por rank_estado (ranking no estado inteiro) — como o grão "
        "da mart é (órgão, fornecedor), um mesmo fornecedor pode aparecer mais de uma vez, uma por órgão."
    ),
)
async def get_concentracao_fornecedor(
    cod_unidade_gestora: str | None = Query(None, description="Código da unidade gestora"),
    top_n: int = Query(10, ge=1, description="Quantidade máxima de fornecedores retornados"),
) -> list[dict]:
    conditions = []
    params: dict = {"top_n": top_n}
    if cod_unidade_gestora is not None:
        conditions.append("cod_unidade_gestora = %(cod_unidade_gestora)s")
        params["cod_unidade_gestora"] = cod_unidade_gestora
        order_by = "rank_no_orgao"
    else:
        order_by = "rank_estado"

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
        SELECT * FROM marts.mart_concentracao_fornecedor
        {where}
        ORDER BY {order_by}
        LIMIT %(top_n)s
    """

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()
