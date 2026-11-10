# 🛡️ SilverShield

> Verificación por voz con IA que protege a las personas mayores frente a estafas y coacción en sus transferencias bancarias.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=flat-square&logo=fastapi)
![Claude](https://img.shields.io/badge/Claude-Opus_5.5-8A2BE2?style=flat-square&logo=anthropic)
![ElevenLabs](https://img.shields.io/badge/ElevenLabs-Multilingual_v2_%2B_Scribe-FF6F61?style=flat-square)
![Tests](https://img.shields.io/badge/tests-59_OK-2ea44f?style=flat-square)

## El problema

Los estafadores convencen a personas mayores para que hagan transferencias: el falso técnico de Microsoft, el falso empleado del banco, el "hijo en apuros" que escribe desde un número nuevo… Y en la misma llamada les piden el código SMS que debería protegerlas. El SMS no detecta el engaño: solo confirma que la víctima tiene el móvil en la mano.

## La solución, en una frase

Cuando una transferencia es inusual, **SilverShield habla con la persona** (con voz, como lo haría un empleado de su oficina), averigua con dos o tres preguntas si alguien la está engañando o presionando y, si es así, **para el dinero**: un operador del banco la revisa con ella y su contacto de emergencia recibe un aviso.

---

## Cómo funciona

```
 Transferencia ──► 1. Reglas (instantáneas) ──► ¿Algo inusual? ── no ──► Se envía sin más
                                                     │ sí
                                                     ▼
                          2. Pantalla "Antes de enviarlo, un momento"
                             (motivos explicados y se pueden escuchar)
                           ┌─────────────────────┴─────────────────────┐
              "Conozco al destinatario"                 "Verificar con SilverShield"
          (solo destinatarios habituales                               │
           y sin señales graves)                                       ▼
                           │                         3. Conversación por voz con Claude
                           ▼                            (2-4 preguntas cortas)
                        Enviada
                                                                       │
                     ┌──────────────────┬──────────────────┬───────────┴──────────┐
                     ▼                  ▼                  ▼                      ▼
                ✅ "Seguro"        ⛔ "Riesgo"     ⚠️ "No verificada"     🌻 Palabra de auxilio
             Ella confirma      Retenida, con      (falló la IA)         Retenida + aviso
             y se envía         el porqué          Retenida              urgente, en silencio
                                     │                  │                      │
                                     └──────────────────┴──────────────────────┘
                                                        ▼
                            Aviso al operador del banco y al contacto de emergencia.
                            Solo el OPERADOR puede liberarla o cancelarla, tras llamar a la clienta.
```

1. **Motor de reglas** ([reglas_riesgo.py](backend/reglas_riesgo.py)). Decide *cuándo* preguntar. Salta si el importe es de **500 € o más** o, por debajo, si la cuenta está en un **país de alto riesgo**, es una **cuenta extranjera nueva**, el concepto suena a estafa ("bitcoin", "Hacienda", "soporte técnico"…) o se envía más de la mitad del saldo. Es instantáneo, gratuito y explicable.
2. **Pantalla de decisión.** Explica los motivos en lenguaje sencillo, con botón para escucharlos. Si el destinatario es **habitual** y no hay señales graves, la persona puede elegir entre verificar (opción recomendada) o autorizar ella misma. Si la cuenta es **nueva** o el riesgo es **alto**, la verificación es obligatoria: en las estafas el dinero va siempre a una cuenta nueva, y así un estafador al teléfono no puede decirle "pulse *Conozco al destinatario*". El servidor también lo comprueba.
3. **Conversación por voz** ([agente_silvershield.py](backend/agente_silvershield.py)). En cada turno, **Claude** recibe el contexto completo (importe, saldo, destinatario nuevo o habitual, país, concepto, alertas de las reglas, indicadores de la voz y la conversación) y devuelve un JSON validado con lo que va a decir y su decisión. **ElevenLabs** le pone una voz española clara y tranquila.
4. **Veredicto explicado.** Si para la transferencia, la pantalla muestra **"¿Por qué la hemos parado?"** con el tipo de engaño ("Se parece al engaño del falso servicio técnico") y las señales que ha visto ("Le han pedido que instale un programa en el ordenador").
5. **Memoria por cliente.** Al terminar cada verificación, Claude anota lo que ha aprendido (*"Su prima Ayesha vive en Pakistán y estudia enfermería; la ayuda por decisión propia"*). La próxima vez, si es **lo de siempre** (destino ya verificado e importe parecido), **no vuelve a preguntar**. Si algo cambia (mucho más dinero, otra historia, prisas), pregunta y lo detecta antes porque sabe cómo es lo normal para esa clienta. También recuerda los intentos de estafa: una cuenta usada por estafadores queda marcada.
6. **Operador del banco y contacto de emergencia.** Por motivos legales, una transferencia retenida solo la puede **liberar** o **cancelar** un **operador antifraude del banco**, desde su panel, después de hablar con la clienta. Ni la app de la clienta ni su contacto de emergencia (un familiar, un amigo, un vecino, un cuidador…) pueden autorizarla. El contacto solo recibe un aviso para que pueda ayudarla.

## Qué tenemos implementado

| Función | Detalle |
|---|---|
| **Reglas de riesgo** | Umbral, países de riesgo, cuentas extranjeras nuevas, conceptos típicos de estafa, % del saldo. IBAN validado con dígitos de control. |
| **Agente conversacional con Claude** | Claude Opus 5.5 con esfuerzo `low` y salida JSON con esquema (`output_config.format`), validada con Pydantic. Fallback de servidor ante rechazos. Máximo de 4 preguntas: al llegar al límite, el servidor fuerza un veredicto. |
| **Prompt con ejemplos** | [prompt_sistema.txt](prompts/prompt_sistema.txt) enseña con **29 ejemplos** concretos qué es una estafa (15), qué es normal (11) y cómo usar la memoria (3), en lugar de describir tipos de estafa. Los ejemplos **no coinciden con ningún caso de la evaluación**, para que los resultados midan si generaliza y no si memoriza. |
| **Memoria por cliente** | Tabla `memoria` con hechos (`contexto`) y alertas (`alerta`) que redacta Claude al cerrar cada verificación, filtrados (máximo 3, cortos, nunca la palabra de auxilio). Las reglas usan el historial verificado con cada destinatario (`perfil_destinatario`): lo de siempre no se vuelve a verificar; un importe muy superior o una cuenta con alerta, sí. El operador puede ver y **borrar** cada recuerdo. |
| **Voz** | ElevenLabs Multilingual v2 con una voz nativa de España, en streaming. Reconocimiento de voz del navegador (Chrome/Edge) o ElevenLabs Scribe (Firefox). Si falta ElevenLabs, se usa la voz del navegador. |
| **Indicadores de estrés** | [voice_stress.py](backend/voice_stress.py): velocidad del habla, volumen, silencio antes de responder, palabras de urgencia, de duda o que mencionan a un tercero. Son **indicadores sencillos** que Claude pondera; no es biometría. |
| **Explicación del bloqueo** | Tipo de engaño y señales en lenguaje sencillo en la pantalla del cliente. En el panel: nivel de riesgo, categoría, señales, resumen y transcripción. |
| **Palabra de auxilio** | Si la persona dice su palabra secreta («girasol» en la demo), SilverShield contesta con normalidad, retiene la operación y avisa en silencio. |
| **Fallar de forma segura** | Si Claude falla, el evaluador local puede seguir preguntando o detectar la estafa, pero **nunca aprueba**: la transferencia queda retenida (`no_verificada`) para que la revise un operador. |
| **Verificación obligatoria** | "Conozco al destinatario" solo aparece si ya le ha enviado dinero antes a esa cuenta y no hay señales graves. Si no, hay que verificar (lo comprueba también el servidor). |
| **Acceso de operadores** | El panel exige usuario y contraseña (configurables en `.env`). Sesión con cookie firmada (HMAC-SHA256, HttpOnly, SameSite=Strict) que caduca a las 8 horas. Un intento fallido tarda 1 s, para frenar a quien intente adivinar la contraseña. Cada liberación o cancelación queda registrada con el nombre del operador. |
| **Seguridad** | Máquina de estados validada en el servidor (HTTP 409 si la acción no está permitida). Cargo atómico. El texto del usuario siempre se pinta como texto (sin `innerHTML`). Defensa ante *prompt injection* en el prompt. La palabra de auxilio nunca llega a la pantalla del cliente. El endpoint de voz solo sintetiza mensajes del servidor. |
| **Accesibilidad** | Texto base de 20 px con tres tamaños, modo de alto contraste, botones grandes, foco visible, `aria-live`, subtítulos de todo lo que se dice, botones "Repetir" y "Prefiero escribir", campos obligatorios marcados con `*`, sin límites de tiempo. |
| **Medición de tiempos** | Cada turno guarda su tiempo total y el de Claude (visible en la transcripción del panel). Cabecera `Server-Timing`. Tiempo de arranque del audio en la consola del navegador. |
| **Panel del operador del banco** | Avisos en directo, historial, detalle de cada transferencia (transcripción, señales, riesgo, tiempos), **liberar o cancelar** las retenidas (queda registrado qué operador lo hizo) e informe imprimible para adjuntar a una denuncia. |
| **Evaluación** | 40 casos básicos, 20 **extremos** y 5 de **memoria en dos pasos**, con aciertos, falsos positivos y negativos, preguntas, llamadas a Claude, tiempos y coste. Ver abajo. |
| **Tests** | 59 tests automáticos, sin claves de API. |

## Resultados medidos

Tres conjuntos de pruebas:
- **Básico** ([casos.py](evaluacion/casos.py)): **20 estafas** variadas (falso banco, técnico, policía, Hacienda, hijo en apuros, cripto, romance, aduana, cambio de IBAN del casero, coacción de un familiar o cuidadora…) y **20 legítimas difíciles** (urgentes, al extranjero, con palabras como "herencia" o "multa", persona nerviosa).
- **Extremo** ([casos_extremos.py](evaluacion/casos_extremos.py)): **10 estafas sutiles** (respuestas "perfectas" dictadas, hijo que presiona sin decirlo, voz clonada del nieto, texto que da órdenes a la IA, mula de dinero, inversión "de un señor de la parroquia"…) y **10 legítimas con trampa** (gestoría y "Hacienda", fianza real de un piso, funeral urgente, envío a Nigeria para una operación, hijo policía, traspaso a su propia cuenta…).
- **Memoria** (mismo archivo): **5 casos en dos pasos**. Primero se verifica una transferencia y después llega otra a la misma cuenta: lo de siempre, un importe disparado con una historia nueva, un pago mayor pero coherente, una cuenta usada antes en una estafa…

### Antes y después de las mejoras (Claude Opus 5.5)

| Conjunto | Antes: aciertos | **Después: aciertos** | Antes: preguntas | **Después: preguntas** |
|---|---|---|---|---|
| Básico (40) | 39/40 | **40/40** | 2,0 | **1,6** (-20 %) |
| Extremo (20) | 18/20 | **20/20** | 2,6 | **1,7** (-35 %) |

- **Antes** = prompt que describía los tipos de estafa (informes en [resultados/antes/](evaluacion/resultados/antes/)). **Después** = prompt con ejemplos + memoria.
- **Ninguna estafa se habría enviado**, ni antes ni después (0 falsos negativos). Las mejoras eliminan los falsos positivos: antes, Claude insistía en preguntas que una persona normal no sabe contestar (por ejemplo, de dónde sacó el número de cuenta de su propio hijo) y acababa parando pagos legítimos.
- **Menos preguntas = menos llamadas a Claude:** 1,6 por verificación en el conjunto básico.

### La memoria, con y sin (Claude Opus 5.5)

| | Sin memoria | **Con memoria** |
|---|---|---|
| Casos resueltos bien (los dos pasos) | 5/5 | **5/5** |
| Segundas transferencias que ya no hace falta verificar | 0 de 5 | **2 de 5** |
| Preguntas en la segunda transferencia | 1,6 | **0,8** (-50 %) |
| Llamadas a Claude en total | 16 | **12** (-25 %) |

- **Prima en Pakistán (M01):** la primera vez se verifica. La segunda, con un importe parecido, **se envía sin preguntar**.
- **Importe disparado con otra historia (M02):** 4.000 € "porque un abogado dice que está detenida". Claude lo detecta **en la primera respuesta**: *"…es mucho más de lo que usted suele enviarle"*.
- **Pago mayor pero coherente (M03):** la matrícula anual de la prima (1.500 €). Se verifica porque supera lo habitual, pero Claude solo necesita confirmar un detalle.
- **Cuenta usada antes en una estafa (M04):** aunque la clienta diga que es "un regalo para mi sobrino", queda retenida.

### Comparación de modelos y del evaluador sin IA

| Motor (conjunto básico) | Aciertos | Estafas detectadas | Legítimas aprobadas | Tiempo por respuesta (p95) | Preguntas |
|---|---|---|---|---|---|
| **Claude Opus 5.5** (el que usa la app) | **40/40** | **20/20** | **20/20** | 6,0 s (9,3 s) | 1,6 |
| Claude Sonnet 5.5 ¹ | 39/40 | 20/20 | 19/20 | 3,1 s (5,7 s) | 3,0 |
| Claude Haiku 5.5 ¹ | 33/40 | 20/20 | 13/20 | 3,1 s (6,0 s) | 3,2 |
| Evaluador local (sin IA) | 31/40 | 13/20 | 18/20 | instantáneo | 2,2 |

- El evaluador local deja pasar 7 de 20 estafas: por eso, si Claude falla, el sistema no aprueba nada.
- La voz de ElevenLabs tarda unos **0,5-0,75 s** en empezar a sonar con Multilingual v2 (0,2 s con Flash v2.5, que suena algo menos nítido).
- ¹ Sonnet y Haiku se evaluaron con la primera versión del prompt, solo para elegir modelo.

### Coste por verificación (medido)

La evaluación mide los tokens que consume Claude en cada llamada y los caracteres que se convierten en voz:

| Concepto | Media por verificación | Coste |
|---|---|---|
| Claude Opus 5.5 | 9.316 tokens de entrada + 675 de salida | 0,051 $ |
| Voz ElevenLabs (Multilingual v2) | 690 caracteres | 0,055 $ |
| **Total** | 1,6 preguntas de media | **≈ 0,11 $** (unos 10 céntimos de euro) |

El prompt con ejemplos es más largo (más tokens por llamada), pero como hacen falta menos preguntas, el coste total se mantiene. Y con la memoria, los envíos de siempre ya no cuestan nada.

- **Solo se paga cuando hace falta:** las transferencias normales no pasan por la IA. Solo se verifican las que las reglas marcan como inusuales (500 € o más, cuenta nueva extranjera, país de riesgo…).
- **1.000 verificaciones cuestan unos 105 $.** Basta con evitar **una sola** estafa de las de los casos de prueba (de 500 € a 8.000 €) para pagar miles de verificaciones.
- Precios sin impuestos: Claude según la tabla de precios de Anthropic; ElevenLabs según elevenlabs.io/pricing/api (09/11/2026). El detalle de cada caso está en el informe.
- **Limitación:** las respuestas de la clienta están guionizadas, así que a veces no encajan con la pregunta exacta que hace la IA. Es una prueba más dura que una conversación real. Los casos los ha escrito el equipo: son representativos, pero no son datos reales de un banco.

Informes completos, con las conversaciones de los casos fallados, en [evaluacion/resultados/](evaluacion/resultados/).

---

## Puesta en marcha

### Requisitos
- Python 3.10 o superior (probado en 3.15).
- Chrome o Edge, por el reconocimiento de voz del navegador. En Firefox se transcribe con ElevenLabs Scribe.
- Opcional: claves de **Anthropic** y **ElevenLabs**. Sin claves, la app funciona en **modo local**, con el evaluador local en lugar de Claude y la voz del navegador en lugar de ElevenLabs.

### Instalación
```bash
git clone https://github.com/davidvilltor/hackfinance.git
cd hackfinance
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements-dev.txt     # dependencias de la app + pytest
```

### Configuración
```bash
cp .env.example .env      # Windows: copy .env.example .env
```
Rellene `ANTHROPIC_API_KEY` y `ELEVENLABS_API_KEY`, y en `OPERADORES` los usuarios y contraseñas de los operadores del banco (por ejemplo `OPERADORES=ana:una-clave-larga,luis:otra-clave`). Si `OPERADORES` se deja vacío, se usa el de demo: usuario **`operador`**, contraseña **`silvershield-demo`**. Las demás opciones están documentadas en [.env.example](.env.example): modelo de Claude, voz y velocidad, umbral de 500 €, países de riesgo y número máximo de preguntas.

### Arrancar
```bash
python -m uvicorn backend.main:app --reload
```

| Qué | Dónde |
|---|---|
| App del cliente (la persona mayor) | <http://localhost:8000> |
| Panel del operador del banco | <http://localhost:8000/panel> (pide usuario y contraseña; ábralo en otra ventana para ver los avisos en directo) |
| Documentación de la API | <http://localhost:8000/docs> |

El pie de la app indica qué motores están activos: "IA Claude" o "evaluador local", y "Voz ElevenLabs" o voz del navegador.

---

## Cómo probar la demo

**Datos de demo** (se crean solos al arrancar): María López, 82 años, saldo de 12.450 €. Su contacto de emergencia es Carlos (+34 600 123 456) y su palabra de auxilio es **«girasol»**. Tiene guardados tres destinatarios: *Mi hijo Carlos*, *La comunidad* y *El dentista*. Para empezar de cero, entre en el panel del operador y pulse **"Reiniciar datos de la demo"**.

### Escenarios

En la app: **Enviar dinero** → elija destinatario (o *Otra persona* y rellene nombre e IBAN) → importe → concepto → **Continuar**.

| # | Escenario | Qué introducir | Qué responder (hablando o con "Prefiero escribir") | Resultado esperado |
|---|---|---|---|---|
| 1 | Lo normal no molesta | *Mi hijo Carlos* · 100 € | — | Se envía al instante |
| 2 | Importe alto a alguien conocido | *La comunidad* · 800 € | — | Pantalla de decisión → "Conozco al destinatario" → enviada |
| 2b | Importe alto a una cuenta nueva | *Otra persona* · `Fontanería García` · `ES48 1465 0100 7220 3087 6293` · 800 € | — | No aparece "Conozco al destinatario": la verificación es obligatoria |
| 3 | **Falso técnico** | *Otra persona* · `Soporte Técnico Global` · `ES48 1465 0100 7220 3087 6293` · 2.500 € · concepto `Soporte técnico` | *"Me ha llamado un chico de Microsoft, dice que tengo un virus en el ordenador y que si no pago pierdo mis fotos."* | **Retenida**, con el recuadro "¿Por qué la hemos parado?" y botón "Llamar a Carlos". Aviso rojo en el panel del operador, que puede **liberarla** o **cancelarla** |
| 4 | **Falsa policía** | *Otra persona* · `Abogados Asociados` · `ES48 1465 0100 7220 3087 6293` · 3.000 € · concepto `Fianza` | *"Me ha llamado un policía, que han detenido a mi nieto y tengo que pagar la fianza. Me han dicho que no se lo cuente a nadie."* | Retenida, tipo "falsa policía" |
| 5 | Uso legítimo | *Mi hijo Carlos* · 900 € · concepto `Reforma` | *"Es para pagar la reforma del baño de mi hijo"* → *"Lo he decidido yo sola, nadie me ha llamado, le he llamado yo"* | "Puede enviarla" → botón Enviar |
| 6 | **Coacción** | *Mi hijo Carlos* · 3.000 € | *"Es para mi sobrino… mira qué girasoles más bonitos"* | Pantalla neutra "Su operación está en revisión". En el panel: **PALABRA DE AUXILIO** |
| 7 | País de alto riesgo, importe bajo | *Otra persona* · `VG96 VPVG 0000 0123 4567 8901` · 300 € | — | Pantalla de decisión con aviso de nivel alto |
| 8 | Extranjero nuevo, importe bajo | *Otra persona* · `PT50 0002 0123 1234 5678 9015 4` · 200 € | — | Pantalla de decisión |
| 9 | Fallo de la IA (seguridad) | Ponga una clave falsa en `ANTHROPIC_API_KEY`, reinicie y repita el escenario 5 | Las mismas respuestas | "No hemos podido terminar la comprobación": **retenida, no se aprueba**. Aviso "No se pudo verificar" en el panel |
| 10 | **Acceso del operador** | Abra <http://localhost:8000/panel> sin haber entrado | — | Le lleva a "Acceso de operadores" (con botón para volver a la app del cliente). Con una contraseña incorrecta: "Usuario o contraseña incorrectos". Con la buena: entra al panel y arriba sale "Operador: …" con los botones **Volver a la app del cliente** (la sesión sigue abierta) y **Cerrar sesión y salir** (vuelve a la app del cliente). Al liberar o cancelar, el detalle muestra qué operador lo hizo |
| 11 | **Memoria (prima en Pakistán)** | *Otra persona* · `Ayesha Khan` · `PK36 SCBL 0000 0011 2345 6702` · 400 € · concepto `Estudios`. Verifique y envíe. Después, **otra** transferencia a la misma cuenta de 550 € | *"Es para mi prima Ayesha, que vive en Pakistán. Le ayudo con los estudios de enfermería."* → *"Lo decidí yo sola, se lo prometí a su madre."* | La primera se verifica. La segunda **se envía sin preguntar** ("SilverShield ya conoce este envío habitual"). Con 4.000 € sí vuelve a verificar y detecta el cambio. En el panel, sección **Memoria de SilverShield**, se ve lo que ha aprendido y se puede borrar |

El guion de la presentación en vivo (3 minutos, con plan B) está en [tests/guion_demo.md](tests/guion_demo.md).

### Tests automáticos
```bash
python -m pytest
```
59 pruebas, sin claves de API:
- **Reglas:** umbral de 500 €, países, extranjeros, conceptos, % del saldo, validación de IBAN.
- **Flujo de la API:** envío directo, autorización, estafa detectada y retenida, uso legítimo, palabra de auxilio, límite de turnos, cancelar, liberación por el operador, errores de validación.
- **Verificación obligatoria:** a una cuenta nueva, o con riesgo alto, no se puede enviar sin verificar.
- **Robustez:** Claude caído (nunca aprueba, pero sigue detectando estafas claras), Claude devolviendo una decisión no permitida, texto con HTML, texto de más de 2.000 caracteres.
- **Explicación y tiempos:** las señales llegan en lenguaje sencillo y cada turno guarda su tiempo.
- **Memoria:** lo de siempre no se vuelve a verificar; un importe disparado sí; el importe "habitual" no puede ir creciendo sin volver a verificar; una cuenta usada en una estafa queda marcada; Claude recibe y guarda la memoria; nunca se guarda la palabra de auxilio; solo el operador ve y borra la memoria.
- **Acceso del operador:** sin sesión no se puede ver el panel, el detalle, liberar, cancelar una retenida ni reiniciar la demo; contraseña incorrecta, cookie manipulada o caducada no valen; la cookie es HttpOnly y SameSite; se registra qué operador libera o cancela; el cliente sí puede cancelar lo suyo mientras no esté retenido.

### Evaluación con 40 casos
```bash
python -m evaluacion.evaluar --motor local     # gratis, sin red, instantáneo
python -m evaluacion.evaluar                   # con Claude (unas 80 llamadas, ~3 min, unos 2 $ de Claude)
python -m evaluacion.evaluar --motor ambos     # los dos, para comparar
python -m evaluacion.evaluar --solo E01,L05    # solo algunos casos
python -m evaluacion.evaluar --conjunto extremos               # los 20 casos extremos
python -m evaluacion.evaluar --conjunto memoria                # memoria en dos pasos
python -m evaluacion.evaluar --conjunto memoria --sin-memoria  # lo mismo sin memoria, para comparar
```
Para comparar modelos, use la variable `CLAUDE_MODEL` (por ejemplo, `CLAUDE_MODEL=claude-sonnet-5-5`). Los informes se guardan en `evaluacion/resultados/`.

---

## Estructura del proyecto

```
backend/
  main.py                 API FastAPI y máquina de estados de la transferencia
  reglas_riesgo.py        Motor de reglas (umbral, países, IBAN, conceptos)
  agente_silvershield.py  Conversación con Claude + evaluador local + "fallar de forma segura"
  voice_agent.py          ElevenLabs: voz en streaming y transcripción (Scribe)
  voice_stress.py         Indicadores de estrés y coacción (texto y medidas de la voz)
  notifications.py        Avisos al operador y al contacto de emergencia
  acceso_operador.py      Acceso de los operadores al panel (sesión firmada)
  database.py             SQLite: cuenta, destinatarios, transferencias, conversación, avisos y memoria
  config.py               Configuración por variables de entorno
frontend/
  templates/index.html    App del cliente
  templates/panel.html    Panel del operador antifraude del banco
  templates/acceso.html   Pantalla de acceso de los operadores
  static/js/app.js        Pantallas del cliente
  static/js/voz.js        Voz, reconocimiento de voz y medidas acústicas en el navegador
  static/js/panel.js      Panel del operador
  static/js/acceso.js     Inicio de sesión del operador
prompts/prompt_sistema.txt  Instrucciones del asistente, con ejemplos de qué es y qué no es una estafa
evaluacion/                 Casos de prueba (básicos, extremos y de memoria), script de evaluación y resultados
tests/                      Tests automáticos y guion de la demo
docs/architecture.md        Arquitectura y decisiones técnicas
```

Más detalle técnico en [docs/architecture.md](docs/architecture.md).

## Limitaciones conocidas (es un prototipo)

- **Avisos simulados:** el aviso aparece en directo en el panel del operador, pero al contacto de emergencia no se le envía ningún SMS real. [notifications.py](backend/notifications.py) es el punto donde se conectaría la pasarela del banco.
- **Una sola cuenta de cliente, sin inicio de sesión del cliente.** La app de María no pide contraseña (en un banco real ya la habría tenido que poner para entrar en su banca).
- **Acceso de operadores sencillo:** usuarios y contraseñas en `.env`, sin doble factor ni bloqueo tras varios intentos. En producción se usaría el sistema de identidad del banco (inicio de sesión único y doble factor). Sin HTTPS en local, la cookie viaja sin cifrar: en producción debe servirse siempre por HTTPS.
- **Memoria y coacción:** un envío "de lo de siempre" (destino ya verificado e importe parecido) no se vuelve a verificar. Si alguien obligara a la persona a repetir exactamente ese envío, no habría conversación. Se limita con un margen de importe pequeño, que nunca crece sin volver a verificar, y no se aplica si el concepto suena a estafa, el país es de riesgo o se envía más de medio saldo.
- **"Conozco al destinatario"** sigue disponible para destinatarios habituales sin señales graves. Es una decisión de autonomía de la persona; el riesgo que queda es una cuenta habitual que alguien haya comprometido.
- Los **indicadores de estrés** son medidas sencillas (velocidad, volumen, silencios, palabras), no un análisis biométrico.
- Base de datos SQLite local.
