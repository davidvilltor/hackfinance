/* SilverShield · Panel del operador antifraude del banco (único que puede liberar o cancelar). */
(function () {
  "use strict";

  const $ = sel => document.querySelector(sel);
  const formatoEuros = new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR", useGrouping: "always" });
  const euros = n => formatoEuros.format(n);
  const fechaHora = iso => new Intl.DateTimeFormat("es-ES", {
    day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
  }).format(new Date(iso));

  const ESTADOS = {
    completada: "Enviada", retenida: "Retenida", cancelada: "Cancelada",
    pendiente_decision: "Esperando decisión", en_verificacion: "Verificando por voz",
    verificada_segura: "Verificada (sin enviar)",
  };
  const VIAS = {
    directa: "Sin alertas", autorizada_cliente: "Autorizada por el cliente (sin verificación)",
    verificada_ia: "Verificada por SilverShield", liberada_operador: "Liberada por un operador del banco",
    liberada_contacto: "Liberada (versión anterior)",
    habitual_verificado: "Envío habitual ya verificado por SilverShield (sin preguntas)",
  };
  const CATEGORIAS = {
    ninguna: "Ninguna", falso_banco: "Falso empleado del banco", falso_tecnico: "Falso servicio técnico",
    falsa_autoridad: "Falsa autoridad (policía, Hacienda)", hijo_en_apuros: "Hijo/nieto en apuros",
    inversion_cripto: "Inversión / criptomonedas", premio_herencia: "Premio o herencia falsa",
    romance: "Estafa romántica", compra_online: "Paquete / compra online",
    coaccion_familiar: "Coacción", otra: "Otra",
  };
  const VEREDICTOS = {
    preguntar: "En curso", seguro: "Sin señales de estafa", riesgo: "Riesgo de estafa",
    no_verificada: "No verificada (fallo técnico de la IA)",
  };
  const TIPOS_ALERTA = { COACCION: "Palabra de auxilio", POSIBLE_ESTAFA: "Posible estafa", NO_VERIFICADA: "No se pudo verificar" };
  const MOTORES = { claude: "Claude (IA)", reglas: "Evaluador local", palabra_auxilio: "Palabra de auxilio" };

  let seleccionada = null;
  let alertasVistas = null;

  function el(etiqueta, props = {}, ...hijos) {
    const nodo = document.createElement(etiqueta);
    for (const [clave, valor] of Object.entries(props)) {
      if (clave === "class") nodo.className = valor;
      else if (clave.startsWith("on")) nodo.addEventListener(clave.slice(2), valor);
      else nodo.setAttribute(clave, valor);
    }
    nodo.append(...hijos.filter(h => h !== null && h !== undefined));
    return nodo;
  }

  async function api(ruta, metodo = "GET") {
    const r = await fetch(ruta, { method: metodo });
    if (r.status === 401) {
      // Sesión caducada o cerrada: vuelta a la pantalla de acceso.
      window.location.replace("/acceso");
      throw new Error("Sesión caducada");
    }
    const datos = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(datos.detail || "Error de servidor");
    return datos;
  }

  function barraRiesgo(nivel) {
    if (nivel === null || nivel === undefined) return el("span", { class: "texto-suave" }, "—");
    const color = nivel >= 60 ? "var(--rojo)" : nivel >= 30 ? "#c99700" : "var(--verde)";
    const relleno = el("span");
    relleno.style.width = `${nivel}%`;
    relleno.style.background = color;
    return el("span", { class: "riesgo-barra" }, el("span", { class: "pista" }, relleno), `${nivel}`);
  }

  // ------------------------------------------------------------------ pintar
  function pintarMemoria(memoria) {
    const lista = $("#lista-memoria");
    lista.replaceChildren();
    if (!memoria || !memoria.length) {
      lista.append(el("li", { class: "vacio" }, "Todavía no ha aprendido nada de esta clienta."));
      return;
    }
    for (const m of memoria) {
      lista.append(el("li", { class: `recuerdo ${m.tipo}` },
        el("span", { class: "tipo" }, m.tipo === "alerta" ? "Alerta" : "Contexto"),
        " ", el("span", { class: "cuando" }, `· ${fechaHora(m.fecha)}${m.beneficiario ? ` · ${m.beneficiario}` : ""}`),
        el("p", {}, m.texto),
        el("button", {
          type: "button", class: "btn btn-texto",
          "aria-label": `Borrar el recuerdo: ${m.texto}`,
          onclick: async () => {
            if (!window.confirm("¿Borrar este recuerdo? SilverShield dejará de tenerlo en cuenta.")) return;
            try {
              await api(`/api/memoria/${m.id}`, "DELETE");
              refrescar();
            } catch (e) {
              window.alert(e.message);
            }
          },
        }, "Borrar"),
      ));
    }
  }

  function pintarAlertas(alertas) {
    const lista = $("#lista-alertas");
    const nuevas = alertasVistas === null ? new Set() :
      new Set(alertas.filter(a => !alertasVistas.has(a.id)).map(a => a.id));
    alertasVistas = new Set(alertas.map(a => a.id));
    lista.replaceChildren();
    if (!alertas.length) {
      lista.append(el("li", { class: "vacio" }, "No hay avisos. Todo en calma."));
      return;
    }
    for (const a of alertas) {
      const clases = ["alerta", a.tipo === "COACCION" ? "coaccion" : "", nuevas.has(a.id) ? "nueva" : ""].join(" ");
      lista.append(el("li", { class: clases },
        el("span", { class: "tipo" }, TIPOS_ALERTA[a.tipo] || a.tipo),
        " ", el("span", { class: "cuando" }, `· ${fechaHora(a.fecha)} · ${a.canal}`),
        el("p", {}, a.mensaje),
        a.transferencia_id ? el("button", {
          type: "button", class: "btn btn-secundario pequeno",
          onclick: () => verDetalle(a.transferencia_id),
        }, "Ver transferencia") : null,
      ));
    }
    if (nuevas.size && document.hidden === false) document.title = "🔴 Nuevo aviso · SilverShield";
  }

  function pintarTabla(transferencias) {
    const cuerpo = $("#tabla-transferencias");
    cuerpo.replaceChildren();
    for (const t of transferencias) {
      cuerpo.append(el("tr", { class: t.id === seleccionada ? "seleccionada" : "" },
        el("td", {}, fechaHora(t.fecha)),
        el("td", {}, t.beneficiario_nombre, el("br"), el("small", { class: "texto-suave" }, `${t.iban.slice(0, 2)} · …${t.iban.slice(-4)}`)),
        el("td", { class: "num" }, euros(t.importe)),
        el("td", {}, el("span", { class: `estado ${t.estado}` }, ESTADOS[t.estado] || t.estado)),
        el("td", {}, barraRiesgo(t.nivel_riesgo_ia ?? (t.evaluacion ? t.evaluacion.puntuacion : null))),
        el("td", {}, el("button", {
          type: "button", class: "btn btn-texto", onclick: () => verDetalle(t.id),
          "aria-label": `Ver detalle de la transferencia a ${t.beneficiario_nombre}`,
        }, "Ver")),
      ));
    }
  }

  function bloque(titulo, ...contenido) {
    return el("div", { class: "bloque" }, el("h3", {}, titulo), ...contenido);
  }
  function lista(items, vacio) {
    if (!items || !items.length) return el("p", { class: "texto-suave" }, vacio);
    return el("ul", {}, ...items.map(i => el("li", {}, i)));
  }

  function textoMetricas(senales) {
    const voz = senales && senales.voz;
    const analisis = senales && senales.analisis;
    const partes = [];
    if (voz && voz.via) partes.push(voz.via === "voz" ? "🎙️ por voz" : "⌨️ escrito");
    if (voz && voz.palabras_por_minuto) partes.push(`${voz.palabras_por_minuto} palabras/min`);
    if (voz && voz.volumen_medio !== undefined) partes.push(`volumen ${voz.volumen_medio}/100`);
    if (analisis) partes.push(`estrés estimado ${analisis.nivel_porcentaje}%`);
    return partes.join(" · ");
  }

  // "⏱ 2,4 s · Claude 2,1 s": cuánto tardó SilverShield en contestar ese turno.
  function textoTiempos(senales) {
    if (!senales || senales.tiempo_ms === undefined) return "";
    const seg = ms => `${(ms / 1000).toLocaleString("es-ES", { maximumFractionDigits: 1 })} s`;
    const partes = [`⏱ respuesta en ${seg(senales.tiempo_ms)}`];
    if (senales.tiempo_ia_ms !== null && senales.tiempo_ia_ms !== undefined) {
      partes.push(`${senales.motor === "claude" ? "Claude" : "Claude (falló)"} ${seg(senales.tiempo_ia_ms)}`);
    } else if (senales.motor) {
      partes.push(MOTORES[senales.motor] || senales.motor);
    }
    return partes.join(" · ");
  }

  async function verDetalle(id, enfocar = true) {
    seleccionada = id;
    const { transferencia: t, mensajes } = await api(`/api/transferencias/${id}`);
    const caja = $("#contenido-detalle");
    const acciones = $("#acciones-detalle");
    $("#t-detalle").textContent = `Transferencia #${t.id} · ${euros(t.importe)} a ${t.beneficiario_nombre}`;
    acciones.replaceChildren();
    if (t.estado === "retenida") {
      acciones.append(
        el("button", { type: "button", class: "btn btn-exito pequeno", onclick: () => accion(t.id, "liberar",
          "¿Ha hablado con el cliente por un canal seguro y confirma que la transferencia es legítima?") }, "Liberar y enviar"),
        el("button", { type: "button", class: "btn btn-peligro pequeno", onclick: () => accion(t.id, "cancelar",
          "¿Cancelar definitivamente esta transferencia?") }, "Cancelar transferencia"),
      );
    }
    acciones.append(el("button", { type: "button", class: "btn btn-secundario pequeno", onclick: () => window.print() },
      "Imprimir informe"));

    const ev = t.evaluacion || {};
    caja.replaceChildren(
      el("p", { class: "solo-impresion" },
        `Informe SilverShield generado el ${new Date().toLocaleString("es-ES")}. ` +
        "Puede adjuntarse a una denuncia ante la Policía Nacional o la Guardia Civil."),
      el("div", { class: "rejilla-detalle" },
        bloque("Operación",
          el("dl", { class: "datos" },
            el("div", {}, el("dt", {}, "Estado"), el("dd", {}, el("span", { class: `estado ${t.estado}` }, ESTADOS[t.estado] || t.estado))),
            el("div", {}, el("dt", {}, "Fecha"), el("dd", {}, fechaHora(t.fecha))),
            el("div", {}, el("dt", {}, "Cuenta destino"), el("dd", {}, t.iban)),
            el("div", {}, el("dt", {}, "País"), el("dd", {}, ev.pais_nombre || t.pais)),
            el("div", {}, el("dt", {}, "Concepto"), el("dd", {}, t.concepto || "—")),
            el("div", {}, el("dt", {}, "Resolución"), el("dd", {}, VIAS[t.via] || (t.estado === "cancelada" ? "Cancelada" : "—"))),
            ev.destino_habitual_verificado ? el("div", {}, el("dt", {}, "Memoria"),
              el("dd", {}, "Destino ya verificado e importe habitual: no se volvió a preguntar")) : null,
            t.operador ? el("div", {}, el("dt", {}, "Operador"), el("dd", {}, t.operador)) : null,
          )),
        bloque("Alertas del motor de reglas", lista((ev.motivos || []).map(m => m.texto), "Ninguna alerta.")),
        bloque("Análisis de SilverShield (IA)",
          t.veredicto_ia ? el("dl", { class: "datos" },
            el("div", {}, el("dt", {}, "Veredicto"), el("dd", {}, VEREDICTOS[t.veredicto_ia] || t.veredicto_ia)),
            el("div", {}, el("dt", {}, "Riesgo"), el("dd", {}, barraRiesgo(t.nivel_riesgo_ia))),
            el("div", {}, el("dt", {}, "Tipo de estafa"), el("dd", {}, CATEGORIAS[t.categoria_estafa] || t.categoria_estafa || "—")),
            el("div", {}, el("dt", {}, "Motor"), el("dd", {}, MOTORES[t.motor_ia] || t.motor_ia || "—")),
          ) : el("p", { class: "texto-suave" }, "No se ha hecho verificación por voz."),
          t.resumen_ia ? el("p", {}, t.resumen_ia) : null,
          t.senales_ia && t.senales_ia.length ? lista(t.senales_ia) : null,
        ),
      ),
      mensajes.length ? bloque("Transcripción de la verificación",
        el("ol", { class: "transcripcion" }, ...mensajes.map(m => el("li", { class: m.rol },
          el("span", { class: "quien" }, `${m.rol === "asistente" ? "SilverShield" : "Cliente"} · ${fechaHora(m.fecha)}`),
          m.texto,
          m.rol === "cliente" && m.senales ? el("span", { class: "metricas" }, textoMetricas(m.senales)) : null,
          m.rol === "asistente" && m.senales ? el("span", { class: "metricas" }, textoTiempos(m.senales)) : null,
        )))) : null,
    );
    $("#detalle").hidden = false;
    if (enfocar) {
      $("#t-detalle").focus();
      refrescar();
    }
  }

  async function accion(id, tipo, pregunta) {
    if (!window.confirm(pregunta)) return;
    try {
      await api(`/api/transferencias/${id}/${tipo}`, "POST");
      await verDetalle(id);
    } catch (e) {
      window.alert(e.message);
    }
  }

  // ------------------------------------------------------------------ ciclo
  async function refrescar() {
    try {
      const datos = await api("/api/panel");
      const c = datos.cuenta;
      $("#nombre-contacto").textContent =
        `${c.contacto_nombre}${c.contacto_relacion ? ` (${c.contacto_relacion})` : ""} · ${c.contacto_telefono}`;
      $("#nombre-titular").textContent = datos.cuenta.titular;
      $("#nombre-operador").textContent = datos.operador;
      $("#palabra-auxilio").textContent = `«${datos.cuenta.palabra_seguridad}»`;
      $("#umbral").textContent = `${euros(datos.estado.umbral_verificacion)} o destino sospechoso`;
      $("#motor-ia").textContent = datos.estado.ia ? `Claude · ${datos.estado.modelo}` : "Evaluador local (sin clave de Anthropic)";
      $("#motor-voz").textContent = datos.estado.voz_elevenlabs ? "ElevenLabs" : "Voz del navegador";
      pintarAlertas(datos.alertas);
      pintarMemoria(datos.memoria);
      pintarTabla(datos.transferencias);
    } catch (e) {
      console.warn("No se pudo actualizar el panel", e);
    }
  }

  document.addEventListener("visibilitychange", () => { if (!document.hidden) document.title = "SilverShield · Panel del operador"; });
  $("#btn-salir").addEventListener("click", async () => {
    await fetch("/api/operador/salir", { method: "POST" }).catch(() => {});
    window.location.replace("/");   // cierra la sesión y vuelve a la app del cliente
  });
  $("#btn-reiniciar").addEventListener("click", async () => {
    if (!window.confirm("Se borrarán todas las transferencias y avisos de la demo. ¿Continuar?")) return;
    await api("/api/demo/reiniciar", "POST");
    seleccionada = null;
    alertasVistas = null;
    $("#detalle").hidden = true;
    refrescar();
  });

  refrescar();
  setInterval(() => {
    refrescar();
    // Mantiene al día el detalle abierto (p. ej. una verificación en curso).
    if (seleccionada !== null && !$("#detalle").hidden) verDetalle(seleccionada, false).catch(() => {});
  }, 3000);
})();
