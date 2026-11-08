import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env en la raíz
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")