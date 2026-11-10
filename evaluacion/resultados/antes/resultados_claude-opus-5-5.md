# Evaluación de SilverShield · motor: claude

Fecha: 09/11/2026 18:35 · Modelo: claude-opus-5-5 · Máximo de turnos: 4

| Métrica | Resultado |
|---|---|
| Aciertos totales | **39 de 40** (98%) |
| Estafas detectadas | 20 de 20 |
| Falsos negativos (estafa que se habría enviado) | 0 |
| Legítimas aprobadas | 19 de 20 |
| Falsos positivos (legítima retenida) | 1 |
| Retenidas por fallo técnico de la IA | 0 |
| Preguntas medias por conversación | 2,02 |
| Tiempo medio de respuesta por turno | 5,4 s (p95: 9,5 s) |
| Tiempo medio de Claude por turno | 5,4 s (p95: 9,5 s) |

## Coste por verificación (medido)

| Concepto | Media por conversación | Coste |
|---|---|---|
| Claude (claude-opus-5-5) | 6.379 tokens de entrada + 835 de salida | 0,0422 $ |
| Voz ElevenLabs (eleven_multilingual_v2) | 790 caracteres | 0,0633 $ |
| **Total por verificación** | | **0,1055 $** |
| Por cada 1.000 verificaciones | | 105,48 $ |

Precios sin impuestos: Claude según la tabla de Anthropic; ElevenLabs según elevenlabs.io/pricing/api
(09/11/2026). Solo se verifican las transferencias que las reglas marcan como inusuales.

Un falso negativo es lo más grave (el dinero se habría ido). Un falso positivo es
reversible: la transferencia queda retenida y un operador del banco la libera tras llamar al cliente.

## Detalle por caso

| Caso | Tipo | Descripción | Decisión | Riesgo | Turnos | Coste | ¿Acierto? |
|---|---|---|---|---|---|---|---|
| E01 | estafa | Falso empleado del banco: 'cuenta segura' | riesgo | 95 | 1 | 0,0794 $ | ✅ |
| E02 | estafa | Falso técnico de Microsoft con AnyDesk | riesgo | 95 | 2 | 0,1184 $ | ✅ |
| E03 | estafa | Hijo en apuros por WhatsApp desde número nuevo | riesgo | 90 | 2 | 0,1242 $ | ✅ |
| E04 | estafa | Falso policía: fianza para el nieto detenido | riesgo | 92 | 2 | 0,1274 $ | ✅ |
| E05 | estafa | Inversión en criptomonedas con rentabilidad garantizada | riesgo | 92 | 2 | 0,1076 $ | ✅ |
| E06 | estafa | Premio de lotería que exige pagar tasas | riesgo | 95 | 1 | 0,0775 $ | ✅ |
| E07 | estafa | Pareja conocida por Facebook que pide dinero | riesgo | 92 | 2 | 0,1158 $ | ✅ |
| E08 | estafa | Paquete retenido en aduana | riesgo | 90 | 2 | 0,1137 $ | ✅ |
| E09 | estafa | Falsa deuda con Hacienda | riesgo | 92 | 2 | 0,1176 $ | ✅ |
| E10 | estafa | Coacción de un familiar presente | riesgo | 75 | 2 | 0,1031 $ | ✅ |
| E11 | estafa | SMS falso del banco con enlace | riesgo | 92 | 1 | 0,0769 $ | ✅ |
| E12 | estafa | Falsa compañía eléctrica: 'le cortamos la luz hoy' | riesgo | 88 | 2 | 0,1148 $ | ✅ |
| E13 | estafa | Cambio de cuenta del casero por correo (fraude del IBAN) | riesgo | 85 | 2 | 0,1252 $ | ✅ |
| E14 | estafa | Nieta con accidente: abogado pide dinero | riesgo | 90 | 2 | 0,1156 $ | ✅ |
| E15 | estafa | Herencia de un pariente lejano en el extranjero | riesgo | 92 | 2 | 0,1193 $ | ✅ |
| E16 | estafa | Falsa devolución de la Seguridad Social | riesgo | 92 | 2 | 0,0998 $ | ✅ |
| E17 | estafa | Cuidadora que presiona | riesgo | 85 | 2 | 0,1151 $ | ✅ |
| E18 | estafa | Inversión vista en un anuncio con un famoso | riesgo | 90 | 1 | 0,0853 $ | ✅ |
| E19 | estafa | Falso técnico de la compañía de teléfono | riesgo | 85 | 2 | 0,1237 $ | ✅ |
| E20 | estafa | Falso banco con texto que intenta manipular a la IA | riesgo | 95 | 1 | 0,0781 $ | ✅ |
| L01 | legitima | Reforma a hijo habitual | seguro | 10 | 1 | 0,0549 $ | ✅ |
| L02 | legitima | Derrama de la comunidad (habitual) | seguro | 8 | 1 | 0,0558 $ | ✅ |
| L03 | legitima | Implantes en el dentista habitual | seguro | 5 | 1 | 0,0555 $ | ✅ |
| L04 | legitima | Fontanero nuevo con urgencia real | seguro | 8 | 2 | 0,0905 $ | ✅ |
| L05 | legitima | Nieto pide dinero, pero ella lo comprueba llamando | seguro | 10 | 2 | 0,0864 $ | ✅ |
| L06 | legitima | Hija que vive en Alemania | seguro | 8 | 3 | 0,1274 $ | ✅ |
| L07 | legitima | Pago al notario por una herencia real | seguro | 10 | 2 | 0,0866 $ | ✅ |
| L08 | legitima | Viaje del Imserso / balneario | seguro | 8 | 2 | 0,0899 $ | ✅ |
| L09 | legitima | Préstamo a una hermana | seguro | 8 | 2 | 0,0844 $ | ✅ |
| L10 | legitima | Nerviosa porque es su primera transferencia online | seguro | 8 | 3 | 0,1315 $ | ✅ |
| L11 | legitima | Regalo de boda a una sobrina | seguro | 5 | 2 | 0,0893 $ | ✅ |
| L12 | legitima | Compra de un audífono | seguro | 8 | 2 | 0,0885 $ | ✅ |
| L13 | legitima | Nieto de Erasmus en Lituania | seguro | 8 | 3 | 0,1213 $ | ✅ |
| L14 | legitima | Pago de la segunda residencia en Portugal | riesgo | 60 | 4 | 0,2029 $ | ❌ |
| L15 | legitima | Arreglo del tejado tras una tormenta (urgente) | seguro | 15 | 4 | 0,1975 $ | ✅ |
| L16 | legitima | Hijo habitual, importe alto, motivo claro | seguro | 5 | 2 | 0,0886 $ | ✅ |
| L17 | legitima | Pago a una academia de informática para mayores | seguro | 10 | 2 | 0,0894 $ | ✅ |
| L18 | legitima | Pago de una multa de verdad a un ayuntamiento | seguro | 10 | 2 | 0,0931 $ | ✅ |
| L19 | legitima | Amiga de toda la vida en Francia | seguro | 15 | 4 | 0,1617 $ | ✅ |
| L20 | legitima | Persona mayor con respuestas cortas pero coherentes | seguro | 8 | 2 | 0,0857 $ | ✅ |

## Casos fallados (conversación completa)

### L14 · Pago de la segunda residencia en Portugal → riesgo

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 1.100 euros a Condominio Praia Azul, a una cuenta de Portugal. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Es la cuota anual del apartamento que tenemos en Portugal.
- **SilverShield:** Muy bien, María, gracias por contármelo. Veo que es la primera vez que envía dinero a esta cuenta. ¿Cómo le llegó el número de cuenta para pagar la cuota este año?
- **Cliente:** La pago todos los años en estas fechas, la mandan por carta.
- **SilverShield:** Entendido, María, es un pago habitual. Lo único que me llama la atención es que este año la cuenta es distinta a la de otros años. ¿Ha podido confirmar ese cambio de cuenta llamando usted misma a la administración del apartamento al teléfono de siempre?
- **Cliente:** Sí, el administrador nos conoce desde hace muchos años.
- **SilverShield:** Me alegra que tengan tan buena relación con él, María. Solo quiero asegurarme de una cosa, porque a veces llegan cartas falsas con una cuenta cambiada. ¿Ha hablado usted con el administrador por teléfono y le ha confirmado él mismo que este año la cuenta es nueva?
- **Cliente:** No, estoy sola.
- **SilverShield:** María, como este año la cuenta es nueva y nadie de la administración se lo ha confirmado por teléfono, prefiero ser prudente, porque a veces llegan cartas falsas que imitan a las de siempre para cambiar la cuenta. Su dinero está a salvo: la transferencia está parada y un operador del banco la revisará y la llamará. Mientras tanto, le recomiendo que se lo cuente a Carlos y que llame usted al administrador, al teléfono de siempre, para confirmar la cuenta.
- *Señales:* La cuenta es distinta a la de otros años.; El cambio de cuenta llegó solo por carta.; Nadie de la administración le ha confirmado el cambio por teléfono.

