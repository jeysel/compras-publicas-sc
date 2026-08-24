from fastapi import APIRouter, Query

from app.db import get_connection
from app.schemas.concentracao_fornecedor import ConcentracaoFornecedor

router = APIRouter(tags=["concentracao-fornecedor"])


@router.get(
    "/concentracao-fornecedor",
    response_model=list[ConcentracaoFornecedor],
    description=(
        "Concentração de gasto por fornecedor (mart_concentracao_fornecedor, spec 007/013/014/024/029). "
        "A mart tem grão (órgão, fornecedor, ano_assinatura) desde a spec 029 — rank/perc armazenados na "
        "mart só valem dentro de um único ano, então este endpoint sempre reagrega (SUM) e recalcula "
        "rank/perc no próprio SQL sobre o intervalo ano_inicio/ano_fim informado (ou sobre todo o "
        "histórico, se nenhum dos dois for informado — resultado idêntico ao grão antigo, pré-spec-029). "
        "Com cod_unidade_gestora informado, ordena e limita por rank_no_orgao recalculado. Sem "
        "cod_unidade_gestora, agrega por fornecedor somando todos os órgãos e ordena por rank_estado "
        "recalculado; cod_unidade_gestora/nm_unidade_gestora exibidos passam a ser o órgão de maior gasto "
        "do fornecedor dentro do intervalo (antes era um órgão arbitrário via DISTINCT ON)."
    ),
)
async def get_concentracao_fornecedor(
    cod_unidade_gestora: str | None = Query(None, description="Código da unidade gestora"),
    ano_inicio: int | None = Query(None, description="Ano inicial de ano_assinatura (inclusive)"),
    ano_fim: int | None = Query(None, description="Ano final de ano_assinatura (inclusive)"),
    top_n: int = Query(10, ge=1, le=100, description="Quantidade máxima de fornecedores retornados"),
) -> list[dict]:
    params: dict = {"top_n": top_n}
    ano_conditions = []
    if ano_inicio is not None:
        ano_conditions.append("ano_assinatura >= %(ano_inicio)s")
        params["ano_inicio"] = ano_inicio
    if ano_fim is not None:
        ano_conditions.append("ano_assinatura <= %(ano_fim)s")
        params["ano_fim"] = ano_fim

    if cod_unidade_gestora is not None:
        params["cod_unidade_gestora"] = cod_unidade_gestora
        where = " AND ".join(["cod_unidade_gestora = %(cod_unidade_gestora)s", *ano_conditions])
        sql = f"""
            WITH filtrado AS (
                SELECT cod_unidade_gestora, nm_unidade_gestora, id_contratado, nm_contratado,
                       vl_total_fornecedor_orgao
                FROM marts.mart_concentracao_fornecedor
                WHERE {where}
            ),
            agregado AS (
                SELECT
                    cod_unidade_gestora, nm_unidade_gestora, id_contratado, nm_contratado,
                    sum(vl_total_fornecedor_orgao) AS vl_total_fornecedor_orgao
                FROM filtrado
                GROUP BY 1, 2, 3, 4
            )
            SELECT
                cod_unidade_gestora, nm_unidade_gestora, id_contratado, nm_contratado,
                vl_total_fornecedor_orgao,
                sum(vl_total_fornecedor_orgao) OVER ()                       AS vl_total_orgao,
                rank() OVER (ORDER BY vl_total_fornecedor_orgao DESC)        AS rank_no_orgao,
                round(
                    vl_total_fornecedor_orgao * 100.0
                    / nullif(sum(vl_total_fornecedor_orgao) OVER (), 0), 2
                )                                                            AS perc_sobre_total_orgao
            FROM agregado
            ORDER BY rank_no_orgao
            LIMIT %(top_n)s
        """
    else:
        where = f"WHERE {' AND '.join(ano_conditions)}" if ano_conditions else ""
        sql = f"""
            WITH filtrado AS (
                SELECT cod_unidade_gestora, nm_unidade_gestora, id_contratado, nm_contratado,
                       vl_total_fornecedor_orgao
                FROM marts.mart_concentracao_fornecedor
                {where}
            ),
            por_orgao AS (
                -- Soma por (fornecedor, órgão) dentro do intervalo — necessário porque, com
                -- ano no grão da mart, um mesmo (fornecedor, órgão) pode ter mais de uma linha
                -- (uma por ano) dentro do intervalo filtrado.
                SELECT
                    cod_unidade_gestora, nm_unidade_gestora, id_contratado, nm_contratado,
                    sum(vl_total_fornecedor_orgao) AS vl_total_fornecedor_orgao
                FROM filtrado
                GROUP BY 1, 2, 3, 4
            ),
            agregado AS (
                SELECT
                    id_contratado,
                    max(nm_contratado)                                                    AS nm_contratado,
                    sum(vl_total_fornecedor_orgao)                                         AS vl_total_fornecedor_estado,
                    -- Órgão de maior gasto do fornecedor no intervalo, só para exibição —
                    -- substitui o DISTINCT ON arbitrário do grão antigo (pré-spec-029).
                    (array_agg(cod_unidade_gestora ORDER BY vl_total_fornecedor_orgao DESC))[1] AS cod_unidade_gestora,
                    (array_agg(nm_unidade_gestora ORDER BY vl_total_fornecedor_orgao DESC))[1]  AS nm_unidade_gestora
                FROM por_orgao
                GROUP BY id_contratado
            )
            SELECT
                cod_unidade_gestora, nm_unidade_gestora, id_contratado, nm_contratado,
                vl_total_fornecedor_estado,
                sum(vl_total_fornecedor_estado) OVER ()                      AS vl_total_estado,
                rank() OVER (ORDER BY vl_total_fornecedor_estado DESC)       AS rank_estado,
                round(
                    vl_total_fornecedor_estado * 100.0
                    / nullif(sum(vl_total_fornecedor_estado) OVER (), 0), 2
                )                                                            AS perc_sobre_total_estado
            FROM agregado
            ORDER BY rank_estado
            LIMIT %(top_n)s
        """

    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()
