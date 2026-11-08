# 🎬 Guion de Demostración: SilverShield
**Duración total:** 3:30 - 4:00 minutos  
**Roles:** Presentador/a, "Juan" (Usuario mayor, puede ser actuado o simulado), "Estafador" (Voz en off o texto).

## ⏱️ Minuto 0:00 - 0:45 | El Gancho (El Problema)
**Presentador:** 
"Cada año, miles de personas mayores pierden sus ahorros de toda la vida en cuestión de minutos. No por falta de inteligencia, sino por la sofisticación de la ingeniería social: urgencia, miedo y suplantación de identidad. 
Hoy presentamos **SilverShield**: no es solo un detector de fraude, es un guardián empático que escucha, analiza el estrés vocal y actúa en tiempo real para proteger a quienes más lo necesitan."

## ⏱️ Minuto 0:45 - 1:15 | La Solución (Cómo funciona)
**Presentador:** 
"SilverShield se integra en el flujo bancario. Analiza el contexto de la conversación en tiempo real usando IA (Claude 3 Opus), detecta patrones de estafa, mide el estrés vocal del usuario y, si hay peligro, interrumpe la operación con una voz calmada y notifica automáticamente a un familiar de confianza. Veámoslo en acción."

## ⏱️ Minuto 1:15 - 2:45 | La Demo en Vivo (El Clímax)
*(El presentador comparte pantalla mostrando el `index.html` de SilverShield)*

**Presentador:** 
"Imaginemos a Juan. Está en su web bancaria y recibe una llamada: *'Señor, somos de Microsoft, su ordenador tiene un virus y vamos a bloquear su cuenta. Necesito que descargue AnyDesk ahora mismo y me diga el código SMS que le acaba de llegar'*."

*(Acción en pantalla: El presentador escribe o dicta en el micrófono de la app: "Me dice que soy de Microsoft, que tengo un virus, que descargue AnyDesk ya y que le dé el código del banco o me bloquean la cuenta". Asegúrate de hablar con un tono ligeramente acelerado para activar el detector de estrés).*

**Presentador:** 
"Observen lo que sucede en tiempo real:
1. El **medidor de estrés** detecta palabras clave ('bloqueo', 'ya', 'Microsoft') y sube a 'Pánico / Alta Coacción'.
2. El **motor de fraude** identifica la suplantación y la petición de AnyDesk.
3. El sistema **BLOQUEA** el botón de transferencia instantáneamente.
4. SilverShield genera una **respuesta de voz calmada** (se reproduce el audio) tranquilizando a Juan.
5. Y aquí está la clave: el sistema ha enviado una **alerta automática** al familiar."

*(Señalar el panel de logs en la parte inferior de la web, donde aparece el registro en rojo: BLOQUEADO).*

## ⏱️ Minuto 2:45 - 3:30 | Cierre e Impacto
**Presentador:** 
"En menos de 3 segundos, SilverShield ha evitado un desastre financiero. 
Nuestra tecnología combina:
- **IA de razonamiento avanzado** (Anthropic) para entender el contexto, no solo palabras clave.
- **Síntesis de voz empática** (ElevenLabs) para calmar, no para asustar.
- **Análisis multimodal** (texto + estrés vocal).

SilverShield no es solo una herramienta, es tranquilidad para las familias y responsabilidad social para la banca. Gracias."

## 💡 Consejos para el día de la demo:
1. **Prueba el audio:** Asegúrate de que el navegador tenga permiso para reproducir audio automáticamente o ten listo el clic para reproducir la respuesta de ElevenLabs.
2. **Plan B:** Si la API de ElevenLabs va lenta, ten un archivo de audio `.mp3` pregrabado en la carpeta `data/` que puedas reproducir manualmente como fallback.
3. **Modo Accesible:** Haz clic en el botón "🔍 A+ Letra Grande" durante la demo para mostrar que el producto está realmente pensado para personas mayores.
