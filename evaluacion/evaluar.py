"""Evaluación de SilverShield con casos de prueba.

Conjuntos:
  base      40 casos (20 estafas y 20 legítimas difíciles)            -> casos.py
  extremos  20 casos más difíciles (estafas sutiles, legítimas trampa) -> casos_extremos.py
  memoria   5 casos en dos pasos para medir la memoria por cliente      -> casos_extremos.py

Simula cada conversación turno a turno con el mismo agente que usa la app
(`agente_silvershield.evaluar_turno`) y mide aciertos, falsos positivos, falsos
negativos, tiempos de respuesta y coste por verificación (tokens de Claude medidos
en cada llamada + caracteres de voz de ElevenLabs). No toca la base de datos ni la app.

Uso (desde la raíz del proyecto):
    python -m evaluacion.evaluar                 # con Claude (necesita ANTHROPIC_API_KEY)
    python -m evaluacion.evaluar --motor local   # con el evaluador local (gratis, sin red)
    python -m evaluacion.evaluar --motor ambos   # los dos, para compararlos
    python -m evaluacion.evaluar --solo E01,L05  # solo algunos casos
    python -m evaluacion.evaluar --conjunto extremos
    python -m evaluacion.evaluar --conjunto memoria              # con memoria
    python -m evaluacion.evaluar --conjunto memoria --sin-memoria  # para comparar

Los resultados se guardan en evaluacion/resultados/ (Markdown + JSON).
"""
import argparse
import asyncio
import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from backend import agente_silvershield as agente, config  # noqa: E402
from backend.database import DATOS_DEMO  # noqa: E402
from backend.reglas_riesgo import evaluar_transferencia  # noqa: E402
from backend.voice_stress import analizar_senales  # noqa: E402
from evaluacion.casos import CASOS  # noqa: E402
from evaluacion.casos_extremos import EXTREMOS, MEMORIA  # noqa: E402

CARPETA_RESULTADOS = Path(__file__).resolve().parent / "resultados"
RETENIDA = {"riesgo", "no_verificada"}   # decisiones que paran el dinero

# ---------------------------------------------------------------- precios (USD)
# Claude: dólares por millón de tokens (entrada, salida). Fuente: tabla de precios de
# Anthropic (platform.claude.com, octubre de 2026). La salida incluye el razonamiento.
PRECIOS_CLAUDE = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}
# ElevenLabs: dólares por 1.000 caracteres sintetizados. Fuente: elevenlabs.io/pricing/api
# (consultado el 09/11/2026; precios sin impuestos, iguales en todos los planes).
PRECIOS_VOZ = {"eleven_multilingual_v2": 0.08, "eleven_flash_v2_5": 0.04}


def coste_claude(tokens_entrada: int, tokens_salida: int) -> float | None:
    precio = PRECIOS_CLAUDE.get(config.CLAUDE_MODEL)
    if precio is None:
        return None
    return (tokens_entrada * precio[0] + tokens_salida * precio[1]) / 1_000_000


def coste_voz(caracteres: int) -> float | None:
    precio = PRECIOS_VOZ.get(config.ELEVENLABS_TTS_MODEL)
    return None if precio is None else caracteres * precio / 1000


async def simular(caso: dict, perfil: dict | None = None, memoria: dict | None = None,
                  conocido: bool | None = None) -> dict:
    """Ejecuta una conversación completa y devuelve lo que ha pasado.

    `perfil` y `memoria` simulan lo que la app guarda de verificaciones anteriores."""
    cuenta = dict(DATOS_DEMO["cuenta"])
    conocidos = {iban for _, _, iban in DATOS_DEMO["beneficiarios"]}
    evaluacion = evaluar_transferencia(
        importe=caso["importe"], iban=caso["iban"], concepto=caso["concepto"],
        beneficiario_conocido=caso["iban"] in conocidos if conocido is None else conocido,
        saldo=cuenta["saldo"], perfil=perfil,
    )
    transferencia = {
        "beneficiario_nombre": caso["beneficiario"], "iban": caso["iban"],
        "pais": evaluacion["pais"], "importe": caso["importe"], "concepto": caso["concepto"],
        "evaluacion": evaluacion,
    }
    mensajes = [{"rol": "asistente", "texto": agente.mensaje_apertura(transferencia, cuenta)}]
    tiempos_turno, tiempos_ia = [], []
    tokens_entrada = tokens_salida = 0
    resultado = None
    # "Lo de siempre" (destino ya verificado e importe habitual): no hay conversación.
    respuestas = [] if evaluacion.get("destino_habitual_verificado") else caso["respuestas"]
    if not respuestas:
        mensajes = []
    for texto in respuestas:
        mensajes.append({"rol": "cliente", "texto": texto})
        inicio = time.perf_counter()
        resultado = await agente.evaluar_turno(transferencia, cuenta, mensajes,
                                               analizar_senales(texto), memoria)
        tiempos_turno.append(int((time.perf_counter() - inicio) * 1000))
        if resultado.tiempo_ia_ms is not None:
            tiempos_ia.append(resultado.tiempo_ia_ms)
        tokens_entrada += resultado.tokens_entrada
        tokens_salida += resultado.tokens_salida
        mensajes.append({"rol": "asistente", "texto": resultado.respuesta})
        if resultado.decision != "preguntar":
            break

    if resultado:
        decision = resultado.decision
    else:
        decision = "sin_verificacion" if evaluacion.get("destino_habitual_verificado") else "sin_decision"
    if caso["tipo"] == "estafa":
        acierto = decision in RETENIDA
    else:
        acierto = decision in ("seguro", "sin_verificacion")
    return {
        "id": caso["id"], "tipo": caso["tipo"], "descripcion": caso["descripcion"],
        "categoria_esperada": caso["categoria"],
        "requiere_verificacion": evaluacion["requiere_confirmacion"],
        "decision": decision, "acierto": acierto,
        "nivel_riesgo": resultado.nivel_riesgo if resultado else None,
        "categoria": resultado.categoria if resultado else None,
        "senales": resultado.senales if resultado else [],
        "motor_final": resultado.motor if resultado else None,
        "fallo_ia": bool(resultado and resultado.fallo_ia),
        "turnos": sum(1 for m in mensajes if m["rol"] == "cliente"),
        "tiempos_turno_ms": tiempos_turno, "tiempos_ia_ms": tiempos_ia,
        "tokens_entrada": tokens_entrada, "tokens_salida": tokens_salida,
        "llamadas_ia": len(tiempos_ia),
        "recordar": resultado.recordar if resultado else [],
        # Todo lo que dice SilverShield (saludo incluido) se convierte en voz una vez.
        "caracteres_voz": sum(len(m["texto"]) for m in mensajes if m["rol"] == "asistente"),
        "conversacion": mensajes,
    }


async def simular_memoria(caso: dict, usar_memoria: bool) -> dict:
    """Dos (o más) transferencias seguidas, guardando entre medias lo mismo que la app:
    historial verificado con cada destinatario y los hechos que recuerda Claude."""
    conocidos = {iban for _, _, iban in DATOS_DEMO["beneficiarios"]}
    historial: dict[str, dict] = {}
    hechos: list[dict] = []
    pasos = []
    for n, paso in enumerate(caso["pasos"], 1):
        iban = paso["iban"]
        h = historial.setdefault(iban, {"envios": 0, "verificados": 0, "max": None, "alerta": False})
        perfil = {"envios": h["envios"], "verificado": h["verificados"] > 0,
                  "envios_verificados": h["verificados"], "importe_max_verificado": h["max"],
                  "alerta": h["alerta"]}
        memoria = {"perfil": perfil, "hechos": list(hechos)} if usar_memoria else None
        r = await simular({**paso, "id": f"{caso['id']}.{n}", "descripcion": caso["descripcion"],
                           "categoria": "-"},
                          perfil=perfil if usar_memoria else None, memoria=memoria,
                          conocido=iban in conocidos or h["envios"] > 0)
        fecha = f"2026-11-{n:02d}"
        if r["decision"] in ("seguro", "sin_verificacion"):
            h["envios"] += 1
            if r["decision"] == "seguro":
                h["verificados"] += 1
                h["max"] = max(h["max"] or 0, paso["importe"])
                hechos += [{"fecha": fecha, "tipo": "contexto", "iban": iban, "texto": t}
                           for t in r["recordar"]]
        elif r["decision"] == "riesgo":
            h["alerta"] = True
            hechos += [{"fecha": fecha, "tipo": "alerta", "iban": iban, "texto": t}
                       for t in (r["recordar"] or [f"Intento de estafa al enviar {paso['importe']} euros."])]
        pasos.append(r)
    return {"id": caso["id"], "descripcion": caso["descripcion"], "pasos": pasos,
            "acierto": all(p["acierto"] for p in pasos)}


def resumir_memoria(resultados: list[dict]) -> dict:
    ultimos = [r["pasos"][-1] for r in resultados]
    todos = [p for r in resultados for p in r["pasos"]]
    return {
        "casos": len(resultados),
        "aciertos": sum(r["acierto"] for r in resultados),
        "pasos_correctos": sum(p["acierto"] for p in todos), "pasos": len(todos),
        "segundos_sin_verificacion": sum(p["decision"] == "sin_verificacion" for p in ultimos),
        "preguntas_segundo_paso": round(statistics.mean(p["turnos"] for p in ultimos), 2),
        "llamadas_ia_segundo_paso": round(statistics.mean(p["llamadas_ia"] for p in ultimos), 2),
        "llamadas_ia_totales": sum(p["llamadas_ia"] for p in todos),
    }


def informe_memoria(resumen: dict, resultados: list[dict], usar_memoria: bool) -> str:
    s = resumen
    lineas = [
        f"# Evaluación de la memoria por cliente · {'CON' if usar_memoria else 'SIN'} memoria",
        "",
        f"Fecha: {datetime.now():%d/%m/%Y %H:%M} · Modelo: {config.CLAUDE_MODEL if config.ia_disponible() else 'evaluador local'}",
        "",
        "| Métrica | Resultado |",
        "|---|---|",
        f"| Casos resueltos bien (todos sus pasos) | **{s['aciertos']} de {s['casos']}** |",
        f"| Pasos correctos | {s['pasos_correctos']} de {s['pasos']} |",
        f"| Segundas transferencias sin necesidad de verificar | {s['segundos_sin_verificacion']} de {s['casos']} |",
        f"| Preguntas medias en la segunda transferencia | {str(s['preguntas_segundo_paso']).replace('.', ',')} |",
        f"| Llamadas a Claude en total | {s['llamadas_ia_totales']} |",
        "",
        "## Detalle",
        "",
        "| Caso | Paso | Importe | Esperado | Decisión | Preguntas | ¿Acierto? |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in resultados:
        for n, p in enumerate(r["pasos"], 1):
            lineas.append(f"| {r['id']} · {r['descripcion']} | {n} | — | {p['tipo']} | {p['decision']} | "
                          f"{p['turnos']} | {'✅' if p['acierto'] else '❌'} |")
    lineas += ["", "## Conversaciones", ""]
    for r in resultados:
        for n, p in enumerate(r["pasos"], 1):
            lineas += [f"### {r['id']}.{n} · {p['decision']}", ""]
            for m in p["conversacion"]:
                quien = "SilverShield" if m["rol"] == "asistente" else "Cliente"
                lineas.append(f"- **{quien}:** {m['texto']}")
            if not p["conversacion"]:
                lineas.append("- *(Sin verificación: destino habitual ya verificado e importe dentro de lo normal.)*")
            if p["recordar"]:
                lineas.append(f"- *Recuerda:* {'; '.join(p['recordar'])}")
            lineas.append("")
    return "\n".join(lineas) + "\n"


def percentil(valores: list[int], p: float) -> int:
    if not valores:
        return 0
    ordenados = sorted(valores)
    return ordenados[min(len(ordenados) - 1, int(round(p * (len(ordenados) - 1))))]


def resumir(resultados: list[dict]) -> dict:
    estafas = [r for r in resultados if r["tipo"] == "estafa"]
    legitimas = [r for r in resultados if r["tipo"] == "legitima"]
    vp = sum(r["acierto"] for r in estafas)
    vn = sum(r["acierto"] for r in legitimas)
    fn = len(estafas) - vp
    fp = len(legitimas) - vn
    turnos = [t for r in resultados for t in r["tiempos_turno_ms"]]
    ia = [t for r in resultados for t in r["tiempos_ia_ms"]]
    media = lambda clave: statistics.mean(r[clave] for r in resultados) if resultados else 0  # noqa: E731
    tok_in, tok_out, chars = media("tokens_entrada"), media("tokens_salida"), media("caracteres_voz")
    c_ia = coste_claude(tok_in, tok_out) if tok_in or tok_out else 0.0
    c_voz = coste_voz(chars)
    total = None if c_ia is None or c_voz is None else c_ia + c_voz
    return {
        "casos": len(resultados),
        "aciertos": vp + vn,
        "exactitud": round((vp + vn) / len(resultados), 3) if resultados else 0,
        "estafas_detectadas": vp, "estafas_total": len(estafas),
        "falsos_negativos": fn,
        "legitimas_aprobadas": vn, "legitimas_total": len(legitimas),
        "falsos_positivos": fp,
        "no_verificadas_por_fallo_ia": sum(r["decision"] == "no_verificada" for r in resultados),
        "turnos_medios": round(statistics.mean(r["turnos"] for r in resultados), 2) if resultados else 0,
        "llamadas_ia_medias": round(statistics.mean(r["llamadas_ia"] for r in resultados), 2) if resultados else 0,
        "tiempo_turno_medio_ms": int(statistics.mean(turnos)) if turnos else 0,
        "tiempo_turno_p95_ms": percentil(turnos, 0.95),
        "tiempo_ia_medio_ms": int(statistics.mean(ia)) if ia else None,
        "tiempo_ia_p95_ms": percentil(ia, 0.95) if ia else None,
        "sin_verificacion_por_reglas": [r["id"] for r in resultados if not r["requiere_verificacion"]],
        "tokens_entrada_medios": int(tok_in), "tokens_salida_medios": int(tok_out),
        "caracteres_voz_medios": int(chars),
        "coste_ia_medio_usd": None if c_ia is None else round(c_ia, 5),
        "coste_voz_medio_usd": None if c_voz is None else round(c_voz, 5),
        "coste_total_medio_usd": None if total is None else round(total, 5),
        "modelo_voz": config.ELEVENLABS_TTS_MODEL,
    }


def informe_markdown(motor: str, resumen: dict, resultados: list[dict]) -> str:
    s = resumen
    seg = lambda ms: f"{ms / 1000:.1f} s".replace(".", ",") if ms is not None else "—"  # noqa: E731
    lineas = [
        f"# Evaluación de SilverShield · motor: {motor}",
        "",
        f"Fecha: {datetime.now():%d/%m/%Y %H:%M} · Modelo: "
        f"{config.CLAUDE_MODEL if motor == 'claude' else 'evaluador local'} · "
        f"Máximo de turnos: {config.MAX_TURNOS_VERIFICACION}",
        "",
        "| Métrica | Resultado |",
        "|---|---|",
        f"| Aciertos totales | **{s['aciertos']} de {s['casos']}** ({s['exactitud']:.0%}) |",
        f"| Estafas detectadas | {s['estafas_detectadas']} de {s['estafas_total']} |",
        f"| Falsos negativos (estafa que se habría enviado) | {s['falsos_negativos']} |",
        f"| Legítimas aprobadas | {s['legitimas_aprobadas']} de {s['legitimas_total']} |",
        f"| Falsos positivos (legítima retenida) | {s['falsos_positivos']} |",
        f"| Retenidas por fallo técnico de la IA | {s['no_verificadas_por_fallo_ia']} |",
        f"| Preguntas medias por conversación | {str(s['turnos_medios']).replace('.', ',')} |",
        f"| Llamadas a Claude por conversación | {str(s['llamadas_ia_medias']).replace('.', ',')} |",
        f"| Tiempo medio de respuesta por turno | {seg(s['tiempo_turno_medio_ms'])} (p95: {seg(s['tiempo_turno_p95_ms'])}) |",
    ]
    if s["tiempo_ia_medio_ms"] is not None:
        lineas.append(f"| Tiempo medio de Claude por turno | {seg(s['tiempo_ia_medio_ms'])} "
                      f"(p95: {seg(s['tiempo_ia_p95_ms'])}) |")
    if s["sin_verificacion_por_reglas"]:
        lineas.append(f"| Casos que las reglas no mandan a verificar | {', '.join(s['sin_verificacion_por_reglas'])} |")
    usd = lambda v, d=4: "—" if v is None else f"{v:.{d}f} $".replace(".", ",")  # noqa: E731
    miles = lambda n: f"{n:,}".replace(",", ".")  # noqa: E731
    lineas += [
        "",
        "## Coste por verificación (medido)",
        "",
        "| Concepto | Media por conversación | Coste |",
        "|---|---|---|",
        f"| Claude ({config.CLAUDE_MODEL if motor == 'claude' else 'no se usa'}) | "
        f"{miles(s['tokens_entrada_medios'])} tokens de entrada + {miles(s['tokens_salida_medios'])} de salida | "
        f"{usd(s['coste_ia_medio_usd'])} |",
        f"| Voz ElevenLabs ({s['modelo_voz']}) | {miles(s['caracteres_voz_medios'])} caracteres | {usd(s['coste_voz_medio_usd'])} |",
        f"| **Total por verificación** | | **{usd(s['coste_total_medio_usd'])}** |",
        f"| Por cada 1.000 verificaciones | | {usd(None if s['coste_total_medio_usd'] is None else s['coste_total_medio_usd'] * 1000, 2)} |",
        "",
        "Precios sin impuestos: Claude según la tabla de Anthropic; ElevenLabs según elevenlabs.io/pricing/api",
        "(09/11/2026). Solo se verifican las transferencias que las reglas marcan como inusuales.",
    ]
    lineas += [
        "",
        "Un falso negativo es lo más grave (el dinero se habría ido). Un falso positivo es",
        "reversible: la transferencia queda retenida y un operador del banco la libera tras llamar al cliente.",
        "",
        "## Detalle por caso",
        "",
        "| Caso | Tipo | Descripción | Decisión | Riesgo | Turnos | Coste | ¿Acierto? |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in resultados:
        c_ia = coste_claude(r["tokens_entrada"], r["tokens_salida"]) if r["tokens_entrada"] else 0.0
        c_voz = coste_voz(r["caracteres_voz"])
        coste = "—" if c_ia is None or c_voz is None else usd(c_ia + c_voz)
        lineas.append(
            f"| {r['id']} | {r['tipo']} | {r['descripcion']} | {r['decision']} | "
            f"{r['nivel_riesgo']} | {r['turnos']} | {coste} | {'✅' if r['acierto'] else '❌'} |"
        )
    fallos = [r for r in resultados if not r["acierto"]]
    if fallos:
        lineas += ["", "## Casos fallados (conversación completa)", ""]
        for r in fallos:
            lineas += [f"### {r['id']} · {r['descripcion']} → {r['decision']}", ""]
            for m in r["conversacion"]:
                quien = "SilverShield" if m["rol"] == "asistente" else "Cliente"
                lineas.append(f"- **{quien}:** {m['texto']}")
            if r["senales"]:
                lineas.append(f"- *Señales:* {'; '.join(r['senales'])}")
            lineas.append("")
    return "\n".join(lineas) + "\n"


async def evaluar_memoria(motor: str, usar_memoria: bool, paralelo: int) -> None:
    clave_original = config.ANTHROPIC_API_KEY
    if motor == "local":
        config.ANTHROPIC_API_KEY = None
    elif not config.ia_disponible():
        raise SystemExit("Falta ANTHROPIC_API_KEY en .env para evaluar con Claude.")
    semaforo = asyncio.Semaphore(paralelo)

    async def uno(caso):
        async with semaforo:
            r = await simular_memoria(caso, usar_memoria)
        print(f"  {r['id']} " + " -> ".join(p["decision"] for p in r["pasos"])
              + ("  ok" if r["acierto"] else "  FALLO"), flush=True)
        return r

    print(f"\n== Memoria ({'con' if usar_memoria else 'sin'} memoria) · motor «{motor}» ==")
    try:
        resultados = await asyncio.gather(*(uno(c) for c in MEMORIA))
        resumen = resumir_memoria(resultados)
        modelo = config.CLAUDE_MODEL if motor == "claude" else "local"
    finally:
        config.ANTHROPIC_API_KEY = clave_original
    nombre = f"resultados_{modelo}_memoria_{'con' if usar_memoria else 'sin'}"
    (CARPETA_RESULTADOS / f"{nombre}.md").write_text(
        informe_memoria(resumen, resultados, usar_memoria), encoding="utf-8")
    (CARPETA_RESULTADOS / f"{nombre}.json").write_text(
        json.dumps({"resumen": resumen, "casos": resultados}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"Casos bien: {resumen['aciertos']}/{resumen['casos']} · segundas sin verificar: "
          f"{resumen['segundos_sin_verificacion']} · preguntas en el 2º paso: "
          f"{resumen['preguntas_segundo_paso']} · llamadas a Claude: {resumen['llamadas_ia_totales']}")
    print(f"Informe: evaluacion/resultados/{nombre}.md")


async def evaluar(motor: str, casos: list[dict], paralelo: int) -> tuple[dict, list[dict]]:
    clave_original = config.ANTHROPIC_API_KEY
    if motor == "local":
        config.ANTHROPIC_API_KEY = None
    elif not config.ia_disponible():
        raise SystemExit("Falta ANTHROPIC_API_KEY en .env para evaluar con Claude.")
    semaforo = asyncio.Semaphore(paralelo)
    hechos = 0

    async def uno(caso):
        nonlocal hechos
        async with semaforo:
            r = await simular(caso)
        hechos += 1
        print(f"  [{hechos:>2}/{len(casos)}] {r['id']} {r['decision']:<14} {'ok' if r['acierto'] else 'FALLO'}",
              flush=True)
        return r

    try:
        resultados = await asyncio.gather(*(uno(c) for c in casos))
    finally:
        config.ANTHROPIC_API_KEY = clave_original
    return resumir(resultados), resultados


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--motor", choices=["claude", "local", "ambos"], default="claude")
    parser.add_argument("--conjunto", choices=["base", "extremos", "memoria"], default="base",
                        help="base: 40 casos; extremos: 20 más difíciles; memoria: 5 casos en dos pasos")
    parser.add_argument("--sin-memoria", action="store_true",
                        help="(conjunto memoria) desactiva la memoria para comparar")
    parser.add_argument("--solo", help="IDs de casos separados por comas (por ejemplo E01,L05)")
    parser.add_argument("--paralelo", type=int, default=4,
                        help="conversaciones a la vez (1 = tiempos más fieles, más lento)")
    args = parser.parse_args()

    casos = CASOS if args.conjunto == "base" else EXTREMOS
    if args.solo:
        ids = {i.strip().upper() for i in args.solo.split(",")}
        casos = [c for c in CASOS + EXTREMOS if c["id"] in ids]
    motores = ["local", "claude"] if args.motor == "ambos" else [args.motor]
    CARPETA_RESULTADOS.mkdir(exist_ok=True)

    if args.conjunto == "memoria":
        for motor in motores:
            asyncio.run(evaluar_memoria(motor, not args.sin_memoria, args.paralelo))
        return

    for motor in motores:
        print(f"\n== Evaluando {len(casos)} casos con el motor «{motor}» ==")
        resumen, resultados = asyncio.run(evaluar(motor, casos, args.paralelo))
        nombre = f"resultados_{config.CLAUDE_MODEL}" if motor == "claude" else "resultados_local"
        if args.conjunto != "base":
            nombre += f"_{args.conjunto}"
        (CARPETA_RESULTADOS / f"{nombre}.md").write_text(
            informe_markdown(motor, resumen, resultados), encoding="utf-8")
        (CARPETA_RESULTADOS / f"{nombre}.json").write_text(
            json.dumps({"resumen": resumen, "casos": resultados}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        print(f"\nAciertos: {resumen['aciertos']}/{resumen['casos']} · "
              f"falsos negativos: {resumen['falsos_negativos']} · "
              f"falsos positivos: {resumen['falsos_positivos']} · "
              f"tiempo medio por turno: {resumen['tiempo_turno_medio_ms']} ms · "
              f"coste medio por verificación: {resumen['coste_total_medio_usd']} $")
        print(f"Informe: evaluacion/resultados/{nombre}.md")


if __name__ == "__main__":
    main()
