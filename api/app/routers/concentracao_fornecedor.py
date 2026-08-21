from fastapi import APIRouter, Query

from app.db import get_connection
from app.schemas.concentracao_fornecedor import ConcentracaoFornecedor

router = APIRouter(tags=["concentracao-fornecedor"])


@router.get(
    "/concentracao-fornecedor",
    response_model=list[ConcentracaoFornecedor],
    description=(
        "Concentração de gasto por fornecedor (mart_concentracao_fornecedor, spec 007/013/014/024). "
        "Com cod_unidade_gestora informado, ordena e limita por rank_no_orgao (ranking dentro do órgão) — "
        "grão (órgão, fornecedor) já é único nesse caso. Sem cod_unidade_gestora, deduplica por id_contratado "
        "(DISTINCT ON) antes de ordenar e limitar por rank_estado — o grão da mart é (órgão, fornecedor), um "
        "mesmo fornecedor tem uma linha por órgão com que contratou, mas rank_estado/vl_total_fornecedor_estado "
        "já vêm pré-agregados por fornecedor (idênticos em todas as linhas dele), então a dedup no SQL não "
        "altera o valor exibido."
    ),
)
async def get_concentracao_fornecedor(
    cod_unidade_gestora: str | None = Query(None, description="Código da unidade gestora"),
    top_n: int = Query(10, ge=1, le=100, description="Quantidade máxima de fornecedores retornados"),
) -> list[dict]:
    params: dict = {"top_n": top_n}
    if cod_unidade_gestora is not None:
        params["cod_unidade_gestora"] = cod_unidade_gestora
        sql = """
            SELECT * FROM marts.mart_concentracao_fornecedor
            WHERE cod_unidade_gestora = %(cod_unidade_gestora)s
            ORDER BY rank_no_orgao
            LIMIT %(top_n)s
        """
    else:
        sql = """
            SELECT * FROM (
                SELECT DISTINCT ON (id_contratado) *
                FROM marts.mart_concentracao_fornecedor
                ORDER BY id_contratado, rank_estado
            ) sub
            ORDER BY rank_estado
            LIMIT %(top_n)s
        """

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()
