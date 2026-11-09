"""Avisos al contacto de confianza.

En la demo el aviso se registra en la base de datos (aparece en tiempo real en el
panel /panel del contacto de confianza) y se muestra en la consola del servidor.
En producción este módulo se conectaría con la pasarela SMS/WhatsApp/push del banco.
"""
import logging

from backend import database

log = logging.getLogger("silvershield.avisos")


def avisar_contacto(cuenta: dict, transferencia_id: int | None, tipo: str, mensaje: str) -> dict:
    destinatario = f"{cuenta.get('contacto_nombre')} ({cuenta.get('contacto_telefono')})"
    alerta = database.guardar_alerta(
        transferencia_id=transferencia_id,
        tipo=tipo,
        mensaje=mensaje,
        canal="SMS + notificación en la app",
        destinatario=destinatario,
    )
    log.warning("AVISO [%s] a %s: %s", tipo, destinatario, mensaje)
    return alerta
