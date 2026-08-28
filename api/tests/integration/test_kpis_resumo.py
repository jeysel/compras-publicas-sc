import pytest

pytestmark = pytest.mark.integration


def test_kpis_resumo_agrega_sobre_todo_o_fixture(client):
    # mart_escalada_custo não exclui fl_valor_suspeito/fl_aditivo_inconsistente
    # (decisão documentada no próprio mart — "contexto, não filtro"), por isso
    # as 8 linhas do fixture contam todas aqui. contratos_com_aditivo conta
    # vl_variacao <> 0: linhas 2 (+5000), 3 (+2000) e 4 (+599500000) = 3.
    response = client.get("/api/v1/kpis-resumo")

    assert response.status_code == 200
    assert response.json() == {
        "total_contratos": 8,
        "fornecedores_distintos": 3,
        "orgaos_distintos": 2,
        "contratos_com_aditivo": 3,
    }
