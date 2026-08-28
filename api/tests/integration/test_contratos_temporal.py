import pytest

pytestmark = pytest.mark.integration


def test_recorte_por_orgao_soma_contratos_do_periodo(client):
    # ORG_A em 2023 só tem as linhas 1 (mar/2023) e 8 (jun/2023) — meses
    # diferentes, então int_contratos_evolucao_por_orgao gera 2 linhas
    # mensais distintas no recorte 'Órgão'. cod_unidade_gestora filtra
    # implicitamente pro recorte 'Órgão' (os outros dois recortes têm
    # cod_unidade_gestora NULL).
    response = client.get(
        "/api/v1/contratos-temporal",
        params={"cod_unidade_gestora": "900001", "ano_inicio": 2023, "ano_fim": 2023},
    )

    assert response.status_code == 200
    body = response.json()

    assert len(body) == 2
    assert all(r["tp_recorte"] == "Órgão" for r in body)
    assert sum(r["qt_contratos"] for r in body) == 2


def test_filtro_ano_sem_resultado_retorna_lista_vazia(client):
    response = client.get("/api/v1/contratos-temporal", params={"ano_inicio": 2099})

    assert response.status_code == 200
    assert response.json() == []
