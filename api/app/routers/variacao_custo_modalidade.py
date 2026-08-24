from fastapi import APIRouter, Query

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
async def get_variacao_custo_modalidade(
    ano_inicio: int | None = Query(None, description="Ano inicial do período (inclusive)"),
    ano_fim: int | None = Query(None, description="Ano final do período (inclusive)"),
) -> list[dict]:
    conditions = ["vl_variacao <> 0", "fl_aditivo_inconsistente IS NOT TRUE", "fl_valor_suspeito IS NOT TRUE"]
    params: dict = {}
    if ano_inicio is not None:
        conditions.append("ano_assinatura >= %(ano_inicio)s")
        params["ano_inicio"] = ano_inicio
    if ano_fim is not None:
        conditions.append("ano_assinatura <= %(ano_fim)s")
        params["ano_fim"] = ano_fim

    where = " AND ".join(conditions)
    sql = f"""
        SELECT
            nm_modalidade_norm AS nm_modalidade,
            count(*) AS qt_contratos_com_aditivo,
            round(avg(perc_variacao), 2) AS perc_variacao_media
        FROM marts.mart_escalada_custo
        WHERE {where}
        GROUP BY nm_modalidade_norm
        ORDER BY qt_contratos_com_aditivo DESC
    """

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()
