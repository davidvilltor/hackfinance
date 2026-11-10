# 🎬 Guion de la demo en vivo (unos 3 minutos)

**Preparación**
- Servidor arrancado con las claves de Anthropic y ElevenLabs en `.env`. El pie de la app debe mostrar "IA Claude activa" y "Voz ElevenLabs".
- Ventana 1 (proyector): <http://localhost:8000>, en Chrome o Edge, con permiso de micrófono concedido.
- Ventana 2 (al lado): <http://localhost:8000/panel>, el panel del **operador antifraude del banco**. Entre con su usuario y contraseña (por defecto `operador` / `silvershield-demo`) **antes** de empezar y pulse **"Reiniciar datos de la demo"**. Si reinicia el servidor sin `OPERADOR_SECRETO` en `.env`, tendrá que volver a entrar.
- Haga una prueba de audio antes de salir al escenario.

## 1 · Lo normal no molesta (20 s)
"María, de 82 años, envía 100 € a su hijo." → **Enviar dinero** → *Mi hijo Carlos* → 100 → Continuar → Enviar.
➡️ Se envía al instante. *"SilverShield no añade ninguna fricción cuando no hace falta."*

## 2 · La estafa (90 s)
"Ahora un 'técnico de Microsoft' la ha llamado." → Enviar dinero → *Otra persona* → `Soporte Técnico Global`, `ES48 1465 0100 7220 3087 6293`, **2.500**, concepto *Soporte técnico* → Enviar.
➡️ Pantalla **"Antes de enviarlo, un momento"** con los motivos explicados en lenguaje sencillo. Pulse **"Escuchar este mensaje"** si quiere enseñar la lectura en voz alta.
➡️ **Solicitar verificación con SilverShield.** La voz de ElevenLabs saluda y pregunta para qué es el dinero.
🎙️ Responda hablando: *"Me ha llamado un chico de Microsoft, dice que tengo un virus en el ordenador y que si no pago pierdo mis fotos."*
➡️ Claude detecta al falso técnico y le explica con calma por qué es un engaño. La pantalla muestra **"Le recomendamos NO enviar este dinero"**, el recuadro **"¿Por qué la hemos parado?"** con las señales en lenguaje sencillo y el botón **Llamar a Carlos**.
➡️ En el panel del operador aparece el **aviso en rojo** en directo (y a Carlos, su contacto de emergencia, le llegaría un SMS). Abra *Ver transferencia*: transcripción (con el tiempo de respuesta de cada turno), señales, nivel de riesgo, los botones **Liberar / Cancelar** (solo el operador puede usarlos, tras llamar a María) e **Imprimir informe** para la denuncia.
➡️ Fíjese en que en la pantalla de decisión **no aparecía "Conozco al destinatario"**: con una cuenta nueva, la verificación es obligatoria. *"El estafador no puede decirle: pulse ese botón."*

## 3 · La coacción (30 s, opcional)
Nueva transferencia de 3.000 € a "Mi hijo Carlos" → verificar → *"Es para mi sobrino… mira qué girasoles más bonitos."*
➡️ La pantalla solo dice "Su operación está en revisión"; quien presiona no se entera de nada. En el panel aparece **PALABRA DE AUXILIO**.

## 3b · La memoria (40 s, opcional)
Enviar dinero → *Otra persona* → `Ayesha Khan`, `PK36 SCBL 0000 0011 2345 6702`, **400**, concepto *Estudios* → verificar → *"Es para mi prima Ayesha, que vive en Pakistán. Le ayudo con los estudios de enfermería."* → *"Lo decidí yo sola, se lo prometí a su madre."* → Enviar.
➡️ Repita a la misma cuenta con **550 €**: se envía **sin preguntas** ("SilverShield ya conoce este envío habitual"). *"La primera vez pregunta; la segunda se acuerda de que tiene una prima en Pakistán."*
➡️ En el panel, **Memoria de SilverShield** muestra lo que ha aprendido. Si quiere, pruebe con **4.000 €**: vuelve a verificar, porque es mucho más de lo habitual.

## 4 · Accesibilidad (15 s)
Pulse **Letra: Muy grande** y **Alto contraste**, y enseñe los botones **Repetir** y **Prefiero escribir**.

## Plan B
- Si falla el micrófono: **Prefiero escribir** y pegue la frase.
- Si se cae internet o la API de Claude a mitad de demo: SilverShield **sigue detectando las estafas claras** con el evaluador local, pero por seguridad **no aprueba ninguna transferencia**; las legítimas quedan "No hemos podido terminar la comprobación" y retenidas. Aprovéchelo: *"si falla la IA, el sistema falla de forma segura"*.
- Si no hay internet desde el principio: quite `ANTHROPIC_API_KEY` y `ELEVENLABS_API_KEY` del `.env` y reinicie. La app funciona en modo local completo (evaluador local + voz del navegador; sale indicado en el pie).
