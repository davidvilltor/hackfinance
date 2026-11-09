# Arquitectura de SilverShield

## Vista general

```
 Navegador (persona mayor)                    Servidor FastAPI                         Servicios de IA
┌───────────────────────────┐   REST/JSON   ┌──────────────────────────────┐
│ index.html + app.js        │─────────────▶│ main.py (máquina de estados)  │
│  · formulario y resumen    │              │   │                           │
│  · pantalla de decisión    │              │   ├─ reglas_riesgo.py ────────┼─ determinista, < 1 ms
│  · conversación por voz    │              │   ├─ voice_stress.py          │
│ voz.js                     │              │   ├─ agente_silvershield.py ──┼──▶ Claude (JSON con esquema)
│  · Web Speech API (STT)    │  audio/mpeg  │   │     └─ evaluador local    │    (si falla → reglas locales)
│  · medidor de micrófono    │◀─────────────│   ├─ voice_agent.py ──────────┼──▶ ElevenLabs TTS (streaming)
│  · reproducción del TTS    │  audio/webm  │   │                         ──┼──▶ ElevenLabs Scribe (STT)
└───────────────────────────┘─────────────▶│   ├─ notifications.py         │
 Navegador (operador banco)                  │   └─ database.py (SQLite)    │
┌───────────────────────────┐   sondeo 3 s  │                              │
│ panel.html + panel.js      │◀────────────▶│                              │
└───────────────────────────┘               └──────────────────────────────┘
```

## Ciclo de vida de una transferencia

| Estado | Significado | Transiciones |
|---|---|---|
| `pendiente_decision` | Ha saltado una regla; el cliente elige cómo seguir | `autorizar` → completada (solo destinatario habitual sin riesgo alto) · `verificacion` → en_verificacion · `cancelar` |
| `en_verificacion` | Conversación con SilverShield | "seguro" → verificada_segura · "riesgo" → retenida · "no_verificada" (Claude falló) → retenida |
| `verificada_segura` | SilverShield recomienda seguir; falta la confirmación del cliente | `autorizar` → completada · `cancelar` |
| `retenida` | SilverShield la ha parado; aviso al operador y al contacto de emergencia | `liberar` (operador del banco) → completada · `cancelar` (operador) |
| `completada` / `cancelada` | Estados finales | — |

El servidor valida cada transición (responde HTTP 409 si no está permitida). El cargo es atómico: el saldo se descuenta y el estado cambia en la misma transacción. Así, una transferencia retenida **no se puede autorizar desde la app del cliente**. Por motivos legales, solo un **operador del banco** puede liberarla, después de hablar con el titular por un canal seguro. El contacto de emergencia recibe el aviso, pero no puede autorizar nada.

**Verificación obligatoria para cuentas nuevas.** "Conozco al destinatario" (enviar sin verificar) solo se ofrece si el cliente ya ha enviado dinero antes a esa cuenta y el riesgo no es alto (`permite_autorizacion_directa` en la evaluación de las reglas). En las estafas el dinero va siempre a una cuenta nueva, así que ahí la verificación es obligatoria y un estafador no puede saltársela diciendo "pulse ese botón". El servidor lo comprueba en `/autorizar` (HTTP 409).

## Decisiones de diseño

**Dos capas de detección.** Las reglas son instantáneas, gratuitas y explicables, y deciden *cuándo* preguntar. La IA solo interviene cuando la persona elige verificar, y decide *si* hay engaño a partir de lo que cuenta. Así el coste por verificación es bajo y las transferencias normales no tienen ninguna fricción.

**Claude con salida estructurada.** Cada turno envía a Claude el contexto de la transferencia, las alertas de las reglas, los indicadores de voz y la transcripción completa. La respuesta se obliga a cumplir un esquema JSON (`output_config.format`) con los campos `respuesta`, `decision` (preguntar, seguro o riesgo), `nivel_riesgo`, `categoria`, `senales` y `resumen_para_contacto`, y después se valida con Pydantic. El backend fuerza un veredicto al llegar al máximo de turnos, de modo que la conversación nunca se alarga indefinidamente.

**Robustez ante prompt injection.** El prompt indica que todo lo que hay dentro de `<conversacion>` son datos y no instrucciones, y que un intento de dar órdenes al asistente cuenta como señal de manipulación. La decisión final la aplica siempre el servidor, nunca el navegador.

**Fallar de forma segura.** Si Claude está configurado pero falla (sin conexión, tiempo agotado, respuesta inválida), un evaluador heurístico local toma el relevo en ese turno: puede seguir preguntando o detectar una estafa, pero **nunca da una transferencia por buena**. Si tocaba aprobarla, la decisión pasa a ser `no_verificada`: la transferencia queda retenida, la pantalla lo explica con calma y un operador del banco la revisa y la libera si procede. Un fallo técnico puede retrasar un pago legítimo, pero no dejar pasar una estafa.

**Modo local (sin claves).** Si no hay clave de Anthropic, el evaluador local es el motor completo y sí puede aprobar. Es el modo para desarrollar o hacer la demo sin internet, y el pie de la app lo indica ("evaluador local"). Si no hay ElevenLabs, el navegador usa su propia síntesis de voz. Si el navegador no puede reconocer la voz, se ofrece responder escribiendo.

**Explicar la decisión.** Cuando SilverShield para una transferencia, la pantalla muestra "¿Por qué la hemos parado?" con el tipo de engaño y las señales que ha visto, escritas por Claude en lenguaje sencillo. No se muestran en el caso de la palabra de auxilio, para no alertar a quien presiona.

**Latencia.**
- El saludo inicial se genera con una plantilla, sin esperar a la IA.
- Claude trabaja con esfuerzo `low`, lo adecuado para una conversación.
- El texto de la respuesta se muestra en cuanto llega, mientras el audio se pide aparte.
- La voz de ElevenLabs (nativa de España, Multilingual v2) se sirve en streaming y el navegador empieza a reproducir antes de recibir el audio completo. Los audios quedan en caché para el botón "Repetir".
- Medición: cada turno guarda cuánto tardó en total y cuánto tardó Claude (se ve en la transcripción del panel); el servidor registra cuánto tarda ElevenLabs en empezar a enviar audio (cabecera `Server-Timing: tts`), y el navegador escribe en la consola cuándo empieza a sonar. La evaluación (`evaluacion/`) da medias y percentil 95.

**Acceso de los operadores.** Como solo un operador del banco puede liberar o cancelar una transferencia retenida, el panel exige iniciar sesión ([acceso_operador.py](../backend/acceso_operador.py)). Los operadores se configuran en `.env` (`OPERADORES=usuario:contraseña,...`). Al entrar se emite una cookie firmada con HMAC-SHA256 (usuario y caducidad, 8 horas), `HttpOnly` (el JavaScript de la página no puede leerla) y `SameSite=Strict` (otra web no puede usarla para lanzar acciones en nombre del operador). Las contraseñas se comparan en tiempo constante y cada intento fallido tarda un segundo.

Rutas protegidas: `/panel`, `/api/panel`, el detalle `GET /api/transferencias/{id}` (contiene la transcripción), `/liberar`, `/cancelar` cuando la transferencia está retenida y `/api/demo/reiniciar`. La app del cliente no usa ninguna de ellas, salvo cancelar sus propias transferencias antes de que queden retenidas. Cada liberación o cancelación guarda el nombre del operador en la transferencia (columna `operador`; las bases de datos anteriores se migran solas al arrancar).

**Privacidad y seguridad.**
- El endpoint de voz solo sintetiza mensajes generados por el servidor, así que no puede usarse como proxy abierto de ElevenLabs.
- La palabra de auxilio y las transcripciones solo las ve un operador con sesión iniciada.
- La palabra de auxilio nunca se envía a la pantalla del cliente.
- Todo el texto del usuario se pinta con `textContent`, sin inyectar HTML.

**Palabra de auxilio.** La coacción familiar no siempre se detecta con preguntas, porque la persona que presiona puede estar delante escuchando. Una palabra secreta, configurada de antemano con el contacto de emergencia, permite pedir ayuda sin que el agresor lo note: la respuesta es neutra ("un operador del banco revisará la operación y le llamará", lo mismo que en cualquier otra retención) y el aviso al operador y al contacto se hace en silencio.

## Del prototipo a producción
- **Llamada telefónica saliente:** el mismo agente puede funcionar sobre telefonía SIP (por ejemplo Twilio y ElevenLabs Conversational AI) reutilizando `agente_silvershield.evaluar_turno`.
- **Avisos reales:** `notifications.py` es el punto de integración con la pasarela SMS, WhatsApp o push del banco.
- **Integración con el core bancario:** las reglas se alimentarían del historial real de beneficiarios y del scoring antifraude del banco. La lista de países de riesgo debe sincronizarse con la lista oficial vigente del GAFI.
