import pytest

pytestmark = pytest.mark.integration


def test_lista_contratos_do_orgao_sem_filtrar_flags_de_qualidade(client):
    # mart_escalada_custo expõe fl_aditivo_inconsistente/fl_valor_suspeito
    # como contexto, não filtro (decisão documentada no próprio .sql) — as 5
    # linhas do ORG_A (1, 2, 3, 6, 8) devem todas aparecer, inclusive a
    # linha 3 (fl_aditivo_inconsistente=true).
    response = client.get("/api/v1/escalada-custo", params={"cod_unidade_gestora": "900001"})

    assert response.status_code == 200
    body = response.json()

    assert len(body) == 5
    assert {c["nu_contrato"] for c in body} == {
        "CT-TESTE-001", "CT-TESTE-002", "CT-TESTE-003", "CT-TESTE-006", "CT-TESTE-008",
    }


def test_filtro_ano_sem_resultado_retorna_lista_vazia(client):
    response = client.get("/api/v1/escalada-custo", params={"ano_inicio": 2099})

    assert response.status_code == 200
    assert response.json() == []
