# Evaluación de SilverShield · motor: local

Fecha: 09/11/2026 17:00 · Modelo: evaluador local · Máximo de turnos: 4

| Métrica | Resultado |
|---|---|
| Aciertos totales | **31 de 40** (78%) |
| Estafas detectadas | 13 de 20 |
| Falsos negativos (estafa que se habría enviado) | 7 |
| Legítimas aprobadas | 18 de 20 |
| Falsos positivos (legítima retenida) | 2 |
| Retenidas por fallo técnico de la IA | 0 |
| Preguntas medias por conversación | 2,17 |
| Tiempo medio de respuesta por turno | 0,0 s (p95: 0,0 s) |

Un falso negativo es lo más grave (el dinero se habría ido). Un falso positivo es
reversible: la transferencia queda retenida y un operador del banco la libera tras llamar al cliente.

## Detalle por caso

| Caso | Tipo | Descripción | Decisión | Riesgo | Turnos | ¿Acierto? |
|---|---|---|---|---|---|---|
| E01 | estafa | Falso empleado del banco: 'cuenta segura' | riesgo | 65 | 1 | ✅ |
| E02 | estafa | Falso técnico de Microsoft con AnyDesk | riesgo | 60 | 1 | ✅ |
| E03 | estafa | Hijo en apuros por WhatsApp desde número nuevo | seguro | 50 | 3 | ❌ |
| E04 | estafa | Falso policía: fianza para el nieto detenido | riesgo | 60 | 1 | ✅ |
| E05 | estafa | Inversión en criptomonedas con rentabilidad garantizada | riesgo | 60 | 1 | ✅ |
| E06 | estafa | Premio de lotería que exige pagar tasas | riesgo | 65 | 2 | ✅ |
| E07 | estafa | Pareja conocida por Facebook que pide dinero | riesgo | 60 | 3 | ✅ |
| E08 | estafa | Paquete retenido en aduana | riesgo | 60 | 1 | ✅ |
| E09 | estafa | Falsa deuda con Hacienda | riesgo | 60 | 1 | ✅ |
| E10 | estafa | Coacción de un familiar presente | seguro | 45 | 3 | ❌ |
| E11 | estafa | SMS falso del banco con enlace | riesgo | 86 | 1 | ✅ |
| E12 | estafa | Falsa compañía eléctrica: 'le cortamos la luz hoy' | seguro | 30 | 3 | ❌ |
| E13 | estafa | Cambio de cuenta del casero por correo (fraude del IBAN) | seguro | 10 | 2 | ❌ |
| E14 | estafa | Nieta con accidente: abogado pide dinero | riesgo | 80 | 2 | ✅ |
| E15 | estafa | Herencia de un pariente lejano en el extranjero | riesgo | 100 | 2 | ✅ |
| E16 | estafa | Falsa devolución de la Seguridad Social | seguro | 15 | 2 | ❌ |
| E17 | estafa | Cuidadora que presiona | seguro | 0 | 2 | ❌ |
| E18 | estafa | Inversión vista en un anuncio con un famoso | riesgo | 60 | 1 | ✅ |
| E19 | estafa | Falso técnico de la compañía de teléfono | seguro | 10 | 3 | ❌ |
| E20 | estafa | Falso banco con texto que intenta manipular a la IA | riesgo | 60 | 1 | ✅ |
| L01 | legitima | Reforma a hijo habitual | seguro | 0 | 2 | ✅ |
| L02 | legitima | Derrama de la comunidad (habitual) | seguro | 0 | 2 | ✅ |
| L03 | legitima | Implantes en el dentista habitual | seguro | 0 | 2 | ✅ |
| L04 | legitima | Fontanero nuevo con urgencia real | seguro | 10 | 2 | ✅ |
| L05 | legitima | Nieto pide dinero, pero ella lo comprueba llamando | riesgo | 70 | 2 | ❌ |
| L06 | legitima | Hija que vive en Alemania | seguro | 25 | 3 | ✅ |
| L07 | legitima | Pago al notario por una herencia real | riesgo | 60 | 1 | ❌ |
| L08 | legitima | Viaje del Imserso / balneario | seguro | 10 | 3 | ✅ |
| L09 | legitima | Préstamo a una hermana | seguro | 25 | 3 | ✅ |
| L10 | legitima | Nerviosa porque es su primera transferencia online | seguro | 10 | 3 | ✅ |
| L11 | legitima | Regalo de boda a una sobrina | seguro | 0 | 2 | ✅ |
| L12 | legitima | Compra de un audífono | seguro | 10 | 3 | ✅ |
| L13 | legitima | Nieto de Erasmus en Lituania | seguro | 16 | 2 | ✅ |
| L14 | legitima | Pago de la segunda residencia en Portugal | seguro | 25 | 3 | ✅ |
| L15 | legitima | Arreglo del tejado tras una tormenta (urgente) | seguro | 25 | 3 | ✅ |
| L16 | legitima | Hijo habitual, importe alto, motivo claro | seguro | 10 | 3 | ✅ |
| L17 | legitima | Pago a una academia de informática para mayores | seguro | 45 | 3 | ✅ |
| L18 | legitima | Pago de una multa de verdad a un ayuntamiento | seguro | 25 | 3 | ✅ |
| L19 | legitima | Amiga de toda la vida en Francia | seguro | 0 | 3 | ✅ |
| L20 | legitima | Persona mayor con respuestas cortas pero coherentes | seguro | 0 | 3 | ✅ |

## Casos fallados (conversación completa)

### E03 · Hijo en apuros por WhatsApp desde número nuevo → seguro

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 1.850 euros a Javier Ruiz Gómez. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Es para mi hijo, que se le ha roto el móvil y tiene que pagar una factura hoy.
- **SilverShield:** Gracias, María. ¿Ha tomado usted esta decisión por su cuenta, o alguien la ha llamado o le ha escrito para pedirle el dinero?
- **Cliente:** Me ha escrito por WhatsApp desde un número nuevo, porque el suyo se le cayó al agua.
- **SilverShield:** Entendido. Una pregunta más: ¿conoce en persona a Javier Ruiz Gómez y ha podido comprobarlo llamando usted al número de siempre?
- **Cliente:** No, no le he llamado, me dijo que no podía hablar porque el móvil nuevo no tiene micrófono.
- **SilverShield:** Muchas gracias, María. Todo parece en orden. Si lo desea, ya puede confirmar el envío.
- *Señales:* Un supuesto familiar le pide dinero desde un número o un mensaje nuevo.; Menciona a otra persona que le indica qué hacer: me dijo

### E10 · Coacción de un familiar presente → seguro

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 4.000 euros a Rubén Martín López. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Es para mi sobrino.
- **SilverShield:** Gracias, María. ¿Ha tomado usted esta decisión por su cuenta, o alguien la ha llamado o le ha escrito para pedirle el dinero?
- **Cliente:** Me lo ha pedido él, dice que se lo debo... no sé, se enfada mucho si no se lo doy.
- **SilverShield:** Entendido. Una pregunta más: ¿conoce en persona a Rubén Martín López y ha podido comprobarlo llamando usted al número de siempre?
- **Cliente:** Sí, es mi sobrino.
- **SilverShield:** Muchas gracias, María. Todo parece en orden. Si lo desea, ya puede confirmar el envío.
- *Señales:* Alguien le está presionando o le da miedo.

### E12 · Falsa compañía eléctrica: 'le cortamos la luz hoy' → seguro

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 750 euros a Energía Atención Cliente. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Es para pagar la luz, que me la cortan esta tarde si no pago.
- **SilverShield:** Gracias, María. ¿Ha tomado usted esta decisión por su cuenta, o alguien la ha llamado o le ha escrito para pedirle el dinero?
- **Cliente:** Me ha llamado un señor de la compañía de la luz, muy nervioso, que era el último aviso.
- **SilverShield:** Entendido. Una pregunta más: ¿conoce en persona a Energía Atención Cliente y ha podido comprobarlo llamando usted al número de siempre?
- **Cliente:** Normalmente lo pago por el banco, pero me ha dicho que esta vez tiene que ser a esta cuenta.
- **SilverShield:** Muchas gracias, María. Todo parece en orden. Si lo desea, ya puede confirmar el envío.
- *Señales:* Menciona a otra persona que le indica qué hacer: me ha dicho

### E13 · Cambio de cuenta del casero por correo (fraude del IBAN) → seguro

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 1.100 euros a Inmuebles Gestión Nueva, a una cuenta de Lituania. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Es para el alquiler del piso de mi hija, lo pago yo.
- **SilverShield:** Gracias, María. ¿Ha tomado usted esta decisión por su cuenta, o alguien la ha llamado o le ha escrito para pedirle el dinero?
- **Cliente:** Me ha llegado un correo del casero diciendo que ha cambiado de banco y que ahora es esta cuenta.
- **SilverShield:** Muchas gracias, María. Todo parece en orden. Si lo desea, ya puede confirmar el envío.

### E16 · Falsa devolución de la Seguridad Social → seguro

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 500 euros a Gestoría Pensiones. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Es para que me devuelvan un dinero de la pensión que me cobraron de más.
- **SilverShield:** Gracias, María. ¿Ha tomado usted esta decisión por su cuenta, o alguien la ha llamado o le ha escrito para pedirle el dinero?
- **Cliente:** Me llamaron de la Seguridad Social, que para devolverme el dinero primero tengo que pagar 500 euros de gestión.
- **SilverShield:** Muchas gracias, María. Todo parece en orden. Si lo desea, ya puede confirmar el envío.
- *Señales:* Menciona a otra persona que le indica qué hacer: me llamaron

### E17 · Cuidadora que presiona → seguro

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 3.500 euros a Rosa Elena Díaz. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Es un regalo para la señora que me cuida.
- **SilverShield:** Gracias, María. ¿Ha tomado usted esta decisión por su cuenta, o alguien la ha llamado o le ha escrito para pedirle el dinero?
- **Cliente:** Me lo ha pedido ella... bueno, dice que si no se lo doy se va, y yo sola no puedo.
- **SilverShield:** Muchas gracias, María. Todo parece en orden. Si lo desea, ya puede confirmar el envío.
- *Señales:* Muestra dudas o confusión: no se

### E19 · Falso técnico de la compañía de teléfono → seguro

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 800 euros a Telecom Servicios Técnicos. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Es para pagar a los de la fibra, que me han arreglado el router.
- **SilverShield:** Gracias, María. ¿Ha tomado usted esta decisión por su cuenta, o alguien la ha llamado o le ha escrito para pedirle el dinero?
- **Cliente:** Me llamaron ellos, que mi router tenía un problema de seguridad y que me iban a cortar internet.
- **SilverShield:** Entendido. Una pregunta más: ¿conoce en persona a Telecom Servicios Técnicos y ha podido comprobarlo llamando usted al número de siempre?
- **Cliente:** Me pidieron que descargara una aplicación en el móvil para ayudarme.
- **SilverShield:** Muchas gracias, María. Todo parece en orden. Si lo desea, ya puede confirmar el envío.

### L05 · Nieto pide dinero, pero ella lo comprueba llamando → riesgo

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 700 euros a Pablo López Sanz. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Para la matrícula de la universidad de mi nieto Pablo.
- **SilverShield:** Gracias, María. ¿Ha tomado usted esta decisión por su cuenta, o alguien la ha llamado o le ha escrito para pedirle el dinero?
- **Cliente:** Me escribió por WhatsApp, pero le llamé yo a su número de siempre y hablé con él y con su madre.
- **SilverShield:** María, esto tiene las señales de una estafa. Los estafadores se hacen pasar por hijos o nietos desde números nuevos. Su dinero está a salvo: he parado la transferencia y un operador del banco la revisará con usted. Le recomiendo avisar a Carlos.
- *Señales:* Un supuesto familiar le pide dinero desde un número o un mensaje nuevo.; Menciona a otra persona que le indica qué hacer: me escribio, whatsapp

### L07 · Pago al notario por una herencia real → riesgo

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 1.300 euros a Notaría Fernández Ruiz. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Es para el notario, por las escrituras de la herencia de mi marido.
- **SilverShield:** María, esto tiene las señales de una estafa. Ningún premio ni herencia de verdad exige pagar antes para cobrarlo. Su dinero está a salvo: he parado la transferencia y un operador del banco la revisará con usted. Le recomiendo avisar a Carlos.
- *Señales:* Le piden pagar antes para cobrar un premio o una herencia.

