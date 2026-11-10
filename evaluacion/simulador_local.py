"""Simulador local del agente de verificación (SOLO para tests y evaluación offline).

La app NUNCA usa este simulador: si Claude no está disponible, la transferencia
queda retenida para que la revise un operador del banco. Este módulo imita las
respuestas de Claude con reglas sencillas para poder probar el flujo completo sin
red ni coste (tests automáticos y `python -m evaluacion.evaluar --motor local`).
"""
from backend import config
from backend.reglas_riesgo import normalizar_texto


_PATRONES = {
    "falso_tecnico": ["microsoft", "tecnico", "virus", "ordenador", "anydesk", "teamviewer",
                      "acceso remoto", "programa", "hackea"],
    "falso_banco": ["del banco", "cuenta segura", "mover el dinero", "mi dinero esta en peligro",
                    "empleado", "codigo", "proteger mi dinero", "fraude en mi cuenta"],
    "falsa_autoridad": ["policia", "guardia civil", "hacienda", "juzgado", "multa", "abogado",
                        "detenido", "fianza"],
    "hijo_en_apuros": ["numero nuevo", "movil nuevo", "se le ha roto", "hola mama", "hola papa",
                       "me ha escrito mi", "por whatsapp", "un apuro", "esta en apuros"],
    "inversion_cripto": ["bitcoin", "cripto", "inversion", "invertir", "rentabilidad",
                         "ganar dinero", "duplicar"],
    "premio_herencia": ["premio", "loteria", "herencia", "sorteo", "he ganado", "tasas"],
    "romance": ["mi novio", "mi novia", "por internet", "nos conocimos", "militar",
                "me quiere", "no le conozco en persona"],
    "compra_online": ["aduana", "paquete retenido", "envio retenido"],
    "coaccion_familiar": ["me obliga", "se enfada", "me grita", "tengo miedo", "no me deja",
                          "me ha amenazado", "me amenaza", "me lo exige"],
}
_SENALES_SENCILLAS = {
    "falso_tecnico": "Habla de un técnico, de un virus o de instalar un programa en el ordenador.",
    "falso_banco": "Alguien que dice ser del banco le pide mover su dinero.",
    "falsa_autoridad": "Alguien que dice ser de la policía, Hacienda o un juzgado le pide dinero.",
    "hijo_en_apuros": "Un supuesto familiar le pide dinero desde un número o un mensaje nuevo.",
    "inversion_cripto": "Le prometen ganar dinero rápido con una inversión.",
    "premio_herencia": "Le piden pagar antes para cobrar un premio o una herencia.",
    "romance": "Le pide dinero alguien a quien solo conoce por internet.",
    "compra_online": "Le piden pagar por un paquete retenido o un envío.",
    "coaccion_familiar": "Alguien le está presionando o le da miedo.",
}
_SENALES_LEGITIMAS = [
    "reforma", "obra", "factura", "comunidad", "dentista", "le he llamado yo",
    "lo he decidido yo", "lo he decidido yo sola", "lo he decidido yo solo", "regalo",
    "cumpleanos", "boda", "alquiler", "le conozco", "la conozco", "de toda la vida",
    "nadie", "yo sola", "yo solo", "he hablado con el", "he hablado con ella",
]
_PREGUNTAS = [
    "Gracias, {nombre}. ¿Ha tomado usted esta decisión por su cuenta, o alguien la ha llamado "
    "o le ha escrito para pedirle el dinero?",
    "Entendido. Una pregunta más: ¿conoce en persona a {destino} y ha podido comprobarlo "
    "llamando usted al número de siempre?",
    "Por último, ¿hay alguien con usted ahora mismo, o al teléfono, diciéndole lo que tiene "
    "que hacer?",
]
_EXPLICACIONES = {
    "falso_tecnico": "Ninguna empresa como Microsoft llama para cobrar por arreglar un ordenador.",
    "falso_banco": "Su banco nunca le pedirá que mueva su dinero a otra cuenta para protegerlo.",
    "falsa_autoridad": "La policía y Hacienda nunca piden dinero por teléfono ni por transferencia.",
    "hijo_en_apuros": "Los estafadores se hacen pasar por hijos o nietos desde números nuevos.",
    "inversion_cripto": "Nadie puede garantizar ganancias rápidas; es un engaño muy habitual.",
    "premio_herencia": "Ningún premio ni herencia de verdad exige pagar antes para cobrarlo.",
    "romance": "Pedir dinero a alguien que solo se conoce por internet es un engaño muy común.",
    "compra_online": "Las aduanas no cobran paquetes con transferencias a particulares.",
    "coaccion_familiar": "Nadie debería presionarle para disponer de su dinero.",
}


def _evaluar_heuristico(transferencia: dict, cuenta: dict, mensajes: list[dict],
                        senales: dict, turno: int, memoria: dict | None = None) -> dict:
    textos_cliente = " ".join(m["texto"] for m in mensajes if m["rol"] == "cliente")
    texto = normalizar_texto(textos_cliente)
    nivel_reglas = (transferencia.get("evaluacion") or {}).get("nivel", "bajo")

    detectadas = {cat: [p for p in patrones if p in texto] for cat, patrones in _PATRONES.items()}
    detectadas = {cat: ps for cat, ps in detectadas.items() if ps}
    legitimas = [p for p in _SENALES_LEGITIMAS if p in texto]

    puntos = {"alto": 25, "medio": 10}.get(nivel_reglas, 0)
    puntos += 35 * len(detectadas)
    puntos += senales.get("nivel_porcentaje", 0) // 3
    if senales.get("menciona_tercero"):
        puntos += 15
    puntos -= 15 * len(legitimas)
    nivel = max(0, min(100, puntos))
    if ((memoria or {}).get("perfil") or {}).get("alerta"):
        # La cuenta ya apareció en un intento de estafa: ninguna explicación la vuelve segura.
        nivel = max(nivel, 60)

    categoria = max(detectadas, key=lambda c: len(detectadas[c])) if detectadas else "ninguna"
    lista_senales = [_SENALES_SENCILLAS[cat] for cat in detectadas]
    lista_senales += senales.get("indicadores", [])
    nombre = cuenta["nombre_corto"]
    contacto = cuenta.get("contacto_nombre") or "su contacto de emergencia"

    if nivel >= 60 or (turno >= config.MAX_TURNOS_VERIFICACION and nivel >= 40):
        explicacion = _EXPLICACIONES.get(categoria, "Hay varias cosas que me hacen pensar en un engaño.")
        return {
            "respuesta": (
                f"{nombre}, esto tiene las señales de una estafa. {explicacion} "
                "Su dinero está a salvo: he parado la transferencia y un operador del banco la "
                f"revisará con usted. Le recomiendo avisar a {contacto}."
            ),
            "decision": "riesgo",
            "nivel_riesgo": max(nivel, 60),
            "categoria": categoria if categoria != "ninguna" else "otra",
            "senales": lista_senales,
            "resumen_para_contacto": (
                f"Señales detectadas: {'; '.join(lista_senales) or 'respuestas poco claras'}."
            ),
        }
    if turno >= min(3, config.MAX_TURNOS_VERIFICACION) or (turno >= 2 and legitimas and nivel < 20):
        return {
            "respuesta": (
                f"Muchas gracias, {nombre}. Todo parece en orden. "
                "Si lo desea, ya puede confirmar el envío."
            ),
            "decision": "seguro",
            "nivel_riesgo": nivel,
            "categoria": "ninguna",
            "senales": lista_senales,
            "resumen_para_contacto": (
                f"{cuenta['titular']} ha explicado el motivo de la transferencia y no se han "
                "detectado señales de estafa."
            ),
        }
    pregunta = _PREGUNTAS[min(turno - 1, len(_PREGUNTAS) - 1)]
    return {
        "respuesta": pregunta.format(nombre=nombre, destino=transferencia["beneficiario_nombre"]),
        "decision": "preguntar",
        "nivel_riesgo": nivel,
        "categoria": categoria,
        "senales": lista_senales,
        "resumen_para_contacto": "",
    }


async def responder_como_claude(transferencia: dict, cuenta: dict, mensajes: list[dict],
                                senales: dict, turno: int, memoria: dict | None = None) -> dict:
    """Sustituto de `agente_silvershield._preguntar_a_claude` (misma firma)."""
    return _evaluar_heuristico(transferencia, cuenta, mensajes, senales, turno, memoria)
