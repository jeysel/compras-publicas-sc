import pytest

pytestmark = pytest.mark.integration


def test_ranking_por_orgao_exclui_fl_valor_suspeito(client):
    # int_concentracao_fornecedor_por_orgao.sql exclui fl_valor_suspeito
    # ANTES do SUM (mesmo padrão de perfil-fornecedores/dim_fornecedores).
    # Dentro de ORG_A, somando todos os anos: F1=95000 (linhas 1+2),
    # F2=37000 (linhas 3+8), F3=15000 (linha 6) — F1 fica em 1º no ranking.
    response = client.get("/api/v1/concentracao-fornecedor", params={"cod_unidade_gestora": "900001"})

    assert response.status_code == 200
    body = response.json()

    assert len(body) == 3
    assert body[0]["rank_no_orgao"] == 1
    assert float(body[0]["vl_total_fornecedor_orgao"]) == 95000.0


def test_orgao_inexistente_retorna_lista_vazia(client):
    response = client.get("/api/v1/concentracao-fornecedor", params={"cod_unidade_gestora": "ORG-INEXISTENTE"})

    assert response.status_code == 200
    assert response.json() == []
