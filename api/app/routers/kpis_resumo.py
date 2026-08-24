from fastapi import APIRouter

from app.db import get_connection
from app.schemas.kpis_resumo import KpisResumo

router = APIRouter(tags=["kpis-resumo"])


@router.get(
    "/kpis-resumo",
    response_model=KpisResumo,
    description=(
        "KPIs resumo da home (spec 026) — agregado em 1 linha sobre marts.mart_escalada_custo. "
        "Sem campos de SUM de valor (valor_total/total_aditivos) — achado durante a spec 026: "
        "fl_valor_suspeito não cobre 13 contratos com |vl_variacao| > R$100mi (gap de detecção "
        "anterior à spec 021, não corrigido aqui), então qualquer SUM de vl_atual/vl_variacao fica "
        "sensível a um único outlier não sinalizado. Contagens (count) não são afetadas por esse "
        "gap — a classificação de um contrato como outlier não muda se ele é contado ou não."
    ),
)
async def get_kpis_resumo() -> dict:
    sql = """
        SELECT
            count(*) AS total_contratos,
            count(DISTINCT id_contratado) AS fornecedores_distintos,
            count(DISTINCT cod_unidade_gestora) AS orgaos_distintos,
            count(*) FILTER (WHERE vl_variacao <> 0) AS contratos_com_aditivo
        FROM marts.mart_escalada_custo
    """

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            return await cur.fetchone()
