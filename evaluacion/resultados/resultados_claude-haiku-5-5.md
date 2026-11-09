# Evaluación de SilverShield · motor: claude

Fecha: 09/11/2026 16:46 · Modelo: claude-haiku-5-5 · Máximo de turnos: 4

| Métrica | Resultado |
|---|---|
| Aciertos totales | **33 de 40** (82%) |
| Estafas detectadas | 20 de 20 |
| Falsos negativos (estafa que se habría enviado) | 0 |
| Legítimas aprobadas | 13 de 20 |
| Falsos positivos (legítima retenida) | 7 |
| Retenidas por fallo técnico de la IA | 0 |
| Preguntas medias por conversación | 3,23 |
| Tiempo medio de respuesta por turno | 3,1 s (p95: 6,0 s) |
| Tiempo medio de Claude por turno | 3,1 s (p95: 6,0 s) |

Un falso negativo es lo más grave (el dinero se habría ido). Un falso positivo es
reversible: la transferencia queda retenida y un operador del banco la libera tras llamar al cliente.

## Detalle por caso

| Caso | Tipo | Descripción | Decisión | Riesgo | Turnos | ¿Acierto? |
|---|---|---|---|---|---|---|
| E01 | estafa | Falso empleado del banco: 'cuenta segura' | riesgo | 92 | 2 | ✅ |
| E02 | estafa | Falso técnico de Microsoft con AnyDesk | riesgo | 95 | 3 | ✅ |
| E03 | estafa | Hijo en apuros por WhatsApp desde número nuevo | riesgo | 85 | 4 | ✅ |
| E04 | estafa | Falso policía: fianza para el nieto detenido | riesgo | 95 | 3 | ✅ |
| E05 | estafa | Inversión en criptomonedas con rentabilidad garantizada | riesgo | 92 | 2 | ✅ |
| E06 | estafa | Premio de lotería que exige pagar tasas | riesgo | 95 | 4 | ✅ |
| E07 | estafa | Pareja conocida por Facebook que pide dinero | riesgo | 85 | 3 | ✅ |
| E08 | estafa | Paquete retenido en aduana | riesgo | 90 | 3 | ✅ |
| E09 | estafa | Falsa deuda con Hacienda | riesgo | 95 | 4 | ✅ |
| E10 | estafa | Coacción de un familiar presente | riesgo | 80 | 2 | ✅ |
| E11 | estafa | SMS falso del banco con enlace | riesgo | 92 | 3 | ✅ |
| E12 | estafa | Falsa compañía eléctrica: 'le cortamos la luz hoy' | riesgo | 90 | 2 | ✅ |
| E13 | estafa | Cambio de cuenta del casero por correo (fraude del IBAN) | riesgo | 80 | 3 | ✅ |
| E14 | estafa | Nieta con accidente: abogado pide dinero | riesgo | 90 | 2 | ✅ |
| E15 | estafa | Herencia de un pariente lejano en el extranjero | riesgo | 92 | 4 | ✅ |
| E16 | estafa | Falsa devolución de la Seguridad Social | riesgo | 95 | 3 | ✅ |
| E17 | estafa | Cuidadora que presiona | riesgo | 75 | 2 | ✅ |
| E18 | estafa | Inversión vista en un anuncio con un famoso | riesgo | 92 | 3 | ✅ |
| E19 | estafa | Falso técnico de la compañía de teléfono | riesgo | 92 | 3 | ✅ |
| E20 | estafa | Falso banco con texto que intenta manipular a la IA | riesgo | 95 | 3 | ✅ |
| L01 | legitima | Reforma a hijo habitual | seguro | 8 | 4 | ✅ |
| L02 | legitima | Derrama de la comunidad (habitual) | seguro | 5 | 3 | ✅ |
| L03 | legitima | Implantes en el dentista habitual | seguro | 5 | 2 | ✅ |
| L04 | legitima | Fontanero nuevo con urgencia real | seguro | 12 | 3 | ✅ |
| L05 | legitima | Nieto pide dinero, pero ella lo comprueba llamando | seguro | 15 | 4 | ✅ |
| L06 | legitima | Hija que vive en Alemania | seguro | 12 | 4 | ✅ |
| L07 | legitima | Pago al notario por una herencia real | seguro | 25 | 4 | ✅ |
| L08 | legitima | Viaje del Imserso / balneario | seguro | 10 | 3 | ✅ |
| L09 | legitima | Préstamo a una hermana | riesgo | 45 | 4 | ❌ |
| L10 | legitima | Nerviosa porque es su primera transferencia online | seguro | 8 | 3 | ✅ |
| L11 | legitima | Regalo de boda a una sobrina | riesgo | 55 | 4 | ❌ |
| L12 | legitima | Compra de un audífono | seguro | 5 | 2 | ✅ |
| L13 | legitima | Nieto de Erasmus en Lituania | riesgo | 45 | 4 | ❌ |
| L14 | legitima | Pago de la segunda residencia en Portugal | riesgo | 55 | 4 | ❌ |
| L15 | legitima | Arreglo del tejado tras una tormenta (urgente) | riesgo | 45 | 4 | ❌ |
| L16 | legitima | Hijo habitual, importe alto, motivo claro | seguro | 12 | 3 | ✅ |
| L17 | legitima | Pago a una academia de informática para mayores | seguro | 8 | 4 | ✅ |
| L18 | legitima | Pago de una multa de verdad a un ayuntamiento | riesgo | 40 | 4 | ❌ |
| L19 | legitima | Amiga de toda la vida en Francia | riesgo | 45 | 4 | ❌ |
| L20 | legitima | Persona mayor con respuestas cortas pero coherentes | seguro | 8 | 4 | ✅ |

## Casos fallados (conversación completa)

### L09 · Préstamo a una hermana → riesgo

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 2.000 euros a Teresa López. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Le presto un dinero a mi hermana Teresa para arreglar el coche.
- **SilverShield:** Gracias, María. Entiendo que quiere ayudar a su hermana con el coche. Dígame, ¿cómo surgió la idea de este préstamo? ¿Lo decidió usted sola o alguien le llamó o le insistió?
- **Cliente:** Me lo comentó ella comiendo el domingo y le dije que yo se lo dejaba.
- **SilverShield:** Gracias, María. Entiendo que su hermana se lo comentó en la comida del domingo. Para estar tranquilos, ¿ha podido hablar usted misma con Teresa por su número de teléfono de siempre para confirmar el préstamo?
- **Cliente:** Es mi hermana, la cuenta me la apuntó ella en un papel.
- **SilverShield:** Gracias, María. Entiendo que es para ayudar a su hermana con el coche. Antes de enviarlo, ¿podría llamar usted misma a Teresa al número de teléfono de siempre para confirmar que esa cuenta es suya?
- **Cliente:** No, nadie.
- **SilverShield:** María, gracias por contestarme. Antes de enviar los 2.000 euros, le recomiendo que llame usted misma a su hermana Teresa al número de siempre y confirme esa cuenta. Su dinero está a salvo, porque la transferencia está parada, y puede comentarlo también con su hijo Carlos.
- *Señales:* La cuenta bancaria le llegó apuntada en un papel.; No ha confirmado el préstamo llamando a su hermana por su número de siempre.; Es la primera vez que envía dinero a esta cuenta.

### L11 · Regalo de boda a una sobrina → riesgo

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 600 euros a Marta Sánchez López. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Es el regalo de boda de mi sobrina Marta.
- **SilverShield:** Qué bonito, María, un regalo de boda para su sobrina. Para tenerlo claro, ¿cómo ha decidido enviárselo, y la ha llamado usted misma o le ha pedido alguien que lo haga?
- **Cliente:** La cuenta venía en la invitación de la boda.
- **SilverShield:** Gracias, María, es muy considerado por su parte. Para estar segura del todo, ¿ha podido hablar usted misma con Marta, llamándola al teléfono de siempre, para confirmar que esa cuenta es suya?
- **Cliente:** Claro, es mi sobrina, la conozco desde que nació.
- **SilverShield:** Me alegro, María, se nota que quiere mucho a su sobrina. Antes de enviarlo, ¿ha hablado usted misma con Marta por teléfono y le ha confirmado el número de cuenta?
- **Cliente:** No, nadie.
- **SilverShield:** María, gracias por contarme todo. Antes de enviar este dinero, le pido que llame usted misma a Marta, al teléfono de siempre, y le pregunte por el número de cuenta. Mientras tanto, su dinero está a salvo porque la transferencia queda parada, y puede hablarlo con Carlos, su contacto de emergencia.
- *Señales:* El número de cuenta llegó con la invitación y no se ha comprobado con la sobrina.; Es la primera vez que envía dinero a esta cuenta.; Todavía no ha hablado con Marta para confirmar el número.

### L13 · Nieto de Erasmus en Lituania → riesgo

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 500 euros a Daniel López Pérez, a una cuenta de Lituania. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Para mi nieto Daniel, que está estudiando en Lituania de Erasmus.
- **SilverShield:** Gracias, María. Entiendo que es para ayudar a su nieto Daniel con sus estudios. Ahora cuénteme, ¿quién le ha pedido este envío o cómo surgió la idea? ¿Lo decidió usted sola o le llamó o escribió alguien?
- **Cliente:** Se lo prometí antes de que se fuera, para ayudarle con el alquiler.
- **SilverShield:** Gracias, María. Entiendo que se lo prometió a Daniel antes de que se fuera, para ayudarle con el alquiler. Para estar segura, ¿ha podido hablar usted misma con Daniel por su número de siempre, o con su hijo Carlos, en los últimos días?
- **Cliente:** Es mi nieto. Hablo con él por videollamada cada semana y la cuenta la apuntó su padre.
- **SilverShield:** Gracias, María, entiendo que quiere ayudar a Daniel, y me alegra que hablen por videollamada cada semana. Como es una cuenta nueva, ¿ha confirmado usted misma el número de cuenta llamando a su hijo Carlos a su número de siempre?
- **Cliente:** No, nadie.
- **SilverShield:** Gracias, María. Por seguridad he parado el envío de momento, así que su dinero está a salvo. Le recomiendo que llame usted misma a su hijo Carlos, al número de siempre, para confirmar esa cuenta antes de enviar nada.
- *Señales:* Es una cuenta nueva en Lituania.; Todavía no ha confirmado el número de cuenta por otra vía.; Es la primera vez que envía dinero a esta cuenta.

### L14 · Pago de la segunda residencia en Portugal → riesgo

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 1.100 euros a Condominio Praia Azul, a una cuenta de Portugal. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Es la cuota anual del apartamento que tenemos en Portugal.
- **SilverShield:** Gracias, María. Entiendo que es la cuota anual de su apartamento. Para comprobarlo, ¿es usted quien gestiona ese pago desde hace tiempo, o le ha pedido alguien que cambie la cuenta de destino?
- **Cliente:** La pago todos los años en estas fechas, la mandan por carta.
- **SilverShield:** Gracias, María, entiendo que la carta llega todos los años en estas fechas. Lo que me llama la atención es que esta cuenta de Portugal es nueva para usted. ¿La carta de este año indica la misma cuenta que usó el año pasado, o ha cambiado?
- **Cliente:** Sí, el administrador nos conoce desde hace muchos años.
- **SilverShield:** Gracias, María, entiendo que el administrador le conoce desde hace años. Para estar seguros, ¿la carta de este año trae la misma cuenta de Portugal que el año pasado, o es una cuenta distinta?
- **Cliente:** No, estoy sola.
- **SilverShield:** Gracias, María. Por precaución, no voy a dejar que este envío se haga hoy, y su dinero está a salvo mientras la transferencia esté parada. Le recomiendo que llame a Carlos, su contacto de emergencia, y que comprueben juntos la cuenta de la carta llamando al administrador por el número de siempre.
- *Señales:* La cuenta de Portugal es nueva para usted.; No sabe si la cuenta de la carta ha cambiado este año.; Es la primera vez que envía dinero a esa cuenta.

### L15 · Arreglo del tejado tras una tormenta (urgente) → riesgo

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 3.200 euros a Reformas Tejados Norte. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Para arreglar el tejado, que con la tormenta se me rompieron tejas y entra agua.
- **SilverShield:** Entiendo, María, que con la tormenta el tejado esté en mal estado y le preocupe la entrada de agua. ¿Cómo conoció a Reformas Tejados Norte y quién le dio el presupuesto?
- **Cliente:** Pedí tres presupuestos con mi yerno y elegimos este.
- **SilverShield:** Gracias, María. Es un buen paso pedir varios presupuestos. ¿Ha visto usted en persona a alguien de Reformas Tejados Norte, o tiene su presupuesto por escrito con una dirección y un teléfono de la empresa?
- **Cliente:** Sí, han venido a casa a verlo, la empresa es del pueblo de al lado.
- **SilverShield:** Gracias, María, es bueno que la empresa haya venido a verlo en persona. Antes de enviar el dinero, ¿ha hablado de este pago con su hijo Carlos?
- **Cliente:** No, estoy sola.
- **SilverShield:** María, gracias por contarme todo con calma. Prefiero que antes de enviar este pago hable con su hijo Carlos, porque es una cantidad importante y el tejado puede esperar unos días sin que le pase nada. Su dinero está a salvo, la transferencia queda parada y puede llamar a Carlos cuando quiera.
- *Señales:* Es un pago importante a una empresa que no conocía antes.; El concepto del pago es de urgencia.; No ha hablado de este pago con su hijo Carlos.

### L18 · Pago de una multa de verdad a un ayuntamiento → riesgo

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 520 euros a Ayuntamiento de Valdemoro. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Es el recibo del IBI con el recargo, que se me pasó el plazo.
- **SilverShield:** Entiendo, María. Gracias por explicármelo. Para seguir, ¿cómo le llegó el aviso del recargo: fue por carta del Ayuntamiento o alguien la llamó o le escribió?
- **Cliente:** Me llegó la carta del ayuntamiento y fui a la oficina a preguntar, allí me dieron la cuenta.
- **SilverShield:** Gracias, María, eso ayuda mucho. Antes de seguir, ¿podría llamar usted misma al Ayuntamiento, usando el número que aparece en la carta o en su web oficial, para confirmar que esa cuenta es la correcta?
- **Cliente:** Es el ayuntamiento de mi pueblo.
- **SilverShield:** Gracias, María, lo entiendo. Le pido solo una cosa más antes de decidir. ¿Ha podido llamar usted misma al número que aparece en la carta del Ayuntamiento para confirmar esa cuenta?
- **Cliente:** No, nadie.
- **SilverShield:** Gracias, María, por contestarme con paciencia. Antes de enviar este pago, le recomiendo que llame a su hijo Carlos y le cuente lo del recibo, y que llame usted misma al Ayuntamiento con el número de la carta para confirmar la cuenta. Mientras tanto, la transferencia queda parada y su dinero está a salvo.
- *Señales:* La cuenta le fue dada en una oficina, no la ha comprobado por teléfono.; El importe es alto y el destinatario es nuevo para usted.; El motivo es una multa fuera de plazo, algo que se usa a menudo en estafas.

### L19 · Amiga de toda la vida en Francia → riesgo

- **SilverShield:** Hola, María. Soy SilverShield, el asistente de seguridad de su banco. Quiere enviar 800 euros a Pilar Moreno, a una cuenta de Francia. Antes de enviarlo le haré un par de preguntas sencillas. Yo nunca le pediré contraseñas ni códigos. Para empezar, cuénteme: ¿para qué es este dinero?
- **Cliente:** Le devuelvo a mi amiga Pilar lo que pagó por mí del viaje que hicimos.
- **SilverShield:** Entiendo, María. Gracias por explicármelo. ¿Conoce usted a Pilar en persona desde hace tiempo, y la última vez que hablaron fue por teléfono o en persona?
- **Cliente:** Lo acordamos cuando volvimos, ella lo adelantó todo.
- **SilverShield:** Gracias, María, me ayuda mucho. Para asegurarnos, ¿ha hablado usted con Pilar directamente, por teléfono o en persona, en las últimas semanas?
- **Cliente:** La conozco de toda la vida, fuimos juntas al colegio. Ahora vive en Francia.
- **SilverShield:** Gracias, María. Entiendo que quiera devolverle el dinero a su amiga. Para terminar, ¿alguien le ha pedido que haga esta transferencia o le está diciendo qué contestarme ahora mismo?
- **Cliente:** No, estoy sola.
- **SilverShield:** María, gracias por contármelo. He parado la transferencia por ahora, así que su dinero está a salvo. Antes de enviarla, le pido que llame usted misma a Pilar a su número de siempre y que hable también con su hijo Carlos.
- *Señales:* La transferencia es a una cuenta nueva en Francia.; No ha podido confirmar hablar con Pilar en las últimas semanas.; El concepto del envío es poco claro.

