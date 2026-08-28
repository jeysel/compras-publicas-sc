import pytest

pytestmark = pytest.mark.integration


def test_modalidades_agrega_contagem_normalizada_por_modalidade(client):
    # dim_modalidades não filtra fl_valor_suspeito (diferente de
    # mart_escalada_custo) — qt_contratos aqui é contagem bruta por
    # nm_modalidade normalizada (Pregão Eletrônico: linhas 1,2,4,6,8 = 5;
    # Dispensa: linhas 3,5,7 = 3).
    response = client.get("/api/v1/modalidades")

    assert response.status_code == 200
    body = response.json()
    by_nome = {m["nm_modalidade"]: m for m in body}

    assert by_nome["Dispensa de Licitação - Leis 8.666/1993 e 14.133/2021"]["qt_contratos"] == 3
    assert by_nome["Pregão Eletrônico - Leis 10.520/2002 e 14.133/2021"]["qt_contratos"] == 5
