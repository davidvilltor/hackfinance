import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.fraud_detector import detectar_fraude
from backend.voice_agent import generar_audio_alerta
from backend.notifications import enviar_alerta_familiar
from backend.voice_stress import analizar_estres
from backend.database import inicializar_bd, guardar_registro, obtener_historial, limpiar_bd

app = FastAPI()

# Inicializamos la base de datos al arrancar el servidor
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

# Ruta para borrar el historial desde la web
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
        analisis_estres = analizar_estres(datos.texto, datos.volumen_alto)
        advertencia = detectar_fraude(datos.texto)
        
        audio_base64 = None
        notificacion_enviada = False
        fue_bloqueado = False

        if "Análisis seguro" not in advertencia:
            fue_bloqueado = True
            audio_base64 = generar_audio_alerta(advertencia)
            
            if analisis_estres["nivel_porcentaje"] >= 50:
                mensaje = f"Posible estafa detectada. El usuario muestra signos de {analisis_estres['estado']}."
                notificacion_enviada = enviar_alerta_familiar(mensaje, "ALTA")

        # Guardamos el registro en la base de datos SQLite
        guardar_registro(datos.texto, analisis_estres["estado"], fue_bloqueado)

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