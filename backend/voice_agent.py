"""Voz de SilverShield con ElevenLabs (texto a voz y voz a texto) vía API REST.

- Texto a voz: modelo de baja latencia (eleven_flash_v2_5) en streaming, de modo
  que el navegador empieza a reproducir el audio antes de que esté completo.
- Voz a texto: ElevenLabs Scribe, usado cuando el navegador no dispone de
  reconocimiento de voz propio (por ejemplo Firefox).

Si no hay clave de ElevenLabs, el navegador usa su síntesis de voz nativa.
"""
import logging
from collections import OrderedDict

import httpx2 as httpx
from fastapi import HTTPException
from fastapi.responses import Response, StreamingResponse

from backend import config

log = logging.getLogger("silvershield.voz")
URL_BASE = "https://api.elevenlabs.io/v1"

# Caché en memoria de audios ya generados (para el botón "Repetir").
_CACHE_MAX = 64
_cache_audio: "OrderedDict[int, bytes]" = OrderedDict()


def _guardar_cache(clave: int, audio: bytes) -> None:
    _cache_audio[clave] = audio
    _cache_audio.move_to_end(clave)
    while len(_cache_audio) > _CACHE_MAX:
        _cache_audio.popitem(last=False)


async def sintetizar_stream(clave: int, texto: str) -> Response:
    """Devuelve una respuesta HTTP con el MP3 de `texto` (en streaming)."""
    if clave in _cache_audio:
        return Response(content=_cache_audio[clave], media_type="audio/mpeg")
    if not config.voz_disponible():
        raise HTTPException(status_code=503, detail="Voz de ElevenLabs no configurada")

    cliente = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0))
    peticion = cliente.build_request(
        "POST",
        f"{URL_BASE}/text-to-speech/{config.ELEVENLABS_VOICE_ID}/stream",
        params={"output_format": "mp3_44100_128"},
        headers={"xi-api-key": config.ELEVENLABS_API_KEY, "Accept": "audio/mpeg"},
        json={
            "text": texto,
            "model_id": config.ELEVENLABS_TTS_MODEL,
            "language_code": "es",
            "voice_settings": {
                "stability": 0.75,          # tono estable y sereno
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True,
                "speed": config.ELEVENLABS_VELOCIDAD,
            },
        },
    )
    try:
        respuesta = await cliente.send(peticion, stream=True)
    except httpx.HTTPError as error:
        await cliente.aclose()
        log.error("ElevenLabs TTS no responde: %s", error)
        raise HTTPException(status_code=502, detail="Servicio de voz no disponible") from error

    if respuesta.status_code != 200:
        cuerpo = await respuesta.aread()
        await respuesta.aclose()
        await cliente.aclose()
        log.error("ElevenLabs TTS error %s: %s", respuesta.status_code, cuerpo[:300])
        raise HTTPException(status_code=502, detail="Servicio de voz no disponible")

    async def emitir():
        acumulado = bytearray()
        completo = False
        try:
            async for trozo in respuesta.aiter_bytes():
                acumulado.extend(trozo)
                yield trozo
            completo = True
        finally:
            await respuesta.aclose()
            await cliente.aclose()
            if completo:
                _guardar_cache(clave, bytes(acumulado))

    return StreamingResponse(emitir(), media_type="audio/mpeg")


async def transcribir(audio: bytes, tipo_mime: str) -> str:
    """Convierte la grabación del cliente en texto con ElevenLabs Scribe."""
    if not config.voz_disponible():
        raise HTTPException(status_code=503, detail="Transcripción de ElevenLabs no configurada")
    extension = "webm" if "webm" in tipo_mime else "ogg" if "ogg" in tipo_mime else "wav"
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as cliente:
        try:
            respuesta = await cliente.post(
                f"{URL_BASE}/speech-to-text",
                headers={"xi-api-key": config.ELEVENLABS_API_KEY},
                data={"model_id": config.ELEVENLABS_STT_MODEL, "language_code": "spa"},
                files={"file": (f"respuesta.{extension}", audio, tipo_mime or "audio/webm")},
            )
        except httpx.HTTPError as error:
            log.error("ElevenLabs STT no responde: %s", error)
            raise HTTPException(status_code=502, detail="Servicio de voz no disponible") from error
    if respuesta.status_code != 200:
        log.error("ElevenLabs STT error %s: %s", respuesta.status_code, respuesta.text[:300])
        raise HTTPException(status_code=502, detail="No se pudo entender el audio")
    return (respuesta.json().get("text") or "").strip()
