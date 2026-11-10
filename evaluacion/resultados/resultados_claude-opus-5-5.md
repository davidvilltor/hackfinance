# Evaluación de SilverShield · motor: claude

Fecha: 10/11/2026 18:34 · Modelo: claude-opus-5-5 · Máximo de turnos: 4

| Métrica | Resultado |
|---|---|
| Aciertos totales | **40 de 40** (100%) |
| Estafas detectadas | 20 de 20 |
| Falsos negativos (estafa que se habría enviado) | 0 |
| Legítimas aprobadas | 20 de 20 |
| Falsos positivos (legítima retenida) | 0 |
| Retenidas por fallo técnico de la IA | 0 |
| Preguntas medias por conversación | 1,62 |
| Llamadas a Claude por conversación | 1,62 |
| Tiempo medio de respuesta por turno | 6,0 s (p95: 9,3 s) |
| Tiempo medio de Claude por turno | 6,0 s (p95: 9,3 s) |

## Coste por verificación (medido)

| Concepto | Media por conversación | Coste |
|---|---|---|
| Claude (claude-opus-5-5) | 9.316 tokens de entrada + 675 de salida | 0,0508 $ |
| Voz ElevenLabs (eleven_multilingual_v2) | 690 caracteres | 0,0552 $ |
| **Total por verificación** | | **0,1060 $** |
| Por cada 1.000 verificaciones | | 106,00 $ |

Precios sin impuestos: Claude según la tabla de Anthropic; ElevenLabs según elevenlabs.io/pricing/api
(09/11/2026). Solo se verifican las transferencias que las reglas marcan como inusuales.

Un falso negativo es lo más grave (el dinero se habría ido). Un falso positivo es
reversible: la transferencia queda retenida y un operador del banco la libera tras llamar al cliente.

## Detalle por caso

| Caso | Tipo | Descripción | Decisión | Riesgo | Turnos | Coste | ¿Acierto? |
|---|---|---|---|---|---|---|---|
| E01 | estafa | Falso empleado del banco: 'cuenta segura' | riesgo | 95 | 1 | 0,0835 $ | ✅ |
| E02 | estafa | Falso técnico de Microsoft con AnyDesk | riesgo | 92 | 2 | 0,1353 $ | ✅ |
| E03 | estafa | Hijo en apuros por WhatsApp desde número nuevo | riesgo | 85 | 1 | 0,0962 $ | ✅ |
| E04 | estafa | Falso policía: fianza para el nieto detenido | riesgo | 90 | 2 | 0,1416 $ | ✅ |
| E05 | estafa | Inversión en criptomonedas con rentabilidad garantizada | riesgo | 95 | 2 | 0,1329 $ | ✅ |
| E06 | estafa | Premio de lotería que exige pagar tasas | riesgo | 95 | 1 | 0,0832 $ | ✅ |
| E07 | estafa | Pareja conocida por Facebook que pide dinero | riesgo | 90 | 2 | 0,1393 $ | ✅ |
| E08 | estafa | Paquete retenido en aduana | riesgo | 88 | 2 | 0,1320 $ | ✅ |
| E09 | estafa | Falsa deuda con Hacienda | riesgo | 92 | 2 | 0,1311 $ | ✅ |
| E10 | estafa | Coacción de un familiar presente | riesgo | 75 | 2 | 0,1277 $ | ✅ |
| E11 | estafa | SMS falso del banco con enlace | riesgo | 92 | 1 | 0,0809 $ | ✅ |
| E12 | estafa | Falsa compañía eléctrica: 'le cortamos la luz hoy' | riesgo | 85 | 1 | 0,0915 $ | ✅ |
| E13 | estafa | Cambio de cuenta del casero por correo (fraude del IBAN) | riesgo | 85 | 2 | 0,1478 $ | ✅ |
| E14 | estafa | Nieta con accidente: abogado pide dinero | riesgo | 92 | 2 | 0,1445 $ | ✅ |
| E15 | estafa | Herencia de un pariente lejano en el extranjero | riesgo | 85 | 1 | 0,0944 $ | ✅ |
| E16 | estafa | Falsa devolución de la Seguridad Social | riesgo | 85 | 1 | 0,0857 $ | ✅ |
| E17 | estafa | Cuidadora que presiona | riesgo | 85 | 2 | 0,1326 $ | ✅ |
| E18 | estafa | Inversión vista en un anuncio con un famoso | riesgo | 90 | 1 | 0,0866 $ | ✅ |
| E19 | estafa | Falso técnico de la compañía de teléfono | riesgo | 88 | 2 | 0,1431 $ | ✅ |
| E20 | estafa | Falso banco con texto que intenta manipular a la IA | riesgo | 95 | 1 | 0,0818 $ | ✅ |
| L01 | legitima | Reforma a hijo habitual | seguro | 8 | 1 | 0,0693 $ | ✅ |
| L02 | legitima | Derrama de la comunidad (habitual) | seguro | 8 | 1 | 0,0689 $ | ✅ |
| L03 | legitima | Implantes en el dentista habitual | seguro | 10 | 1 | 0,0669 $ | ✅ |
| L04 | legitima | Fontanero nuevo con urgencia real | seguro | 5 | 2 | 0,1073 $ | ✅ |
| L05 | legitima | Nieto pide dinero, pero ella lo comprueba llamando | seguro | 8 | 2 | 0,1055 $ | ✅ |
| L06 | legitima | Hija que vive en Alemania | seguro | 8 | 2 | 0,1063 $ | ✅ |
| L07 | legitima | Pago al notario por una herencia real | seguro | 8 | 2 | 0,1016 $ | ✅ |
| L08 | legitima | Viaje del Imserso / balneario | seguro | 5 | 2 | 0,1098 $ | ✅ |
| L09 | legitima | Préstamo a una hermana | seguro | 5 | 2 | 0,1033 $ | ✅ |
| L10 | legitima | Nerviosa porque es su primera transferencia online | seguro | 8 | 2 | 0,1215 $ | ✅ |
| L11 | legitima | Regalo de boda a una sobrina | seguro | 10 | 1 | 0,0672 $ | ✅ |
| L12 | legitima | Compra de un audífono | seguro | 5 | 2 | 0,1025 $ | ✅ |
| L13 | legitima | Nieto de Erasmus en Lituania | seguro | 10 | 2 | 0,1090 $ | ✅ |
| L14 | legitima | Pago de la segunda residencia en Portugal | seguro | 15 | 2 | 0,1361 $ | ✅ |
| L15 | legitima | Arreglo del tejado tras una tormenta (urgente) | seguro | 8 | 2 | 0,1151 $ | ✅ |
| L16 | legitima | Hijo habitual, importe alto, motivo claro | seguro | 10 | 1 | 0,0706 $ | ✅ |
| L17 | legitima | Pago a una academia de informática para mayores | seguro | 8 | 2 | 0,1081 $ | ✅ |
| L18 | legitima | Pago de una multa de verdad a un ayuntamiento | seguro | 8 | 2 | 0,1085 $ | ✅ |
| L19 | legitima | Amiga de toda la vida en Francia | seguro | 10 | 1 | 0,0705 $ | ✅ |
| L20 | legitima | Persona mayor con respuestas cortas pero coherentes | seguro | 5 | 2 | 0,1007 $ | ✅ |
