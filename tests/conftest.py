import os
import sys
import tempfile
from pathlib import Path

import pytest

# Entorno aislado: base de datos temporal y sin claves de API (modo local).
_DB_TEMPORAL = Path(tempfile.mkdtemp()) / "test.db"
os.environ["SILVERSHIELD_DB"] = str(_DB_TEMPORAL)
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["ANTHROPIC_AUTH_TOKEN"] = ""
os.environ["ELEVENLABS_API_KEY"] = ""
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402


@pytest.fixture()
def cliente():
    with TestClient(app) as c:
        c.post("/api/demo/reiniciar")
        yield c
