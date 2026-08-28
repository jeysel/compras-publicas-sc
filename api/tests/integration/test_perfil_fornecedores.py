import pytest

pytestmark = pytest.mark.integration


def test_exclui_fl_valor_suspeito_antes_de_classificar_porte(client):
    # int_contratos_por_fornecedor.sql exclui fl_valor_suspeito ANTES do SUM
    # (spec 021/026). Sem esse filtro, o fornecedor da linha 4
    # (vl_atual=600 milhões) pularia de 'Micro' para 'Grande' — é exatamente
    # o bug histórico documentado no CLAUDE.md (gap de ~R$32,5 bi). Com o
    # filtro correto: F1 (125000, linhas 1/2/7) = 'Pequeno'; F2 (37000,
    # linhas 3/8, linha 4 excluída) e F3 (35000, linhas 5/6) = 'Micro'.
    response = client.get("/api/v1/perfil-fornecedores")

    assert response.status_code == 200
    body = response.json()
    by_porte = {p["porte_fornecedor"]: p for p in body}

    assert by_porte["Pequeno"]["qt_fornecedores"] == 1
    assert float(by_porte["Pequeno"]["valor_total"]) == 125000.0

    assert by_porte["Micro"]["qt_fornecedores"] == 2
    assert float(by_porte["Micro"]["valor_total"]) == 72000.0

    assert "Grande" not in by_porte


def test_filtro_ano_sem_atividade_retorna_lista_vazia(client):
    response = client.get("/api/v1/perfil-fornecedores", params={"ano_inicio": 2099})

    assert response.status_code == 200
    assert response.json() == []
