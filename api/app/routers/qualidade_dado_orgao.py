from fastapi import APIRouter, Query

from app.db import get_connection
from app.schemas.qualidade_dado_orgao import QualidadeDadoOrgao

router = APIRouter(tags=["qualidade-dado-orgao"])


@router.get(
    "/qualidade-dado-orgao",
    response_model=list[QualidadeDadoOrgao],
    description=(
        "Ranking de órgãos por qualidade de dado (spec 025) — agrega fl_aditivo_inconsistente/"
        "fl_valor_suspeito por cod_unidade_gestora direto no SQL sobre marts.mart_escalada_custo. "
        "As duas flags são a métrica aqui, não um filtro — nenhum contrato é excluído da contagem."
    ),
)
async def get_qualidade_dado_orgao(
    ano_inicio: int | None = Query(None, description="Ano inicial do período (inclusive)"),
    ano_fim: int | None = Query(None, description="Ano final do período (inclusive)"),
) -> list[dict]:
    conditions = []
    params: dict = {}
    if ano_inicio is not None:
        conditions.append("ano_assinatura >= %(ano_inicio)s")
        params["ano_inicio"] = ano_inicio
    if ano_fim is not None:
        conditions.append("ano_assinatura <= %(ano_fim)s")
        params["ano_fim"] = ano_fim

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
        SELECT
            cod_unidade_gestora,
            nm_unidade_gestora,
            count(*) AS qt_contratos,
            count(*) FILTER (WHERE fl_aditivo_inconsistente) AS qt_aditivo_inconsistente,
            round(
                100.0 * count(*) FILTER (WHERE fl_aditivo_inconsistente) / count(*), 2
            ) AS perc_aditivo_inconsistente,
            count(*) FILTER (WHERE fl_valor_suspeito) AS qt_valor_suspeito,
            round(
                100.0 * count(*) FILTER (WHERE fl_valor_suspeito) / count(*), 2
            ) AS perc_valor_suspeito
        FROM marts.mart_escalada_custo
        {where}
        GROUP BY cod_unidade_gestora, nm_unidade_gestora
        ORDER BY qt_contratos DESC
    """

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()
