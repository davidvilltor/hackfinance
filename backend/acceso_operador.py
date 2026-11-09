"""Acceso de los operadores del banco al panel de SilverShield.

Por motivos legales, solo un operador del banco puede liberar o cancelar una
transferencia retenida. Este módulo comprueba quién es el operador:

- Los operadores y sus contraseñas se configuran en `.env` (variable OPERADORES).
- Al entrar se crea una cookie de sesión firmada con HMAC-SHA256 (usuario y fecha de
  caducidad). Es HttpOnly (el JavaScript de la página no puede leerla) y
  SameSite=Strict (otra web no puede usarla para lanzar acciones en nombre del operador).
- Cada liberación o cancelación queda registrada con el nombre del operador.

Es un acceso sencillo para el prototipo, sin dependencias externas. En producción
se sustituiría por el sistema de identidad del banco (SSO, doble factor).
"""
import base64
import hashlib
import hmac
import time

from fastapi import HTTPException, Request, Response

from backend import config

COOKIE = "ss_operador"


def _firma(datos: str) -> str:
    return hmac.new(config.OPERADOR_SECRETO.encode(), datos.encode(), hashlib.sha256).hexdigest()


def credenciales_validas(usuario: str, contrasena: str) -> bool:
    esperada = config.OPERADORES.get(usuario)
    # Se compara siempre (aunque el usuario no exista) para no dar pistas por el tiempo de respuesta.
    correcta = hmac.compare_digest(contrasena.encode(), (esperada or "\0").encode())
    return esperada is not None and correcta


def abrir_sesion(respuesta: Response, usuario: str) -> None:
    duracion_s = int(config.OPERADOR_SESION_HORAS * 3600)
    datos = f"{usuario}|{int(time.time()) + duracion_s}"
    token = base64.urlsafe_b64encode(f"{datos}|{_firma(datos)}".encode()).decode()
    respuesta.set_cookie(COOKIE, token, max_age=duracion_s, httponly=True, samesite="strict", path="/")


def cerrar_sesion(respuesta: Response) -> None:
    respuesta.delete_cookie(COOKIE, path="/")


def operador_actual(request: Request) -> str | None:
    """Devuelve el usuario del operador si la cookie es válida y no ha caducado."""
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    try:
        usuario, expira, firma = base64.urlsafe_b64decode(token.encode()).decode().rsplit("|", 2)
        caducada = int(expira) < time.time()
    except (ValueError, UnicodeDecodeError):
        return None
    if caducada or not hmac.compare_digest(firma, _firma(f"{usuario}|{expira}")):
        return None
    # Si se ha quitado al operador de la configuración, su sesión deja de valer.
    return usuario if usuario in config.OPERADORES else None


def exigir_operador(request: Request) -> str:
    """Dependencia de FastAPI para las rutas reservadas a operadores."""
    usuario = operador_actual(request)
    if usuario is None:
        raise HTTPException(status_code=401, detail="Acceso reservado a operadores del banco. Inicie sesión.")
    return usuario
