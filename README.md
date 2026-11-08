# 🛡️ SilverShield
> **Escudo de protección bancaria inteligente y empático contra fraudes dirigido a la tercera edad.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=flat-square&logo=fastapi)
![Anthropic Claude](https://img.shields.io/badge/Claude_3.5-Sonnet-8A2BE2?style=flat-square&logo=anthropic)
![ElevenLabs](https://img.shields.io/badge/ElevenLabs-Voice_AI-FF6F61?style=flat-square&logo=elevenlabs)
![PSD2 Compliant](https://img.shields.io/badge/Compliance-PSD2_%2F_TLS_1.3-success?style=flat-square)

## 📌 ¿Qué es SilverShield?
Las campañas tradicionales de ciberseguridad bancaria suelen fallar en el sector senior debido a la brecha digital y al miedo que provocan los estafadores (falsos técnicos, estafas del familiar en apuros, smishing). 

**SilverShield** actúa como una capa defensiva integrada de forma nativa en la banca digital (*SilverBank*). Analiza en tiempo real los intentos de fraude a través de múltiples canales (llamadas, WhatsApp, enlaces web), utilizando inteligencia artificial cognitiva para neutralizar el pánico, bloquear transacciones maliciosas y alertar instantáneamente a los familiares de confianza.

## 🚀 Características Principales
* **Inteligencia Cognitiva Adaptativa (Claude 3.5 Sonnet):** Analiza el contexto de la amenaza y desmiente los engaños con la lógica y la cercanía que una persona mayor necesita.
* **Síntesis de Voz Empática (ElevenLabs):** Genera alertas auditivas con un tono extremadamente calmado y protector para evitar que el usuario entre en pánico.
* **Omnicanalidad:** Detecta fraudes procedentes de llamadas telefónicas, chats (WhatsApp/SMS) o enlaces web fraudulentos (Smishing).
* **Auditoría y Persistencia (SQLite):** Registra cada evento con marcas de tiempo, texto analizado y estado de bloqueo para cumplir con los estándares de trazabilidad legal bancaria.
* **Accesibilidad Extrema:** Interfaz diseñada con tipografía de alto contraste, botón *"A+ Letra Grande"* y soporte de lectura por voz nativa como respaldo universal.

## 🛠️ Stack Tecnológico
* **Backend:** Python, FastAPI, Uvicorn, SQLite.
* **Inteligencia Artificial & Voz:** Anthropic API (`claude-3-5-sonnet-20240620`), ElevenLabs API (Text-to-Speech).
* **Frontend:** HTML5, CSS3 moderno, JavaScript Vanilla (Web Speech API para dictado por voz y síntesis nativa).

## ⚙️ Guía de Instalación y Ejecución Local

Sigue estos pasos para poner en marcha el proyecto en tu entorno local:

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
