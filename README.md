# Hackfinance
# 🛡️ SilverShield - Guardián de Voz contra el Fraude Financiero

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![ElevenLabs](https://img.shields.io/badge/ElevenLabs-API-orange.svg)
![Twilio](https://img.shields.io/badge/Twilio-Voice-red.svg)

## 📋 Descripción del Proyecto

**SilverShield** es un asistente de voz impulsado por IA que protege a las personas mayores de fraudes financieros en tiempo real. Utiliza análisis de lenguaje natural (GPTAdvisor) y síntesis de voz hiperrealista (ElevenLabs) para verificar transferencias bancarias, detectar patrones de estafa y prevenir la coacción financiera.

### 🎯 Problema que Resuelve

Cada año, los adultos mayores pierden **$27 mil millones** en estafas financieras. Las soluciones actuales (SMS, apps complejas) fallan porque:

- Los estafadores engañan a las víctimas para que compartan códigos SMS
- Las interfaces digitales son confusas para personas con baja alfabetización digital
- No detectan coacción familiar o estrés emocional

### 💡 Nuestra Solución

Un sistema que **llama por teléfono** (la tecnología más familiar para este segmento) y:

1. **Verifica transferencias inusuales** mediante conversación natural
2. **Detecta patrones de fraude** (urgencia, autoridad falsa, emergencias familiares)
3. **Analiza estrés vocal** para identificar coacción o confusión
4. **Bloquea operaciones sospechosas** y notifica a contactos de confianza

## 🚀 Características Principales

- ✅ **Detección de fraude en tiempo real** con LLMs
- ✅ **Análisis de estrés vocal** para identificar coacción
- ✅ **Voz natural y empática** con ElevenLabs
- ✅ **Integración telefónica** vía Twilio
- ✅ **Notificaciones automáticas** a contactos de emergencia
- ✅ **Dashboard de monitoreo** para familiares/tutores

## 🛠️ Stack Tecnológico

| Componente        | Tecnología                    | Propósito                                  |
| ----------------- | ----------------------------- | ------------------------------------------ |
| Backend           | Python + FastAPI              | API REST asíncrona                         |
| IA Conversacional | GPTAdvisor (OpenAI/Anthropic) | Análisis semántico y detección de fraude   |
| Síntesis de Voz   | ElevenLabs API                | Voz natural y empática                     |
| Telefonía         | Twilio Voice                  | Llamadas entrantes/salientes               |
| Transcripción     | OpenAI Whisper / Twilio STT   | Speech-to-text                             |
| Base de Datos     | SQLite / PostgreSQL           | Almacenamiento de usuarios y transacciones |
| Frontend          | Streamlit                     | Dashboard de monitoreo                     |

## Requisitos

- Python 3.10 o superior
- Cuenta en Twilio (con número de teléfono)
- API Key de ElevenLabs
- API Key de OpenAI o Anthropic (GPTAdvisor)
- (Opcional) Cuenta en Belvo o Plaid para Open Banking

## 🔧 Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/davidvilltor/hackfinance.git
cd hackfinance
```

### 2. Flujo de trabajo diario

Antes de cambiar nada, en Git Bash situado en la carpeta "hackfinance": cd hackfinance. Hacer el siguiente comando para actualizar la última versión del main (Por si alguien ha modificado algo nuevo):
```bash
git pull
```

Con git status vemos como estamos respecto al código. Importante usar mucho git status para comprobar que lo que subimos es lo bueno y no tocamos nada más.
```bash
git status
```

Cuando tengamos el main actual, trabajamos lo que toque en VSCode. Una vez terminado y guardado lo de VSCode, volvemos a Git Bash y añadimos el archivo que hayamos cambiado.
```bash
git add "frontend/templates/index.html"
```

Con git diff --staged comprobamos lo que hemos cambiado en el archivo 
```bash
git diff --staged
```

Si nos equivocamos con el archivo que añadimos: 
```bash
git restore --staged "frontend/templates/index.html"
```

Si todo está bien, subimos el cambio poniendo poca info sobre lo cambiado con:
```bash
git commit -m "Añade <parte de código o función> de <nombre_archivo>"
```
O para añadir una descripción mayor(En VSCode abre un editor, la 1era línea se pone el título, dejamos un línea en blanco y debajo la descripción): 
```bash
git commit
```

Para cambiarlo en GitHub:
```bash
git push
```
