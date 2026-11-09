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
      frase.rate = 0.9;          // algo más lento de lo normal
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
      const analizador = ctx.createAnalyser();
      analizador.fftSize = 1024;
      ctx.createMediaStreamSource(stream).connect(analizador);
      const muestras = new Float32Array(analizador.fftSize);
      const medidor = {
        stream, inicio: performance.now(), primerSonido: null, ultimoSonido: null,
        suma: 0, n: 0, activo: true,
        volumenMedio() { return this.n ? Math.round((this.suma / this.n) * 100) : null; },
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
  function escucharNavegador(medidor, onParcial) {
    return new Promise((resolve, reject) => {
      const rec = new Reconocedor();
      rec.lang = "es-ES";
      rec.continuous = true;
      rec.interimResults = true;
      const tInicio = performance.now();
      let textoFinal = "", ultimoParcial = "", tPrimer = null, tUltimo = null;
      let error = null, cancelado = false, temporizador = null;

      const programarFin = ms => { clearTimeout(temporizador); temporizador = setTimeout(() => rec.stop(), ms); };
      const limiteTotal = setTimeout(() => rec.stop(), DURACION_MAX_MS);

      rec.onresult = evento => {
        let provisional = "";
        for (let i = evento.resultIndex; i < evento.results.length; i++) {
          const resultado = evento.results[i];
          if (resultado.isFinal) textoFinal += resultado[0].transcript + " ";
          else provisional += resultado[0].transcript;
        }
        const ahora = performance.now();
        if (tPrimer === null) tPrimer = ahora;
        tUltimo = ahora;
        ultimoParcial = (textoFinal + provisional).trim();
        if (onParcial) onParcial(ultimoParcial);
        programarFin(SILENCIO_FIN_MS);
      };
      rec.onerror = evento => {
        if (evento.error !== "no-speech" && evento.error !== "aborted") error = evento.error;
      };
      rec.onend = () => {
        clearTimeout(temporizador);
        clearTimeout(limiteTotal);
        if (medidor) medidor.parar();
        escuchaActual = null;
        if (cancelado) return resolve({ texto: "", cancelado: true });
        const texto = (textoFinal.trim() || ultimoParcial).trim();
        if (error && !texto) return reject(new Error(error));
        resolve({ texto, senales: calcularSenales(texto, medidor, tInicio, tPrimer, tUltimo) });
      };

      escuchaActual = {
        terminar: () => rec.stop(),
        cancelar: () => { cancelado = true; rec.abort(); },
      };
      programarFin(ESPERA_INICIAL_MS);
      rec.start();
    });
  }

  // ------------------------------------------------------------- grabación + ElevenLabs Scribe
  function escucharGrabando(medidor) {
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
        if (sinEmpezar || silencio || ahora - tInicio > DURACION_MAX_MS) terminar();
      }, 200);
      const terminar = () => { if (grabadora.state !== "inactive") grabadora.stop(); };

      grabadora.ondataavailable = e => { if (e.data.size) trozos.push(e.data); };
      grabadora.onstop = async () => {
        clearInterval(vigilancia);
        escuchaActual = null;
        const senalesBase = calcularSenales("", medidor, tInicio, null, null);
        const huboSonido = medidor.primerSonido !== null;
        medidor.parar();
        if (cancelado) return resolve({ texto: "", cancelado: true });
        if (!huboSonido) return resolve({ texto: "", senales: senalesBase });
        try {
          const blob = new Blob(trozos, { type: grabadora.mimeType || "audio/webm" });
          const r = await fetch("/api/voz/transcribir", {
            method: "POST", headers: { "Content-Type": blob.type }, body: blob,
          });
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

      escuchaActual = {
        terminar,
        cancelar: () => { cancelado = true; terminar(); },
      };
      grabadora.start(250);
    });
  }

  // ------------------------------------------------------------- API pública
  async function escuchar({ onParcial, onNivel } = {}) {
    cancelarEscucha();
    if (!puedeEscuchar()) throw new Error("sin-reconocimiento");
    const medidor = await iniciarMedidor(onNivel);
    if (Reconocedor) return escucharNavegador(medidor, onParcial);
    return escucharGrabando(medidor);
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
