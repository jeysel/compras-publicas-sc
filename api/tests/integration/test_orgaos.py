import pytest

pytestmark = pytest.mark.integration


def test_orgaos_lista_ambos_orgaos_do_fixture(client):
    # dim_orgaos exclui fl_valor_suspeito ANTES do count/SUM (int_contratos_por_orgao.sql) —
    # por isso ORG_B aqui tem qt_contratos=2 (exclui a linha 4, suspeita), mesmo
    # ORG_B tendo 3 linhas no fixture. Ver também test_qualidade_dado_orgao, que usa
    # mart_escalada_custo (sem essa exclusão) e por isso reporta 3 para ORG_B.
    response = client.get("/api/v1/orgaos")

    assert response.status_code == 200
    body = response.json()
    by_cod = {o["cod_unidade_gestora"]: o for o in body}

    assert by_cod["900001"]["qt_contratos"] == 5
    assert by_cod["900002"]["qt_contratos"] == 2


def test_orgaos_filtro_ano_sem_atividade_retorna_lista_vazia(client):
    response = client.get("/api/v1/orgaos", params={"ano_inicio": 2099})

    assert response.status_code == 200
    assert response.json() == []
