"""Agente conversacional de verificación de SilverShield.

Cada turno envía a Claude el contexto de la transferencia, las alertas del motor
de reglas, los indicadores de voz, la memoria de la clienta (lo aprendido en
verificaciones anteriores) y la conversación completa, y recibe una respuesta
estructurada (JSON validado por esquema) con lo que hay que decir en voz alta, la
decisión (seguir preguntando, "seguro" o "riesgo") y los hechos que conviene
recordar para la próxima vez.

Si Claude no está configurado (sin clave) o falla (sin conexión, timeout,
respuesta inválida...), no hay ningún evaluador de reserva: la decisión es
"no_verificada" y la operación queda retenida para que un operador del banco la
autorice o la pare tras hablar con el titular ("fallar de forma segura").
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

# "no_verificada" solo la genera el servidor (nunca Claude): la IA no está disponible
# y la transferencia queda retenida para un operador.
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
    motor: str = "claude"             # "sin_ia" si la IA no estaba disponible
    tiempo_ia_ms: int | None = None   # cuánto ha tardado Claude (None si no se usó)
    fallo_ia: bool = False            # la IA no estaba configurada o no respondió bien
    # Tokens consumidos en la llamada a Claude (para medir el coste por verificación).
    # La salida incluye el razonamiento interno del modelo, que también se factura.
    tokens_entrada: int = 0
    tokens_salida: int = 0
    # Hechos que SilverShield quiere recordar de esta clienta para la próxima vez.
    recordar: list[str] = []


ESQUEMA_RESPUESTA = {
    "type": "object",
    "properties": {
        "respuesta": {"type": "string"},
        "decision": {"type": "string", "enum": ["preguntar", "seguro", "riesgo"]},
        "nivel_riesgo": {"type": "integer"},
        "categoria": {"type": "string", "enum": CATEGORIAS},
        "senales": {"type": "array", "items": {"type": "string"}},
        "resumen_para_contacto": {"type": "string"},
        "recordar": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["respuesta", "decision", "nivel_riesgo", "categoria", "senales",
                 "resumen_para_contacto", "recordar"],
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

MAX_RECUERDOS_POR_TURNO = 3
MAX_LARGO_RECUERDO = 220


def limpiar_recuerdos(recuerdos: list[str], cuenta: dict) -> list[str]:
    """Filtra lo que se guarda en la memoria: pocos hechos, cortos y sin datos sensibles.
    Nunca se guarda la palabra de auxilio (si apareciera, el hecho se descarta)."""
    palabra = normalizar_texto(cuenta.get("palabra_seguridad") or "")
    limpios = []
    for texto in recuerdos or []:
        texto = " ".join(str(texto).split())[:MAX_LARGO_RECUERDO]
        if not texto or (palabra and palabra in normalizar_texto(texto)):
            continue
        limpios.append(texto)
    return limpios[:MAX_RECUERDOS_POR_TURNO]


def _texto_memoria(memoria: dict | None, transferencia: dict) -> str:
    if not memoria:
        return "Sin memoria previa de esta clienta."
    perfil = memoria.get("perfil") or {}
    lineas = []
    if perfil.get("envios"):
        maximo = perfil.get("importe_max_verificado")
        lineas.append(
            f"Envíos anteriores completados a esta misma cuenta: {perfil['envios']}"
            f" (verificados por SilverShield: {perfil.get('envios_verificados', 0)}"
            + (f"; el mayor importe verificado fue {euros_hablados(maximo)}" if maximo else "")
            + ")."
        )
    else:
        lineas.append("Es la primera vez que la clienta envía dinero a esta cuenta.")
    if perfil.get("alerta"):
        lineas.append("ATENCIÓN: esta cuenta ya apareció en un intento de estafa anterior.")
    iban = transferencia.get("iban")
    propios = [m for m in memoria.get("hechos", []) if m.get("iban") == iban]
    otros = [m for m in memoria.get("hechos", []) if m.get("iban") != iban]
    if propios:
        lineas.append("Lo que recuerdas de verificaciones anteriores con este destinatario:")
        lineas += [f"- ({m['fecha'][:10]}, {m['tipo']}) {m['texto']}" for m in propios]
    if otros:
        lineas.append("Alertas recientes de la clienta con otros destinatarios:")
        lineas += [f"- ({m['fecha'][:10]}) {m['texto']}" for m in otros]
    return "\n".join(lineas)


def _construir_contexto(transferencia: dict, cuenta: dict, mensajes: list[dict],
                        senales: dict, turno: int, memoria: dict | None = None) -> str:
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

<memoria_cliente>
{_texto_memoria(memoria, transferencia)}
</memoria_cliente>

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


# --------------------------------------------------------------------------- API pública

async def _preguntar_a_claude(transferencia: dict, cuenta: dict, mensajes: list[dict],
                             senales: dict, turno: int, memoria: dict | None) -> dict:
    contexto = _construir_contexto(transferencia, cuenta, mensajes, senales, turno, memoria)
    return await _llamar_claude(contexto)


async def evaluar_turno(transferencia: dict, cuenta: dict, mensajes: list[dict],
                        senales: dict, memoria: dict | None = None) -> ResultadoTurno:
    """Evalúa la última respuesta del cliente y devuelve el siguiente paso.

    `memoria` = {"perfil": historial con este destinatario, "hechos": recuerdos}.
    Si Claude no está configurado o no responde bien, la decisión es "no_verificada":
    no hay plan B automático, la transferencia queda retenida para un operador."""
    turno = sum(1 for m in mensajes if m["rol"] == "cliente")
    if not config.ia_disponible():
        log.error("Verificación sin IA configurada (falta ANTHROPIC_API_KEY): se retiene.")
        return resultado_no_verificada(cuenta)

    inicio = time.perf_counter()
    try:
        datos = await _preguntar_a_claude(transferencia, cuenta, mensajes, senales, turno, memoria)
        uso = datos.pop("_uso", {"entrada": 0, "salida": 0})
        if datos.get("decision") not in ("preguntar", "seguro", "riesgo"):
            raise ValueError(f"Decisión no permitida: {datos.get('decision')!r}")
        datos["nivel_riesgo"] = max(0, min(100, int(datos.get("nivel_riesgo", 0))))
        resultado = ResultadoTurno(**datos, motor="claude")
    except Exception as error:  # noqa: BLE001 - cualquier fallo -> retenida
        log.error("Fallo al consultar Claude; la transferencia queda retenida: %s", error)
        resultado = resultado_no_verificada(cuenta)
        resultado.tiempo_ia_ms = int((time.perf_counter() - inicio) * 1000)
        return resultado
    resultado.tiempo_ia_ms = int((time.perf_counter() - inicio) * 1000)
    resultado.tokens_entrada, resultado.tokens_salida = uso["entrada"], uso["salida"]

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

    # Solo se recuerda algo cuando hay una decisión final.
    resultado.recordar = (limpiar_recuerdos(resultado.recordar, cuenta)
                          if resultado.decision in ("seguro", "riesgo") else [])
    return resultado


def resultado_no_verificada(cuenta: dict) -> ResultadoTurno:
    """La IA no está disponible: la transferencia se retiene para un operador del banco."""
    return ResultadoTurno(
        decision="no_verificada",
        nivel_riesgo=0,
        motor="sin_ia",
        fallo_ia=True,
        respuesta=(
            f"{cuenta['nombre_corto']}, ahora mismo no puedo hacer la comprobación por un "
            "problema técnico. Por precaución he dejado la transferencia parada y su dinero está "
            "a salvo. Un operador del banco la revisará y le llamará para terminarla con usted."
        ),
        senales=["No se pudo hacer la verificación con la IA (sin conexión o sin configurar)."],
        resumen_para_contacto=(
            "SilverShield no ha podido verificar la transferencia con la IA por un problema "
            "técnico. Ha quedado retenida por precaución: el operador debe hablar con "
            f"{cuenta['titular']} antes de liberarla o cancelarla."
        ),
    )
