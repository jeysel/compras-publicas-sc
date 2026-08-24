from fastapi import APIRouter, Query, Response
from pydantic import TypeAdapter

from app.db import get_connection
from app.schemas.diversidade_vencedores import DiversidadeVencedores

router = APIRouter(tags=["diversidade-vencedores"])

_adapter = TypeAdapter(list[DiversidadeVencedores])


@router.get(
    "/diversidade-vencedores",
    response_model=list[DiversidadeVencedores],
    description=(
        "Diversidade de vencedores por processo licitatório (mart_diversidade_vencedores, spec 007). "
        "ano_inicio/ano_fim filtram por ano_abertura (ano de dt_primeiro_contrato, spec 029) — o grão "
        "continua sendo o processo, não período; processos multi-ano ficam atribuídos ao ano de abertura."
    ),
)
async def get_diversidade_vencedores(
    cod_unidade_gestora: str | None = Query(None, description="Código da unidade gestora"),
    ano_inicio: int | None = Query(None, description="Ano inicial de ano_abertura (inclusive)"),
    ano_fim: int | None = Query(None, description="Ano final de ano_abertura (inclusive)"),
    limit: int = Query(
        200_000,
        ge=1,
        le=200_000,
        description=(
            "Teto de segurança — não é paginação. O frontend consome o dataset completo "
            "(grão é processo, não é 'top N'); volume real em staging é ~51812 linhas (2026-08-21)."
        ),
    ),
) -> Response:
    conditions = []
    params: dict = {"limit": limit}
    if cod_unidade_gestora is not None:
        conditions.append("cod_unidade_gestora = %(cod_unidade_gestora)s")
        params["cod_unidade_gestora"] = cod_unidade_gestora
    if ano_inicio is not None:
        conditions.append("ano_abertura >= %(ano_inicio)s")
        params["ano_inicio"] = ano_inicio
    if ano_fim is not None:
        conditions.append("ano_abertura <= %(ano_fim)s")
        params["ano_fim"] = ano_fim

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM marts.mart_diversidade_vencedores {where} ORDER BY cod_unidade_gestora, nu_processo LIMIT %(limit)s"

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            rows = await cur.fetchall()

    # Retorna Response já serializado (bypassa a revalidação/jsonable_encoder
    # do response_model, que duplicava toda a lista em memória — causa do
    # OOM em produção em 2026-08-21 mesmo com dataset pequeno).
    return Response(content=_adapter.dump_json(_adapter.validate_python(rows)), media_type="application/json")
