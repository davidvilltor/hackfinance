"""Indicadores de estrés, confusión y coacción en la respuesta del cliente.

Combina dos fuentes:
  1. Lingüística: palabras de urgencia, titubeos, frases típicas de un guion
     dictado por un estafador.
  2. Paralingüística: métricas medidas en el navegador mientras el cliente habla
     (volumen medio, velocidad del habla, duración de los silencios).

No es un diagnóstico: son pistas que se entregan a Claude junto con la
conversación para que valore el riesgo con más contexto.
"""
from backend.reglas_riesgo import normalizar_texto

PALABRAS_URGENCIA = [
    "rapido", "urgente", "ahora mismo", "inmediat", "ya mismo", "hoy mismo", "bloque",
    "multa", "peligro", "policia", "carcel", "delito", "juzgado", "consecuencias",
    "denuncia", "embargo", "antes de que",
]
PALABRAS_DUDA = [
    "no se", "no lo se", "creo que", "supongo", "no entiendo", "no estoy segur",
    "me lio", "no me acuerdo", "eh", "mmm", "pues no se",
]
# Frases que sugieren que un tercero está dirigiendo la operación.
PALABRAS_TERCERO = [
    "me ha dicho", "me han dicho", "me dijo", "me dicen", "me llamo", "me llamaron",
    "me ha llamado", "me han llamado", "me ha escrito", "me escribio", "me pidio",
    "me ha pedido", "esta aqui conmigo", "esta a mi lado", "me esta escuchando",
    "al telefono", "sigue al telefono", "no puedo colgar", "no se lo diga",
    "no se lo cuente", "es un secreto", "whatsapp", "sms", "mensaje",
]


def _coincidencias(texto: str, lista: list[str]) -> list[str]:
    palabras = f" {texto} "
    return [p for p in lista if f" {p}" in palabras or (len(p) > 4 and p in texto)]


def analizar_senales(texto: str, senales_voz: dict | None = None) -> dict:
    texto_norm = normalizar_texto(texto)
    urgencia = _coincidencias(texto_norm, PALABRAS_URGENCIA)
    duda = _coincidencias(texto_norm, PALABRAS_DUDA)
    tercero = _coincidencias(texto_norm, PALABRAS_TERCERO)

    puntos = 20 * len(urgencia) + 12 * len(duda) + 15 * len(tercero)
    indicadores: list[str] = []
    if urgencia:
        indicadores.append("Usa palabras de urgencia o miedo: " + ", ".join(urgencia))
    if duda:
        indicadores.append("Muestra dudas o confusión: " + ", ".join(duda))
    if tercero:
        indicadores.append("Menciona a otra persona que le indica qué hacer: " + ", ".join(tercero))

    voz = senales_voz or {}
    ppm = voz.get("palabras_por_minuto")
    volumen = voz.get("volumen_medio")          # 0-100 normalizado en el navegador
    silencio = voz.get("silencio_inicial_s")    # segundos hasta empezar a hablar
    if isinstance(ppm, (int, float)) and ppm > 0:
        if ppm > 190:
            puntos += 20
            indicadores.append(f"Habla muy deprisa ({int(ppm)} palabras/min)")
        elif ppm < 70:
            puntos += 10
            indicadores.append(f"Habla muy despacio o con pausas ({int(ppm)} palabras/min)")
    if isinstance(volumen, (int, float)) and volumen > 70:
        puntos += 15
        indicadores.append("Volumen de voz alto (posible nerviosismo)")
    if isinstance(silencio, (int, float)) and silencio > 4:
        puntos += 10
        indicadores.append(f"Tarda {silencio:.0f} s en empezar a responder")

    nivel = min(100, puntos)
    if nivel >= 50:
        estado = "Alto (posible presión o coacción)"
    elif nivel > 0:
        estado = "Moderado"
    else:
        estado = "Tranquilo"
    return {
        "nivel_porcentaje": nivel,
        "estado": estado,
        "indicadores": indicadores,
        "menciona_tercero": bool(tercero),
    }
