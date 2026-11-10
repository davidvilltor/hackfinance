"""Pruebas de extremo a extremo de la API (Claude imitado por el simulador local, sin red)."""
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


def test_paginas_y_estado(cliente, sin_ia):
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


def test_verificacion_detecta_estafa_retiene_y_avisa(cliente, operador):
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

    # El cliente no puede autorizarla; solo un operador del banco puede liberarla.
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


def test_palabra_de_auxilio_retiene_en_silencio(cliente, operador):
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


def test_usa_la_respuesta_estructurada_de_claude(cliente, operador, claude_falso):
    async def falso_claude(_contexto):
        return {
            "respuesta": "Nadie del banco le pedirá mover su dinero. La he parado.",
            "decision": "riesgo", "nivel_riesgo": 140, "categoria": "falso_banco",
            "senales": ["Pide mover el dinero a una cuenta segura"],
            "resumen_para_contacto": "Falso empleado del banco.",
        }
    claude_falso(falso_claude)
    tid = crear(cliente, 2000)["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    datos = responder(cliente, tid, "El del banco me ha dicho que la mueva a una cuenta segura")
    assert datos["motor"] == "claude"
    assert datos["nivel_riesgo"] == 100           # se acota a 0-100
    t = cliente.get(f"/api/transferencias/{tid}").json()["transferencia"]
    assert t["categoria_estafa"] == "falso_banco"


def _comprobar_retenida_para_operador(cliente, tid, datos, saldo_inicial):
    assert datos["decision"] == "no_verificada" and datos["final"] is True
    assert datos["transferencia"]["estado"] == "retenida"
    assert datos["contacto_avisado"] is True
    assert cliente.post(f"/api/transferencias/{tid}/autorizar").status_code == 409
    assert saldo(cliente) == saldo_inicial


def test_sin_clave_de_ia_la_verificacion_se_retiene_para_el_operador(cliente, sin_ia):
    """Sin IA no hay chatbot de reserva: la transferencia queda retenida al instante."""
    inicial = saldo(cliente)
    tid = crear(cliente, 900, IBAN_CARLOS, "Carlos López", "Reforma")["transferencia"]["id"]
    datos = cliente.post(f"/api/transferencias/{tid}/verificacion").json()
    _comprobar_retenida_para_operador(cliente, tid, datos, inicial)
    assert len(datos["mensajes"]) == 1 and "operador" in datos["mensajes"][0]["texto"]
    # Solo un operador del banco puede pararla o liberarla.
    assert cliente.post(f"/api/transferencias/{tid}/cancelar").status_code == 401
    # No se puede abrir una conversación sobre una transferencia ya retenida.
    assert cliente.post(f"/api/transferencias/{tid}/verificacion/mensajes",
                        json={"texto": "Hola"}).status_code == 409


def test_sin_clave_de_ia_el_operador_decide(operador, sin_ia):
    inicial = saldo(operador)
    tid = crear(operador, 900, IBAN_CARLOS, "Carlos López", "Reforma")["transferencia"]["id"]
    operador.post(f"/api/transferencias/{tid}/verificacion")
    panel = operador.get("/api/panel").json()
    assert panel["alertas"][0]["tipo"] == "NO_VERIFICADA"
    t = operador.get(f"/api/transferencias/{tid}").json()["transferencia"]
    assert t["veredicto_ia"] == "no_verificada" and t["motor_ia"] == "sin_ia"
    assert operador.post(f"/api/transferencias/{tid}/liberar").status_code == 200
    assert saldo(operador) == inicial - 900


def _claude_caido(claude_falso):
    async def claude_caido(_contexto):
        raise TimeoutError("sin conexión")
    claude_falso(claude_caido)


def test_si_claude_falla_queda_retenida_sin_chatbot_local(cliente, operador, claude_falso):
    """Fallar de forma segura: sin conexión con la IA no se sigue con un evaluador local;
    la transferencia queda retenida para un operador del banco."""
    _claude_caido(claude_falso)
    inicial = saldo(cliente)
    tid = crear(cliente, 900, IBAN_CARLOS, "Carlos López", "Reforma")["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    datos = responder(cliente, tid, "Es para pagar la reforma del baño de mi hijo")
    assert datos["motor"] == "sin_ia"
    _comprobar_retenida_para_operador(cliente, tid, datos, inicial)
    assert cliente.get("/api/panel").json()["alertas"][0]["tipo"] == "NO_VERIFICADA"


def test_si_claude_falla_a_mitad_tambien_se_retiene(cliente, claude_falso):
    llamadas = []

    async def claude_que_se_cae(_contexto):
        llamadas.append(1)
        if len(llamadas) > 1:
            raise ConnectionError("sin conexión")
        return {"respuesta": "¿Quién le ha pedido el dinero?", "decision": "preguntar",
                "nivel_riesgo": 20, "categoria": "ninguna", "senales": [],
                "resumen_para_contacto": "", "recordar": []}
    claude_falso(claude_que_se_cae)
    tid = crear(cliente, 2000)["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    assert responder(cliente, tid, "Es para una cosa")["decision"] == "preguntar"
    datos = responder(cliente, tid, "Me lo ha pedido un amigo")
    assert datos["decision"] == "no_verificada"
    assert datos["transferencia"]["estado"] == "retenida"


def test_claude_no_puede_inventarse_una_decision(cliente, claude_falso):
    async def claude_raro(_contexto):
        return {"respuesta": "Vale", "decision": "no_verificada", "nivel_riesgo": 0,
                "categoria": "ninguna", "senales": [], "resumen_para_contacto": ""}
    claude_falso(claude_raro)
    tid = crear(cliente, 2000)["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    datos = responder(cliente, tid, "Es para la comunidad de vecinos")
    assert datos["motor"] == "sin_ia" and datos["transferencia"]["estado"] == "retenida"


def test_la_respuesta_incluye_las_senales_para_explicar_el_bloqueo(cliente, operador):
    tid = crear(cliente, 2500)["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    datos = responder(cliente, tid, "Me ha llamado uno de la policía, dice que hay que pagar una "
                                    "fianza urgente por mi nieto")
    assert datos["decision"] == "riesgo"
    assert datos["categoria"] == "falsa_autoridad"
    assert datos["senales"] and all("Menciona:" not in s for s in datos["senales"])
    # Cada turno guarda cuánto tardó, para el panel.
    mensajes = cliente.get(f"/api/transferencias/{tid}").json()["mensajes"]
    assert "tiempo_ms" in mensajes[-1]["senales"]


def test_texto_con_html_se_guarda_como_texto(cliente, operador):
    tid = crear(cliente, 2000)["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    malicioso = '<img src=x onerror="alert(1)"> es para la comunidad'
    responder(cliente, tid, malicioso)
    mensajes = cliente.get(f"/api/transferencias/{tid}").json()["mensajes"]
    assert mensajes[1]["texto"] == malicioso      # se guarda tal cual; el frontend lo pinta con textContent


def test_texto_demasiado_largo_se_rechaza(cliente):
    tid = crear(cliente, 2000)["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    r = cliente.post(f"/api/transferencias/{tid}/verificacion/mensajes", json={"texto": "a" * 2001})
    assert r.status_code == 422


def test_a_un_destinatario_nuevo_no_se_puede_enviar_sin_verificar(cliente):
    """'Conozco al destinatario' solo vale para cuentas a las que ya ha enviado dinero."""
    datos = crear(cliente, 800)          # cuenta nueva
    assert datos["evaluacion"]["permite_autorizacion_directa"] is False
    r = cliente.post(f"/api/transferencias/{datos['transferencia']['id']}/autorizar")
    assert r.status_code == 409
    assert "verificación" in r.json()["detail"]


def test_a_un_habitual_con_riesgo_alto_tampoco(cliente):
    datos = crear(cliente, 7000, IBAN_CARLOS, "Carlos López", "Bitcoin urgente")
    assert datos["evaluacion"]["nivel"] == "alto"
    assert datos["evaluacion"]["permite_autorizacion_directa"] is False
    assert cliente.post(f"/api/transferencias/{datos['transferencia']['id']}/autorizar").status_code == 409


def test_la_liberacion_queda_registrada_como_del_operador(cliente, operador):
    tid = crear(cliente, 2500, concepto="Soporte técnico")["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    responder(cliente, tid, "Me ha llamado un técnico de Microsoft y me ha instalado AnyDesk")
    r = cliente.post(f"/api/transferencias/{tid}/liberar")
    assert r.json()["transferencia"]["via"] == "liberada_operador"
