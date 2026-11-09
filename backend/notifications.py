"""Avisos cuando SilverShield retiene una transferencia.

Cada aviso llega a dos sitios:
- al panel del operador del banco (/panel), que es quien revisa la operación y el
  único que puede liberarla o cancelarla;
- al contacto de emergencia del cliente, solo para informarle (no puede autorizar nada).

En la demo el aviso se guarda en la base de datos (aparece en directo en el panel
del operador) y se escribe en la consola del servidor: NO se envía ningún SMS real.
En producción, aquí se conectaría la pasarela SMS/WhatsApp/push del banco.
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
        canal="Panel del operador · aviso al contacto simulado (SMS en producción)",
        destinatario=destinatario,
    )
    log.warning("AVISO [%s] a %s: %s", tipo, destinatario, mensaje)
    return alerta
