import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel
from backend.fraud_detector import detectar_fraude
from backend.voice_agent import generar_audio_alerta
from backend.notifications import enviar_alerta_familiar
from backend.database import inicializar_bd, guardar_registro, obtener_historial, limpiar_bd

# Los detalles de los errores van a la terminal, nunca al cliente
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("silvershield")

# El usuario puede escribir hasta 1000 caracteres; el resto es margen para el prefijo "[Canal: ...]"
MAX_CARACTERES_TEXTO = 1100

ERROR_ANALISIS = "No hemos podido verificar la operación en este momento. Por tu seguridad, la operación queda retenida. Inténtalo de nuevo en unos minutos."

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

# Ruta para evitar el error 404 de favicon.ico en la terminal
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content=b"", media_type="image/x-icon")

# Los endpoints que usan clientes síncronos (SQLite, Anthropic, ElevenLabs) son "def":
# FastAPI los ejecuta en un hilo aparte y no bloquean el servidor.
@app.get("/historial")
def ver_historial():
    try:
        return {"historial": obtener_historial()}
    except Exception:
        logger.exception("Error leyendo el historial de la base de datos")
        return JSONResponse(status_code=500, content={"exito": False, "error": "No se ha podido cargar el historial."})

@app.delete("/limpiar-historial")
def borrar_historial():
    try:
        limpiar_bd()
        return {"exito": True}
    except Exception:
        logger.exception("Error borrando el historial de la base de datos")
        return JSONResponse(status_code=500, content={"exito": False, "error": "No se ha podido borrar el historial."})

@app.post("/analizar")
def analizar_conversacion(datos: SolicitudAnalisis):
    if not datos.texto.strip():
        raise HTTPException(status_code=400, detail="El texto recibido está vacío.")
    if len(datos.texto) > MAX_CARACTERES_TEXTO:
        raise HTTPException(status_code=400, detail="El texto es demasiado largo. Resume lo ocurrido en un máximo de 1000 caracteres.")

    try:
        advertencia = detectar_fraude(datos.texto)
        fue_bloqueado = "Análisis seguro" not in advertencia

        # Se registra antes de avisar: si la BD falla, no se manda un aviso de algo que no consta
        guardar_registro(datos.texto, "N/A", fue_bloqueado)

        audio_base64 = None
        notificacion_enviada = False
        if fue_bloqueado:
            # El audio es opcional: si ElevenLabs falla, el veredicto se muestra igualmente sin voz
            try:
                audio_base64 = generar_audio_alerta(advertencia)
            except Exception:
                logger.exception("Error generando el audio con ElevenLabs; se continúa sin audio")
            notificacion_enviada = enviar_alerta_familiar("Posible estafa detectada en la cuenta del usuario.", "ALTA")

        return {
            "exito": True,
            "advertencia": advertencia,
            "audio_base64": audio_base64,
            "familiar_avisado": notificacion_enviada
        }

    except Exception:
        # Fallo cerrado: sin veredicto fiable, la operación no se aprueba ni se registra como permitida
        logger.exception("Error analizando el texto en /analizar")
        return JSONResponse(status_code=503, content={"exito": False, "error": ERROR_ANALISIS})
