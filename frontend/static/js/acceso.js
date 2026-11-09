/* SilverShield · Acceso de los operadores del banco al panel. */
(function () {
  "use strict";

  const formulario = document.getElementById("form-acceso");
  const usuario = document.getElementById("campo-usuario");
  const contrasena = document.getElementById("campo-contrasena");
  const error = document.getElementById("error-acceso");
  const boton = document.getElementById("btn-entrar");

  function mostrarError(texto) {
    error.textContent = texto;
    error.hidden = false;
  }

  formulario.addEventListener("submit", async evento => {
    evento.preventDefault();
    error.hidden = true;
    if (!usuario.value.trim() || !contrasena.value) {
      mostrarError("Escriba su usuario y su contraseña.");
      (usuario.value.trim() ? contrasena : usuario).focus();
      return;
    }
    boton.disabled = true;
    boton.textContent = "Comprobando…";
    try {
      const r = await fetch("/api/operador/acceso", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ usuario: usuario.value.trim(), contrasena: contrasena.value }),
      });
      if (r.ok) {
        window.location.replace("/panel");
        return;
      }
      const datos = await r.json().catch(() => ({}));
      mostrarError(r.status === 401 ? (datos.detail || "Usuario o contraseña incorrectos.")
                                    : "No se ha podido entrar. Inténtelo de nuevo.");
      contrasena.value = "";
      contrasena.focus();
    } catch (e) {
      mostrarError("No hay conexión con el servidor.");
    } finally {
      boton.disabled = false;
      boton.textContent = "Entrar";
    }
  });

  usuario.focus();
})();
