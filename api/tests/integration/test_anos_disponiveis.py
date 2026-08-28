import pytest

pytestmark = pytest.mark.integration


def test_anos_disponiveis_reflete_intervalo_real_do_fixture(client):
    # Fixture (tests/fixtures/contratos.py) cobre ano_assinatura de 2023 a 2025.
    response = client.get("/api/v1/anos-disponiveis")

    assert response.status_code == 200
    body = response.json()
    assert body == {"ano_min": 2023, "ano_max": 2025}
