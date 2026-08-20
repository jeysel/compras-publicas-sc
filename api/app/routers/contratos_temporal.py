from fastapi import APIRouter, Query

from app.db import get_connection
from app.schemas.contratos_temporal import ContratosTemporal

router = APIRouter(tags=["contratos-temporal"])


@router.get(
    "/contratos-temporal",
    response_model=list[ContratosTemporal],
    description="Série temporal de valor contratado (mart_contratos_temporal, spec 007/013).",
)
async def get_contratos_temporal(
    cod_unidade_gestora: str | None = Query(None, description="Código da unidade gestora"),
    nm_modalidade: str | None = Query(None, description="Modalidade de licitação"),
    ano_inicio: int | None = Query(None, description="Ano inicial do período (inclusive)"),
    ano_fim: int | None = Query(None, description="Ano final do período (inclusive)"),
) -> list[dict]:
    conditions = []
    params: dict = {}
    if cod_unidade_gestora is not None:
        conditions.append("cod_unidade_gestora = %(cod_unidade_gestora)s")
        params["cod_unidade_gestora"] = cod_unidade_gestora
    if nm_modalidade is not None:
        conditions.append("nm_modalidade = %(nm_modalidade)s")
        params["nm_modalidade"] = nm_modalidade
    if ano_inicio is not None:
        conditions.append("ano_assinatura >= %(ano_inicio)s")
        params["ano_inicio"] = ano_inicio
    if ano_fim is not None:
        conditions.append("ano_assinatura <= %(ano_fim)s")
        params["ano_fim"] = ano_fim

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
        SELECT * FROM marts.mart_contratos_temporal
        {where}
        ORDER BY tp_recorte, ano_assinatura, mes_assinatura, cod_unidade_gestora, nm_modalidade
    """

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()
