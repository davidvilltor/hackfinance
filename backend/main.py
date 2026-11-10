"""API de SilverShield / SilverBank (FastAPI).

Flujo de una transferencia:

    POST /api/transferencias
        ├─ sin alertas ─────────────────────────────► completada
        └─ importe >= 500 € o destino sospechoso ───► pendiente_decision
               ├─ /autorizar  ("conozco al destinatario") ─► completada
               ├─ /cancelar ───────────────────────────────► cancelada
               └─ /verificacion (SilverShield)
                      ├─ IA sin clave ─► retenida + aviso ("no_verificada")
                      └─ en_verificacion
                         └─ /verificacion/mensajes (conversación por voz)
                             ├─ "seguro" ─► verificada_segura ─► /autorizar ─► completada
                             ├─ "riesgo" ─► retenida + aviso al contacto de emergencia
                             │                └─ /liberar o /cancelar (operador del banco)
                             └─ "no_verificada" (IA caída) ─► retenida + aviso
                                (fallar de forma segura: sin IA no hay comprobación
                                 automática; decide un operador del banco)

Por motivos legales, solo un operador del banco puede liberar una transferencia
retenida (tras hablar con el titular). El contacto de emergencia solo recibe avisos.
Las rutas del operador exigen haber iniciado sesión (ver acceso_operador.py).

Memoria por cliente: al terminar cada verificación, SilverShield guarda lo que ha
aprendido (hechos de una transferencia legítima o el patrón de un intento de
estafa). La próxima vez, las reglas usan el historial con ese destinatario (un
envío "de lo de siempre" ya verificado no se vuelve a preguntar) y Claude recibe
esos recuerdos como contexto para preguntar menos y detectar cambios.
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from backend import config, database as db
from backend.acceso_operador import (
    abrir_sesion, cerrar_sesion, credenciales_validas, exigir_operador, operador_actual,
)
from backend.agente_silvershield import evaluar_turno, mensaje_apertura, resultado_no_verificada
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
        f"Claude ({config.CLAUDE_MODEL})" if config.ia_disponible()
        else "NO configurada (las verificaciones quedarán retenidas para un operador)",
        "sí" if config.voz_disponible() else "voz del navegador",
    )
    if not config.OPERADORES:
        log.error("OPERADORES está mal escrito en .env (formato: usuario:contraseña,usuario2:contraseña2): "
                  "nadie podrá entrar en el panel del operador.")
    elif config.OPERADORES_SON_DE_DEMO:
        log.warning("Panel del operador con la contraseña de DEMO. Defina OPERADORES en .env "
                    "antes de usarlo fuera de una demostración.")
    yield


app = FastAPI(title="SilverShield", version="1.0.0", lifespan=ciclo_de_vida)
app.mount("/static", StaticFiles(directory=FRONTEND / "static"), name="static")


@app.middleware("http")
async def medir_tiempo(request: Request, call_next):
    inicio = time.perf_counter()
    respuesta = await call_next(request)
    medida = f"app;dur={(time.perf_counter() - inicio) * 1000:.0f}"
    previa = respuesta.headers.get("Server-Timing")
    respuesta.headers["Server-Timing"] = f"{previa}, {medida}" if previa else medida
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


class AccesoOperador(BaseModel):
    usuario: str = Field(min_length=1, max_length=60)
    contrasena: str = Field(min_length=1, max_length=200)


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
async def pagina_panel(request: Request):
    if operador_actual(request) is None:
        return RedirectResponse("/acceso", status_code=303)
    return FileResponse(FRONTEND / "templates" / "panel.html")


@app.get("/acceso", include_in_schema=False)
async def pagina_acceso(request: Request):
    if operador_actual(request) is not None:
        return RedirectResponse("/panel", status_code=303)
    return FileResponse(FRONTEND / "templates" / "acceso.html")


# ------------------------------------------------------------------ acceso del operador

@app.post("/api/operador/acceso")
async def acceso_operador(datos: AccesoOperador, respuesta: Response):
    if not credenciales_validas(datos.usuario, datos.contrasena):
        log.warning("Intento de acceso fallido al panel con el usuario «%s»", datos.usuario)
        await asyncio.sleep(1)   # frena los intentos de adivinar la contraseña
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")
    abrir_sesion(respuesta, datos.usuario)
    log.info("El operador «%s» ha entrado en el panel", datos.usuario)
    return {"operador": datos.usuario}


@app.post("/api/operador/salir")
async def salir_operador(respuesta: Response):
    cerrar_sesion(respuesta)
    return {"ok": True}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


# ------------------------------------------------------------------ cuenta

@app.get("/api/estado")
async def estado():
    return {
        "ia": config.ia_disponible(),
        "modelo": config.CLAUDE_MODEL if config.ia_disponible() else "sin IA (se retiene para el operador)",
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
        perfil=db.perfil_destinatario(iban),
    )
    estado_inicial = db.PENDIENTE_DECISION if evaluacion["requiere_confirmacion"] else db.COMPLETADA
    t = db.crear_transferencia(
        datos.beneficiario_nombre, iban, evaluacion["pais"], importe, datos.concepto,
        db.PENDIENTE_DECISION, evaluacion,
    )
    if estado_inicial == db.COMPLETADA:
        via = "habitual_verificado" if evaluacion["destino_habitual_verificado"] else "directa"
        t = _completar(t["id"], via=via)
    return {"transferencia": t, "evaluacion": evaluacion, "saldo": db.obtener_cuenta()["saldo"]}


@app.get("/api/transferencias/{transferencia_id}")
async def ver_transferencia(transferencia_id: int, _operador: str = Depends(exigir_operador)):
    """Detalle completo con la transcripción (solo para el operador)."""
    t = _transferencia_o_404(transferencia_id)
    return {"transferencia": t, "mensajes": db.obtener_mensajes(transferencia_id)}


@app.post("/api/transferencias/{transferencia_id}/autorizar")
async def autorizar(transferencia_id: int):
    """El cliente confirma el envío: tras elegir "Conozco al destinatario" o
    después de que SilverShield haya recomendado seguir."""
    t = _transferencia_o_404(transferencia_id)
    _exigir_estado(t, db.PENDIENTE_DECISION, db.VERIFICADA_SEGURA)
    if t["estado"] == db.PENDIENTE_DECISION and not (t.get("evaluacion") or {}).get("permite_autorizacion_directa"):
        raise HTTPException(
            status_code=409,
            detail="Esta transferencia necesita una verificación con SilverShield antes de enviarse.",
        )
    via = "verificada_ia" if t["estado"] == db.VERIFICADA_SEGURA else "autorizada_cliente"
    t = _completar(transferencia_id, via)
    return {"transferencia": t, "saldo": db.obtener_cuenta()["saldo"]}


@app.post("/api/transferencias/{transferencia_id}/cancelar")
async def cancelar(transferencia_id: int, request: Request):
    """El cliente puede cancelar sus transferencias en curso. Una retenida solo la
    puede cancelar un operador del banco."""
    t = _transferencia_o_404(transferencia_id)
    _exigir_estado(t, *db.ESTADOS_ACTIVOS)
    campos = dict(estado=db.CANCELADA, fecha_resolucion=db.ahora())
    if t["estado"] == db.RETENIDA:
        campos["operador"] = exigir_operador(request)
        log.info("El operador «%s» ha cancelado la transferencia #%s", campos["operador"], transferencia_id)
    t = db.actualizar_transferencia(transferencia_id, **campos)
    return {"transferencia": t}


@app.post("/api/transferencias/{transferencia_id}/liberar")
async def liberar(transferencia_id: int, operador: str = Depends(exigir_operador)):
    """Acción del operador del banco: libera una transferencia retenida después de
    hablar con el titular. El contacto de emergencia no puede hacerlo."""
    t = _transferencia_o_404(transferencia_id)
    _exigir_estado(t, db.RETENIDA)
    _completar(transferencia_id, via="liberada_operador")
    t = db.actualizar_transferencia(transferencia_id, operador=operador)
    log.info("El operador «%s» ha liberado la transferencia #%s", operador, transferencia_id)
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
    if not config.ia_disponible():
        # Sin IA no hay comprobación automática: se retiene directamente para el operador.
        log.error("Verificación #%s sin IA configurada: queda retenida.", transferencia_id)
        resultado = resultado_no_verificada(cuenta)
        aviso = db.guardar_mensaje(transferencia_id, "asistente", resultado.respuesta,
                                   {"motor": resultado.motor})
        t = _retener_no_verificada(t, cuenta, resultado)
        return {
            "transferencia": t,
            "mensajes": [_mensaje_publico(aviso)],
            "final": True,
            "decision": resultado.decision,
            "contacto_avisado": True,
        }
    t = db.actualizar_transferencia(transferencia_id, estado=db.EN_VERIFICACION)
    saludo = db.guardar_mensaje(transferencia_id, "asistente", mensaje_apertura(t, cuenta))
    return {"transferencia": t, "mensajes": [_mensaje_publico(saludo)], "final": False}


def _retener_no_verificada(t: dict, cuenta: dict, resultado) -> dict:
    """La IA no está disponible: retiene la transferencia y avisa (operador + contacto)."""
    t = db.actualizar_transferencia(
        t["id"], estado=db.RETENIDA, fecha_resolucion=db.ahora(),
        veredicto_ia=resultado.decision, nivel_riesgo_ia=resultado.nivel_riesgo,
        categoria_estafa=resultado.categoria, senales_ia=resultado.senales,
        resumen_ia=resultado.resumen_para_contacto, motor_ia=resultado.motor,
    )
    avisar_contacto(
        cuenta, t["id"], "NO_VERIFICADA",
        f"SilverShield no ha podido verificar una transferencia de "
        f"{euros_hablados(t['importe'])} de {cuenta['titular']} a {t['beneficiario_nombre']} "
        "por un problema técnico y la ha dejado retenida. Un operador del banco la revisará.",
    )
    return t


def _recordar(resultado, t: dict, transferencia_id: int) -> None:
    """Guarda en la memoria de la clienta lo aprendido en una verificación terminada."""
    if resultado.decision == "seguro" and resultado.recordar:
        db.guardar_memoria("contexto", resultado.recordar, t["iban"], t["beneficiario_nombre"],
                           transferencia_id)
    elif resultado.decision == "riesgo":
        hechos = resultado.recordar or [
            f"Intento de estafa detectado ({resultado.categoria}) al enviar "
            f"{euros_hablados(t['importe'])} a {t['beneficiario_nombre']}."
        ]
        db.guardar_memoria("alerta", hechos, t["iban"], t["beneficiario_nombre"], transferencia_id)


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
    # retiene la operación y avisa en silencio al contacto de emergencia.
    if _contiene_palabra_seguridad(datos.texto, cuenta.get("palabra_seguridad")):
        texto = (
            f"De acuerdo, {cuenta['nombre_corto']}. Para terminar, un operador del banco revisará "
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
        # Se recuerda la coacción (sin la palabra) para futuras verificaciones.
        db.guardar_memoria("alerta", [
            f"Usó su palabra de auxilio (posible coacción) al intentar enviar "
            f"{euros_hablados(t['importe'])} a {t['beneficiario_nombre']}."
        ], t["iban"], t["beneficiario_nombre"], transferencia_id)
        return {
            "respuesta": _mensaje_publico(respuesta),
            "decision": "revision",
            "final": True,
            "transferencia": db.obtener_transferencia(transferencia_id),
            "contacto_avisado": True,
            "tiempo_ms": int((time.perf_counter() - inicio) * 1000),
        }

    memoria = {"perfil": db.perfil_destinatario(t["iban"]), "hechos": db.memoria_para(t["iban"])}
    resultado = await evaluar_turno(t, cuenta, mensajes, senales, memoria)
    tiempo_ms = int((time.perf_counter() - inicio) * 1000)
    respuesta = db.guardar_mensaje(transferencia_id, "asistente", resultado.respuesta, {
        "motor": resultado.motor, "tiempo_ms": tiempo_ms, "tiempo_ia_ms": resultado.tiempo_ia_ms,
        "tokens_entrada": resultado.tokens_entrada, "tokens_salida": resultado.tokens_salida,
    })
    log.info("Turno de verificación #%s: %s ms en total (IA: %s ms, motor: %s)",
             transferencia_id, tiempo_ms, resultado.tiempo_ia_ms, resultado.motor)

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
    if resultado.decision == "no_verificada":
        t = _retener_no_verificada(t, cuenta, resultado)
        contacto_avisado = True
    else:
        t = db.actualizar_transferencia(transferencia_id, **campos)
    _recordar(resultado, t, transferencia_id)

    return {
        "respuesta": _mensaje_publico(respuesta),
        "decision": resultado.decision,
        "final": resultado.decision != "preguntar",
        "nivel_riesgo": resultado.nivel_riesgo,
        # Para explicar en pantalla por qué se ha parado (solo se muestran si hay riesgo).
        "categoria": resultado.categoria,
        "senales": resultado.senales,
        "transferencia": t,
        "contacto_avisado": contacto_avisado,
        "motor": resultado.motor,
        "tiempo_ms": tiempo_ms,
        "tiempo_ia_ms": resultado.tiempo_ia_ms,
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


# ------------------------------------------------------------------ panel del operador del banco

@app.get("/api/panel")
async def datos_panel(operador: str = Depends(exigir_operador)):
    cuenta = db.obtener_cuenta()
    return {
        "operador": operador,
        "cuenta": cuenta,
        "transferencias": db.listar_transferencias(limite=50),
        "alertas": db.listar_alertas(),
        "memoria": db.listar_memoria(),
        "estado": await estado(),
    }


@app.get("/api/memoria")
async def ver_memoria(_operador: str = Depends(exigir_operador)):
    """Todo lo que SilverShield recuerda de la clienta (solo para el operador)."""
    return {"memoria": db.listar_memoria()}


@app.delete("/api/memoria/{memoria_id}")
async def borrar_recuerdo(memoria_id: int, operador: str = Depends(exigir_operador)):
    """El operador puede borrar un recuerdo erróneo (por ejemplo, un falso positivo)."""
    if not db.borrar_memoria(memoria_id):
        raise HTTPException(status_code=404, detail="Recuerdo no encontrado")
    log.info("El operador «%s» ha borrado el recuerdo #%s", operador, memoria_id)
    return {"ok": True}


@app.post("/api/demo/reiniciar")
async def reiniciar_demo(_operador: str = Depends(exigir_operador)):
    db.reiniciar_demo()
    return {"ok": True}
