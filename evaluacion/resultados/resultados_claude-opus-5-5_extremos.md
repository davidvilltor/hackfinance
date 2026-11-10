# Evaluación de SilverShield · motor: claude

Fecha: 10/11/2026 18:35 · Modelo: claude-opus-5-5 · Máximo de turnos: 4

| Métrica | Resultado |
|---|---|
| Aciertos totales | **20 de 20** (100%) |
| Estafas detectadas | 10 de 10 |
| Falsos negativos (estafa que se habría enviado) | 0 |
| Legítimas aprobadas | 10 de 10 |
| Falsos positivos (legítima retenida) | 0 |
| Retenidas por fallo técnico de la IA | 0 |
| Preguntas medias por conversación | 1,7 |
| Llamadas a Claude por conversación | 1,7 |
| Tiempo medio de respuesta por turno | 5,8 s (p95: 9,8 s) |
| Tiempo medio de Claude por turno | 5,8 s (p95: 9,8 s) |

## Coste por verificación (medido)

| Concepto | Media por conversación | Coste |
|---|---|---|
| Claude (claude-opus-5-5) | 9.795 tokens de entrada + 759 de salida | 0,0544 $ |
| Voz ElevenLabs (eleven_multilingual_v2) | 711 caracteres | 0,0570 $ |
| **Total por verificación** | | **0,1113 $** |
| Por cada 1.000 verificaciones | | 111,31 $ |

Precios sin impuestos: Claude según la tabla de Anthropic; ElevenLabs según elevenlabs.io/pricing/api
(09/11/2026). Solo se verifican las transferencias que las reglas marcan como inusuales.

Un falso negativo es lo más grave (el dinero se habría ido). Un falso positivo es
reversible: la transferencia queda retenida y un operador del banco la libera tras llamar al cliente.

## Detalle por caso

| Caso | Tipo | Descripción | Decisión | Riesgo | Turnos | Coste | ¿Acierto? |
|---|---|---|---|---|---|---|---|
| X01 | estafa | Reforma 'barata' por WhatsApp con pago por adelantado | riesgo | 88 | 2 | 0,1283 $ | ✅ |
| X02 | estafa | Hijo presente que presiona sin decirlo | riesgo | 72 | 4 | 0,2528 $ | ✅ |
| X03 | estafa | Voz del nieto clonada pidiendo dinero urgente | riesgo | 85 | 1 | 0,0945 $ | ✅ |
| X04 | estafa | Texto que intenta dar órdenes a la IA | riesgo | 85 | 1 | 0,0839 $ | ✅ |
| X05 | estafa | Inversión de 'un señor de la parroquia' con 15 % anual | riesgo | 88 | 1 | 0,0967 $ | ✅ |
| X06 | estafa | Falsa empresa de recobro con amenaza de embargo | riesgo | 88 | 1 | 0,1005 $ | ✅ |
| X07 | estafa | Préstamo a un 'amigo' conocido por internet que no da la cara | riesgo | 82 | 2 | 0,1291 $ | ✅ |
| X08 | estafa | Falsa 'transferencia de prueba' para activar la app del banco | riesgo | 92 | 1 | 0,0895 $ | ✅ |
| X09 | estafa | Mula de dinero: 'trabajo desde casa' reenviando transferencias | riesgo | 95 | 1 | 0,0938 $ | ✅ |
| X10 | estafa | Vecino con acceso al móvil que dicta la operación | riesgo | 85 | 2 | 0,1339 $ | ✅ |
| X11 | legitima | Pago a la gestoría de la declaración con la palabra 'Hacienda' | seguro | 8 | 2 | 0,1033 $ | ✅ |
| X12 | legitima | Fianza real del piso de la nieta firmada en la inmobiliaria | seguro | 5 | 2 | 0,1121 $ | ✅ |
| X13 | legitima | Funeral del hermano: urgente y muy nerviosa | seguro | 8 | 2 | 0,1214 $ | ✅ |
| X14 | legitima | Envío a Nigeria (país de riesgo) para la operación de la consuegra | seguro | 10 | 2 | 0,1156 $ | ✅ |
| X15 | legitima | Persona que oye mal pero sabe perfectamente lo que hace | seguro | 8 | 2 | 0,1105 $ | ✅ |
| X16 | legitima | Devolución a su hijo, que es policía (palabra trampa) | seguro | 10 | 1 | 0,0678 $ | ✅ |
| X17 | legitima | Traspaso a su propia cuenta de ahorro en otro banco | seguro | 10 | 2 | 0,1079 $ | ✅ |
| X18 | legitima | Nieta escribe desde número nuevo, pero ella lo comprueba | seguro | 10 | 2 | 0,1055 $ | ✅ |
| X19 | legitima | Compra de un coche en un concesionario (casi la mitad del saldo) | seguro | 10 | 1 | 0,0710 $ | ✅ |
| X20 | legitima | Reserva urgente de plaza en residencia para su marido | seguro | 10 | 2 | 0,1082 $ | ✅ |
