/* SilverShield · Aplicación del cliente (banca accesible). */
(function () {
  "use strict";

  const $ = sel => document.querySelector(sel);
  const $$ = sel => Array.from(document.querySelectorAll(sel));

  const estado = {
    cuenta: null,
    beneficiarios: [],
    borrador: null,          // datos del formulario pendientes de enviar
    transferencia: null,
    evaluacion: null,
    ultimoAsistente: null,
    modoTexto: false,
    finalizada: false,
    procesando: false,
    hablando: false,
    escuchando: false,
  };

  // ================================================================ utilidades
  // useGrouping "always": en español Intl no separa los miles de números de 4 cifras (2500 €).
  const formatoEuros = new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR", useGrouping: "always" });
  const euros = n => formatoEuros.format(n);
  const formatoFecha = new Intl.DateTimeFormat("es-ES", { day: "numeric", month: "long" });

  // "Carlos (hijo)", "Lucía (vecina)"... o solo el nombre si no se indicó la relación.
  function describirContacto(cuenta) {
    const nombre = cuenta.contacto_nombre || "su contacto de emergencia";
    return cuenta.contacto_relacion ? `${nombre} (${cuenta.contacto_relacion})` : nombre;
  }

  function formatearIban(iban) {
    return iban.replace(/\s+/g, "").toUpperCase().replace(/(.{4})/g, "$1 ").trim();
  }

  function ibanValido(iban) {
    const limpio = iban.replace(/[\s-]/g, "").toUpperCase();
    if (!/^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$/.test(limpio)) return false;
    const reordenado = limpio.slice(4) + limpio.slice(0, 4);
    let resto = 0;
    for (const c of reordenado) {
      const valor = parseInt(c, 36).toString();
      for (const d of valor) resto = (resto * 10 + Number(d)) % 97;
    }
    return resto === 1;
  }

  /** Interpreta importes escritos a la española: "1.500", "1.500,50", "300,5", "300.50". */
  function leerImporte(texto) {
    let t = (texto || "").replace(/[€\s]/g, "");
    if (!t) return NaN;
    if (t.includes(",")) t = t.replace(/\./g, "").replace(",", ".");
    else if (/^\d{1,3}(\.\d{3})+$/.test(t)) t = t.replace(/\./g, "");
    if (!/^\d+(\.\d{1,2})?$/.test(t)) return NaN;
    return parseFloat(t);
  }

  async function api(ruta, { metodo = "GET", cuerpo } = {}) {
    let respuesta;
    try {
      respuesta = await fetch(ruta, {
        method: metodo,
        headers: cuerpo ? { "Content-Type": "application/json" } : undefined,
        body: cuerpo ? JSON.stringify(cuerpo) : undefined,
      });
    } catch (e) {
      throw new Error("No hay conexión con el banco. Compruebe su conexión a internet e inténtelo de nuevo.");
    }
    const datos = await respuesta.json().catch(() => ({}));
    if (!respuesta.ok) {
      const detalle = Array.isArray(datos.detail) ? "Revise los datos introducidos." : datos.detail;
      const error = new Error(detalle || "Ha ocurrido un problema. Inténtelo de nuevo.");
      error.estado = respuesta.status;
      throw error;
    }
    return datos;
  }

  function mostrarError(mensaje) {
    const banner = $("#banner-error");
    banner.textContent = mensaje;
    banner.hidden = false;
    banner.scrollIntoView({ behavior: "smooth", block: "center" });
  }
  function ocultarError() { $("#banner-error").hidden = true; }

  /** Pone un botón en estado "cargando" mientras dura la promesa. */
  async function conCarga(boton, textoCarga, accion) {
    const original = boton.innerHTML;
    boton.disabled = true;
    boton.setAttribute("aria-busy", "true");
    boton.innerHTML = `<span class="girando" aria-hidden="true"></span> ${textoCarga}`;
    try {
      return await accion();
    } finally {
      boton.disabled = false;
      boton.removeAttribute("aria-busy");
      boton.innerHTML = original;
    }
  }

  // ================================================================ navegación
  const TITULOS = {
    inicio: "Inicio", formulario: "Nueva transferencia", resumen: "Revisar transferencia",
    decision: "Confirmar transferencia", verificacion: "Verificación SilverShield", resultado: "Resultado",
  };

  function mostrarPantalla(nombre) {
    if (nombre !== "verificacion") { Voz.detener(); Voz.cancelarEscucha(); }
    ocultarError();
    $$(".pantalla").forEach(p => { p.hidden = p.id !== `pantalla-${nombre}`; });
    document.title = `${TITULOS[nombre]} · SilverBank`;
    window.scrollTo(0, 0);
    const titulo = $(`#pantalla-${nombre} h1`);
    if (titulo) titulo.focus({ preventScroll: true });
  }

  $$("[data-ir]").forEach(boton => boton.addEventListener("click", () => {
    const destino = boton.dataset.ir;
    if (destino === "inicio") cargarCuenta();
    mostrarPantalla(destino);
  }));

  // ================================================================ ajustes de accesibilidad
  const TAMANOS = [["", "Normal"], ["letra-grande", "Grande"], ["letra-muy-grande", "Muy grande"]];
  let indiceTamano = Number(localStorage.getItem("ss-letra") || 0);

  function aplicarTamano() {
    TAMANOS.forEach(([clase]) => clase && document.documentElement.classList.remove(clase));
    const [clase, etiqueta] = TAMANOS[indiceTamano] || TAMANOS[0];
    if (clase) document.documentElement.classList.add(clase);
    $("#btn-letra").textContent = `Letra: ${etiqueta}`;
  }
  $("#btn-letra").addEventListener("click", () => {
    indiceTamano = (indiceTamano + 1) % TAMANOS.length;
    localStorage.setItem("ss-letra", indiceTamano);
    aplicarTamano();
  });

  function aplicarContraste(activo) {
    document.body.classList.toggle("alto-contraste", activo);
    $("#btn-contraste").setAttribute("aria-pressed", String(activo));
  }
  $("#btn-contraste").addEventListener("click", () => {
    const activo = !document.body.classList.contains("alto-contraste");
    localStorage.setItem("ss-contraste", activo ? "1" : "0");
    aplicarContraste(activo);
  });

  // ================================================================ inicio
  async function cargarEstadoServicios() {
    try {
      const info = await api("/api/estado");
      Voz.configurar({ elevenlabs: info.voz_elevenlabs });
      $("#punto-ia").classList.toggle("on", info.ia);
      $("#txt-ia").textContent = info.ia ? "IA Claude activa" : "IA en modo local";
      $("#punto-voz").classList.toggle("on", info.voz_elevenlabs);
      $("#txt-voz").textContent = info.voz_elevenlabs ? "Voz ElevenLabs" : "Voz del navegador";
    } catch (e) { /* el pie es informativo; no bloquea */ }
  }

  async function cargarCuenta() {
    try {
      const datos = await api("/api/cuenta");
      estado.cuenta = datos.cuenta;
      estado.beneficiarios = datos.beneficiarios;
      $$('[data-dato="nombre"]').forEach(e => { e.textContent = datos.cuenta.nombre_corto; });
      $$('[data-dato="saldo"]').forEach(e => { e.textContent = euros(datos.cuenta.saldo); });
      $$('[data-dato="contacto"]').forEach(e => {
        e.textContent = describirContacto(datos.cuenta);
      });
      $$('[data-dato="tel-contacto"]').forEach(e => { e.href = `tel:${datos.cuenta.contacto_telefono.replace(/\s/g, "")}`; });
      pintarMovimientos(datos.movimientos);
      pintarBeneficiarios();
    } catch (e) {
      mostrarError(e.message);
    }
  }

  function pintarMovimientos(movimientos) {
    const lista = $("#lista-movimientos");
    lista.replaceChildren();
    if (!movimientos.length) {
      const li = document.createElement("li");
      li.textContent = "Todavía no hay movimientos.";
      lista.append(li);
      return;
    }
    for (const m of movimientos) {
      const li = document.createElement("li");
      const izquierda = document.createElement("span");
      izquierda.textContent = m.beneficiario_nombre;
      const fecha = document.createElement("span");
      fecha.className = "fecha";
      fecha.textContent = `${formatoFecha.format(new Date(m.fecha))}${m.concepto ? " · " + m.concepto : ""}`;
      izquierda.append(fecha);
      const importe = document.createElement("span");
      importe.className = "importe";
      importe.textContent = `− ${euros(m.importe)}`;
      importe.setAttribute("aria-label", `${euros(m.importe)} enviados`);
      li.append(izquierda, importe);
      lista.append(li);
    }
  }

  $("#btn-nueva").addEventListener("click", () => {
    $("#form-transferencia").reset();
    pintarBeneficiarios();
    limpiarErroresFormulario();
    mostrarPantalla("formulario");
  });

  // ================================================================ formulario
  function pintarBeneficiarios() {
    const contenedor = $("#lista-destinatarios");
    contenedor.replaceChildren();
    const opciones = [
      ...estado.beneficiarios.map(b => ({
        valor: String(b.id), titulo: b.alias || b.nombre,
        detalle: `${b.nombre} · cuenta acabada en ${b.iban.slice(-4)}`, inicial: b.nombre[0],
      })),
      { valor: "nuevo", titulo: "Otra persona", detalle: "Escribiré su número de cuenta", inicial: "+" },
    ];
    for (const o of opciones) {
      const label = document.createElement("label");
      label.className = "opcion-destinatario";
      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "destinatario";
      radio.value = o.valor;
      const avatar = document.createElement("span");
      avatar.className = "avatar";
      avatar.setAttribute("aria-hidden", "true");
      avatar.textContent = o.inicial.toUpperCase();
      const textos = document.createElement("span");
      const nombre = document.createElement("span");
      nombre.className = "nombre";
      nombre.textContent = o.titulo;
      const detalle = document.createElement("span");
      detalle.className = "detalle";
      detalle.textContent = o.detalle;
      textos.append(nombre, detalle);
      label.append(radio, avatar, textos);
      contenedor.append(label);
      radio.addEventListener("change", () => {
        $("#bloque-nuevo").hidden = radio.value !== "nuevo";
        ponerErrorCampo("destinatario", null);
      });
    }
    $("#bloque-nuevo").hidden = true;
  }

  function ponerErrorCampo(campo, mensaje) {
    const caja = $(`#error-${campo}`);
    const entrada = $(`#campo-${campo}`);
    if (caja) {
      caja.hidden = !mensaje;
      caja.textContent = mensaje ? `⚠ ${mensaje}` : "";
    }
    if (entrada) entrada.setAttribute("aria-invalid", mensaje ? "true" : "false");
  }

  function limpiarErroresFormulario() {
    ["nombre", "iban", "importe"].forEach(c => ponerErrorCampo(c, null));
    const aviso = $("#error-destinatario");
    if (aviso) aviso.remove();
  }

  $("#form-transferencia").addEventListener("submit", evento => {
    evento.preventDefault();
    limpiarErroresFormulario();
    const elegido = document.querySelector('input[name="destinatario"]:checked');
    let primerError = null;
    const marcar = (campo, mensaje) => {
      ponerErrorCampo(campo, mensaje);
      primerError = primerError || $(`#campo-${campo}`);
    };

    let nombre, iban;
    if (!elegido) {
      const aviso = document.createElement("div");
      aviso.id = "error-destinatario";
      aviso.className = "error-campo";
      aviso.setAttribute("role", "alert");
      aviso.textContent = "⚠ Elija a quién quiere enviar el dinero.";
      $("#lista-destinatarios").after(aviso);
      primerError = primerError || document.querySelector('input[name="destinatario"]');
    } else if (elegido.value === "nuevo") {
      nombre = $("#campo-nombre").value.trim();
      iban = $("#campo-iban").value;
      if (nombre.length < 2) marcar("nombre", "Escriba el nombre de quien recibe el dinero.");
      if (!ibanValido(iban)) marcar("iban", "Este número de cuenta no es correcto. Revíselo con calma.");
    } else {
      const b = estado.beneficiarios.find(x => String(x.id) === elegido.value);
      nombre = b.nombre;
      iban = b.iban;
    }

    const importe = leerImporte($("#campo-importe").value);
    if (isNaN(importe) || importe <= 0) marcar("importe", "Escriba la cantidad, por ejemplo: 150 o 150,50.");
    else if (estado.cuenta && importe > estado.cuenta.saldo) {
      marcar("importe", `No tiene suficiente dinero. Su saldo es ${euros(estado.cuenta.saldo)}.`);
    }

    if (primerError) { primerError.focus(); return; }

    estado.borrador = {
      beneficiario_nombre: nombre,
      iban: iban.replace(/[\s-]/g, "").toUpperCase(),
      importe,
      concepto: $("#campo-concepto").value.trim(),
    };
    $('[data-resumen="importe"]').textContent = euros(importe);
    $('[data-resumen="nombre"]').textContent = nombre;
    $('[data-resumen="iban"]').textContent = formatearIban(estado.borrador.iban);
    $('[data-resumen="concepto"]').textContent = estado.borrador.concepto || "(sin concepto)";
    mostrarPantalla("resumen");
  });

  // ================================================================ envío y decisión
  $("#btn-enviar").addEventListener("click", evento => conCarga(evento.currentTarget, "Enviando…", async () => {
    try {
      const datos = await api("/api/transferencias", { metodo: "POST", cuerpo: estado.borrador });
      estado.transferencia = datos.transferencia;
      estado.evaluacion = datos.evaluacion;
      if (datos.transferencia.estado === "completada") {
        mostrarResultadoOk(datos.transferencia, datos.saldo);
      } else {
        mostrarDecision(datos.evaluacion);
      }
    } catch (e) {
      mostrarError(e.message);
    }
  }));

  function mostrarDecision(evaluacion) {
    const lista = $("#lista-motivos");
    lista.replaceChildren(...evaluacion.motivos.map(m => {
      const li = document.createElement("li");
      li.textContent = m.texto;
      return li;
    }));
    $("#aviso-decision").classList.toggle("alto", evaluacion.nivel === "alto");
    // Enviar sin verificar solo se ofrece a destinatarios habituales sin señales graves
    // (el servidor lo vuelve a comprobar).
    const directo = !!evaluacion.permite_autorizacion_directa;
    $("#btn-autorizar-directo").hidden = !directo;
    $("#nota-verificacion").hidden = directo;
    mostrarPantalla("decision");
  }

  $("#btn-escuchar-motivos").addEventListener("click", () => {
    const motivos = estado.evaluacion.motivos.map(m => m.texto).join(" ");
    Voz.leer(
      `Antes de enviarlo, un momento. Hemos notado algo en esta transferencia. ${motivos} ` +
      (estado.evaluacion.permite_autorizacion_directa
        ? "Puede pedir que SilverShield la compruebe con usted, o, si conoce al destinatario, autorizarla directamente."
        : "Como es la primera vez que envía dinero a esta cuenta, o hay señales de estafa, hace falta comprobarla con SilverShield. Solo es un minuto.")
    );
  });

  async function autorizar(boton) {
    return conCarga(boton, "Enviando…", async () => {
      try {
        const datos = await api(`/api/transferencias/${estado.transferencia.id}/autorizar`, { metodo: "POST" });
        mostrarResultadoOk(datos.transferencia, datos.saldo);
      } catch (e) {
        mostrarError(e.message);
      }
    });
  }

  async function cancelar(boton) {
    return conCarga(boton, "Cancelando…", async () => {
      try {
        await api(`/api/transferencias/${estado.transferencia.id}/cancelar`, { metodo: "POST" });
        mostrarResultado("cancelado", "No se ha enviado el dinero",
          "La transferencia está cancelada. Su dinero sigue en su cuenta.");
      } catch (e) {
        mostrarError(e.message);
      }
    });
  }

  $("#btn-autorizar-directo").addEventListener("click", evento => autorizar(evento.currentTarget));
  $("#btn-cancelar-decision").addEventListener("click", e => cancelar(e.currentTarget));
  $("#btn-verificar").addEventListener("click", e => iniciarVerificacion(e.currentTarget));

  // ================================================================ verificación por voz
  const orbe = $("#orbe");
  const btnMicro = $("#btn-micro");

  function ponerEstado(modo, texto) {
    orbe.className = `orbe ${modo}`;
    $("#estado-voz").textContent = texto;
    estado.hablando = modo === "hablando";
    estado.escuchando = modo === "escuchando";
    const etiqueta = btnMicro.querySelector("span");
    btnMicro.classList.toggle("escuchando", modo === "escuchando");
    btnMicro.disabled = modo === "pensando";
    if (modo === "escuchando") etiqueta.textContent = "He terminado de hablar";
    else if (modo === "hablando") etiqueta.textContent = "Interrumpir y responder";
    else if (modo === "pensando") etiqueta.textContent = "Un momento…";
    else etiqueta.textContent = "Pulse para responder hablando";
    $("#nivel-micro").hidden = modo !== "escuchando";
  }

  function anadirBurbuja(rol, texto, provisional = false) {
    const li = document.createElement("li");
    li.className = `burbuja ${rol}${provisional ? " provisional" : ""}`;
    const quien = document.createElement("span");
    quien.className = "quien";
    quien.textContent = rol === "asistente" ? "SilverShield" : "Usted";
    const contenido = document.createElement("span");
    contenido.className = "contenido";
    contenido.textContent = texto;
    li.append(quien, contenido);
    if (provisional) li.setAttribute("aria-hidden", "true");
    $("#dialogo").append(li);
    li.scrollIntoView({ behavior: "smooth", block: "nearest" });
    return li;
  }

  let burbujaProvisional = null;
  function actualizarProvisional(texto) {
    if (!texto) return;
    if (!burbujaProvisional) burbujaProvisional = anadirBurbuja("cliente", texto, true);
    else burbujaProvisional.querySelector(".contenido").textContent = texto;
  }
  function quitarProvisional() {
    if (burbujaProvisional) { burbujaProvisional.remove(); burbujaProvisional = null; }
  }

  async function iniciarVerificacion(boton) {
    await conCarga(boton, "Conectando con SilverShield…", async () => {
      try {
        const datos = await api(`/api/transferencias/${estado.transferencia.id}/verificacion`, { metodo: "POST" });
        estado.transferencia = datos.transferencia;
        estado.finalizada = false;
        estado.modoTexto = false;
        $("#dialogo").replaceChildren();
        $("#veredicto").hidden = true;
        $("#controles-conversacion").hidden = false;
        $("#form-texto").hidden = true;
        $("#control-voz").hidden = false;
        $("#btn-modo-texto span").textContent = "Prefiero escribir";
        $("#mini-resumen").textContent =
          `Comprobando su transferencia de ${euros(datos.transferencia.importe)} a ${datos.transferencia.beneficiario_nombre}`;
        mostrarPantalla("verificacion");
        for (const m of datos.mensajes) {
          if (m.rol === "asistente") estado.ultimoAsistente = m;
        }
        datos.mensajes.forEach(m => anadirBurbuja(m.rol, m.texto));
        if (await decir(estado.ultimoAsistente)) cicloEscucha();
      } catch (e) {
        mostrarError(e.message);
      }
    });
  }

  /** Lee un mensaje en voz alta. Devuelve false si otra locución lo ha sustituido
   *  (p. ej. el cliente respondió escribiendo mientras sonaba), para que el código
   *  que lo llamó no siga con un estado ya obsoleto. */
  let turnoHabla = 0;
  async function decir(mensaje) {
    if (!mensaje) return false;
    const mio = ++turnoHabla;
    ponerEstado("hablando", "SilverShield le está hablando…");
    await Voz.hablar(mensaje.texto, mensaje.audio_url);
    if (mio !== turnoHabla) return false;
    if (estado.procesando) ponerEstado("pensando", "SilverShield está pensando su respuesta…");
    else if (estado.finalizada) ponerEstado("", "Verificación terminada.");
    else ponerEstado("espera", estado.modoTexto ? "Escriba su respuesta cuando quiera." : "Pulse el botón para responder.");
    return true;
  }

  async function cicloEscucha() {
    if (estado.finalizada || estado.procesando || estado.escuchando) return;
    if (estado.modoTexto) {
      ponerEstado("espera", "Escriba su respuesta cuando quiera.");
      return;
    }
    if (!Voz.puedeEscuchar()) {
      activarModoTexto(true, "Este navegador no permite responder hablando. Puede escribir su respuesta.");
      return;
    }
    ponerEstado("escuchando", "Le escucho. Hable con tranquilidad.");
    const barra = $("#nivel-micro span");
    try {
      const resultado = await Voz.escuchar({
        onParcial: actualizarProvisional,
        onNivel: nivel => { barra.style.width = `${Math.round(nivel * 100)}%`; },
        // En cuanto termina la captura, el botón deja de mostrar "He terminado de hablar".
        onFinCaptura: () => ponerEstado("pensando", "Un momento, estoy entendiendo lo que ha dicho…"),
      });
      if (resultado.cancelado) return;
      if (!resultado.texto) {
        quitarProvisional();
        ponerEstado("espera", "No le he oído bien. Pulse el botón para intentarlo otra vez.");
        return;
      }
      await enviarRespuesta(resultado.texto, { ...resultado.senales, via: "voz" });
    } catch (e) {
      quitarProvisional();
      if (e.message === "not-allowed" || e.message === "service-not-allowed") {
        activarModoTexto(true, "No tenemos permiso para usar el micrófono. Puede escribir su respuesta.");
      } else {
        ponerEstado("espera", "No he podido escucharle. Pulse el botón para intentarlo de nuevo.");
      }
    }
  }

  async function enviarRespuesta(texto, senales) {
    if (estado.procesando) return;
    estado.procesando = true;
    turnoHabla++;        // invalida cualquier locución en curso
    Voz.detener();
    Voz.cancelarEscucha();   // si respondió escribiendo mientras se le escuchaba
    quitarProvisional();
    anadirBurbuja("cliente", texto);
    ponerEstado("pensando", "SilverShield está pensando su respuesta…");
    try {
      const datos = await api(`/api/transferencias/${estado.transferencia.id}/verificacion/mensajes`, {
        metodo: "POST", cuerpo: { texto, senales_voz: senales },
      });
      estado.transferencia = datos.transferencia;
      estado.ultimoAsistente = datos.respuesta;
      anadirBurbuja("asistente", datos.respuesta.texto);
      estado.procesando = false;
      if (datos.final) {
        estado.finalizada = true;
        mostrarVeredicto(datos);
        await decir(datos.respuesta);
      } else if (await decir(datos.respuesta)) {
        cicloEscucha();
      }
    } catch (e) {
      estado.procesando = false;
      ponerEstado("espera", "Ha habido un problema. Pulse el botón para intentarlo de nuevo.");
      mostrarError(e.message);
    }
  }

  btnMicro.addEventListener("click", () => {
    if (estado.escuchando) { Voz.terminarEscucha(); return; }
    // Si SilverShield está hablando, se corta el audio y el flujo pasa solo a escuchar.
    if (estado.hablando) { Voz.detener(); return; }
    cicloEscucha();
  });

  $("#btn-repetir").addEventListener("click", () => {
    if (estado.procesando || !estado.ultimoAsistente) return;
    Voz.cancelarEscucha();
    quitarProvisional();
    decir(estado.ultimoAsistente).then(vigente => { if (vigente && !estado.modoTexto) cicloEscucha(); });
  });

  function activarModoTexto(activo, mensaje) {
    estado.modoTexto = activo;
    Voz.cancelarEscucha();
    quitarProvisional();
    $("#form-texto").hidden = !activo;
    $("#control-voz").hidden = activo;
    $("#btn-modo-texto span").textContent = activo ? "Prefiero hablar" : "Prefiero escribir";
    ponerEstado("espera", mensaje || (activo ? "Escriba su respuesta cuando quiera." : "Pulse el botón para responder."));
    if (activo) $("#campo-respuesta").focus();
  }
  $("#btn-modo-texto").addEventListener("click", () => activarModoTexto(!estado.modoTexto));

  $("#form-texto").addEventListener("submit", evento => {
    evento.preventDefault();
    const campo = $("#campo-respuesta");
    const texto = campo.value.trim();
    if (!texto) { campo.focus(); return; }
    campo.value = "";
    enviarRespuesta(texto, { via: "texto" });
  });

  $("#btn-salir-verificacion").addEventListener("click", e => {
    Voz.detener();
    Voz.cancelarEscucha();
    cancelar(e.currentTarget);
  });

  function crearBoton(clase, texto, alPulsar, icono) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = `btn ${clase}`;
    b.innerHTML = icono ? `<svg aria-hidden="true"><use href="#${icono}"/></svg> ` : "";
    b.append(document.createTextNode(texto));
    b.addEventListener("click", () => alPulsar(b));
    return b;
  }

  // Tipo de engaño explicado a la clienta (se muestra junto a las señales).
  const TIPOS_ENGANO = {
    falso_banco: "Se parece al engaño del falso empleado del banco.",
    falso_tecnico: "Se parece al engaño del falso servicio técnico.",
    falsa_autoridad: "Se parece al engaño de la falsa policía o el falso Hacienda.",
    hijo_en_apuros: "Se parece al engaño del familiar en apuros.",
    inversion_cripto: "Se parece a las falsas inversiones que prometen ganar dinero rápido.",
    premio_herencia: "Se parece al engaño del falso premio o la falsa herencia.",
    romance: "Se parece al engaño de la pareja conocida por internet.",
    compra_online: "Se parece al engaño del paquete retenido.",
    coaccion_familiar: "Parece que alguien le está presionando.",
  };

  // Bloque "¿Por qué la hemos parado?" con las señales que ha visto SilverShield.
  function bloqueMotivosIA(datos) {
    const senales = (datos.senales || []).filter(Boolean).slice(0, 4);
    const tipo = TIPOS_ENGANO[datos.categoria];
    if (!senales.length && !tipo) return null;
    const bloque = document.createElement("div");
    bloque.className = "motivos-ia";
    const encabezado = document.createElement("h3");
    encabezado.textContent = "¿Por qué la hemos parado?";
    bloque.append(encabezado);
    if (tipo) {
      const p = document.createElement("p");
      p.textContent = tipo;
      bloque.append(p);
    }
    if (senales.length) {
      const lista = document.createElement("ul");
      lista.append(...senales.map(t => { const li = document.createElement("li"); li.textContent = t; return li; }));
      bloque.append(lista);
    }
    return bloque;
  }

  function botonLlamarContacto(cuenta) {
    const llamar = document.createElement("a");
    llamar.className = "btn btn-primario";
    llamar.href = `tel:${cuenta.contacto_telefono.replace(/\s/g, "")}`;
    llamar.innerHTML = '<svg aria-hidden="true"><use href="#i-telefono"/></svg> ';
    llamar.append(`Llamar a ${cuenta.contacto_nombre}`);
    return llamar;
  }

  function mostrarVeredicto(datos) {
    const caja = $("#veredicto");
    const cuenta = estado.cuenta;
    caja.replaceChildren();
    $("#controles-conversacion").hidden = true;

    const titulo = document.createElement("h2");
    const parrafos = [];
    const acciones = document.createElement("div");
    acciones.className = "acciones";
    const contacto = describirContacto(cuenta);
    const volverInicio = () => { cargarCuenta(); mostrarPantalla("inicio"); };
    let explicacion = null;

    if (datos.decision === "seguro") {
      caja.className = "veredicto seguro";
      titulo.innerHTML = '<svg aria-hidden="true"><use href="#i-check"/></svg>';
      titulo.append("SilverShield recomienda: puede enviarla");
      parrafos.push("No hemos encontrado señales de engaño. Si está de acuerdo, confirme el envío.");
      acciones.classList.add("en-linea");
      acciones.append(
        crearBoton("btn-secundario", "Prefiero no enviarla", cancelar),
        crearBoton("btn-exito", `Enviar ${euros(estado.transferencia.importe)}`, autorizar, "i-enviar"),
      );
    } else if (datos.decision === "riesgo") {
      caja.className = "veredicto riesgo";
      titulo.innerHTML = '<svg aria-hidden="true"><use href="#i-alerta"/></svg>';
      titulo.append("Le recomendamos NO enviar este dinero");
      parrafos.push("Hemos parado la transferencia. Su dinero está a salvo en su cuenta. Un operador de SilverBank la revisará y le llamará.");
      parrafos.push(`Le recomendamos avisar a su contacto de emergencia, ${contacto}. Háblelo con calma antes de hacer nada más.`);
      explicacion = bloqueMotivosIA(datos);
      acciones.append(botonLlamarContacto(cuenta), crearBoton("btn-secundario", "Volver al inicio", volverInicio));
    } else if (datos.decision === "no_verificada") {
      // Claude no respondió: por seguridad no se da por buena, queda retenida.
      caja.className = "veredicto revision";
      titulo.innerHTML = '<svg aria-hidden="true"><use href="#i-reloj"/></svg>';
      titulo.append("No hemos podido terminar la comprobación");
      parrafos.push("Ha habido un problema técnico. Por precaución, la transferencia está parada y su dinero está a salvo en su cuenta.");
      parrafos.push("Un operador de SilverBank la revisará y le llamará para terminar la comprobación con usted.");
      parrafos.push(`Si tiene dudas, puede hablarlo también con su contacto de emergencia, ${contacto}.`);
      acciones.append(botonLlamarContacto(cuenta), crearBoton("btn-secundario", "Volver al inicio", volverInicio));
    } else {
      // "revision": palabra de auxilio. Mensaje neutro para no alertar a quien presiona.
      caja.className = "veredicto revision";
      titulo.innerHTML = '<svg aria-hidden="true"><use href="#i-reloj"/></svg>';
      titulo.append("Su operación está en revisión");
      parrafos.push("Un operador del banco la revisará y le llamará en unos minutos.");
      acciones.append(crearBoton("btn-primario", "Volver al inicio", volverInicio));
    }

    caja.append(titulo, ...parrafos.map(t => { const p = document.createElement("p"); p.textContent = t; return p; }));
    if (explicacion) caja.append(explicacion);
    caja.append(acciones);
    caja.hidden = false;
    caja.focus({ preventScroll: true });
    caja.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  // ================================================================ resultado
  function mostrarResultado(tipo, titulo, texto) {
    const seccion = $("#pantalla-resultado");
    seccion.classList.remove("ok", "cancelado");
    seccion.classList.add(tipo);
    $("#icono-resultado").setAttribute("href", tipo === "ok" ? "#i-check" : "#i-cruz");
    $("#t-resultado").textContent = titulo;
    $("#texto-resultado").textContent = texto;
    mostrarPantalla("resultado");
    cargarCuenta();
  }

  function mostrarResultadoOk(transferencia, saldo) {
    mostrarResultado(
      "ok",
      "Transferencia enviada",
      `Ha enviado ${euros(transferencia.importe)} a ${transferencia.beneficiario_nombre}. ` +
      `Le quedan ${euros(saldo)} en su cuenta.`,
    );
  }

  // ================================================================ arranque
  aplicarTamano();
  aplicarContraste(localStorage.getItem("ss-contraste") === "1");
  cargarEstadoServicios();
  cargarCuenta();
})();
