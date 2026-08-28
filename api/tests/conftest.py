import json
from pathlib import Path

import pytest


def _ensure_vite_manifest_stub() -> None:
    """Garante que `api/app/static/.vite/manifest.json` exista antes de
    `app.main` ser importado (spec 033).

    `app/main.py` lê esse manifest em nível de módulo (`_load_main_entry()`,
    spec 027, REQ-4 — fail-fast intencional, não é pra ser enfraquecido) e
    monta `StaticFiles(directory=api/app/static)`; em produção esse arquivo
    vem do build real do Vite (`npm run build` em `web/`, copiado pelo
    Dockerfile), mas `api/app/static/` é gitignored — não existe num
    checkout limpo (ex.: runner do CI), então a importação falhava antes de
    chegar nos routers de `/api/v1/*` que esta suíte testa.

    `_load_main_entry()` só lê o JSON e monta duas strings (`main_js`/
    `main_css`) — nunca abre os arquivos JS/CSS referenciados. As rotas
    testadas aqui são só `/api/v1/*`, nunca `/static/*` nem as páginas HTML,
    então um manifest forjado nunca precisa ser servido de verdade.

    Se um manifest real já existir (ambiente local após `npm run build`),
    não sobrescreve — respeita o build real.
    """
    static_dir = Path(__file__).resolve().parent.parent / "app" / "static"
    manifest_path = static_dir / ".vite" / "manifest.json"
    if manifest_path.exists():
        return
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps({"src/main.ts": {"file": "assets/main-stub.js", "css": []}}),
        encoding="utf-8",
    )


_ensure_vite_manifest_stub()

from starlette.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    """TestClient como context manager dispara o lifespan da app (abre/fecha
    o pool real de Postgres via app.db.open_pool/close_pool) — sem isso, as
    rotas veriam o pool fechado. Escopo de sessão: dados de teste são só
    leitura (schema `marts` construído uma vez pelo dbt antes da suíte
    rodar), não há necessidade de abrir/fechar por teste."""
    with TestClient(app) as c:
        yield c
