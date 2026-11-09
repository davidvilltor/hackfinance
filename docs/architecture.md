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
 Navegador (familiar/gestor)                 │   └─ database.py (SQLite)    │
┌───────────────────────────┐   sondeo 3 s  │                              │
│ panel.html + panel.js      │◀────────────▶│                              │
└───────────────────────────┘               └──────────────────────────────┘
```

## Ciclo de vida de una transferencia

| Estado | Significado | Transiciones |
|---|---|---|
| `pendiente_decision` | Ha saltado una regla; el cliente elige cómo seguir | `autorizar` → completada · `verificacion` → en_verificacion · `cancelar` |
| `en_verificacion` | Conversación con SilverShield | "seguro" → verificada_segura · "riesgo" → retenida |
| `verificada_segura` | SilverShield recomienda seguir; falta la confirmación del cliente | `autorizar` → completada · `cancelar` |
| `retenida` | SilverShield la ha parado y se ha avisado al contacto de confianza | `liberar` (contacto) → completada · `cancelar` |
| `completada` / `cancelada` | Estados finales | — |

El servidor valida cada transición (responde HTTP 409 si no está permitida). El cargo es atómico: el saldo se descuenta y el estado cambia en la misma transacción. Así, una transferencia retenida **no se puede autorizar desde la app del cliente**: solo el contacto de confianza puede liberarla.

## Decisiones de diseño

**Dos capas de detección.** Las reglas son instantáneas, gratuitas y explicables, y deciden *cuándo* preguntar. La IA solo interviene cuando la persona elige verificar, y decide *si* hay engaño a partir de lo que cuenta. Así el coste por verificación es bajo y las transferencias normales no tienen ninguna fricción.

**Claude con salida estructurada.** Cada turno envía a Claude el contexto de la transferencia, las alertas de las reglas, los indicadores de voz y la transcripción completa. La respuesta se obliga a cumplir un esquema JSON (`output_config.format`) con los campos `respuesta`, `decision` (preguntar, seguro o riesgo), `nivel_riesgo`, `categoria`, `senales` y `resumen_para_contacto`, y después se valida con Pydantic. El backend fuerza un veredicto al llegar al máximo de turnos, de modo que la conversación nunca se alarga indefinidamente.

**Robustez ante prompt injection.** El prompt indica que todo lo que hay dentro de `<conversacion>` son datos y no instrucciones, y que un intento de dar órdenes al asistente cuenta como señal de manipulación. La decisión final la aplica siempre el servidor, nunca el navegador.

**Degradación elegante.** Si no hay clave de Anthropic, o si Claude falla o tarda más de lo previsto, un evaluador heurístico local con la misma interfaz mantiene el servicio. Si no hay ElevenLabs, el navegador usa su propia síntesis de voz. Si el navegador no puede reconocer la voz, se ofrece responder escribiendo.

**Latencia.**
- El saludo inicial se genera con una plantilla, sin esperar a la IA.
- Claude trabaja con esfuerzo `low`, lo adecuado para una conversación.
- El texto de la respuesta se muestra en cuanto llega, mientras el audio se pide aparte.
- ElevenLabs Flash v2.5 se sirve en streaming y el navegador empieza a reproducir antes de recibir el audio completo. Los audios quedan en caché para el botón "Repetir".

**Privacidad y seguridad.**
- El endpoint de voz solo sintetiza mensajes generados por el servidor, así que no puede usarse como proxy abierto de ElevenLabs.
- La palabra de auxilio nunca se envía a la pantalla del cliente.
- Todo el texto del usuario se pinta con `textContent`, sin inyectar HTML.

**Palabra de auxilio.** La coacción familiar no siempre se detecta con preguntas, porque la persona que presiona puede estar delante escuchando. Una palabra secreta, configurada de antemano con el contacto de confianza, permite pedir ayuda sin que el agresor lo note: la respuesta es neutra y la retención y el aviso se hacen en silencio.

## Del prototipo a producción
- **Llamada telefónica saliente:** el mismo agente puede funcionar sobre telefonía SIP (por ejemplo Twilio y ElevenLabs Conversational AI) reutilizando `agente_silvershield.evaluar_turno`.
- **Avisos reales:** `notifications.py` es el punto de integración con la pasarela SMS, WhatsApp o push del banco.
- **Integración con el core bancario:** las reglas se alimentarían del historial real de beneficiarios y del scoring antifraude del banco. La lista de países de riesgo debe sincronizarse con la lista oficial vigente del GAFI.
