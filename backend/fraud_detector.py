import anthropic
from backend.config import ANTHROPIC_API_KEY

cliente_anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def detectar_fraude(texto_usuario: str) -> str:
    prompt_sistema = (
        "Eres SilverShield, el asistente protector del banco. Tu usuario es una persona de la tercera edad que "
        "podría estar siendo víctima de una estafa telefónica (ej. técnicos falsos de Microsoft, estafa del familiar en apuros). "
        "Si detectas peligro, interrumpe con un tono EXTREMADAMENTE calmado, protector y cariñoso. "
        "Tu objetivo no es solo avisar, sino evitar que la persona mayor entre en pánico. "
        "Usa frases como: 'Hola, perdona que te interrumpa. No te preocupes, tu dinero está a salvo, pero la persona con la que hablas no.' "
        "o 'Tranquilo, hemos bloqueado la operación por tu seguridad. Cuelga el teléfono, por favor.' "
        "Sé conciso (máximo 2-3 frases cortas). IMPORTANTE: Termina siempre tus oraciones con un punto final, no dejes frases a medias. Si no hay peligro, di ÚNICAMENTE: Análisis seguro."
    )

    respuesta = cliente_anthropic.messages.create(
        model="claude-opus-5-5",
        max_tokens=400,
        system=prompt_sistema,
        messages=[
            {"role": "user", "content": f"Analiza esta llamada o contexto: {texto_usuario}"}
        ]
    )

    for bloque in respuesta.content:
        if bloque.type == 'text':
            return bloque.text.strip()
    return ""