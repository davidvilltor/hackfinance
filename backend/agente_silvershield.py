"""Agente conversacional de verificación de SilverShield.

Cada turno envía a Claude el contexto de la transferencia, las alertas del motor
de reglas, los indicadores de voz y la conversación completa, y recibe una
respuesta estructurada (JSON validado por esquema) con lo que hay que decir en
voz alta y la decisión: seguir preguntando, "seguro" o "riesgo".

Si Claude no está configurado, un evaluador heurístico local mantiene la demo
funcionando con la misma interfaz. Si Claude SÍ está configurado pero falla
(sin conexión, timeout, respuesta inválida...), el evaluador local puede seguir
preguntando o detectar una estafa, pero nunca da una transferencia por buena:
en ese caso la decisión es "no_verificada" y la operación queda retenida
(principio de "fallar de forma segura").
"""
import json
import logging
import time
from pathlib import Path
from typing import Literal

import anthropic
from pydantic import BaseModel, Field, ValidationError

from backend import config
from backend.reglas_riesgo import euros_hablados, nombre_pais, normalizar_texto

log = logging.getLogger("silvershield.agente")

# "no_verificada" solo la genera el servidor (nunca Claude): la IA falló y no se
# puede dar la transferencia por buena.
Decision = Literal["preguntar", "seguro", "riesgo", "no_verificada"]
CATEGORIAS = [
    "ninguna", "falso_banco", "falso_tecnico", "falsa_autoridad", "hijo_en_apuros",
    "inversion_cripto", "premio_herencia", "romance", "compra_online",
    "coaccion_familiar", "otra",
]


class ResultadoTurno(BaseModel):
    respuesta: str
    decision: Decision
    nivel_riesgo: int = Field(ge=0, le=100)
    categoria: str = "ninguna"
    senales: list[str] = []
    resumen_para_contacto: str = ""
    motor: str = "reglas"
    tiempo_ia_ms: int | None = None   # cuánto ha tardado Claude (None si no se usó)
    fallo_ia: bool = False            # Claude estaba configurado pero no respondió bien
    # Tokens consumidos en la llamada a Claude (para medir el coste por verificación).
    # La salida incluye el razonamiento interno del modelo, que también se factura.
    tokens_entrada: int = 0
    tokens_salida: int = 0


ESQUEMA_RESPUESTA = {
    "type": "object",
    "properties": {
        "respuesta": {"type": "string"},
        "decision": {"type": "string", "enum": ["preguntar", "seguro", "riesgo"]},
        "nivel_riesgo": {"type": "integer"},
        "categoria": {"type": "string", "enum": CATEGORIAS},
        "senales": {"type": "array", "items": {"type": "string"}},
        "resumen_para_contacto": {"type": "string"},
    },
    "required": ["respuesta", "decision", "nivel_riesgo", "categoria", "senales",
                 "resumen_para_contacto"],
    "additionalProperties": False,
}

_RUTA_PROMPT = Path(__file__).resolve().parent.parent / "prompts" / "prompt_sistema.txt"
_cliente: anthropic.AsyncAnthropic | None = None
_fallbacks_soportados = True


def _prompt_sistema() -> str:
    return _RUTA_PROMPT.read_text(encoding="utf-8").strip()


def _obtener_cliente() -> anthropic.AsyncAnthropic:
    global _cliente
    if _cliente is None:
        _cliente = anthropic.AsyncAnthropic(
            api_key=config.ANTHROPIC_API_KEY,
            timeout=config.CLAUDE_TIMEOUT_S,
            max_retries=1,
        )
    return _cliente


# --------------------------------------------------------------------------- apertura

def mensaje_apertura(transferencia: dict, cuenta: dict) -> str:
    """Primer mensaje (plantilla, sin esperar a la IA para que sea instantáneo)."""
    destino = transferencia["beneficiario_nombre"]
    pais = transferencia["pais"]
    donde = "" if pais == config.PAIS_LOCAL else f", a una cuenta de {nombre_pais(pais)}"
    return (
        f"Hola, {cuenta['nombre_corto']}. Soy SilverShield, el asistente de seguridad de su banco. "
        f"Quiere enviar {euros_hablados(transferencia['importe'])} a {destino}{donde}. "
        "Antes de enviarlo le haré un par de preguntas sencillas. "
        "Yo nunca le pediré contraseñas ni códigos. "
        "Para empezar, cuénteme: ¿para qué es este dinero?"
    )


# --------------------------------------------------------------------------- contexto

def _construir_contexto(transferencia: dict, cuenta: dict, mensajes: list[dict],
                        senales: dict, turno: int) -> str:
    evaluacion = transferencia.get("evaluacion") or {}
    motivos = evaluacion.get("motivos") or []
    lineas_motivos = "\n".join(f"- {m['texto']}" for m in motivos) or "- (ninguno)"
    conversacion = "\n".join(
        f"{'SilverShield' if m['rol'] == 'asistente' else 'Cliente'}: {m['texto']}"
        for m in mensajes
    )
    indicadores = "\n".join(f"- {i}" for i in senales.get("indicadores", [])) or "- (ninguno)"
    ultimo = turno >= config.MAX_TURNOS_VERIFICACION
    instruccion_turno = (
        "Este es el ÚLTIMO turno: debes decidir \"seguro\" o \"riesgo\"."
        if ultimo else
        f"Turno {turno} de un máximo de {config.MAX_TURNOS_VERIFICACION}."
    )
    return f"""<transferencia>
Cliente: {cuenta['titular']} ({cuenta.get('edad', '?')} años). Nombre de pila: {cuenta['nombre_corto']}.
Contacto de emergencia: {cuenta.get('contacto_nombre')} ({cuenta.get('contacto_relacion') or 'relación no indicada'}).
Importe: {euros_hablados(transferencia['importe'])}. Saldo disponible: {euros_hablados(cuenta['saldo'])}.
Destinatario: {transferencia['beneficiario_nombre']}.
Cuenta en: {nombre_pais(transferencia['pais'])}. Destinatario {'nuevo' if evaluacion.get('beneficiario_nuevo') else 'habitual'}.
Concepto escrito por el cliente: {transferencia.get('concepto') or '(vacío)'}
Alertas del motor de reglas (nivel {evaluacion.get('nivel', 'desconocido')}):
{lineas_motivos}
</transferencia>

<indicadores_voz>
Nivel de estrés estimado en la última respuesta: {senales.get('nivel_porcentaje', 0)}% ({senales.get('estado', 'sin datos')})
{indicadores}
</indicadores_voz>

<conversacion>
{conversacion}
</conversacion>

{instruccion_turno}"""


# --------------------------------------------------------------------------- Claude

def _extraer_json(respuesta) -> dict:
    textos = [b.text for b in respuesta.content if getattr(b, "type", None) == "text"]
    for texto in reversed(textos):
        try:
            return json.loads(texto)
        except json.JSONDecodeError:
            continue
    raise ValueError("La respuesta del modelo no contiene JSON válido")


async def _llamar_claude(contexto: str) -> dict:
    """Llama a Claude y devuelve el JSON de la respuesta. Añade la clave "_uso" con
    los tokens consumidos (el llamador la retira antes de validar)."""
    global _fallbacks_soportados
    cliente = _obtener_cliente()
    peticion = dict(
        model=config.CLAUDE_MODEL,
        max_tokens=4000,
        system=_prompt_sistema(),
        messages=[{"role": "user", "content": contexto}],
        output_config={
            "effort": config.CLAUDE_EFFORT,
            "format": {"type": "json_schema", "schema": ESQUEMA_RESPUESTA},
        },
    )
    if _fallbacks_soportados:
        try:
            # Si el modelo principal rechaza la petición por un falso positivo de
            # sus filtros de seguridad, el servidor reintenta con otro modelo.
            respuesta = await cliente.beta.messages.create(
                **peticion,
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.BadRequestError as error:
            log.warning("Fallback de servidor no disponible (%s); se desactiva.", error)
            _fallbacks_soportados = False
            respuesta = await cliente.messages.create(**peticion)
    else:
        respuesta = await cliente.messages.create(**peticion)

    if respuesta.stop_reason == "refusal":
        raise RuntimeError("El modelo ha rechazado la petición")
    if respuesta.stop_reason == "max_tokens":
        raise RuntimeError("Respuesta truncada por max_tokens")
    datos = _extraer_json(respuesta)
    uso = respuesta.usage
    datos["_uso"] = {
        "entrada": (uso.input_tokens or 0) + (getattr(uso, "cache_read_input_tokens", 0) or 0)
                   + (getattr(uso, "cache_creation_input_tokens", 0) or 0),
        "salida": uso.output_tokens or 0,
    }
    return datos


# --------------------------------------------------------------------------- heurística

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
                        senales: dict, turno: int) -> dict:
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


# --------------------------------------------------------------------------- API pública

async def evaluar_turno(transferencia: dict, cuenta: dict, mensajes: list[dict],
                        senales: dict) -> ResultadoTurno:
    """Evalúa la última respuesta del cliente y devuelve el siguiente paso."""
    turno = sum(1 for m in mensajes if m["rol"] == "cliente")
    datos: dict | None = None
    motor = "reglas"
    tiempo_ia_ms = None
    uso = {"entrada": 0, "salida": 0}
    if config.ia_disponible():
        inicio = time.perf_counter()
        try:
            contexto = _construir_contexto(transferencia, cuenta, mensajes, senales, turno)
            datos = await _llamar_claude(contexto)
            uso = datos.pop("_uso", uso)
            if datos.get("decision") not in ("preguntar", "seguro", "riesgo"):
                raise ValueError(f"Decisión no permitida: {datos.get('decision')!r}")
            motor = "claude"
        except Exception as error:  # noqa: BLE001 - cualquier fallo -> modo local
            datos = None
            log.error("Fallo al consultar Claude, se usa el evaluador local: %s", error)
        tiempo_ia_ms = int((time.perf_counter() - inicio) * 1000)
    if datos is None:
        datos = _evaluar_heuristico(transferencia, cuenta, mensajes, senales, turno)

    datos["nivel_riesgo"] = max(0, min(100, int(datos.get("nivel_riesgo", 0))))
    try:
        resultado = ResultadoTurno(**datos, motor=motor)
    except ValidationError as error:
        log.error("Respuesta con formato inesperado (%s); se usa el evaluador local.", error)
        datos = _evaluar_heuristico(transferencia, cuenta, mensajes, senales, turno)
        resultado = ResultadoTurno(**datos, motor="reglas")
    resultado.tiempo_ia_ms = tiempo_ia_ms
    resultado.tokens_entrada, resultado.tokens_salida = uso["entrada"], uso["salida"]
    resultado.fallo_ia = config.ia_disponible() and resultado.motor != "claude"

    # Garantía: la conversación nunca se alarga más allá del máximo de turnos.
    if resultado.decision == "preguntar" and turno >= config.MAX_TURNOS_VERIFICACION:
        if resultado.nivel_riesgo >= 40:
            resultado.decision = "riesgo"
            resultado.respuesta = (
                f"{cuenta['nombre_corto']}, no tengo claro que esta transferencia sea segura. "
                "Por precaución la he parado y un operador del banco la revisará con usted. "
                "Su dinero está a salvo. "
                f"Le recomiendo avisar a {cuenta.get('contacto_nombre')} para que lo hablen con calma."
            )
        else:
            resultado.decision = "seguro"
            resultado.respuesta = (
                f"Gracias, {cuenta['nombre_corto']}. No veo señales de engaño. "
                "Si lo desea, ya puede confirmar el envío."
            )

    # Fallar de forma segura: sin la IA no se da ninguna transferencia por buena.
    if resultado.fallo_ia and resultado.decision == "seguro":
        _marcar_no_verificada(resultado, cuenta)
    return resultado


def _marcar_no_verificada(resultado: ResultadoTurno, cuenta: dict) -> None:
    resultado.decision = "no_verificada"
    resultado.categoria = "ninguna"
    resultado.respuesta = (
        f"{cuenta['nombre_corto']}, ahora mismo no puedo terminar la comprobación por un "
        "problema técnico. Por precaución he dejado la transferencia parada y su dinero está "
        "a salvo. Un operador del banco la revisará y le llamará para terminarla con usted."
    )
    resultado.senales = [*resultado.senales, "No se pudo completar la verificación con la IA."]
    resultado.resumen_para_contacto = (
        "SilverShield no ha podido completar la verificación con la IA por un fallo técnico. "
        "La transferencia ha quedado retenida por precaución: el operador debe hablar con "
        f"{cuenta['titular']} antes de liberarla."
    )
