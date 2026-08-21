from fastapi import APIRouter

from app.db import get_connection
from app.schemas.variacao_prazo_modalidade import VariacaoPrazoModalidade

router = APIRouter(tags=["variacao-prazo-modalidade"])


@router.get(
    "/variacao-prazo-modalidade",
    response_model=list[VariacaoPrazoModalidade],
    description=(
        "Variação de prazo por modalidade (spec 025) — agrega dias_variacao por nm_modalidade_norm "
        "direto no SQL sobre marts.mart_escalada_custo. Considera só contratos com dias_variacao <> 0 "
        "(proxy de 'teve aditivo que mudou prazo'). Exclui contratos com fl_aditivo_inconsistente ou "
        "fl_valor_suspeito, mesmo critério do gráfico escalada-custo."
    ),
)
async def get_variacao_prazo_modalidade() -> list[dict]:
    sql = """
        SELECT
            nm_modalidade_norm AS nm_modalidade,
            count(*) AS qt_contratos_com_aditivo_prazo,
            round(avg(dias_variacao), 1) AS dias_variacao_media
        FROM marts.mart_escalada_custo
        WHERE dias_variacao <> 0
          AND fl_aditivo_inconsistente IS NOT TRUE
          AND fl_valor_suspeito IS NOT TRUE
        GROUP BY nm_modalidade_norm
        ORDER BY dias_variacao_media DESC
    """

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            return await cur.fetchall()
