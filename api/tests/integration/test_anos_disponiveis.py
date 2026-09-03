import pytest

pytestmark = pytest.mark.integration


def test_anos_disponiveis_reflete_intervalo_real_do_fixture(client):
    # Fixture (tests/fixtures/contratos.py) cobre ano_assinatura de 2023 a 2025
    # nas linhas de 2016+. A linha CT-TESTE-PRE2016 (2014) é cortada em
    # stg_contratos (spec 034), então não puxa ano_min pra 2014; e o piso
    # GREATEST(..., 2016) do endpoint só entra em ação quando o menor ano real
    # é anterior a 2016 (ver test_cobertura_oficial.py).
    response = client.get("/api/v1/anos-disponiveis")

    assert response.status_code == 200
    body = response.json()
    assert body == {"ano_min": 2023, "ano_max": 2025}
