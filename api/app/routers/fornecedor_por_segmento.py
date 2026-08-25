from datetime import date

from fastapi import APIRouter, Query, Response
from pydantic import TypeAdapter

from app.db import get_connection
from app.schemas.fornecedor_por_segmento import FornecedorPorSegmentoContrato, FornecedorPorSegmentoGrafico

router = APIRouter(tags=["fornecedor-por-segmento"])

_adapter = TypeAdapter(list[FornecedorPorSegmentoContrato])


@router.get(
    "/fornecedor-por-segmento",
    response_model=list[FornecedorPorSegmentoGrafico],
    description=(
        "Top fornecedores por ramo de atividade (spec 031) — agrega marts.fct_contratos_ramo por "
        "(ramo_atividade, id_contratado, nm_contratado) direto no SQL, sem mart nova (mesmo padrão de "
        "qualidade_dado_orgao.py). Sem ramo_atividade informado, o ranking mistura fornecedores de "
        "diferentes ramos, ordenado só por valor. Exclui fl_valor_suspeito = true (spec 021/031, REQ-16) — "
        "achado real: sem esse filtro, o topo do ranking era dominado por contratos com corrupção de dado "
        "conhecida (Piata Comercio de Pecas, VS Vida Saudavel, Claro), não gasto real."
    ),
)
async def get_fornecedor_por_segmento(
    ramo_atividade: str | None = Query(None, description="Ramo de atividade (18 ramos + 'Outros')"),
    top_n: int = Query(10, ge=1, le=100, description="Quantidade máxima de fornecedores retornados"),
    dt_inicio_de: date | None = Query(
        None, description="Filtra contratos com dt_inicio a partir desta data (inclusive)"
    ),
    dt_inicio_ate: date | None = Query(
        None, description="Filtra contratos com dt_inicio até esta data (inclusive)"
    ),
) -> list[dict]:
    conditions = ["fl_valor_suspeito IS NOT TRUE"]
    params: dict = {"top_n": top_n}
    if ramo_atividade is not None:
        conditions.append("ramo_atividade = %(ramo_atividade)s")
        params["ramo_atividade"] = ramo_atividade
    # Mesma semântica do endpoint /contratos (spec 031): filtra só por dt_inicio, registros
    # com dt_inicio NULL sempre aparecem, independente do filtro estar ativo.
    if dt_inicio_de is not None:
        conditions.append("(dt_inicio IS NULL OR dt_inicio >= %(dt_inicio_de)s)")
        params["dt_inicio_de"] = dt_inicio_de
    if dt_inicio_ate is not None:
        conditions.append("(dt_inicio IS NULL OR dt_inicio <= %(dt_inicio_ate)s)")
        params["dt_inicio_ate"] = dt_inicio_ate

    where = f"WHERE {' AND '.join(conditions)}"
    sql = f"""
        SELECT
            ramo_atividade,
            id_contratado,
            nm_contratado,
            sum(vl_atual) AS vl_total
        FROM marts.fct_contratos_ramo
        {where}
        GROUP BY ramo_atividade, id_contratado, nm_contratado
        ORDER BY vl_total DESC
        LIMIT %(top_n)s
    """

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()


@router.get(
    "/fornecedor-por-segmento/contratos",
    response_model=list[FornecedorPorSegmentoContrato],
    description=(
        "Listagem de contratos individuais por segmento (spec 031, REQ-3/REQ-4). SELECT explícito e "
        "estreito (6 colunas) sobre marts.fct_contratos_ramo — validado sob carga real a 512Mi (ver spec "
        "031, seção Validação); qualquer coluna adicional exige repetir esse teste antes do merge (REQ-7). "
        "Exclui fl_valor_suspeito = true (spec 021/031, REQ-16), mesmo critério do endpoint de gráfico. "
        "Response + TypeAdapter (não response_model), mesmo padrão de diversidade_vencedores.py/"
        "contratos_temporal.py, para evitar o OOM de 2026-08-21."
    ),
)
async def get_fornecedor_por_segmento_contratos(
    ramo_atividade: str | None = Query(None, description="Ramo de atividade (18 ramos + 'Outros')"),
    nm_contratado: str | None = Query(None, description="Busca por nome do fornecedor (parcial, case-insensitive)"),
    dt_inicio_de: date | None = Query(
        None, description="Filtra contratos com dt_inicio a partir desta data (inclusive)"
    ),
    dt_inicio_ate: date | None = Query(
        None, description="Filtra contratos com dt_inicio até esta data (inclusive)"
    ),
    limit: int = Query(
        150_000,
        ge=1,
        le=150_000,
        description=(
            "Teto de segurança — não é paginação. O frontend consome o dataset completo (grão é contrato); "
            "volume real em produção ~93978 linhas (spec 031), não reproduzível em dev local (seed menor)."
        ),
    ),
) -> Response:
    conditions = ["fl_valor_suspeito IS NOT TRUE"]
    params: dict = {"limit": limit}
    if ramo_atividade is not None:
        conditions.append("ramo_atividade = %(ramo_atividade)s")
        params["ramo_atividade"] = ramo_atividade
    if nm_contratado is not None:
        conditions.append("nm_contratado ILIKE %(nm_contratado)s")
        params["nm_contratado"] = f"%{nm_contratado}%"
    # Filtra por dt_inicio apenas (não sobreposição de período — decisão consciente, spec 031).
    # Contratos com dt_inicio NULL sempre aparecem, independente do filtro estar ativo (REQ do
    # relatório) — validado manualmente contra o dado real antes de aplicar (118 nulos sempre
    # inclusos, contratos fora do intervalo corretamente excluídos).
    if dt_inicio_de is not None:
        conditions.append("(dt_inicio IS NULL OR dt_inicio >= %(dt_inicio_de)s)")
        params["dt_inicio_de"] = dt_inicio_de
    if dt_inicio_ate is not None:
        conditions.append("(dt_inicio IS NULL OR dt_inicio <= %(dt_inicio_ate)s)")
        params["dt_inicio_ate"] = dt_inicio_ate

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
        SELECT nu_contrato, nm_contratado, vl_atual, dt_inicio, dt_fim_atual, ramo_atividade
        FROM marts.fct_contratos_ramo
        {where}
        ORDER BY nu_contrato DESC
        LIMIT %(limit)s
    """

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            rows = await cur.fetchall()

    # Retorna Response já serializado (bypassa a revalidação/jsonable_encoder
    # do response_model, que duplicava toda a lista em memória — causa do
    # OOM em produção em 2026-08-21 mesmo com dataset pequeno).
    return Response(content=_adapter.dump_json(_adapter.validate_python(rows)), media_type="application/json")
