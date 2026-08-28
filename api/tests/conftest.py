import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    """TestClient como context manager dispara o lifespan da app (abre/fecha
    o pool real de Postgres via app.db.open_pool/close_pool) — sem isso, as
    rotas veriam o pool fechado. Escopo de sessão: dados de teste são só
    leitura (schema `marts` construído uma vez pelo dbt antes da suíte
    rodar), não há necessidade de abrir/fechar por teste."""
    with TestClient(app) as c:
        yield c
