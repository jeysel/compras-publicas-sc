from fastapi import APIRouter

from app.db import get_connection
from app.schemas.variacao_custo_modalidade import VariacaoCustoModalidade

router = APIRouter(tags=["variacao-custo-modalidade"])


@router.get(
    "/variacao-custo-modalidade",
    response_model=list[VariacaoCustoModalidade],
    description=(
        "Variação de custo por modalidade (spec 025) — agrega perc_variacao por nm_modalidade_norm "
        "direto no SQL sobre marts.mart_escalada_custo. Considera só contratos com vl_variacao <> 0 "
        "(proxy de 'teve aditivo que mudou valor' — vl_aditado não é exposto pela mart, spec 013/014). "
        "Exclui contratos com fl_aditivo_inconsistente ou fl_valor_suspeito, mesmo critério do gráfico "
        "escalada-custo."
    ),
)
async def get_variacao_custo_modalidade() -> list[dict]:
    sql = """
        SELECT
            nm_modalidade_norm AS nm_modalidade,
            count(*) AS qt_contratos_com_aditivo,
            round(avg(perc_variacao), 2) AS perc_variacao_media
        FROM marts.mart_escalada_custo
        WHERE vl_variacao <> 0
          AND fl_aditivo_inconsistente IS NOT TRUE
          AND fl_valor_suspeito IS NOT TRUE
        GROUP BY nm_modalidade_norm
        ORDER BY qt_contratos_com_aditivo DESC
    """

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            return await cur.fetchall()
