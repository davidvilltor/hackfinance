import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.fraud_detector import detectar_fraude
from backend.voice_agent import generar_audio_alerta
from backend.notifications import enviar_alerta_familiar
from backend.database import inicializar_bd, guardar_registro, obtener_historial, limpiar_bd

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    inicializar_bd()

class SolicitudAnalisis(BaseModel):
    texto: str
    volumen_alto: bool = False

@app.get("/")
async def cargar_interfaz():
    ruta_html = os.path.join(os.path.dirname(__file__), "..", "frontend", "templates", "index.html")
    return FileResponse(ruta_html)

@app.get("/historial")
async def ver_historial():
    return {"historial": obtener_historial()}

@app.delete("/limpiar-historial")
async def borrar_historial():
    try:
        limpiar_bd()
        return {"exito": True}
    except Exception as e:
        return {"exito": False, "error": str(e)}

@app.post("/analizar")
async def analizar_conversacion(datos: SolicitudAnalisis):
    if not datos.texto.strip():
        raise HTTPException(status_code=400, detail="El texto recibido está vacío.")
    
    try:
        advertencia = detectar_fraude(datos.texto)
        
        audio_base64 = None
        notificacion_enviada = False
        fue_bloqueado = False

        if "Análisis seguro" not in advertencia:
            fue_bloqueado = True
            audio_base64 = generar_audio_alerta(advertencia)
            notificacion_enviada = enviar_alerta_familiar("Posible estafa detectada en la cuenta del usuario.", "ALTA")

        # Guardamos el registro en la base de datos (sin el estado de estrés)
        guardar_registro(datos.texto, "N/A", fue_bloqueado)

        return {
            "exito": True,
            "advertencia": advertencia,
            "audio_base64": audio_base64,
            "familiar_avisado": notificacion_enviada
        }

    except Exception as e:
        return {
            "exito": False,
            "error_detectado": str(e)
        }