import os
import sys
import tempfile
from pathlib import Path

import pytest

# Entorno aislado: base de datos temporal y sin claves de API reales.
_DB_TEMPORAL = Path(tempfile.mkdtemp()) / "test.db"
os.environ["SILVERSHIELD_DB"] = str(_DB_TEMPORAL)
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["ANTHROPIC_AUTH_TOKEN"] = ""
os.environ["ELEVENLABS_API_KEY"] = ""
os.environ["OPERADORES"] = "operadora:clave-de-prueba,otro:otra-clave"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from backend import agente_silvershield, config  # noqa: E402
from backend.main import app  # noqa: E402
from evaluacion.simulador_local import responder_como_claude  # noqa: E402

_PREGUNTAR_A_CLAUDE_REAL = agente_silvershield._preguntar_a_claude

CREDENCIALES = {"usuario": "operadora", "contrasena": "clave-de-prueba"}


def entrar(cliente):
    r = cliente.post("/api/operador/acceso", json=CREDENCIALES)
    assert r.status_code == 200, r.text


@pytest.fixture(autouse=True)
def ia_simulada(monkeypatch):
    """Claude "disponible" en los tests, imitado por el simulador local (sin red).
    Los tests que quieran probar la IA sin clave usan el fixture `sin_ia`."""
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(agente_silvershield, "_preguntar_a_claude", responder_como_claude)


@pytest.fixture()
def sin_ia(monkeypatch):
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", None)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)


@pytest.fixture()
def claude_falso(monkeypatch):
    """Devuelve una función para sustituir la llamada real a Claude (`_llamar_claude`)
    por un doble de prueba, pasando por el código real que construye el contexto."""
    def usar(falso):
        monkeypatch.setattr(agente_silvershield, "_preguntar_a_claude", _PREGUNTAR_A_CLAUDE_REAL)
        monkeypatch.setattr(agente_silvershield, "_llamar_claude", falso)
    return usar


@pytest.fixture()
def cliente():
    """Cliente de la app SIN sesión de operador (como la app de la persona mayor)."""
    with TestClient(app) as c:
        entrar(c)
        c.post("/api/demo/reiniciar")
        c.post("/api/operador/salir")
        c.cookies.clear()
        yield c


@pytest.fixture()
def operador(cliente):
    """El mismo cliente, con la sesión de operador abierta."""
    entrar(cliente)
    return cliente
