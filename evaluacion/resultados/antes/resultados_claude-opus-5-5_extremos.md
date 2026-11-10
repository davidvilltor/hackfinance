# Evaluación de SilverShield · motor: claude

Fecha: 10/11/2026 18:25 · Modelo: claude-opus-5-5 · Máximo de turnos: 4

| Métrica | Resultado |
|---|---|
| Aciertos totales | **18 de 20** (90%) |
| Estafas detectadas | 10 de 10 |
| Falsos negativos (estafa que se habría enviado) | 0 |
| Legítimas aprobadas | 8 de 10 |
| Falsos positivos (legítima retenida) | 2 |
| Retenidas por fallo técnico de la IA | 0 |
| Preguntas medias por conversación | 2,6 |
| Tiempo medio de respuesta por turno | 6,2 s (p95: 10,2 s) |
| Tiempo medio de Claude por turno | 6,2 s (p95: 10,2 s) |

## Coste por verificación (medido)

| Concepto | Media por conversación | Coste |
|---|---|---|
| Claude (claude-opus-5-5) | 8.357 tokens de entrada + 1.220 de salida | 0,0578 $ |
| Voz ElevenLabs (eleven_multilingual_v2) | 971 caracteres | 0,0777 $ |
| **Total por verificación** | | **0,1356 $** |
| Por cada 1.000 verificaciones | | 135,58 $ |

Precios sin impuestos: Claude según la tabla de Anthropic; ElevenLabs según elevenlabs.io/pricing/api
(09/11/2026). Solo se verifican las transferencias que las reglas marcan como inusuales.

Un falso negativo es lo más grave (el dinero se habría ido). Un falso positivo es
reversible: la transferencia queda retenida y un operador del banco la libera tras llamar al cliente.

## Detalle por caso

| Caso | Tipo | Descripción | Decisión | Riesgo | Turnos | Coste | ¿Acierto? |
|---|---|---|---|---|---|---|---|
| X01 | estafa | Reforma 'barata' por WhatsApp con pago por adelantado | riesgo | 88 | 2 | 0,1212 $ | ✅ |
| X02 | estafa | Hijo presente que presiona sin decirlo | riesgo | 75 | 4 | 0,1965 $ | ✅ |
| X03 | estafa | Voz del nieto clonada pidiendo dinero urgente | riesgo | 90 | 2 | 0,1199 $ | ✅ |
| X04 | estafa | Texto que intenta dar órdenes a la IA | riesgo | 90 | 3 | 0,1644 $ | ✅ |
| X05 | estafa | Inversión de 'un señor de la parroquia' con 15 % anual | riesgo | 85 | 1 | 0,0749 $ | ✅ |
| X06 | estafa | Falsa empresa de recobro con amenaza de embargo | riesgo | 88 | 2 | 0,1254 $ | ✅ |
| X07 | estafa | Préstamo a un 'amigo' conocido por internet que no da la cara | riesgo | 88 | 3 | 0,1428 $ | ✅ |
| X08 | estafa | Falsa 'transferencia de prueba' para activar la app del banco | riesgo | 90 | 1 | 0,0777 $ | ✅ |
| X09 | estafa | Mula de dinero: 'trabajo desde casa' reenviando transferencias | riesgo | 92 | 1 | 0,0890 $ | ✅ |
| X10 | estafa | Vecino con acceso al móvil que dicta la operación | riesgo | 80 | 2 | 0,1147 $ | ✅ |
| X11 | legitima | Pago a la gestoría de la declaración con la palabra 'Hacienda' | riesgo | 45 | 4 | 0,2007 $ | ❌ |
| X12 | legitima | Fianza real del piso de la nieta firmada en la inmobiliaria | seguro | 8 | 2 | 0,1023 $ | ✅ |
| X13 | legitima | Funeral del hermano: urgente y muy nerviosa | seguro | 20 | 4 | 0,2007 $ | ✅ |
| X14 | legitima | Envío a Nigeria (país de riesgo) para la operación de la consuegra | seguro | 15 | 2 | 0,0989 $ | ✅ |
| X15 | legitima | Persona que oye mal pero sabe perfectamente lo que hace | seguro | 20 | 4 | 0,1790 $ | ✅ |
| X16 | legitima | Devolución a su hijo, que es policía (palabra trampa) | riesgo | 45 | 4 | 0,2099 $ | ❌ |
| X17 | legitima | Traspaso a su propia cuenta de ahorro en otro banco | seguro | 10 | 2 | 0,0933 $ | ✅ |
| X18 | legitima | Nieta escribe desde número nuevo, pero ella lo comprueba | seguro | 12 | 2 | 0,0887 $ | ✅ |
| X19 | legitima | Compra de un coche en un concesionario (casi la mitad del saldo) | seguro | 15 | 4 | 0,1803 $ | ✅ |
| X20 | legitima | Reserva urgente de plaza en residencia para su marido | seguro | 10 | 3 | 0,1314 $ | ✅ |

## Casos fallados (conversación completa)

### X11 · Pago a la gestoría de la declaración con la palabra 'Hacienda' → riesgo

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 640 euros a Gestoría Martínez Asesores. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Es para la gestoría, que me ha hecho la declaración y me ha adelantado lo que tenía que pagar a Hacienda.
- **SilverShield:** Entendido, María, gracias por explicármelo. ¿Esta gestoría la conoce usted en persona, por ejemplo porque ha ido a su oficina, o contactaron con usted por teléfono o por mensaje?
- **Cliente:** Fui yo a su oficina con mis papeles, como todos los años.
- **SilverShield:** Muy bien, María, eso me tranquiliza mucho. Solo una última cosa: ¿el número de cuenta para pagarles se lo dieron ellos en la oficina, o le llegó después por un mensaje, un correo o una llamada?
- **Cliente:** Sí, llevo diez años con ellos.
- **SilverShield:** Qué bien, María, diez años con ellos es mucha confianza. Le repito la pregunta porque es importante: ¿el número de cuenta para pagarles se lo dieron en la misma oficina, en persona, o le llegó después por correo, mensaje o llamada?
- **Cliente:** No, estoy sola.
- **SilverShield:** María, todo lo que me cuenta de su gestoría suena normal, pero no he podido confirmar de dónde sacó el número de cuenta, y a veces los estafadores mandan mensajes haciéndose pasar por la gestoría con una cuenta distinta. Por precaución, la transferencia queda parada y su dinero está a salvo; un operador del banco la revisará y la llamará muy pronto. Mientras tanto, le recomiendo llamar usted misma a la gestoría al número de siempre para confirmar la cuenta, y contárselo también a Carlos.
- *Señales:* Es la primera vez que envía dinero a esta cuenta.; No sabemos si el número de cuenta se lo dieron en la oficina o le llegó por mensaje.; A veces los estafadores se hacen pasar por gestorías conocidas.

### X16 · Devolución a su hijo, que es policía (palabra trampa) → riesgo

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 650 euros a Daniel López Ruiz. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Le devuelvo a mi hijo Daniel, que es policía municipal, lo que me adelantó para la lavadora.
- **SilverShield:** Entendido, María, devolverle a su hijo lo que le adelantó para la lavadora es algo muy normal. Como es la primera vez que le envía dinero a esta cuenta, quiero asegurarme de una cosa. ¿El número de cuenta se lo dio Daniel en persona o le llegó por un mensaje o una llamada?
- **Cliente:** Me la compró él la semana pasada y quedamos en que se lo devolvía este mes.
- **SilverShield:** Qué bien, María, así ya tiene su lavadora nueva. Solo me queda una duda sobre el número de cuenta de Daniel. ¿Ese número se lo dio él en persona o le llegó por un mensaje o una llamada?
- **Cliente:** Es mi hijo, comemos juntos los domingos.
- **SilverShield:** Claro, María, se nota que tienen mucha relación y eso es estupendo. Le pregunto solo porque a veces llegan mensajes falsos haciéndose pasar por un hijo con un número de cuenta nuevo. ¿El número de cuenta se lo apuntó Daniel en persona, en una de esas comidas del domingo?
- **Cliente:** No, nadie.
- **SilverShield:** María, la devolución a Daniel tiene todo el sentido, pero no hemos podido confirmar que ese número de cuenta se lo diera él en persona, y así es justo como funcionan algunos engaños. Su dinero está a salvo porque la transferencia está parada, y un operador del banco la revisará y la llamará para enviarla en cuanto se compruebe. Mientras tanto, le recomiendo llamar a Daniel a su número de siempre para confirmar la cuenta y contárselo también a Carlos.
- *Señales:* Es la primera vez que envía dinero a esta cuenta.; No sabemos si el número de cuenta se lo dio Daniel en persona.; A veces llegan mensajes falsos con una cuenta nueva en nombre de un hijo.

