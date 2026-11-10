"""Memoria por cliente: SilverShield recuerda lo aprendido en cada verificación y
personaliza las siguientes (reglas y contexto de Claude)."""
from backend import agente_silvershield, config
from backend.agente_silvershield import limpiar_recuerdos
from conftest import entrar

IBAN_PK = "PK36SCBL0000001123456702"          # prima en Pakistán (cuenta nueva)
IBAN_NUEVO_ES = "ES4814650100722030876293"


def crear(cliente, importe, iban=IBAN_PK, nombre="Ayesha Khan", concepto="Estudios"):
    r = cliente.post("/api/transferencias", json={
        "beneficiario_nombre": nombre, "iban": iban, "importe": importe, "concepto": concepto})
    assert r.status_code == 200, r.text
    return r.json()


def responder(cliente, tid, texto):
    r = cliente.post(f"/api/transferencias/{tid}/verificacion/mensajes", json={"texto": texto})
    assert r.status_code == 200, r.text
    return r.json()


def verificar_y_enviar(cliente, importe):
    """Primera transferencia a la prima: se verifica (modo local) y se envía."""
    datos = crear(cliente, importe)
    assert datos["transferencia"]["estado"] == "pendiente_decision"
    tid = datos["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    responder(cliente, tid, "Es para los estudios de mi prima, le pago la factura de la universidad")
    assert responder(cliente, tid, "Lo he decidido yo sola, nadie me ha llamado")["decision"] == "seguro"
    t = cliente.post(f"/api/transferencias/{tid}/autorizar").json()["transferencia"]
    assert t["via"] == "verificada_ia"


def test_lo_de_siempre_no_se_vuelve_a_verificar(cliente):
    verificar_y_enviar(cliente, 400)
    datos = crear(cliente, 550)               # dentro de 1,5 veces lo verificado (600 €)
    assert datos["transferencia"]["estado"] == "completada"
    assert datos["transferencia"]["via"] == "habitual_verificado"
    assert datos["evaluacion"]["destino_habitual_verificado"] is True


def test_un_importe_disparado_vuelve_a_verificar(cliente):
    verificar_y_enviar(cliente, 400)
    datos = crear(cliente, 2000)
    assert datos["transferencia"]["estado"] == "pendiente_decision"
    codigos = {m["codigo"] for m in datos["evaluacion"]["motivos"]}
    assert "IMPORTE_INUSUAL_DESTINATARIO" in codigos


def test_el_importe_habitual_no_crece_sin_volver_a_verificar(cliente):
    """Lo enviado sin verificar no cuenta para subir el límite (evita la escalada)."""
    verificar_y_enviar(cliente, 400)
    assert crear(cliente, 600)["transferencia"]["via"] == "habitual_verificado"
    assert crear(cliente, 700)["transferencia"]["estado"] == "pendiente_decision"


def test_sin_verificacion_previa_no_hay_atajo(cliente):
    """Carlos es habitual pero SilverShield nunca le ha verificado: se sigue preguntando."""
    datos = crear(cliente, 800, "ES9121000418450200051332", "Carlos López", "")
    assert datos["transferencia"]["estado"] == "pendiente_decision"
    assert datos["evaluacion"]["destino_habitual_verificado"] is False


def test_una_cuenta_usada_en_una_estafa_queda_marcada(cliente, operador):
    tid = crear(cliente, 2500, IBAN_NUEVO_ES, "Soporte Técnico Global", "Soporte técnico")["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    assert responder(cliente, tid, "Me ha llamado Microsoft, tengo un virus, me han instalado AnyDesk")["decision"] == "riesgo"
    memoria = cliente.get("/api/memoria").json()["memoria"]
    assert memoria[0]["tipo"] == "alerta" and memoria[0]["iban"] == IBAN_NUEVO_ES

    datos = crear(cliente, 100, IBAN_NUEVO_ES, "Soporte Técnico Global", "")
    assert datos["transferencia"]["estado"] == "pendiente_decision"
    assert datos["evaluacion"]["nivel"] == "alto"
    assert datos["evaluacion"]["permite_autorizacion_directa"] is False
    assert "CUENTA_CON_ALERTA" in {m["codigo"] for m in datos["evaluacion"]["motivos"]}


def test_claude_guarda_y_recibe_la_memoria(cliente, operador, claude_falso):
    contextos = []

    async def falso_claude(contexto):
        contextos.append(contexto)
        return {
            "respuesta": "Todo en orden, María.", "decision": "seguro", "nivel_riesgo": 5,
            "categoria": "ninguna", "senales": [], "resumen_para_contacto": "Ayuda a su prima.",
            "recordar": ["Su prima Ayesha vive en Pakistán; le paga los estudios cada trimestre.",
                         "La clave secreta es girasol."],
        }
    claude_falso(falso_claude)

    tid = crear(cliente, 400)["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    responder(cliente, tid, "Es para los estudios de mi prima Ayesha")
    assert "Sin memoria previa" not in contextos[0]
    assert "primera vez que la clienta envía dinero a esta cuenta" in contextos[0]

    textos = [m["texto"] for m in cliente.get("/api/memoria").json()["memoria"]]
    assert any("Ayesha" in t for t in textos)
    assert not any("girasol" in t.lower() for t in textos)     # nunca se guarda la palabra de auxilio

    cliente.post(f"/api/transferencias/{tid}/autorizar")
    tid2 = crear(cliente, 3000)["transferencia"]["id"]           # más de lo habitual: se verifica
    cliente.post(f"/api/transferencias/{tid2}/verificacion")
    responder(cliente, tid2, "Es la matrícula anual de Ayesha")
    assert "<memoria_cliente>" in contextos[-1]
    assert "Ayesha vive en Pakistán" in contextos[-1]
    assert "el mayor importe verificado fue 400 euros" in contextos[-1]


def test_la_palabra_de_auxilio_se_recuerda_sin_revelarla(cliente, operador):
    tid = crear(cliente, 3000, "ES9121000418450200051332", "Carlos López", "")["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    assert responder(cliente, tid, "Mira qué girasoles más bonitos")["decision"] == "revision"
    memoria = cliente.get("/api/memoria").json()["memoria"]
    assert memoria[0]["tipo"] == "alerta" and "palabra de auxilio" in memoria[0]["texto"]
    assert "girasol" not in memoria[0]["texto"].lower()


def test_la_memoria_es_solo_para_el_operador_y_se_puede_borrar(cliente):
    tid = crear(cliente, 2500, IBAN_NUEVO_ES, "Soporte Técnico Global", "Soporte técnico")["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    responder(cliente, tid, "Me ha llamado Microsoft, tengo un virus, me han instalado AnyDesk")
    assert cliente.get("/api/memoria").status_code == 401
    assert cliente.delete("/api/memoria/1").status_code == 401
    entrar(cliente)
    recuerdo = cliente.get("/api/memoria").json()["memoria"][0]
    assert cliente.delete(f"/api/memoria/{recuerdo['id']}").status_code == 200
    assert cliente.delete(f"/api/memoria/{recuerdo['id']}").status_code == 404
    # Al borrar la alerta, la cuenta deja de estar marcada.
    assert "CUENTA_CON_ALERTA" not in {m["codigo"] for m in crear(cliente, 2500, IBAN_NUEVO_ES)["evaluacion"]["motivos"]}


def test_reiniciar_la_demo_borra_la_memoria(cliente, operador):
    verificar_y_enviar(cliente, 400)
    tid = crear(cliente, 2500, IBAN_NUEVO_ES, "Soporte Técnico Global", "Soporte técnico")["transferencia"]["id"]
    cliente.post(f"/api/transferencias/{tid}/verificacion")
    responder(cliente, tid, "Me ha llamado Microsoft, tengo un virus, me han instalado AnyDesk")
    assert cliente.get("/api/memoria").json()["memoria"]
    cliente.post("/api/demo/reiniciar")
    assert cliente.get("/api/memoria").json()["memoria"] == []


def test_limpiar_recuerdos():
    cuenta = {"palabra_seguridad": "Girasol"}
    largo = "x" * 500
    limpios = limpiar_recuerdos(["  uno  ", "", "Mi palabra es GIRASOL", largo, "dos", "tres"], cuenta)
    assert limpios[0] == "uno"
    assert len(limpios) == 3 and all(len(t) <= 220 for t in limpios)
    assert not any("girasol" in t.lower() for t in limpios)
