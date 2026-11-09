import os
import json
import anthropic
from backend.config import ANTHROPIC_API_KEY

MODELO = "claude-opus-5-5"  # prueba también "claude-sonnet-5-5" y compara tiempos

cliente_anthropic = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY,
    timeout=30.0,
    max_retries=1,
)

# Claude está obligado a responder con esta estructura (salida estructurada JSON).
# claude-opus-5-5 no admite forzar herramientas con tool_choice, así que usamos output_config.format.
ESQUEMA_VEREDICTO = {
    "type": "object",
    "properties": {
        "nivel_riesgo": {
            "type": "string",
            "enum": ["seguro", "sospechoso", "estafa"],
            "description": "seguro: sin riesgo financiero. sospechoso: señales de alerta pero no concluyentes. estafa: patrón claro de fraude.",
        },
        "senales": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Señales de alerta detectadas, breves. Vacío si es seguro.",
        },
        "mensaje": {
            "type": "string",
            "description": "Mensaje para el usuario (2-3 frases cortas, cada una acabada en punto). Vacío si es seguro.",
        },
    },
    "required": ["nivel_riesgo", "senales", "mensaje"],
    "additionalProperties": False,
}


def cargar_prompt_externo() -> str:
    """Lee el prompt del sistema. Si falta el archivo, falla con error claro (sin respaldo silencioso)."""
    ruta = os.path.join(os.path.dirname(__file__), "..", "prompts", "prompt_sistema.txt")
    with open(ruta, "r", encoding="utf-8") as archivo:
        return archivo.read().strip()


def analizar_riesgo(texto_usuario: str) -> dict:
    # Evitamos que el usuario cierre la etiqueta y se salga del bloque de datos
    relato = texto_usuario.replace("</relato>", "")

    respuesta = cliente_anthropic.messages.create(
        model=MODELO,
        # Margen para el razonamiento interno (siempre activo en este modelo) más el JSON
        max_tokens=2000,
        system=cargar_prompt_externo(),
        output_config={
            "effort": "low",  # clasificación corta: menos latencia y coste
            "format": {"type": "json_schema", "schema": ESQUEMA_VEREDICTO},
        },
        messages=[
            {"role": "user", "content": f"Analiza este relato:\n<relato>\n{relato}\n</relato>"}
        ],
    )

    # Si la respuesta se corta o Claude la rechaza, no hay veredicto fiable: fallamos (cerrado)
    if respuesta.stop_reason != "end_turn":
        raise ValueError(f"Claude no completó el veredicto (stop_reason={respuesta.stop_reason}).")

    for bloque in respuesta.content:
        if bloque.type == "text":
            return json.loads(bloque.text)
    raise ValueError("Claude no devolvió un veredicto.")


def detectar_fraude(texto_usuario: str) -> str:
    veredicto = analizar_riesgo(texto_usuario)
    print(f"[SilverShield] riesgo={veredicto.get('nivel_riesgo')} señales={veredicto.get('senales')}")

    if veredicto.get("nivel_riesgo") == "seguro":
        return "Análisis seguro."

    mensaje = (veredicto.get("mensaje") or "").strip()
    if not mensaje:
        mensaje = "Hemos detenido la operación por tu seguridad. Habla con alguien de confianza antes de continuar."
    return mensaje