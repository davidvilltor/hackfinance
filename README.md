# 🛡️ SilverShield

> Verificación por voz con IA que protege a las personas mayores frente a estafas y coacción en sus transferencias bancarias.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=flat-square&logo=fastapi)
![Claude](https://img.shields.io/badge/Claude-Opus_5.5-8A2BE2?style=flat-square&logo=anthropic)
![ElevenLabs](https://img.shields.io/badge/ElevenLabs-Multilingual_v2_%2B_Scribe-FF6F61?style=flat-square)

## El problema
Los estafadores convencen a personas mayores para que hagan transferencias (falso técnico, falso empleado del banco, "hijo en apuros"...) y les piden en la misma llamada el código SMS que debería protegerlas. El SMS no detecta el engaño: solo confirma que la víctima tiene el móvil en la mano.

## La solución
SilverShield se integra en la banca online y actúa solo cuando hace falta:

1. **Motor de reglas instantáneo.** Una transferencia normal se envía sin fricción. Se pide confirmación si:
   - el importe es de **500 € o más**, o
   - por debajo de 500 €, la cuenta está en un **país de alto riesgo**, es una **cuenta extranjera nueva**, el concepto es típico de estafa ("bitcoin", "Hacienda", "soporte técnico"...) o supera la mitad del saldo.
2. **Pantalla de decisión** con dos opciones grandes y claras:
   - **"Solicitar verificación con SilverShield"** (recomendada).
   - **"Conozco al destinatario: autorizar directamente"** (si el riesgo es alto, se pide una segunda confirmación).
3. **Conversación por voz con IA.** SilverShield explica la operación en lenguaje sencillo y hace preguntas cortas (para qué es el dinero, si alguien se lo ha pedido, si hay alguien al lado dictando). **Claude** analiza cada respuesta junto con el contexto de la transferencia y con indicadores de estrés de la voz (velocidad del habla, volumen, titubeos). **ElevenLabs** pone una voz española, clara, pausada y tranquila.
4. **Veredicto:**
   - ✅ *Puede enviarla*: la persona confirma el envío con un botón.
   - ⛔ *No la envíe*: la transferencia queda **retenida**, se explica con calma por qué parece un engaño y se **avisa al contacto de confianza**, que puede liberarla o cancelarla desde su panel.
5. **Palabra de auxilio (contra la coacción).** Si alguien obliga a la persona a transferir, basta con que diga su palabra secreta durante la conversación. SilverShield responde con normalidad (para no alertar a quien presiona), retiene la operación y avisa en silencio al familiar.

## Accesibilidad y experiencia de usuario
- Una tarea por pantalla, lenguaje llano, texto base de 20 px con tres tamaños (Normal, Grande, Muy grande) y **modo de alto contraste**, que se recuerdan entre visitas.
- Botones de 64 a 96 px, iconos siempre con texto, foco de teclado muy visible y compatible con lectores de pantalla (`aria-live`, roles, gestión del foco al cambiar de pantalla).
- Subtítulos de todo lo que dice el asistente, botón **"Repetir"**, opción **"Prefiero escribir"** y botón **"Escuchar este mensaje"** en la pantalla de decisión.
- Sin límites de tiempo y respetando la preferencia de "reducir movimiento" del sistema.
- **Latencia baja:** el saludo es instantáneo (plantilla), Claude trabaja con esfuerzo `low` y la voz de ElevenLabs (nativa de España, modelo Multilingual v2) llega en streaming, así que el audio empieza a sonar antes de estar completo. La cabecera `Server-Timing` mide cada petición.

## Requisitos
- Python 3.10 o superior (probado en 3.15).
- Chrome o Edge (recomendado, por el reconocimiento de voz del navegador). En Firefox se usa ElevenLabs Scribe para transcribir.
- Opcional: claves de **Anthropic** y **ElevenLabs**. **Sin claves la app funciona igual**: usa un evaluador local en lugar de Claude y la voz del navegador en lugar de ElevenLabs.

## Instalación
```bash
git clone https://github.com/davidvilltor/hackfinance.git
cd hackfinance
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
```

## Configuración
```bash
cp .env.example .env      # Windows: copy .env.example .env
```
Rellene `ANTHROPIC_API_KEY` y `ELEVENLABS_API_KEY`. El resto de opciones (modelo, voz, umbral, países de riesgo, número máximo de preguntas) están documentadas en `.env.example`.

## Ejecución
```bash
python -m uvicorn backend.main:app --reload
```
- App del cliente: <http://localhost:8000>
- Panel del contacto de confianza / gestor: <http://localhost:8000/panel> (ábralo en otra ventana para ver los avisos en directo)
- Documentación de la API: <http://localhost:8000/docs>

La base de datos SQLite se crea sola con datos de demo (María López, 82 años, contacto de confianza: su hijo Carlos, palabra de auxilio: «girasol»). Para empezar de cero use el botón **"Reiniciar datos de la demo"** del panel.

## Cómo probarlo
### Escenarios de demo
| Escenario | Destinatario e IBAN | Importe | Resultado esperado |
|---|---|---|---|
| Transferencia habitual | "Mi hijo Carlos" (guardado) | 100 € | Se envía directamente |
| Importe alto, destinatario conocido | "La comunidad" (guardado) | 800 € | Pantalla de decisión → "Conozco al destinatario" → enviada |
| Estafa del falso técnico | Otra persona · `ES48 1465 0100 7220 3087 6293` · concepto "Soporte técnico" | 2.500 € | Decisión → SilverShield → responder *"Me ha llamado un chico de Microsoft, dice que tengo un virus"* → **retenida** y aviso en el panel |
| País de alto riesgo por debajo de 500 € | Otra persona · `VG96 VPVG 0000 0123 4567 8901` | 300 € | Pantalla de decisión con aviso de nivel alto |
| Extranjero nuevo por debajo de 500 € | Otra persona · `PT50 0002 0123 1234 5678 9015 4` | 200 € | Pantalla de decisión |
| Coacción | Cualquier transferencia que pase a verificación | ≥ 500 € | Decir una frase con «girasol» → "en revisión" + aviso urgente en el panel |
| Uso legítimo | "Mi hijo Carlos" · concepto "Reforma" | 900 € | Verificación → *"Es para la reforma del baño"*, *"Lo he decidido yo, le he llamado yo"* → recomendación de enviar |

### Tests automáticos
```bash
pip install -r requirements-dev.txt
python -m pytest
```
29 pruebas: reglas de riesgo y validación de IBAN, el flujo completo de la API (envío directo, autorización, estafa detectada, uso legítimo, palabra de auxilio, límite de turnos y errores), la respuesta estructurada de Claude y el paso al evaluador local si Claude falla. Los tests no necesitan claves de API.

## Estructura
```
backend/
  main.py                 API FastAPI y máquina de estados de la transferencia
  reglas_riesgo.py        Motor de reglas (umbral, países, IBAN, conceptos)
  agente_silvershield.py  Conversación con Claude (salida JSON con esquema) + evaluador local de respaldo
  voice_agent.py          ElevenLabs: voz (streaming) y transcripción (Scribe)
  voice_stress.py         Indicadores de estrés y coacción (texto y métricas acústicas)
  notifications.py        Avisos al contacto de confianza
  database.py             SQLite: cuenta, beneficiarios, transferencias, conversación y alertas
  config.py               Configuración por variables de entorno
frontend/
  templates/index.html    App del cliente (persona mayor)
  templates/panel.html    Panel del contacto de confianza / gestor del banco
  static/js/voz.js        Síntesis de voz, reconocimiento de voz y medición acústica en el navegador
  static/js/app.js        Lógica de las pantallas del cliente
prompts/prompt_sistema.txt  Instrucciones del asistente
docs/architecture.md        Arquitectura y decisiones técnicas
tests/                      Pruebas automáticas y guion de la demo
```

Más detalle en [docs/architecture.md](docs/architecture.md).
