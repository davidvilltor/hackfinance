# Evaluación de SilverShield · motor: claude

Fecha: 09/11/2026 17:54 · Modelo: claude-opus-5-5 · Máximo de turnos: 4

| Métrica | Resultado |
|---|---|
| Aciertos totales | **39 de 40** (98%) |
| Estafas detectadas | 20 de 20 |
| Falsos negativos (estafa que se habría enviado) | 0 |
| Legítimas aprobadas | 19 de 20 |
| Falsos positivos (legítima retenida) | 1 |
| Retenidas por fallo técnico de la IA | 0 |
| Preguntas medias por conversación | 2,12 |
| Tiempo medio de respuesta por turno | 3,7 s (p95: 6,2 s) |
| Tiempo medio de Claude por turno | 3,7 s (p95: 6,2 s) |

Un falso negativo es lo más grave (el dinero se habría ido). Un falso positivo es
reversible: la transferencia queda retenida y un operador del banco la libera tras llamar al cliente.

## Detalle por caso

| Caso | Tipo | Descripción | Decisión | Riesgo | Turnos | ¿Acierto? |
|---|---|---|---|---|---|---|
| E01 | estafa | Falso empleado del banco: 'cuenta segura' | riesgo | 95 | 1 | ✅ |
| E02 | estafa | Falso técnico de Microsoft con AnyDesk | riesgo | 95 | 2 | ✅ |
| E03 | estafa | Hijo en apuros por WhatsApp desde número nuevo | riesgo | 90 | 2 | ✅ |
| E04 | estafa | Falso policía: fianza para el nieto detenido | riesgo | 90 | 2 | ✅ |
| E05 | estafa | Inversión en criptomonedas con rentabilidad garantizada | riesgo | 92 | 2 | ✅ |
| E06 | estafa | Premio de lotería que exige pagar tasas | riesgo | 95 | 1 | ✅ |
| E07 | estafa | Pareja conocida por Facebook que pide dinero | riesgo | 92 | 3 | ✅ |
| E08 | estafa | Paquete retenido en aduana | riesgo | 88 | 2 | ✅ |
| E09 | estafa | Falsa deuda con Hacienda | riesgo | 92 | 2 | ✅ |
| E10 | estafa | Coacción de un familiar presente | riesgo | 75 | 2 | ✅ |
| E11 | estafa | SMS falso del banco con enlace | riesgo | 92 | 1 | ✅ |
| E12 | estafa | Falsa compañía eléctrica: 'le cortamos la luz hoy' | riesgo | 88 | 2 | ✅ |
| E13 | estafa | Cambio de cuenta del casero por correo (fraude del IBAN) | riesgo | 80 | 2 | ✅ |
| E14 | estafa | Nieta con accidente: abogado pide dinero | riesgo | 90 | 2 | ✅ |
| E15 | estafa | Herencia de un pariente lejano en el extranjero | riesgo | 92 | 2 | ✅ |
| E16 | estafa | Falsa devolución de la Seguridad Social | riesgo | 90 | 2 | ✅ |
| E17 | estafa | Cuidadora que presiona | riesgo | 80 | 2 | ✅ |
| E18 | estafa | Inversión vista en un anuncio con un famoso | riesgo | 90 | 1 | ✅ |
| E19 | estafa | Falso técnico de la compañía de teléfono | riesgo | 85 | 2 | ✅ |
| E20 | estafa | Falso banco con texto que intenta manipular a la IA | riesgo | 95 | 1 | ✅ |
| L01 | legitima | Reforma a hijo habitual | seguro | 5 | 2 | ✅ |
| L02 | legitima | Derrama de la comunidad (habitual) | seguro | 5 | 2 | ✅ |
| L03 | legitima | Implantes en el dentista habitual | seguro | 5 | 2 | ✅ |
| L04 | legitima | Fontanero nuevo con urgencia real | seguro | 8 | 2 | ✅ |
| L05 | legitima | Nieto pide dinero, pero ella lo comprueba llamando | seguro | 10 | 2 | ✅ |
| L06 | legitima | Hija que vive en Alemania | seguro | 8 | 3 | ✅ |
| L07 | legitima | Pago al notario por una herencia real | seguro | 8 | 2 | ✅ |
| L08 | legitima | Viaje del Imserso / balneario | seguro | 5 | 2 | ✅ |
| L09 | legitima | Préstamo a una hermana | seguro | 8 | 2 | ✅ |
| L10 | legitima | Nerviosa porque es su primera transferencia online | seguro | 8 | 3 | ✅ |
| L11 | legitima | Regalo de boda a una sobrina | seguro | 8 | 2 | ✅ |
| L12 | legitima | Compra de un audífono | seguro | 5 | 2 | ✅ |
| L13 | legitima | Nieto de Erasmus en Lituania | seguro | 8 | 3 | ✅ |
| L14 | legitima | Pago de la segunda residencia en Portugal | riesgo | 45 | 4 | ❌ |
| L15 | legitima | Arreglo del tejado tras una tormenta (urgente) | seguro | 10 | 2 | ✅ |
| L16 | legitima | Hijo habitual, importe alto, motivo claro | seguro | 5 | 2 | ✅ |
| L17 | legitima | Pago a una academia de informática para mayores | seguro | 12 | 4 | ✅ |
| L18 | legitima | Pago de una multa de verdad a un ayuntamiento | seguro | 8 | 2 | ✅ |
| L19 | legitima | Amiga de toda la vida en Francia | seguro | 20 | 4 | ✅ |
| L20 | legitima | Persona mayor con respuestas cortas pero coherentes | seguro | 10 | 2 | ✅ |

## Casos fallados (conversación completa)

### L14 · Pago de la segunda residencia en Portugal → riesgo

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 1.100 euros a Condominio Praia Azul, a una cuenta de Portugal. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Es la cuota anual del apartamento que tenemos en Portugal.
- **SilverShield:** Muy bien, María, gracias por explicármelo. ¿Cómo le ha llegado esta vez la petición de pago, con la carta o el aviso de todos los años, o le han escrito o llamado para pedirle el pago a una cuenta nueva?
- **Cliente:** La pago todos los años en estas fechas, la mandan por carta.
- **SilverShield:** Perfecto, María, gracias. Veo que es la primera vez que envía dinero a esta cuenta desde aquí. ¿Es la misma cuenta a la que pagó otros años, o en la carta de este año le han indicado una cuenta distinta?
- **Cliente:** Sí, el administrador nos conoce desde hace muchos años.
- **SilverShield:** Entiendo, María, es estupendo tener un administrador de confianza. Solo una cosa más, porque a veces los estafadores envían cartas o correos falsos cambiando el número de cuenta. ¿El número de cuenta de este año es el mismo de otros años, o es nuevo?
- **Cliente:** No, estoy sola.
- **SilverShield:** María, todo lo que me cuenta tiene sentido, pero no he podido confirmar si el número de cuenta es el de siempre, y a veces los estafadores mandan cartas falsas cambiando solo ese número. Su dinero está a salvo porque la transferencia está parada, y un operador del banco la revisará y la llamará; mientras tanto, puede llamar usted al administrador a su número de siempre para confirmar la cuenta. Le recomiendo también que se lo comente a Carlos.
- *Señales:* Es la primera vez que envía dinero a esta cuenta.; No hemos podido confirmar que la cuenta sea la de otros años.

