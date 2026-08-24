from fastapi import APIRouter, Query

from app.db import get_connection
from app.schemas.perfil_fornecedores import PerfilFornecedores

router = APIRouter(tags=["perfil-fornecedores"])


@router.get(
    "/perfil-fornecedores",
    response_model=list[PerfilFornecedores],
    description=(
        "Distribuição de fornecedores por porte (spec 026) — GROUP BY porte_fornecedor sobre "
        "marts.dim_fornecedores; a classificação já vem pronta da mart (dim_fornecedores.sql), "
        "este endpoint só agrega o que já existe, não reclassifica nada. ano_inicio/ano_fim "
        "(spec 029) filtram fornecedores por atividade — ao menos um contrato em fct_contratos "
        "dentro do intervalo — sem recalcular porte_fornecedor, que continua histórico/acumulado."
    ),
)
async def get_perfil_fornecedores(
    ano_inicio: int | None = Query(None, description="Ano inicial de atividade (inclusive)"),
    ano_fim: int | None = Query(None, description="Ano final de atividade (inclusive)"),
) -> list[dict]:
    conditions = ["c.id_contratado = f.id_contratado"]
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
        SELECT
            porte_fornecedor,
            count(*) AS qt_fornecedores,
            sum(vl_total_atual) AS valor_total
        FROM marts.dim_fornecedores f
        WHERE true
        {activity_filter}
        GROUP BY porte_fornecedor
        ORDER BY sum(vl_total_atual) DESC
    """

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()
