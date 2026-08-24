from fastapi import APIRouter

from app.db import get_connection
from app.schemas.anos_disponiveis import AnosDisponiveis

router = APIRouter(tags=["anos-disponiveis"])


@router.get(
    "/anos-disponiveis",
    response_model=AnosDisponiveis,
    description=(
        "Intervalo real de ano_assinatura em fct_contratos (grão de contrato, fonte de todo o dado "
        "usado pelos filtros de ano) — usado para popular os dropdowns de ano no frontend sem hardcode "
        "de intervalo, que ficava desatualizado tanto pra trás (dados anteriores a 2016 ficavam de fora) "
        "quanto pra frente (anos futuros sem dado real apareciam como opção)."
    ),
)
async def get_anos_disponiveis() -> dict:
    sql = "SELECT MIN(ano_assinatura)::int AS ano_min, MAX(ano_assinatura)::int AS ano_max FROM marts.fct_contratos"

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            return await cur.fetchone()
