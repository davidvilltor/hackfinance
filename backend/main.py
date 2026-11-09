"""API de SilverShield / SilverBank (FastAPI).

Flujo de una transferencia:

    POST /api/transferencias
        ├─ sin alertas ─────────────────────────────► completada
        └─ importe >= 500 € o destino sospechoso ───► pendiente_decision
               ├─ /autorizar  ("conozco al destinatario") ─► completada
               ├─ /cancelar ───────────────────────────────► cancelada
               └─ /verificacion (SilverShield) ────────────► en_verificacion
                      └─ /verificacion/mensajes (conversación por voz)
                             ├─ "seguro" ─► verificada_segura ─► /autorizar ─► completada
                             └─ "riesgo" ─► retenida + aviso al contacto de confianza
                                              └─ /liberar o /cancelar (panel del contacto)
"""
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from backend import config, database as db
from backend.agente_silvershield import evaluar_turno, mensaje_apertura
from backend.notifications import avisar_contacto
from backend.reglas_riesgo import (
    IbanInvalido, euros_hablados, evaluar_transferencia, formatear_euros, normalizar_texto,
    validar_iban,
)
from backend.voice_agent import sintetizar_stream, transcribir
from backend.voice_stress import analizar_senales

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("silvershield")

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI):
    db.inicializar_bd()
    log.info(
        "SilverShield listo. IA: %s | Voz ElevenLabs: %s",
        f"Claude ({config.CLAUDE_MODEL})" if config.ia_disponible() else "evaluador local",
        "sí" if config.voz_disponible() else "voz del navegador",
    )
    yield


app = FastAPI(title="SilverShield", version="1.0.0", lifespan=ciclo_de_vida)
app.mount("/static", StaticFiles(directory=FRONTEND / "static"), name="static")


@app.middleware("http")
async def medir_tiempo(request: Request, call_next):
    inicio = time.perf_counter()
    respuesta = await call_next(request)
    respuesta.headers["Server-Timing"] = f"app;dur={(time.perf_counter() - inicio) * 1000:.0f}"
    # Que el navegador compruebe siempre si hay una versión nueva de los JS/CSS
    # (si no, puede seguir usando una copia antigua tras cambiar el código).
    if request.url.path.startswith("/static/"):
        respuesta.headers["Cache-Control"] = "no-cache"
    return respuesta


# ------------------------------------------------------------------ modelos de entrada

class NuevaTransferencia(BaseModel):
    beneficiario_nombre: str = Field(min_length=2, max_length=80)
    iban: str = Field(min_length=10, max_length=42)
    importe: float = Field(gt=0, le=1_000_000)
    concepto: str = Field(default="", max_length=140)

    @field_validator("beneficiario_nombre", "concepto")
    @classmethod
    def recortar(cls, valor: str) -> str:
        return valor.strip()


class SenalesVoz(BaseModel):
    palabras_por_minuto: float | None = None
    volumen_medio: float | None = None
    silencio_inicial_s: float | None = None
    duracion_s: float | None = None
    via: str | None = None  # "voz" o "texto"


class RespuestaCliente(BaseModel):
    texto: str = Field(min_length=1, max_length=2000)
    senales_voz: SenalesVoz | None = None


# ------------------------------------------------------------------ utilidades

def _transferencia_o_404(transferencia_id: int) -> dict:
    t = db.obtener_transferencia(transferencia_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Transferencia no encontrada")
    return t


def _exigir_estado(t: dict, *estados: str) -> None:
    if t["estado"] not in estados:
        raise HTTPException(
            status_code=409,
            detail=f"La transferencia está «{t['estado']}» y no admite esta acción.",
        )


def _completar(transferencia_id: int, via: str) -> dict:
    try:
        return db.completar_transferencia(transferencia_id, via)
    except db.SaldoInsuficiente as error:
        raise HTTPException(
            status_code=400, detail="No tiene saldo suficiente para esta transferencia."
        ) from error


def _mensaje_publico(mensaje: dict) -> dict:
    return {
        "id": mensaje["id"],
        "rol": mensaje["rol"],
        "texto": mensaje["texto"],
        "audio_url": f"/api/voz/mensajes/{mensaje['id']}" if mensaje["rol"] == "asistente" else None,
    }


# ------------------------------------------------------------------ páginas

@app.get("/", include_in_schema=False)
async def pagina_cliente():
    return FileResponse(FRONTEND / "templates" / "index.html")


@app.get("/panel", include_in_schema=False)
async def pagina_panel():
    return FileResponse(FRONTEND / "templates" / "panel.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


# ------------------------------------------------------------------ cuenta

@app.get("/api/estado")
async def estado():
    return {
        "ia": config.ia_disponible(),
        "modelo": config.CLAUDE_MODEL if config.ia_disponible() else "evaluador local",
        "voz_elevenlabs": config.voz_disponible(),
        "umbral_verificacion": config.UMBRAL_VERIFICACION_EUR,
        "max_turnos": config.MAX_TURNOS_VERIFICACION,
    }


@app.get("/api/cuenta")
async def ver_cuenta():
    cuenta = db.obtener_cuenta()
    cuenta.pop("palabra_seguridad", None)  # nunca se envía a la pantalla del cliente
    return {
        "cuenta": cuenta,
        "beneficiarios": db.listar_beneficiarios(),
        "movimientos": db.listar_transferencias(limite=5, solo_completadas=True),
    }


# ------------------------------------------------------------------ transferencias

@app.post("/api/transferencias")
async def crear_transferencia(datos: NuevaTransferencia):
    try:
        iban = validar_iban(datos.iban)
    except IbanInvalido as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    importe = round(datos.importe, 2)
    cuenta = db.obtener_cuenta()
    if iban == cuenta["iban"]:
        raise HTTPException(status_code=422, detail="Esa es su propia cuenta.")
    if importe > cuenta["saldo"]:
        raise HTTPException(
            status_code=400,
            detail=f"No tiene saldo suficiente. Su saldo es {formatear_euros(cuenta['saldo'])}.",
        )

    evaluacion = evaluar_transferencia(
        importe=importe,
        iban=iban,
        concepto=datos.concepto,
        beneficiario_conocido=db.beneficiario_conocido(iban),
        saldo=cuenta["saldo"],
    )
    estado_inicial = db.PENDIENTE_DECISION if evaluacion["requiere_confirmacion"] else db.COMPLETADA
    t = db.crear_transferencia(
        datos.beneficiario_nombre, iban, evaluacion["pais"], importe, datos.concepto,
        db.PENDIENTE_DECISION, evaluacion,
    )
    if estado_inicial == db.COMPLETADA:
        t = _completar(t["id"], via="directa")
    return {"transferencia": t, "evaluacion": evaluacion, "saldo": db.obtener_cuenta()["saldo"]}


@app.get("/api/transferencias/{transferencia_id}")
async def ver_transferencia(transferencia_id: int):
    t = _transferencia_o_404(transferencia_id)
    return {"transferencia": t, "mensajes": db.obtener_mensajes(transferencia_id)}


@app.post("/api/transferencias/{transferencia_id}/autorizar")
async def autorizar(transferencia_id: int):
    """El cliente confirma el envío: tras elegir "Conozco al destinatario" o
    después de que SilverShield haya recomendado seguir."""
    t = _transferencia_o_404(transferencia_id)
    _exigir_estado(t, db.PENDIENTE_DECISION, db.VERIFICADA_SEGURA)
    via = "verificada_ia" if t["estado"] == db.VERIFICADA_SEGURA else "autorizada_cliente"
    t = _completar(transferencia_id, via)
    return {"transferencia": t, "saldo": db.obtener_cuenta()["saldo"]}


@app.post("/api/transferencias/{transferencia_id}/cancelar")
async def cancelar(transferencia_id: int):
    t = _transferencia_o_404(transferencia_id)
    _exigir_estado(t, *db.ESTADOS_ACTIVOS)
    t = db.actualizar_transferencia(
        transferencia_id, estado=db.CANCELADA, fecha_resolucion=db.ahora()
    )
    return {"transferencia": t}


@app.post("/api/transferencias/{transferencia_id}/liberar")
async def liberar(transferencia_id: int):
    """Acción del contacto de confianza / gestor: libera una transferencia retenida."""
    t = _transferencia_o_404(transferencia_id)
    _exigir_estado(t, db.RETENIDA)
    t = _completar(transferencia_id, via="liberada_contacto")
    return {"transferencia": t, "saldo": db.obtener_cuenta()["saldo"]}


# ------------------------------------------------------------------ verificación

@app.post("/api/transferencias/{transferencia_id}/verificacion")
async def iniciar_verificacion(transferencia_id: int):
    t = _transferencia_o_404(transferencia_id)
    _exigir_estado(t, db.PENDIENTE_DECISION, db.EN_VERIFICACION)
    if t["estado"] == db.EN_VERIFICACION:
        # Reanudación (p. ej. recarga de página): se devuelve la conversación existente.
        return {
            "transferencia": t,
            "mensajes": [_mensaje_publico(m) for m in db.obtener_mensajes(transferencia_id)],
        }
    cuenta = db.obtener_cuenta()
    t = db.actualizar_transferencia(transferencia_id, estado=db.EN_VERIFICACION)
    saludo = db.guardar_mensaje(transferencia_id, "asistente", mensaje_apertura(t, cuenta))
    return {"transferencia": t, "mensajes": [_mensaje_publico(saludo)]}


def _contiene_palabra_seguridad(texto: str, palabra: str | None) -> bool:
    return bool(palabra) and normalizar_texto(palabra) in normalizar_texto(texto)


@app.post("/api/transferencias/{transferencia_id}/verificacion/mensajes")
async def responder_verificacion(transferencia_id: int, datos: RespuestaCliente):
    inicio = time.perf_counter()
    t = _transferencia_o_404(transferencia_id)
    _exigir_estado(t, db.EN_VERIFICACION)
    cuenta = db.obtener_cuenta()

    senales_voz = datos.senales_voz.model_dump(exclude_none=True) if datos.senales_voz else None
    senales = analizar_senales(datos.texto, senales_voz)
    db.guardar_mensaje(transferencia_id, "cliente", datos.texto.strip(),
                       {"voz": senales_voz, "analisis": senales})
    mensajes = db.obtener_mensajes(transferencia_id)

    # Palabra de auxilio: el cliente la pronuncia si alguien le está obligando.
    # SilverShield responde con normalidad (para no alertar a quien presiona),
    # retiene la operación y avisa en silencio al contacto de confianza.
    if _contiene_palabra_seguridad(datos.texto, cuenta.get("palabra_seguridad")):
        texto = (
            f"De acuerdo, {cuenta['nombre_corto']}. Para terminar, un gestor del banco revisará "
            "la operación y le llamará en unos minutos. Muchas gracias por su paciencia."
        )
        respuesta = db.guardar_mensaje(transferencia_id, "asistente", texto)
        db.actualizar_transferencia(
            transferencia_id, estado=db.RETENIDA, veredicto_ia="riesgo", nivel_riesgo_ia=100,
            categoria_estafa="coaccion_familiar", senales_ia=["Palabra de auxilio pronunciada"],
            resumen_ia="El cliente ha pronunciado su palabra de auxilio durante la verificación.",
            motor_ia="palabra_auxilio", fecha_resolucion=db.ahora(),
        )
        avisar_contacto(
            cuenta, transferencia_id, "COACCION",
            f"URGENTE: {cuenta['titular']} ha usado su palabra de auxilio al intentar enviar "
            f"{euros_hablados(t['importe'])} a {t['beneficiario_nombre']}. Llámele o acuda en persona.",
        )
        return {
            "respuesta": _mensaje_publico(respuesta),
            "decision": "revision",
            "final": True,
            "transferencia": db.obtener_transferencia(transferencia_id),
            "contacto_avisado": True,
            "tiempo_ms": int((time.perf_counter() - inicio) * 1000),
        }

    resultado = await evaluar_turno(t, cuenta, mensajes, senales)
    respuesta = db.guardar_mensaje(transferencia_id, "asistente", resultado.respuesta)

    contacto_avisado = False
    campos = dict(
        veredicto_ia=resultado.decision, nivel_riesgo_ia=resultado.nivel_riesgo,
        categoria_estafa=resultado.categoria, senales_ia=resultado.senales,
        resumen_ia=resultado.resumen_para_contacto or None, motor_ia=resultado.motor,
    )
    if resultado.decision == "riesgo":
        campos.update(estado=db.RETENIDA, fecha_resolucion=db.ahora())
        avisar_contacto(
            cuenta, transferencia_id, "POSIBLE_ESTAFA",
            f"SilverShield ha parado una transferencia de {euros_hablados(t['importe'])} de "
            f"{cuenta['titular']} a {t['beneficiario_nombre']}. "
            f"{resultado.resumen_para_contacto}".strip(),
        )
        contacto_avisado = True
    elif resultado.decision == "seguro":
        campos.update(estado=db.VERIFICADA_SEGURA)
    t = db.actualizar_transferencia(transferencia_id, **campos)

    return {
        "respuesta": _mensaje_publico(respuesta),
        "decision": resultado.decision,
        "final": resultado.decision != "preguntar",
        "nivel_riesgo": resultado.nivel_riesgo,
        "transferencia": t,
        "contacto_avisado": contacto_avisado,
        "motor": resultado.motor,
        "tiempo_ms": int((time.perf_counter() - inicio) * 1000),
    }


# ------------------------------------------------------------------ voz

@app.get("/api/voz/mensajes/{mensaje_id}")
async def audio_mensaje(mensaje_id: int):
    """MP3 (ElevenLabs) de un mensaje de SilverShield. Solo sintetiza textos
    generados por el propio servidor, así que no puede usarse como proxy abierto."""
    mensaje = db.obtener_mensaje(mensaje_id)
    if mensaje is None or mensaje["rol"] != "asistente":
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    return await sintetizar_stream(mensaje_id, mensaje["texto"])


@app.post("/api/voz/transcribir")
async def transcribir_audio(request: Request):
    audio = await request.body()
    if not audio:
        raise HTTPException(status_code=400, detail="No se ha recibido audio")
    if len(audio) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="La grabación es demasiado larga")
    texto = await transcribir(audio, request.headers.get("content-type", "audio/webm"))
    return {"texto": texto}


# ------------------------------------------------------------------ panel del contacto / banco

@app.get("/api/panel")
async def datos_panel():
    cuenta = db.obtener_cuenta()
    return {
        "cuenta": cuenta,
        "transferencias": db.listar_transferencias(limite=50),
        "alertas": db.listar_alertas(),
        "estado": await estado(),
    }


@app.post("/api/demo/reiniciar")
async def reiniciar_demo():
    db.reiniciar_demo()
    return {"ok": True}
