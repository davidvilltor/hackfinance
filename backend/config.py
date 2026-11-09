"""Configuración central de SilverShield.

Todos los valores se pueden sobrescribir con variables de entorno (o un archivo
.env en la raíz del proyecto). Ver .env.example.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ_PROYECTO / ".env")


def _lista_env(nombre: str, por_defecto: str) -> set[str]:
    valor = os.getenv(nombre, por_defecto)
    return {c.strip().upper() for c in valor.split(",") if c.strip()}


# --- IA de lenguaje (Anthropic Claude) ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or None
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
# Esfuerzo bajo = respuestas rápidas, adecuado para una conversación por voz.
CLAUDE_EFFORT = os.getenv("CLAUDE_EFFORT", "low")
CLAUDE_TIMEOUT_S = float(os.getenv("CLAUDE_TIMEOUT_S", "25"))

# --- Voz (ElevenLabs) ---
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY") or None
# Voz nativa de España, cálida y pausada ("Sara Martin - Gentle", biblioteca de ElevenLabs).
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "KHCvMklQZZo0O30ERnVn")
# eleven_multilingual_v2: la pronunciación más clara y natural en español.
# Para menos latencia puede usarse eleven_flash_v2_5 (algo menos nítido).
ELEVENLABS_TTS_MODEL = os.getenv("ELEVENLABS_TTS_MODEL", "eleven_multilingual_v2")
ELEVENLABS_STT_MODEL = os.getenv("ELEVENLABS_STT_MODEL", "scribe_v1")
# Velocidad del habla (0.7 - 1.2). Algo más lenta que la normal para personas mayores.
ELEVENLABS_VELOCIDAD = float(os.getenv("ELEVENLABS_VELOCIDAD", "0.92"))

# --- Reglas de negocio ---
UMBRAL_VERIFICACION_EUR = float(os.getenv("UMBRAL_VERIFICACION_EUR", "500"))
# Porcentaje del saldo a partir del cual una transferencia se considera inusual.
PORCENTAJE_SALDO_INUSUAL = float(os.getenv("PORCENTAJE_SALDO_INUSUAL", "0.5"))
# País del banco del cliente: las cuentas de otros países se consideran "extranjeras".
PAIS_LOCAL = os.getenv("PAIS_LOCAL", "ES").upper()
# Lista ilustrativa basada en las jurisdicciones bajo vigilancia del GAFI/FATF y en
# destinos habituales de cuentas mula. En producción debe sincronizarse con la
# lista oficial vigente y con la inteligencia antifraude del propio banco.
PAISES_ALTO_RIESGO = _lista_env(
    "PAISES_ALTO_RIESGO", "IR,KP,MM,SY,YE,LB,VG,HT,VE,NG,GH,KE,PH"
)
# Máximo de respuestas del cliente antes de que SilverShield dé un veredicto.
MAX_TURNOS_VERIFICACION = int(os.getenv("MAX_TURNOS_VERIFICACION", "4"))

# --- Persistencia ---
DB_PATH = os.getenv("SILVERSHIELD_DB", str(RAIZ_PROYECTO / "backend" / "silvershield.db"))


def ia_disponible() -> bool:
    return bool(ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_AUTH_TOKEN"))


def voz_disponible() -> bool:
    return bool(ELEVENLABS_API_KEY)
