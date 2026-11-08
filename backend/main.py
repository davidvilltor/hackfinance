import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Importamos las funciones de los otros archivos
from backend.fraud_detector import detectar_fraude
from backend.voice_agent import generar_audio_alerta

app = FastAPI()

class SolicitudAnalisis(BaseModel):
    texto: str

@app.get("/")
async def cargar_interfaz():
    ruta_html = os.path.join(os.path.dirname(__file__), "..", "frontend", "templates", "index.html")
    return FileResponse(ruta_html)

@app.post("/analizar")
async def analizar_conversacion(datos: SolicitudAnalisis):
    if not datos.texto.strip():
        raise HTTPException(status_code=400, detail="El texto recibido está vacío.")
    
    try:
        # 1. Pasamos el texto a Claude
        advertencia = detectar_fraude(datos.texto)
        audio_base64 = None

        # 2. Si hay peligro, generamos el audio con ElevenLabs
        if "Análisis seguro" not in advertencia:
            audio_base64 = generar_audio_alerta(advertencia)

        return {
            "exito": True,
            "advertencia": advertencia,
            "audio_base64": audio_base64
        }

    except Exception as e:
        return {
            "exito": False,
            "error_detectado": str(e)
        }