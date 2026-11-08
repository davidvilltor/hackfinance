import base64
from elevenlabs.client import ElevenLabs
from backend.config import ELEVENLABS_API_KEY

cliente_elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)

def generar_audio_alerta(texto: str) -> str:
    audio_stream = cliente_elevenlabs.text_to_speech.convert(
        text=texto,
        voice_id="pNInz6obpgDQGcFmaJgB",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    audio_bytes = b"".join(audio_stream)
    return base64.b64encode(audio_bytes).decode("utf-8")
