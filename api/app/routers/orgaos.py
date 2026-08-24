from fastapi import APIRouter, Query

from app.db import get_connection
from app.schemas.orgaos import Orgao

router = APIRouter(tags=["orgaos"])


@router.get(
    "/orgaos",
    response_model=list[Orgao],
    description=(
        "Lista de órgãos (dim_orgaos, spec 007) — usada para popular filtro de órgão no frontend "
        "(sem ano_inicio/ano_fim) e para o gráfico de distribuição por perfil (com, spec 029). "
        "ano_inicio/ano_fim filtram órgãos por atividade — ao menos um contrato em fct_contratos "
        "dentro do intervalo — sem recalcular ds_perfil_contratacao, que continua histórico/acumulado. "
        "Sem os parâmetros, comportamento idêntico ao anterior à spec 029 (REQ-8)."
    ),
)
async def get_orgaos(
    ano_inicio: int | None = Query(None, description="Ano inicial de atividade (inclusive)"),
    ano_fim: int | None = Query(None, description="Ano final de atividade (inclusive)"),
) -> list[dict]:
    conditions = ["c.cod_unidade_gestora = o.cod_unidade_gestora"]
    params: dict = {}
    if ano_inicio is not None:
        conditions.append("c.ano_assinatura >= %(ano_inicio)s")
        params["ano_inicio"] = ano_inicio
    if ano_fim is not None:
        conditions.append("c.ano_assinatura <= %(ano_fim)s")
        params["ano_fim"] = ano_fim

    activity_filter = (
        f"AND EXISTS (SELECT 1 FROM marts.fct_contratos c WHERE {' AND '.join(conditions)})"
        if ano_inicio is not None or ano_fim is not None
        else ""
    )

    sql = f"""
        SELECT * FROM marts.dim_orgaos o
        WHERE true
        {activity_filter}
        ORDER BY nm_unidade_gestora
    """

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()
