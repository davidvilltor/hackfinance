import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.fraud_detector import detectar_fraude
from backend.voice_agent import generar_audio_alerta
from backend.notifications import enviar_alerta_familiar
from backend.voice_stress import analizar_estres

app = FastAPI()

# Añadimos el nuevo campo de volumen
class SolicitudAnalisis(BaseModel):
    texto: str
    volumen_alto: bool = False

@app.get("/")
async def cargar_interfaz():
    ruta_html = os.path.join(os.path.dirname(__file__), "..", "frontend", "templates", "index.html")
    return FileResponse(ruta_html)

@app.post("/analizar")
async def analizar_conversacion(datos: SolicitudAnalisis):
    if not datos.texto.strip():
        raise HTTPException(status_code=400, detail="El texto recibido está vacío.")
    
    try:
        # 1. Analizar el nivel de estrés sumando texto + análisis de volumen
        analisis_estres = analizar_estres(datos.texto, datos.volumen_alto)
        
        # 2. Detectar fraude con Claude
        advertencia = detectar_fraude(datos.texto)
        audio_base64 = None
        notificacion_enviada = False

        # 3. Protocolo de emergencia
        if "Análisis seguro" not in advertencia:
            audio_base64 = generar_audio_alerta(advertencia)
            
            if analisis_estres["nivel_porcentaje"] >= 50:
                mensaje = f"Posible estafa detectada. El usuario muestra signos de {analisis_estres['estado']}."
                notificacion_enviada = enviar_alerta_familiar(mensaje, "ALTA")

        return {
            "exito": True,
            "advertencia": advertencia,
            "audio_base64": audio_base64,
            "nivel_estres": analisis_estres["estado"],
            "familiar_avisado": notificacion_enviada
        }

    except Exception as e:
        return {
            "exito": False,
            "error_detectado": str(e)
        }