import pytest

pytestmark = pytest.mark.integration


def test_identifica_processo_com_multiplos_fornecedores(client):
    # ORG_A tem 4 processos elegíveis (nu_processo sem placeholder): PROC001
    # (linhas 1 e 8, fornecedores F1 e F2 distintos — "Múltiplos
    # fornecedores"), PROC002 (linha 2), PROC003 (linha 3) e PROC004
    # (linha 6), cada um com 1 único fornecedor.
    response = client.get("/api/v1/diversidade-vencedores", params={"cod_unidade_gestora": "900001"})

    assert response.status_code == 200
    body = response.json()

    assert len(body) == 4
    multiplos = [p for p in body if p["ds_diversidade"] == "Múltiplos fornecedores"]
    assert len(multiplos) == 1
    assert multiplos[0]["nu_processo"] == "2023PROC001"
    assert multiplos[0]["qt_fornecedores_distintos"] == 2
    assert multiplos[0]["ano_abertura"] == 2023


def test_filtro_ano_sem_resultado_retorna_lista_vazia(client):
    response = client.get("/api/v1/diversidade-vencedores", params={"ano_inicio": 2099})

    assert response.status_code == 200
    assert response.json() == []
