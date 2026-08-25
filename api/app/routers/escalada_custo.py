from collections.abc import AsyncIterator
from uuid import uuid4

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import TypeAdapter

from app.db import get_connection
from app.schemas.escalada_custo import EscaladaCusto

router = APIRouter(tags=["escalada-custo"])

_adapter = TypeAdapter(list[EscaladaCusto])

_BATCH_SIZE = 2_000


async def _stream_rows(sql: str, params: dict) -> AsyncIterator[bytes]:
    # Cursor nomeado (server-side): o Postgres mantém o result set e entrega em
    # lotes via fetchmany, em vez do driver puxar as 76 mil linhas de uma vez
    # (fetchall) para dentro do processo Python. Cada lote é validado e
    # serializado isoladamente — nunca existe, ao mesmo tempo, a lista completa
    # de instâncias Pydantic nem a string JSON completa em memória. Causa do
    # OOM em produção em 2026-08-21: TypeAdapter+Response (fetchall + validate
    # + dump_json de uma vez) resolveu contratos-temporal/diversidade-vencedores
    # (10810/51812 linhas) mas piorou o pico de memória em escalada_custo
    # (76041-95508 linhas) — confirmado sob container com limite de 512Mi
    # (mesmo teto do pod em produção): código antigo sobrevive, TypeAdapter
    # não-streaming morre com OOMKilled já na primeira requisição.
    yield b"["
    first = True
    async with get_connection() as conn:
        async with conn.cursor(name=f"escalada_custo_{uuid4().hex}") as cur:
            await cur.execute(sql, params)
            while True:
                batch = await cur.fetchmany(_BATCH_SIZE)
                if not batch:
                    break
                # dump_json de uma lista produz "[...]" — removemos os colchetes
                # para colar os lotes com vírgula e formar um único array JSON.
                chunk = _adapter.dump_json(_adapter.validate_python(batch))
                inner = chunk[1:-1]
                if not inner:
                    continue
                if not first:
                    yield b","
                yield inner
                first = False
    yield b"]"


@router.get(
    "/escalada-custo",
    response_model=list[EscaladaCusto],
    description="Escalada de custo por contrato (mart_escalada_custo, spec 007/013/014).",
)
async def get_escalada_custo(
    cod_unidade_gestora: str | None = Query(None, description="Código da unidade gestora"),
    nm_modalidade: str | None = Query(None, description="Modalidade de licitação"),
    ano_inicio: int | None = Query(None, description="Ano inicial de assinatura do contrato (inclusive)"),
    ano_fim: int | None = Query(None, description="Ano final de assinatura do contrato (inclusive)"),
    limit: int = Query(
        150_000,
        ge=1,
        le=150_000,
        description=(
            "Teto de segurança — não é paginação. O frontend consome o dataset completo "
            "(grão é contrato, 1:1 com raw.contratos); volume real em dev é ~76041 linhas, "
            "teto de raw.contratos confirmado em 95508 linhas (spec 019, 2026-08-21)."
        ),
    ),
) -> StreamingResponse:
    conditions = []
    params: dict = {"limit": limit}
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
        SELECT * FROM marts.mart_escalada_custo
        {where}
        ORDER BY cod_unidade_gestora, nu_contrato
        LIMIT %(limit)s
    """

    return StreamingResponse(_stream_rows(sql, params), media_type="application/json")
