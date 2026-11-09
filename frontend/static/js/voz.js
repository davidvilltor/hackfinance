/* SilverShield · Módulo de voz del navegador.
 *
 * - hablar(): reproduce la voz de ElevenLabs (streaming desde el backend) y, si no
 *   está disponible, usa la síntesis de voz del navegador como respaldo.
 * - escuchar(): captura la respuesta del cliente. Usa el reconocimiento de voz del
 *   navegador (Chrome/Edge/Safari) y, si no existe, graba el audio y lo transcribe
 *   ElevenLabs Scribe en el servidor. Mientras tanto mide señales paralingüísticas
 *   (volumen, velocidad del habla, tiempo hasta empezar a hablar) que el backend
 *   usa como indicadores de estrés.
 */
(function () {
  "use strict";

  const Reconocedor = window.SpeechRecognition || window.webkitSpeechRecognition;
  const puedeGrabar = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
  const SILENCIO_FIN_MS = 2500;      // pausa que da por terminada la respuesta
  const ESPERA_INICIAL_MS = 15000;   // tiempo máximo esperando a que empiece a hablar
  const DURACION_MAX_MS = 60000;

  let usarElevenLabs = false;
  let vozNavegador = null;
  let finHablaActual = null;   // resuelve la promesa de hablar() si se interrumpe
  let audioActual = null;
  let escuchaActual = null;

  // ------------------------------------------------------------- síntesis
  function elegirVoz() {
    const voces = window.speechSynthesis ? speechSynthesis.getVoices() : [];
    vozNavegador = voces.find(v => v.lang === "es-ES") || voces.find(v => v.lang.startsWith("es")) || null;
  }
  if ("speechSynthesis" in window) {
    elegirVoz();
    speechSynthesis.onvoiceschanged = elegirVoz;
  }

  function hablarNavegador(texto) {
    return new Promise(resolve => {
      if (!("speechSynthesis" in window)) return resolve();
      speechSynthesis.cancel();
      const frase = new SpeechSynthesisUtterance(texto);
      frase.lang = "es-ES";
      frase.rate = 1.0;          // ritmo natural
      if (vozNavegador) frase.voice = vozNavegador;
      // Salvaguarda: algunos navegadores no emiten "onend" de forma fiable.
      const limite = setTimeout(() => terminar(), 2000 + texto.length * 75);
      const terminar = () => { clearTimeout(limite); resolve(); };
      frase.onend = frase.onerror = terminar;
      finHablaActual = terminar;
      speechSynthesis.speak(frase);
    });
  }

  function hablar(texto, audioUrl) {
    detener();
    if (!usarElevenLabs || !audioUrl) return hablarNavegador(texto);
    return new Promise(resolve => {
      const audio = new Audio(audioUrl);
      audioActual = audio;
      let terminado = false;
      const terminar = () => {
        if (terminado) return;
        terminado = true;
        if (audioActual === audio) audioActual = null;
        finHablaActual = null;
        resolve();
      };
      const respaldo = () => {
        if (terminado || audioActual !== audio) return terminar();
        audioActual = null;
        hablarNavegador(texto).then(terminar);
      };
      finHablaActual = terminar;
      audio.onended = terminar;
      audio.onerror = respaldo;
      audio.play().catch(respaldo);
    });
  }

  function detener() {
    if (audioActual) { audioActual.pause(); audioActual = null; }
    if ("speechSynthesis" in window) speechSynthesis.cancel();
    if (finHablaActual) { const fin = finHablaActual; finHablaActual = null; fin(); }
  }

  // ------------------------------------------------------------- medidor de micrófono
  async function iniciarMedidor(onNivel) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
      });
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      // A partir del 2.º turno la escucha arranca sola (sin clic) y el navegador
      // puede crear el AudioContext en pausa: se intenta reanudar.
      if (ctx.state === "suspended") ctx.resume().catch(() => {});
      const analizador = ctx.createAnalyser();
      analizador.fftSize = 1024;
      ctx.createMediaStreamSource(stream).connect(analizador);
      const muestras = new Float32Array(analizador.fftSize);
      const medidor = {
        stream, inicio: performance.now(), primerSonido: null, ultimoSonido: null,
        suma: 0, n: 0, activo: true,
        volumenMedio() { return this.n ? Math.round((this.suma / this.n) * 100) : null; },
        /** false si el AudioContext no llegó a funcionar: entonces "no hubo sonido" no es fiable. */
        fiable() { return ctx.state === "running"; },
        parar() {
          if (!this.activo) return;
          this.activo = false;
          stream.getTracks().forEach(p => p.stop());
          ctx.close().catch(() => {});
          if (onNivel) onNivel(0);
        },
      };
      const bucle = () => {
        if (!medidor.activo) return;
        analizador.getFloatTimeDomainData(muestras);
        let energia = 0;
        for (let i = 0; i < muestras.length; i++) energia += muestras[i] * muestras[i];
        const rms = Math.sqrt(energia / muestras.length);
        const nivel = Math.min(1, rms * 8);
        if (onNivel) onNivel(nivel);
        if (rms > 0.02) {
          const ahora = performance.now();
          if (medidor.primerSonido === null) medidor.primerSonido = ahora;
          medidor.ultimoSonido = ahora;
          medidor.suma += nivel;
          medidor.n++;
        }
        requestAnimationFrame(bucle);
      };
      bucle();
      return medidor;
    } catch (error) {
      if (error && error.name === "NotAllowedError") throw new Error("not-allowed");
      return null;   // sin medidor: seguimos sin métricas acústicas
    }
  }

  function calcularSenales(texto, medidor, tInicio, tPrimer, tUltimo) {
    const palabras = texto.trim() ? texto.trim().split(/\s+/).length : 0;
    const primer = (medidor && medidor.primerSonido) || tPrimer;
    const ultimo = (medidor && medidor.ultimoSonido) || tUltimo;
    const senales = {};
    if (primer) senales.silencio_inicial_s = Math.max(0, (primer - tInicio) / 1000);
    if (primer && ultimo && ultimo > primer) {
      const duracion = (ultimo - primer) / 1000;
      senales.duracion_s = Math.round(duracion * 10) / 10;
      if (palabras >= 4 && duracion >= 1) senales.palabras_por_minuto = Math.round(palabras / duracion * 60);
    }
    const volumen = medidor && medidor.volumenMedio();
    if (volumen !== null && volumen !== undefined) senales.volumen_medio = volumen;
    return senales;
  }

  // ------------------------------------------------------------- reconocimiento del navegador
  // Chrome solo admite un reconocedor activo por página: antes de crear otro hay
  // que esperar a que el anterior se haya cerrado de verdad (evento "end").
  let reconocedorVivo = null;   // { rec, cerrado: Promise }

  function crearReconocedor() {
    const rec = new Reconocedor();
    rec.lang = "es-ES";
    rec.continuous = true;
    rec.interimResults = true;
    let avisarCierre;
    const vivo = { rec, cerrado: new Promise(r => { avisarCierre = r; }) };
    rec.addEventListener("end", () => {
      avisarCierre();
      if (reconocedorVivo === vivo) reconocedorVivo = null;
    });
    reconocedorVivo = vivo;
    return rec;
  }

  async function liberarReconocedor() {
    const anterior = reconocedorVivo;
    if (!anterior) return;
    try { anterior.rec.abort(); } catch (_) { /* ya estaba parado */ }
    await Promise.race([anterior.cerrado, new Promise(r => setTimeout(r, 1500))]);
    reconocedorVivo = null;
  }

  const espera = ms => new Promise(r => setTimeout(r, ms));
  const ERRORES_FATALES = ["not-allowed", "service-not-allowed", "audio-capture", "language-not-supported"];

  function escucharNavegador(medidor, { onParcial, onFinCaptura } = {}) {
    return new Promise((resolve, reject) => {
      const tInicio = performance.now();
      let rec = null;
      let textoFinal = "", ultimoParcial = "", tPrimer = null, tUltimo = null;
      let error = null, cancelado = false, temporizador = null, terminado = false;
      let salvaguarda = null, pidioParar = false, reintentos = 0;

      // rec.stop() no siempre provoca "end"; tras un margen se cierra a la fuerza.
      const parar = () => {
        if (pidioParar) return;
        pidioParar = true;
        if (onFinCaptura) onFinCaptura();
        try { if (rec) rec.stop(); } catch (_) { /* no había arrancado */ }
        salvaguarda = setTimeout(() => {
          console.info("[voz] el reconocedor no respondió a stop(); se cierra a la fuerza");
          cerrar();
        }, 1500);
      };
      const programarFin = ms => { clearTimeout(temporizador); temporizador = setTimeout(parar, ms); };
      const limiteTotal = setTimeout(parar, DURACION_MAX_MS);

      const cerrar = () => {
        if (terminado) return;
        terminado = true;
        clearTimeout(temporizador);
        clearTimeout(limiteTotal);
        clearTimeout(salvaguarda);
        // Si el reconocedor sigue vivo, se aborta para que no bloquee la siguiente escucha.
        if (rec) { rec.onresult = rec.onerror = rec.onend = null; try { rec.abort(); } catch (_) { /* */ } }
        if (medidor) medidor.parar();
        if (escuchaActual === control) escuchaActual = null;
        if (cancelado) return resolve({ texto: "", cancelado: true });
        const texto = (textoFinal.trim() || ultimoParcial).trim();
        console.info("[voz] fin de escucha", { texto, error, reintentos });
        if (error && !texto) return reject(new Error(error));
        resolve({ texto, senales: calcularSenales(texto, medidor, tInicio, tPrimer, tUltimo) });
      };

      const arrancar = async () => {
        await liberarReconocedor();
        if (terminado) return;
        rec = crearReconocedor();
        // Los resultados de cada sesión empiezan desde cero; se acumula lo ya confirmado.
        let finalesSesion = "";
        rec.onstart = () => console.info("[voz] escuchando…");
        rec.onresult = evento => {
          let provisional = "";
          finalesSesion = "";
          for (let i = 0; i < evento.results.length; i++) {
            const r = evento.results[i];
            if (r.isFinal) finalesSesion += r[0].transcript + " ";
            else provisional += r[0].transcript;
          }
          const ahora = performance.now();
          if (tPrimer === null) tPrimer = ahora;
          tUltimo = ahora;
          ultimoParcial = (textoFinal + finalesSesion + provisional).trim();
          if (onParcial) onParcial(ultimoParcial);
          programarFin(SILENCIO_FIN_MS);
        };
        rec.onerror = evento => {
          console.info("[voz] error del reconocedor:", evento.error);
          if (evento.error !== "no-speech" && evento.error !== "aborted") error = evento.error;
        };
        rec.onend = () => {
          textoFinal += finalesSesion;
          finalesSesion = "";
          if (terminado) return;
          const hayTexto = !!(textoFinal.trim() || ultimoParcial);
          const quedaTiempo = performance.now() - tInicio < ESPERA_INICIAL_MS;
          // Chrome a veces corta la escucha por su cuenta (red, reconocedor ocupado…).
          // Si el cliente aún no ha dicho nada, se vuelve a arrancar en silencio.
          if (!pidioParar && !cancelado && !hayTexto && quedaTiempo && reintentos < 5
              && !ERRORES_FATALES.includes(error)) {
            reintentos++;
            error = null;
            console.info("[voz] el reconocedor se cerró solo; reintento", reintentos);
            espera(300).then(arrancar);
            return;
          }
          cerrar();
        };
        try {
          rec.start();
        } catch (e) {
          console.info("[voz] no se pudo arrancar el reconocedor:", e);
          error = "start-failed";
          cerrar();
        }
      };

      const control = {
        terminar: parar,
        cancelar: () => { cancelado = true; cerrar(); },
      };
      escuchaActual = control;
      programarFin(ESPERA_INICIAL_MS);
      arrancar();
    });
  }

  // ------------------------------------------------------------- grabación + ElevenLabs Scribe
  function escucharGrabando(medidor, { onFinCaptura } = {}) {
    return new Promise((resolve, reject) => {
      if (!medidor) return reject(new Error("sin-microfono"));
      const grabadora = new MediaRecorder(medidor.stream);
      const trozos = [];
      const tInicio = performance.now();
      let cancelado = false;

      const vigilancia = setInterval(() => {
        const ahora = performance.now();
        const sinEmpezar = medidor.primerSonido === null && ahora - tInicio > ESPERA_INICIAL_MS;
        const silencio = medidor.ultimoSonido !== null && ahora - medidor.ultimoSonido > SILENCIO_FIN_MS;
        // Si el medidor no funciona, no se puede detectar el silencio: solo el límite total.
        const medible = medidor.fiable();
        if ((medible && (sinEmpezar || silencio)) || ahora - tInicio > DURACION_MAX_MS) terminar();
      }, 200);
      const pararGrabadora = () => { if (grabadora.state !== "inactive") grabadora.stop(); };
      let avisado = false;
      const terminar = () => {
        if (!avisado && onFinCaptura) { avisado = true; onFinCaptura(); }
        pararGrabadora();
      };

      grabadora.ondataavailable = e => { if (e.data.size) trozos.push(e.data); };
      grabadora.onstop = async () => {
        clearInterval(vigilancia);
        if (escuchaActual === control) escuchaActual = null;
        const senalesBase = calcularSenales("", medidor, tInicio, null, null);
        const huboSonido = medidor.primerSonido !== null || !medidor.fiable();
        medidor.parar();
        if (cancelado) return resolve({ texto: "", cancelado: true });
        if (!huboSonido) return resolve({ texto: "", senales: senalesBase });
        try {
          const blob = new Blob(trozos, { type: grabadora.mimeType || "audio/webm" });
          // Límite de tiempo: si el servidor no responde, la escucha no puede quedarse colgada.
          const corte = new AbortController();
          const limite = setTimeout(() => corte.abort(), 30000);
          let r;
          try {
            r = await fetch("/api/voz/transcribir", {
              method: "POST", headers: { "Content-Type": blob.type }, body: blob, signal: corte.signal,
            });
          } finally {
            clearTimeout(limite);
          }
          if (!r.ok) throw new Error("transcripcion");
          const { texto } = await r.json();
          const senales = { ...senalesBase };
          const palabras = texto.trim() ? texto.trim().split(/\s+/).length : 0;
          if (senales.duracion_s >= 1 && palabras >= 4) {
            senales.palabras_por_minuto = Math.round(palabras / senales.duracion_s * 60);
          }
          resolve({ texto, senales });
        } catch (e) {
          reject(e);
        }
      };

      const control = {
        terminar,
        cancelar: () => { cancelado = true; pararGrabadora(); },
      };
      escuchaActual = control;
      grabadora.start(250);
    });
  }

  // ------------------------------------------------------------- API pública
  function escuchar(opciones = {}) {
    cancelarEscucha();
    if (!puedeEscuchar()) return Promise.reject(new Error("sin-reconocimiento"));
    return new Promise((resolve, reject) => {
      // Mientras se abre el micrófono (incluido el aviso de permisos), pulsar
      // "He terminado de hablar" o cancelar debe responder al momento, aunque
      // getUserMedia tarde o no conteste nunca.
      let abandonado = false;
      const pendiente = {
        terminar: () => { abandonado = true; escuchaActual = null; resolve({ texto: "", senales: {} }); },
        cancelar: () => { abandonado = true; escuchaActual = null; resolve({ texto: "", cancelado: true }); },
      };
      escuchaActual = pendiente;
      iniciarMedidor(opciones.onNivel).then(medidor => {
        if (abandonado) { if (medidor) medidor.parar(); return; }
        escuchaActual = null;
        const escucha = Reconocedor ? escucharNavegador(medidor, opciones) : escucharGrabando(medidor, opciones);
        escucha.then(resolve, reject);
      }, error => {
        if (abandonado) return;
        escuchaActual = null;
        reject(error);
      });
    });
  }

  function terminarEscucha() { if (escuchaActual) escuchaActual.terminar(); }
  function cancelarEscucha() { if (escuchaActual) escuchaActual.cancelar(); }
  function puedeEscuchar() { return !!Reconocedor || (puedeGrabar && usarElevenLabs); }

  window.Voz = {
    configurar(opciones) { usarElevenLabs = !!opciones.elevenlabs; },
    hablar,
    leer: hablarNavegador,
    detener,
    escuchar,
    terminarEscucha,
    cancelarEscucha,
    puedeEscuchar,
    escuchando: () => escuchaActual !== null,
  };
})();
