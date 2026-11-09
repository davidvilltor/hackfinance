"""Persistencia SQLite de SilverShield (cuenta demo, transferencias, conversación
de verificación y alertas al contacto de confianza)."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from backend import config

# Estados posibles de una transferencia
PENDIENTE_DECISION = "pendiente_decision"   # Ha saltado una regla: el cliente elige
EN_VERIFICACION = "en_verificacion"         # Conversando con SilverShield
VERIFICADA_SEGURA = "verificada_segura"     # SilverShield recomienda seguir
RETENIDA = "retenida"                       # SilverShield la ha parado; decide el contacto
COMPLETADA = "completada"
CANCELADA = "cancelada"

ESTADOS_ACTIVOS = {PENDIENTE_DECISION, EN_VERIFICACION, VERIFICADA_SEGURA, RETENIDA}

DATOS_DEMO = {
    "cuenta": {
        "titular": "María López",
        "nombre_corto": "María",
        "edad": 82,
        "iban": "ES6201822370420201504455",
        "saldo": 12450.00,
        "contacto_nombre": "Carlos",
        "contacto_relacion": "hijo",
        "contacto_telefono": "+34 600 123 456",
        "palabra_seguridad": "girasol",
    },
    "beneficiarios": [
        ("Carlos López", "Mi hijo Carlos", "ES9121000418450200051332"),
        ("Comunidad de Propietarios C/ Mayor 12", "La comunidad", "ES6000491500051234567892"),
        ("Clínica Dental Sonrisa", "El dentista", "ES9820385778983000760236"),
    ],
}

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS cuenta (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    titular TEXT NOT NULL,
    nombre_corto TEXT NOT NULL,
    edad INTEGER,
    iban TEXT NOT NULL,
    saldo REAL NOT NULL,
    contacto_nombre TEXT,
    contacto_relacion TEXT,
    contacto_telefono TEXT,
    palabra_seguridad TEXT
);
CREATE TABLE IF NOT EXISTS beneficiarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    alias TEXT,
    iban TEXT NOT NULL UNIQUE,
    fecha_alta TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS transferencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    beneficiario_nombre TEXT NOT NULL,
    iban TEXT NOT NULL,
    pais TEXT NOT NULL,
    importe REAL NOT NULL,
    concepto TEXT,
    estado TEXT NOT NULL,
    via TEXT,
    evaluacion TEXT,
    veredicto_ia TEXT,
    nivel_riesgo_ia INTEGER,
    categoria_estafa TEXT,
    senales_ia TEXT,
    resumen_ia TEXT,
    motor_ia TEXT,
    fecha_resolucion TEXT
);
CREATE TABLE IF NOT EXISTS mensajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transferencia_id INTEGER NOT NULL REFERENCES transferencias(id),
    fecha TEXT NOT NULL,
    rol TEXT NOT NULL CHECK (rol IN ('asistente', 'cliente')),
    texto TEXT NOT NULL,
    senales TEXT
);
CREATE TABLE IF NOT EXISTS alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    transferencia_id INTEGER REFERENCES transferencias(id),
    tipo TEXT NOT NULL,
    mensaje TEXT NOT NULL,
    canal TEXT NOT NULL,
    destinatario TEXT
);
"""


def ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


@contextmanager
def conectar():
    conexion = sqlite3.connect(config.DB_PATH)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    try:
        yield conexion
        conexion.commit()
    finally:
        conexion.close()


def inicializar_bd() -> None:
    with conectar() as db:
        db.executescript(_ESQUEMA)
        if db.execute("SELECT COUNT(*) FROM cuenta").fetchone()[0] == 0:
            _sembrar(db)


def _sembrar(db: sqlite3.Connection) -> None:
    c = DATOS_DEMO["cuenta"]
    db.execute(
        """INSERT INTO cuenta (id, titular, nombre_corto, edad, iban, saldo, contacto_nombre,
           contacto_relacion, contacto_telefono, palabra_seguridad)
           VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (c["titular"], c["nombre_corto"], c["edad"], c["iban"], c["saldo"],
         c["contacto_nombre"], c["contacto_relacion"], c["contacto_telefono"],
         c["palabra_seguridad"]),
    )
    for nombre, alias, iban in DATOS_DEMO["beneficiarios"]:
        db.execute(
            "INSERT INTO beneficiarios (nombre, alias, iban, fecha_alta) VALUES (?, ?, ?, ?)",
            (nombre, alias, iban, ahora()),
        )
    # Un par de movimientos previos para que la pantalla de inicio no esté vacía.
    for dias, (nombre, iban, importe, concepto) in enumerate([
        ("Comunidad de Propietarios C/ Mayor 12", "ES6000491500051234567892", 85.0, "Cuota comunidad"),
        ("Carlos López", "ES9121000418450200051332", 150.0, "Cumpleaños Lucía"),
    ], start=1):
        db.execute(
            """INSERT INTO transferencias (fecha, beneficiario_nombre, iban, pais, importe,
               concepto, estado, via, fecha_resolucion)
               VALUES (strftime('%Y-%m-%dT%H:%M:%S', 'now', 'localtime', ?), ?, ?, 'ES', ?, ?, ?,
                       'directa', strftime('%Y-%m-%dT%H:%M:%S', 'now', 'localtime', ?))""",
            (f"-{dias * 3} days", nombre, iban, importe, concepto, COMPLETADA, f"-{dias * 3} days"),
        )


def reiniciar_demo() -> None:
    with conectar() as db:
        for tabla in ("alertas", "mensajes", "transferencias", "beneficiarios", "cuenta"):
            db.execute(f"DELETE FROM {tabla}")
        db.execute("DELETE FROM sqlite_sequence")
        _sembrar(db)


# ---------------------------------------------------------------- Cuenta

def obtener_cuenta() -> dict:
    with conectar() as db:
        return dict(db.execute("SELECT * FROM cuenta WHERE id = 1").fetchone())


def listar_beneficiarios() -> list[dict]:
    with conectar() as db:
        filas = db.execute("SELECT * FROM beneficiarios ORDER BY id").fetchall()
        return [dict(f) for f in filas]


def beneficiario_conocido(iban: str) -> bool:
    with conectar() as db:
        return db.execute(
            "SELECT 1 FROM beneficiarios WHERE iban = ?", (iban,)
        ).fetchone() is not None


# ---------------------------------------------------------------- Transferencias

def _deserializar(fila: sqlite3.Row | None) -> dict | None:
    if fila is None:
        return None
    datos = dict(fila)
    for campo in ("evaluacion", "senales_ia"):
        if datos.get(campo):
            datos[campo] = json.loads(datos[campo])
    return datos


def crear_transferencia(nombre: str, iban: str, pais: str, importe: float,
                        concepto: str, estado: str, evaluacion: dict) -> dict:
    with conectar() as db:
        cursor = db.execute(
            """INSERT INTO transferencias (fecha, beneficiario_nombre, iban, pais, importe,
               concepto, estado, evaluacion) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (ahora(), nombre, iban, pais, importe, concepto, estado,
             json.dumps(evaluacion, ensure_ascii=False)),
        )
        nuevo_id = cursor.lastrowid
    return obtener_transferencia(nuevo_id)


def obtener_transferencia(transferencia_id: int) -> dict | None:
    with conectar() as db:
        fila = db.execute(
            "SELECT * FROM transferencias WHERE id = ?", (transferencia_id,)
        ).fetchone()
        return _deserializar(fila)


def listar_transferencias(limite: int = 50, solo_completadas: bool = False) -> list[dict]:
    consulta = "SELECT * FROM transferencias"
    if solo_completadas:
        consulta += f" WHERE estado = '{COMPLETADA}'"
    consulta += " ORDER BY fecha DESC, id DESC LIMIT ?"
    with conectar() as db:
        return [_deserializar(f) for f in db.execute(consulta, (limite,)).fetchall()]


def actualizar_transferencia(transferencia_id: int, **campos) -> dict:
    if "senales_ia" in campos and campos["senales_ia"] is not None:
        campos["senales_ia"] = json.dumps(campos["senales_ia"], ensure_ascii=False)
    asignaciones = ", ".join(f"{k} = ?" for k in campos)
    with conectar() as db:
        db.execute(
            f"UPDATE transferencias SET {asignaciones} WHERE id = ?",
            (*campos.values(), transferencia_id),
        )
    return obtener_transferencia(transferencia_id)


class SaldoInsuficiente(Exception):
    pass


def completar_transferencia(transferencia_id: int, via: str, guardar_beneficiario: bool = True) -> dict:
    """Ejecuta el cargo de forma atómica: descuenta el saldo y marca la
    transferencia como completada."""
    with conectar() as db:
        t = db.execute("SELECT * FROM transferencias WHERE id = ?", (transferencia_id,)).fetchone()
        saldo = db.execute("SELECT saldo FROM cuenta WHERE id = 1").fetchone()[0]
        if t["importe"] > saldo:
            raise SaldoInsuficiente()
        db.execute("UPDATE cuenta SET saldo = saldo - ? WHERE id = 1", (t["importe"],))
        db.execute(
            "UPDATE transferencias SET estado = ?, via = ?, fecha_resolucion = ? WHERE id = ?",
            (COMPLETADA, via, ahora(), transferencia_id),
        )
        if guardar_beneficiario:
            db.execute(
                "INSERT OR IGNORE INTO beneficiarios (nombre, alias, iban, fecha_alta) "
                "VALUES (?, ?, ?, ?)",
                (t["beneficiario_nombre"], t["beneficiario_nombre"], t["iban"], ahora()),
            )
    return obtener_transferencia(transferencia_id)


# ---------------------------------------------------------------- Conversación

def guardar_mensaje(transferencia_id: int, rol: str, texto: str, senales: dict | None = None) -> dict:
    with conectar() as db:
        cursor = db.execute(
            "INSERT INTO mensajes (transferencia_id, fecha, rol, texto, senales) VALUES (?, ?, ?, ?, ?)",
            (transferencia_id, ahora(), rol, texto,
             json.dumps(senales, ensure_ascii=False) if senales else None),
        )
        return {"id": cursor.lastrowid, "rol": rol, "texto": texto}


def obtener_mensajes(transferencia_id: int) -> list[dict]:
    with conectar() as db:
        filas = db.execute(
            "SELECT * FROM mensajes WHERE transferencia_id = ? ORDER BY id", (transferencia_id,)
        ).fetchall()
    mensajes = []
    for f in filas:
        m = dict(f)
        m["senales"] = json.loads(m["senales"]) if m["senales"] else None
        mensajes.append(m)
    return mensajes


def obtener_mensaje(mensaje_id: int) -> dict | None:
    with conectar() as db:
        fila = db.execute("SELECT * FROM mensajes WHERE id = ?", (mensaje_id,)).fetchone()
        return dict(fila) if fila else None


# ---------------------------------------------------------------- Alertas

def guardar_alerta(transferencia_id: int | None, tipo: str, mensaje: str,
                   canal: str, destinatario: str) -> dict:
    with conectar() as db:
        cursor = db.execute(
            "INSERT INTO alertas (fecha, transferencia_id, tipo, mensaje, canal, destinatario) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ahora(), transferencia_id, tipo, mensaje, canal, destinatario),
        )
        return {"id": cursor.lastrowid, "tipo": tipo, "mensaje": mensaje}


def listar_alertas(limite: int = 30) -> list[dict]:
    with conectar() as db:
        filas = db.execute(
            "SELECT * FROM alertas ORDER BY id DESC LIMIT ?", (limite,)
        ).fetchall()
        return [dict(f) for f in filas]
