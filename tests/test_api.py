"""Pruebas de extremo a extremo de la API en modo local (sin claves de API)."""
from backend import agente_silvershield, config

IBAN_CARLOS = "ES9121000418450200051332"        # beneficiario habitual
IBAN_NUEVO_ES = "ES4814650100722030876293"
IBAN_VG = "VG96VPVG0000012345678901"


def crear(cliente, importe, iban=IBAN_NUEVO_ES, nombre="Soporte Técnico Global", concepto=""):
    r = cliente.post("/api/transferencias", json={
        "beneficiario_nombre": nombre, "iban": iban, "importe": importe, "concepto": concepto,
    })
    assert r.status_code == 200, r.text
    return r.json()


def responder(cliente, tid, texto):
    r = cliente.post(f"/api/transferencias/{tid}/verificacion/mensajes", json={"texto": texto})
    assert r.status_code == 200, r.text
    return r.json()


def saldo(cliente):
    return cliente.get("/api/cuenta").json()["cuenta"]["saldo"]


def test_paginas_y_estado(cliente):
    assert cliente.get("/").status_code == 200
    assert cliente.get("/panel").status_code == 200
    assert cliente.get("/static/js/app.js").status_code == 200
    estado = cliente.get("/api/estado").json()
    assert estado["ia"] is False and estado["umbral_verificacion"] == 500


def test_la_pantalla_del_cliente_no_expone_la_palabra_de_auxilio(cliente):
    assert "palabra_seguridad" not in cliente.get("/api/cuenta").json()["cuenta"]


def test_transferencia_pequena_a_conocido_se_completa_directamente(cliente):
    inicial = saldo(cliente)
    datos = crear(cliente, 120, IBAN_CARLOS, "Carlos López")
    assert datos["transferencia"]["estado"] == "completada"
    assert datos["transferencia"]["via"] == "directa"
    assert saldo(cliente) == inicial - 120


def test_transferencia_pequena_a_pais_de_riesgo_pide_confirmacion(cliente):
    datos = crear(cliente, 300, IBAN_VG, "Global Assets Ltd")
    assert datos["transferencia"]["estado"] == "pendiente_decision"
    assert datos["evaluacion"]["nivel"] == "alto"


def test_conozco_al_destinatario_autoriza_directamente(cliente):
    inicial = saldo(cliente)
    tid = crear(cliente, 800, IBAN_CARLOS, "Carlos López")["transferencia"]["id"]
    r = cliente.post(f"/api/transferencias/{tid}/autorizar")
    assert r.status_code == 200
    assert r.json()["transferencia"]["via"] == "autorizada_cliente"
    assert saldo(cliente) == inicial - 800
    # No se puede autorizar dos veces
    assert cliente.post(f"/api/transferencias/{tid}/autorizar").status_code == 409


def test_verificacion_detecta_estafa_retiene_y_avisa(cliente):
    inicial = saldo(cliente)
    tid = crear(cliente, 2500, concepto="Soporte técnico")["transferencia"]["id"]
    inicio = cliente.post(f"/api/transferencias/{tid}/verificacion").json()
    assert inicio["mensajes"][0]["rol"] == "asistente"
    assert "2.500 euros" in inicio["mensajes"][0]["texto"]

    datos = responder(cliente, tid, "Me ha llamado un chico de Microsoft diciendo que tengo un virus "
                                    "en el ordenador y que tengo que pagar urgente")
    assert datos["decision"] == "riesgo" and datos["final"] is True
    assert datos["transferencia"]["estado"] == "retenida"
    assert datos["contacto_avisado"] is True
    assert datos["respuesta"]["audio_url"].startswith("/api/voz/mensajes/")
    assert saldo(cliente) == inicial

    panel = cliente.get("/api/panel").json()
    assert panel["alertas"][0]["tipo"] == "POSIBLE_ESTAFA"
    assert panel["alertas"][0]["transferencia_id"] == tid

    # El cliente no puede autorizarla; el contacto de confianza sí puede liberarla.
    assert cliente.post(f"/api/transferencias/{tid}/autorizar").status_code == 409
    assert cliente.post(f"/api/transferencias/{tid}/liberar").status_code == 200
    assert saldo(cliente) == inicial - 2500


def test_verificacion_legitima_recomienda_seguir(cliente):
    tid = crear(cliente, 900, IBAN_CARLOS, "Carlos López", "Reforma")["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    primera = responder(cliente, tid, "Es para pagar la reforma del baño de mi hijo")
    assert primera["decision"] == "preguntar"
    segunda = responder(cliente, tid, "Lo he decidido yo sola, nadie me ha llamado, le he llamado yo")
    assert segunda["decision"] == "seguro"
    assert segunda["transferencia"]["estado"] == "verificada_segura"
    r = cliente.post(f"/api/transferencias/{tid}/autorizar")
    assert r.json()["transferencia"]["via"] == "verificada_ia"


def test_la_conversacion_termina_en_el_maximo_de_turnos(cliente):
    tid = crear(cliente, 700)["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    datos = None
    for _ in range(config.MAX_TURNOS_VERIFICACION):
        datos = responder(cliente, tid, "Pues para una cosa")
        if datos["final"]:
            break
    assert datos["final"] is True
    assert datos["decision"] in {"seguro", "riesgo"}


def test_palabra_de_auxilio_retiene_en_silencio(cliente):
    tid = crear(cliente, 3000, IBAN_CARLOS, "Carlos López")["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    datos = responder(cliente, tid, "Es para mi sobrino, me gustan mucho los girasoles")
    assert datos["decision"] == "revision"
    assert "estafa" not in datos["respuesta"]["texto"].lower()
    assert datos["transferencia"]["estado"] == "retenida"
    assert cliente.get("/api/panel").json()["alertas"][0]["tipo"] == "COACCION"


def test_errores_de_validacion(cliente):
    r = cliente.post("/api/transferencias", json={
        "beneficiario_nombre": "X Y", "iban": "ES9121000418450200051333", "importe": 10,
    })
    assert r.status_code == 422 and "número de cuenta" in r.json()["detail"]
    r = cliente.post("/api/transferencias", json={
        "beneficiario_nombre": "X Y", "iban": IBAN_CARLOS, "importe": 99999,
    })
    assert r.status_code == 400 and "saldo" in r.json()["detail"]


def test_cancelar(cliente):
    tid = crear(cliente, 1000)["transferencia"]["id"]
    assert cliente.post(f"/api/transferencias/{tid}/cancelar").json()["transferencia"]["estado"] == "cancelada"
    assert cliente.post(f"/api/transferencias/{tid}/verificacion").status_code == 409


def test_audio_sin_elevenlabs_devuelve_503(cliente):
    tid = crear(cliente, 1000)["transferencia"]["id"]
    mensaje = cliente.post(f"/api/transferencias/{tid}/verificacion").json()["mensajes"][0]
    assert cliente.get(mensaje["audio_url"]).status_code == 503


def test_usa_la_respuesta_estructurada_de_claude(cliente, monkeypatch):
    async def falso_claude(_contexto):
        return {
            "respuesta": "Nadie del banco le pedirá mover su dinero. La he parado.",
            "decision": "riesgo", "nivel_riesgo": 140, "categoria": "falso_banco",
            "senales": ["Pide mover el dinero a una cuenta segura"],
            "resumen_para_contacto": "Falso empleado del banco.",
        }
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(agente_silvershield, "_llamar_claude", falso_claude)
    tid = crear(cliente, 2000)["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    datos = responder(cliente, tid, "El del banco me ha dicho que la mueva a una cuenta segura")
    assert datos["motor"] == "claude"
    assert datos["nivel_riesgo"] == 100           # se acota a 0-100
    t = cliente.get(f"/api/transferencias/{tid}").json()["transferencia"]
    assert t["categoria_estafa"] == "falso_banco"


def test_si_claude_falla_usa_el_evaluador_local(cliente, monkeypatch):
    async def claude_caido(_contexto):
        raise TimeoutError("sin conexión")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(agente_silvershield, "_llamar_claude", claude_caido)
    tid = crear(cliente, 2000)["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    datos = responder(cliente, tid, "Es para la comunidad de vecinos")
    assert datos["motor"] == "reglas"
