import sqlite3
import os
from datetime import datetime

# La base de datos se guardará en la carpeta backend
DB_PATH = os.path.join(os.path.dirname(__file__), "silvershield.db")

def inicializar_bd():
    """Crea la tabla si no existe al arrancar el servidor."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registro_alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            texto_usuario TEXT,
            nivel_estres TEXT,
            bloqueado BOOLEAN
        )
    ''')
    conexion.commit()
    conexion.close()

def guardar_registro(texto: str, nivel_estres: str, bloqueado: bool):
    """Guarda un nuevo evento en el historial."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    cursor.execute(
        "INSERT INTO registro_alertas (fecha, texto_usuario, nivel_estres, bloqueado) VALUES (?, ?, ?, ?)",
        (fecha_actual, texto, nivel_estres, bloqueado)
    )
    conexion.commit()
    conexion.close()

def obtener_historial():
    """Devuelve los últimos 5 registros para mostrarlos en la web."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT fecha, texto_usuario, nivel_estres, bloqueado FROM registro_alertas ORDER BY id DESC LIMIT 5")
    filas = cursor.fetchall()
    conexion.close()
    
    historial = []
    for fila in filas:
        historial.append({
            "fecha": fila[0],
            "texto": fila[1],
            "estres": fila[2],
            "bloqueado": bool(fila[3])
        })
    return historial

def limpiar_bd():
    """Borra todos los registros de la tabla."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM registro_alertas")
    conexion.commit()
    conexion.close()