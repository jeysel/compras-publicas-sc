import pytest

pytestmark = pytest.mark.integration

_MOD_PE_NORM = "Pregão Eletrônico - Leis 10.520/2002 e 14.133/2021"


def test_exclui_fl_aditivo_inconsistente_e_fl_valor_suspeito_da_agregacao(client):
    # Caso de borda citado explicitamente na spec 033: linhas com
    # fl_valor_suspeito ou fl_aditivo_inconsistente não podem entrar em
    # agregações de valor. Das linhas com vl_variacao <> 0 no fixture (2, 3 e
    # 4), só a linha 2 (aditivo consistente, não suspeito) deve aparecer —
    # linha 3 é fl_aditivo_inconsistente, linha 4 é fl_valor_suspeito (e
    # tem vl_variacao de +599,5 milhões: se a exclusão falhasse, isso
    # dominaria a média e o teste pegaria o erro).
    response = client.get("/api/v1/variacao-custo-modalidade")

    assert response.status_code == 200
    body = response.json()

    assert len(body) == 1
    assert body[0]["nm_modalidade"] == _MOD_PE_NORM
    assert body[0]["qt_contratos_com_aditivo"] == 1
    assert float(body[0]["perc_variacao_media"]) == 12.5


def test_parametro_ano_invalido_retorna_422(client):
    response = client.get("/api/v1/variacao-custo-modalidade", params={"ano_inicio": "abc"})

    assert response.status_code == 422
