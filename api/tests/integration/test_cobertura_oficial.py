import pytest

pytestmark = pytest.mark.integration

# Fronteira de cobertura oficial (spec 034): 2016 é o piso. O fixture tem a
# linha CT-TESTE-PRE2016 (assinada em 2014); ela é cortada em stg_contratos e
# não pode aparecer em nenhuma mart nem no intervalo de anos-disponiveis.

PRE_2016 = "CT-TESTE-PRE2016"


def test_contrato_pre_2016_ausente_de_escalada_custo(client):
    response = client.get("/api/v1/escalada-custo")

    assert response.status_code == 200
    numeros = {c["nu_contrato"] for c in response.json()}
    assert numeros  # sanidade: a rota devolveu contratos
    assert PRE_2016 not in numeros


def test_contrato_pre_2016_ausente_de_fornecedor_por_segmento_contratos(client):
    # fct_contratos_ramo é grão de contrato — se a linha de 2014 tivesse
    # vazado de stg_contratos, apareceria nesta listagem também.
    response = client.get("/api/v1/fornecedor-por-segmento/contratos")

    assert response.status_code == 200
    numeros = {c["nu_contrato"] for c in response.json()}
    assert PRE_2016 not in numeros


def test_anos_disponiveis_nunca_abaixo_de_2016(client):
    # Contrato de piso: mesmo que fct_contratos passe a conter linhas
    # anteriores a 2016 (estado possível em produção antes do próximo
    # `dbt build` manual — ingestão é cron gated por ETag, spec 030), o
    # endpoint aplica GREATEST(MIN(ano_assinatura), 2016).
    response = client.get("/api/v1/anos-disponiveis")

    assert response.status_code == 200
    assert response.json()["ano_min"] >= 2016
