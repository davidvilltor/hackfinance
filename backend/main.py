import os
import base64
import requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class Transcripcion(BaseModel):
    texto: str

@app.get("/", response_class=HTMLResponse)
def cargar_interfaz():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/analizar")
def analizar_conversacion(datos: Transcripcion):
    try:
        # 1. Llamada a Claude
        prompt_sistema = "Eres SilverShield, un asistente de seguridad bancaria integrado. Analiza el contexto de la conversación del usuario mientras intenta hacer una transferencia. Tu objetivo es detectar la estafa del 'Falso técnico de Microsoft'. Sé muy directo y responde en 2 líneas. Si detectas peligro, dile que cancele. Si no, di 'Análisis seguro'."
        
        respuesta = anthropic.messages.create(
            model="claude-opus-5-5",
            max_tokens=150,
            system=prompt_sistema,
            messages=[
                {"role": "user", "content": f"El usuario está diciendo esto en voz alta: '{datos.texto}'"}
            ]
        )
        
        texto_final = ""
        for bloque in respuesta.content:
            if bloque.type == 'text':
                texto_final += bloque.text

        # 2. Llamada a ElevenLabs para generar la voz
        audio_base64 = None
        api_key_eleven = os.getenv("ELEVENLABS_API_KEY")
        
        if api_key_eleven:
            voice_id = "N2lVS1w4EtoT3dr4eOWO"
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key_eleven
            }
            payload = {
                "text": texto_final,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.7}
            }
            
            # AÑADIDO: timeout=5 fuerza a cortar si la red del hackathon bloquea la petición
            respuesta_voz = requests.post(url, json=payload, headers=headers, timeout=5)
            
            if respuesta_voz.status_code == 200:
                audio_base64 = base64.b64encode(respuesta_voz.content).decode('utf-8')
            else:
                return {"exito": False, "error_detectado": f"Error ElevenLabs: {respuesta_voz.status_code} - {respuesta_voz.text}"}

        return {"exito": True, "advertencia": texto_final, "audio_base64": audio_base64}
        
    except requests.exceptions.Timeout:
        return {"exito": False, "error_detectado": "El Wi-Fi está bloqueando ElevenLabs (Timeout)."}
    except Exception as e:
        return {"exito": False, "error_detectado": str(e)}
