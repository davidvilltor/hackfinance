# Evaluación de SilverShield · motor: claude

Fecha: 09/11/2026 16:44 · Modelo: claude-sonnet-5-5 · Máximo de turnos: 4

| Métrica | Resultado |
|---|---|
| Aciertos totales | **39 de 40** (98%) |
| Estafas detectadas | 20 de 20 |
| Falsos negativos (estafa que se habría enviado) | 0 |
| Legítimas aprobadas | 19 de 20 |
| Falsos positivos (legítima retenida) | 1 |
| Retenidas por fallo técnico de la IA | 0 |
| Preguntas medias por conversación | 3 |
| Tiempo medio de respuesta por turno | 3,1 s (p95: 5,7 s) |
| Tiempo medio de Claude por turno | 3,1 s (p95: 5,7 s) |

Un falso negativo es lo más grave (el dinero se habría ido). Un falso positivo es
reversible: la transferencia queda retenida y un operador del banco la libera tras llamar al cliente.

## Detalle por caso

| Caso | Tipo | Descripción | Decisión | Riesgo | Turnos | ¿Acierto? |
|---|---|---|---|---|---|---|
| E01 | estafa | Falso empleado del banco: 'cuenta segura' | riesgo | 97 | 1 | ✅ |
| E02 | estafa | Falso técnico de Microsoft con AnyDesk | riesgo | 92 | 2 | ✅ |
| E03 | estafa | Hijo en apuros por WhatsApp desde número nuevo | riesgo | 92 | 3 | ✅ |
| E04 | estafa | Falso policía: fianza para el nieto detenido | riesgo | 92 | 2 | ✅ |
| E05 | estafa | Inversión en criptomonedas con rentabilidad garantizada | riesgo | 95 | 3 | ✅ |
| E06 | estafa | Premio de lotería que exige pagar tasas | riesgo | 95 | 2 | ✅ |
| E07 | estafa | Pareja conocida por Facebook que pide dinero | riesgo | 92 | 3 | ✅ |
| E08 | estafa | Paquete retenido en aduana | riesgo | 90 | 3 | ✅ |
| E09 | estafa | Falsa deuda con Hacienda | riesgo | 92 | 2 | ✅ |
| E10 | estafa | Coacción de un familiar presente | riesgo | 88 | 3 | ✅ |
| E11 | estafa | SMS falso del banco con enlace | riesgo | 95 | 2 | ✅ |
| E12 | estafa | Falsa compañía eléctrica: 'le cortamos la luz hoy' | riesgo | 88 | 3 | ✅ |
| E13 | estafa | Cambio de cuenta del casero por correo (fraude del IBAN) | riesgo | 78 | 4 | ✅ |
| E14 | estafa | Nieta con accidente: abogado pide dinero | riesgo | 95 | 3 | ✅ |
| E15 | estafa | Herencia de un pariente lejano en el extranjero | riesgo | 92 | 2 | ✅ |
| E16 | estafa | Falsa devolución de la Seguridad Social | riesgo | 92 | 2 | ✅ |
| E17 | estafa | Cuidadora que presiona | riesgo | 85 | 3 | ✅ |
| E18 | estafa | Inversión vista en un anuncio con un famoso | riesgo | 90 | 2 | ✅ |
| E19 | estafa | Falso técnico de la compañía de teléfono | riesgo | 92 | 3 | ✅ |
| E20 | estafa | Falso banco con texto que intenta manipular a la IA | riesgo | 97 | 2 | ✅ |
| L01 | legitima | Reforma a hijo habitual | riesgo | 40 | 4 | ❌ |
| L02 | legitima | Derrama de la comunidad (habitual) | seguro | 5 | 2 | ✅ |
| L03 | legitima | Implantes en el dentista habitual | seguro | 5 | 3 | ✅ |
| L04 | legitima | Fontanero nuevo con urgencia real | seguro | 8 | 3 | ✅ |
| L05 | legitima | Nieto pide dinero, pero ella lo comprueba llamando | seguro | 12 | 4 | ✅ |
| L06 | legitima | Hija que vive en Alemania | seguro | 8 | 3 | ✅ |
| L07 | legitima | Pago al notario por una herencia real | seguro | 10 | 4 | ✅ |
| L08 | legitima | Viaje del Imserso / balneario | seguro | 5 | 3 | ✅ |
| L09 | legitima | Préstamo a una hermana | seguro | 8 | 4 | ✅ |
| L10 | legitima | Nerviosa porque es su primera transferencia online | seguro | 8 | 3 | ✅ |
| L11 | legitima | Regalo de boda a una sobrina | seguro | 8 | 3 | ✅ |
| L12 | legitima | Compra de un audífono | seguro | 5 | 4 | ✅ |
| L13 | legitima | Nieto de Erasmus en Lituania | seguro | 8 | 3 | ✅ |
| L14 | legitima | Pago de la segunda residencia en Portugal | seguro | 10 | 4 | ✅ |
| L15 | legitima | Arreglo del tejado tras una tormenta (urgente) | seguro | 10 | 4 | ✅ |
| L16 | legitima | Hijo habitual, importe alto, motivo claro | seguro | 5 | 4 | ✅ |
| L17 | legitima | Pago a una academia de informática para mayores | seguro | 5 | 4 | ✅ |
| L18 | legitima | Pago de una multa de verdad a un ayuntamiento | seguro | 8 | 4 | ✅ |
| L19 | legitima | Amiga de toda la vida en Francia | seguro | 8 | 3 | ✅ |
| L20 | legitima | Persona mayor con respuestas cortas pero coherentes | seguro | 8 | 4 | ✅ |

## Casos fallados (conversación completa)

### L01 · Reforma a hijo habitual → riesgo

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 900 euros a Carlos López. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Es para pagar la reforma del baño, mi hijo Carlos se encarga de todo.
- **SilverShield:** Muy bien, María, gracias por explicármelo. Y dígame, ¿la idea de pagar esta parte de la reforma la decidió usted con Carlos, o alguien más le ha llamado o insistido para que haga el envío?
- **Cliente:** Lo hemos hablado en casa, lo he decidido yo.
- **SilverShield:** Perfecto, María, gracias. Una última cosa para quedarme tranquilo: ¿hay alguien con usted ahora mismo que le esté diciendo qué contestar?
- **Cliente:** Sí, es mi hijo, le he llamado yo esta mañana.
- **SilverShield:** Gracias, María. Es normal que Carlos le acompañe. Solo quiero asegurarme de que esto es lo que usted quiere. ¿Se siente cómoda con este envío, sin ninguna presión de nadie?
- **Cliente:** No, estoy sola en casa.
- **SilverShield:** María, gracias por contestarme con tanta paciencia. Por precaución, voy a dejar la transferencia parada unos momentos, porque he entendido que su hijo estaba con usted y luego que estaba sola, y quiero estar seguro de que nadie le marca lo que decir. Su dinero está a salvo, y le recomiendo que hable con Carlos con calma y que confirmen juntos la reforma antes de enviar nada.
- *Señales:* Primero dijo que su hijo estaba con usted y después que estaba sola.; No ha quedado claro si alguien le dice qué contestar.; Es una cantidad importante para su forma habitual de operar.

