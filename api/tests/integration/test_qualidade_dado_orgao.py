import pytest

pytestmark = pytest.mark.integration


def test_qualidade_dado_orgao_conta_flags_como_metrica_nao_como_filtro(client):
    # ORG_A: 5 contratos, 1 com fl_aditivo_inconsistente (linha 3), 0 com
    # fl_valor_suspeito. ORG_B: 3 contratos, 0 com fl_aditivo_inconsistente
    # (fl_aditivo_inconsistente da linha 4 é NULL, não true — vladitado=0),
    # 1 com fl_valor_suspeito (linha 4).
    response = client.get("/api/v1/qualidade-dado-orgao")

    assert response.status_code == 200
    body = response.json()
    by_cod = {o["cod_unidade_gestora"]: o for o in body}

    org_a = by_cod["900001"]
    assert org_a["qt_contratos"] == 5
    assert org_a["qt_aditivo_inconsistente"] == 1
    assert float(org_a["perc_aditivo_inconsistente"]) == 20.0
    assert org_a["qt_valor_suspeito"] == 0

    org_b = by_cod["900002"]
    assert org_b["qt_contratos"] == 3
    assert org_b["qt_aditivo_inconsistente"] == 0
    assert org_b["qt_valor_suspeito"] == 1
    assert float(org_b["perc_valor_suspeito"]) == 33.33


def test_qualidade_dado_orgao_filtro_ano_sem_resultado_retorna_lista_vazia(client):
    response = client.get("/api/v1/qualidade-dado-orgao", params={"ano_inicio": 2099})

    assert response.status_code == 200
    assert response.json() == []
