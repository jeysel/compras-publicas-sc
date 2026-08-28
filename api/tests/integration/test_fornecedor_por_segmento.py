import pytest

pytestmark = pytest.mark.integration


def test_exclui_fl_valor_suspeito_no_ranking_do_ramo(client):
    # Linhas 4 e 6 classificam no mesmo ramo ("Combustíveis e Energia"), mas
    # a linha 4 é fl_valor_suspeito=true (vl_atual=600 milhões) — exatamente
    # o caso real documentado no router (REQ-16/spec 021/031): sem o filtro
    # "fl_valor_suspeito IS NOT TRUE", o topo do ranking ficaria dominado por
    # esse outlier em vez do gasto real (linha 6, F3, R$15.000).
    response = client.get("/api/v1/fornecedor-por-segmento", params={"ramo_atividade": "Combustíveis e Energia"})

    assert response.status_code == 200
    body = response.json()

    assert len(body) == 1
    assert float(body[0]["vl_total"]) == 15000.0
    assert body[0]["nm_contratado"] == "Fornecedor Gamma Teste Ltda"


def test_ramo_sem_contrato_retorna_lista_vazia(client):
    response = client.get("/api/v1/fornecedor-por-segmento", params={"ramo_atividade": "Agropecuária"})

    assert response.status_code == 200
    assert response.json() == []
