import os
import anthropic
from backend.config import ANTHROPIC_API_KEY

cliente_anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def cargar_prompt_externo() -> str:
    """Lee el prompt del sistema desde la carpeta externa /prompts."""
    ruta_prompt = os.path.join(os.path.dirname(__file__), "..", "prompts", "prompt_sistema.txt")
    try:
        with open(ruta_prompt, "r", encoding="utf-8") as archivo:
            return archivo.read().strip()
    except FileNotFoundError:
        # Fallback de seguridad por si el archivo no se encuentra
        return "Eres SilverShield, un asistente protector bancario. Sé conciso y termina con un punto."

def detectar_fraude(texto_usuario: str) -> str:
    prompt_sistema = cargar_prompt_externo()

    respuesta = cliente_anthropic.messages.create(
        model="claude-opus-5-5",
        max_tokens=500,
        system=prompt_sistema,
        messages=[
            {"role": "user", "content": f"Analiza esta llamada o contexto: {texto_usuario}"}
        ]
    )

    for bloque in respuesta.content:
        if bloque.type == 'text':
            return bloque.text.strip()
    return ""