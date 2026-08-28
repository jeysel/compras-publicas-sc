import pytest

pytestmark = pytest.mark.integration

_MOD_PE_NORM = "Pregão Eletrônico - Leis 10.520/2002 e 14.133/2021"


def test_exclui_fl_aditivo_inconsistente_e_fl_valor_suspeito_da_agregacao(client):
    # Mesmo critério de exclusão de variacao-custo-modalidade, aplicado a
    # dias_variacao. Linha 3 (dias_variacao=30) e linha 4 (dias_variacao=5)
    # têm prazo alterado mas são excluídas (inconsistente/suspeita); só a
    # linha 2 (dias_variacao=15, consistente) deve contar.
    response = client.get("/api/v1/variacao-prazo-modalidade")

    assert response.status_code == 200
    body = response.json()

    assert len(body) == 1
    assert body[0]["nm_modalidade"] == _MOD_PE_NORM
    assert body[0]["qt_contratos_com_aditivo_prazo"] == 1
    assert float(body[0]["dias_variacao_media"]) == 15.0


def test_filtro_ano_sem_resultado_retorna_lista_vazia(client):
    response = client.get("/api/v1/variacao-prazo-modalidade", params={"ano_inicio": 2099})

    assert response.status_code == 200
    assert response.json() == []
