from fastapi import APIRouter

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
async def get_qualidade_dado_orgao() -> list[dict]:
    sql = """
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
        GROUP BY cod_unidade_gestora, nm_unidade_gestora
        ORDER BY perc_aditivo_inconsistente DESC, perc_valor_suspeito DESC
    """

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            return await cur.fetchall()
