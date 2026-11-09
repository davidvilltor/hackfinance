"""Acceso de los operadores del banco: solo ellos pueden ver el panel y liberar o
cancelar transferencias retenidas."""
import base64
import time

from backend import acceso_operador
from conftest import CREDENCIALES, entrar

IBAN_NUEVO_ES = "ES4814650100722030876293"


def crear_retenida(cliente):
    tid = cliente.post("/api/transferencias", json={
        "beneficiario_nombre": "Soporte Técnico Global", "iban": IBAN_NUEVO_ES,
        "importe": 2500, "concepto": "Soporte técnico",
    }).json()["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    datos = cliente.post(f"/api/transferencias/{tid}/verificacion/mensajes", json={
        "texto": "Me ha llamado un técnico de Microsoft y me ha hecho instalar AnyDesk"}).json()
    assert datos["transferencia"]["estado"] == "retenida"
    return tid


def test_sin_sesion_no_se_entra_en_el_panel(cliente):
    r = cliente.get("/panel", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/acceso"
    assert cliente.get("/acceso").status_code == 200
    assert cliente.get("/api/panel").status_code == 401
    assert cliente.post("/api/demo/reiniciar").status_code == 401


def test_sin_sesion_no_se_puede_liberar_ni_ver_el_detalle(cliente):
    tid = crear_retenida(cliente)
    assert cliente.post(f"/api/transferencias/{tid}/liberar").status_code == 401
    assert cliente.post(f"/api/transferencias/{tid}/cancelar").status_code == 401
    assert cliente.get(f"/api/transferencias/{tid}").status_code == 401
    assert cliente.get(f"/api/transferencias/{tid}").json()["detail"].startswith("Acceso reservado")


def test_contrasena_incorrecta(cliente):
    for datos in ({"usuario": "operadora", "contrasena": "mal"},
                  {"usuario": "nadie", "contrasena": "clave-de-prueba"}):
        r = cliente.post("/api/operador/acceso", json=datos)
        assert r.status_code == 401
        assert acceso_operador.COOKIE not in r.cookies
    assert cliente.get("/api/panel").status_code == 401


def test_la_cookie_es_httponly_y_samesite(cliente):
    r = cliente.post("/api/operador/acceso", json=CREDENCIALES)
    cabecera = r.headers["set-cookie"].lower()
    assert "httponly" in cabecera and "samesite=strict" in cabecera


def test_el_operador_libera_y_queda_registrado(cliente):
    tid = crear_retenida(cliente)
    entrar(cliente)
    assert cliente.get("/panel", follow_redirects=False).status_code == 200
    assert cliente.get("/api/panel").json()["operador"] == "operadora"
    t = cliente.post(f"/api/transferencias/{tid}/liberar").json()["transferencia"]
    assert t["estado"] == "completada"
    assert t["via"] == "liberada_operador" and t["operador"] == "operadora"


def test_el_operador_cancela_una_retenida_y_queda_registrado(cliente):
    tid = crear_retenida(cliente)
    entrar(cliente)
    t = cliente.post(f"/api/transferencias/{tid}/cancelar").json()["transferencia"]
    assert t["estado"] == "cancelada" and t["operador"] == "operadora"


def test_el_cliente_puede_cancelar_lo_suyo_sin_sesion(cliente):
    """Cancelar una transferencia que aún no está retenida no necesita operador."""
    tid = cliente.post("/api/transferencias", json={
        "beneficiario_nombre": "Fontanería García", "iban": IBAN_NUEVO_ES, "importe": 800,
    }).json()["transferencia"]["id"]
    r = cliente.post(f"/api/transferencias/{tid}/cancelar")
    assert r.status_code == 200 and r.json()["transferencia"]["operador"] is None


def test_salir_cierra_la_sesion(cliente):
    entrar(cliente)
    assert cliente.get("/api/panel").status_code == 200
    cliente.post("/api/operador/salir")
    cliente.cookies.clear()      # el navegador borra la cookie al recibir la orden
    assert cliente.get("/api/panel").status_code == 401


def test_una_cookie_manipulada_no_vale(cliente):
    caducidad = int(time.time()) + 3600
    falsa = base64.urlsafe_b64encode(f"operadora|{caducidad}|firmafalsa".encode()).decode()
    cliente.cookies.set(acceso_operador.COOKIE, falsa)
    assert cliente.get("/api/panel").status_code == 401
    cliente.cookies.set(acceso_operador.COOKIE, "basura")
    assert cliente.get("/api/panel").status_code == 401


def test_una_sesion_caducada_no_vale(cliente, monkeypatch):
    # Se fabrica una cookie bien firmada pero caducada y se envía a mano.
    from fastapi import Response
    monkeypatch.setattr(acceso_operador.config, "OPERADOR_SESION_HORAS", -1)
    respuesta = Response()
    acceso_operador.abrir_sesion(respuesta, "operadora")
    token = respuesta.headers["set-cookie"].split(";")[0].split("=", 1)[1]
    cliente.cookies.set(acceso_operador.COOKIE, token)
    assert cliente.get("/api/panel").status_code == 401
