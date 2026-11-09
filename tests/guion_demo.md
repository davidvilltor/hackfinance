# 🎬 Guion de la demo en vivo (unos 3 minutos)

**Preparación**
- Servidor arrancado con las claves de Anthropic y ElevenLabs en `.env`. El pie de la app debe mostrar "IA Claude activa" y "Voz ElevenLabs".
- Ventana 1 (proyector): <http://localhost:8000>, en Chrome o Edge, con permiso de micrófono concedido.
- Ventana 2 (al lado, o en un móvil): <http://localhost:8000/panel>, el panel de Carlos, el hijo. Pulse **"Reiniciar datos de la demo"**.
- Haga una prueba de audio antes de salir al escenario.

## 1 · Lo normal no molesta (20 s)
"María, de 82 años, envía 100 € a su hijo." → **Enviar dinero** → *Mi hijo Carlos* → 100 → Continuar → Enviar.
➡️ Se envía al instante. *"SilverShield no añade ninguna fricción cuando no hace falta."*

## 2 · La estafa (90 s)
"Ahora un 'técnico de Microsoft' la ha llamado." → Enviar dinero → *Otra persona* → `Soporte Técnico Global`, `ES48 1465 0100 7220 3087 6293`, **2.500**, concepto *Soporte técnico* → Enviar.
➡️ Pantalla **"Antes de enviarlo, un momento"** con los motivos explicados en lenguaje sencillo. Pulse **"Escuchar este mensaje"** si quiere enseñar la lectura en voz alta.
➡️ **Solicitar verificación con SilverShield.** La voz de ElevenLabs saluda y pregunta para qué es el dinero.
🎙️ Responda hablando: *"Me ha llamado un chico de Microsoft, dice que tengo un virus en el ordenador y que si no pago pierdo mis fotos."*
➡️ Claude detecta al falso técnico y le explica con calma por qué es un engaño. La pantalla muestra **"Le recomendamos NO enviar este dinero"** y el botón **Llamar a Carlos**.
➡️ En el panel de Carlos aparece el **aviso en rojo** en directo. Abra *Ver transferencia*: transcripción, señales, nivel de riesgo y el botón **Imprimir informe** para la denuncia.

## 3 · La coacción (30 s, opcional)
Nueva transferencia de 3.000 € a "Mi hijo Carlos" → verificar → *"Es para mi sobrino… mira qué girasoles más bonitos."*
➡️ La pantalla solo dice "Su operación está en revisión"; quien presiona no se entera de nada. En el panel aparece **PALABRA DE AUXILIO**.

## 4 · Accesibilidad (15 s)
Pulse **Letra: Muy grande** y **Alto contraste**, y enseñe los botones **Repetir** y **Prefiero escribir**.

## Plan B
- Si falla el micrófono: **Prefiero escribir** y pegue la frase.
- Si se cae internet o la API: la app sigue funcionando con el evaluador local y la voz del navegador (sale indicado en el pie). La demo funciona igual.
