"""Evaluación de SilverShield con 40 casos (20 estafas y 20 legítimas difíciles).

Simula cada conversación turno a turno con el mismo agente que usa la app
(`agente_silvershield.evaluar_turno`) y mide aciertos, falsos positivos, falsos
negativos y tiempos de respuesta. No toca la base de datos ni la app.

Uso (desde la raíz del proyecto):
    python -m evaluacion.evaluar                 # con Claude (necesita ANTHROPIC_API_KEY)
    python -m evaluacion.evaluar --motor local   # con el evaluador local (gratis, sin red)
    python -m evaluacion.evaluar --motor ambos   # los dos, para compararlos
    python -m evaluacion.evaluar --solo E01,L05  # solo algunos casos

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

CARPETA_RESULTADOS = Path(__file__).resolve().parent / "resultados"
RETENIDA = {"riesgo", "no_verificada"}   # decisiones que paran el dinero


async def simular(caso: dict) -> dict:
    """Ejecuta una conversación completa y devuelve lo que ha pasado."""
    cuenta = dict(DATOS_DEMO["cuenta"])
    conocidos = {iban for _, _, iban in DATOS_DEMO["beneficiarios"]}
    evaluacion = evaluar_transferencia(
        importe=caso["importe"], iban=caso["iban"], concepto=caso["concepto"],
        beneficiario_conocido=caso["iban"] in conocidos, saldo=cuenta["saldo"],
    )
    transferencia = {
        "beneficiario_nombre": caso["beneficiario"], "iban": caso["iban"],
        "pais": evaluacion["pais"], "importe": caso["importe"], "concepto": caso["concepto"],
        "evaluacion": evaluacion,
    }
    mensajes = [{"rol": "asistente", "texto": agente.mensaje_apertura(transferencia, cuenta)}]
    tiempos_turno, tiempos_ia = [], []
    resultado = None
    for texto in caso["respuestas"]:
        mensajes.append({"rol": "cliente", "texto": texto})
        inicio = time.perf_counter()
        resultado = await agente.evaluar_turno(transferencia, cuenta, mensajes, analizar_senales(texto))
        tiempos_turno.append(int((time.perf_counter() - inicio) * 1000))
        if resultado.tiempo_ia_ms is not None:
            tiempos_ia.append(resultado.tiempo_ia_ms)
        mensajes.append({"rol": "asistente", "texto": resultado.respuesta})
        if resultado.decision != "preguntar":
            break

    decision = resultado.decision if resultado else "sin_decision"
    if caso["tipo"] == "estafa":
        acierto = decision in RETENIDA
    else:
        acierto = decision == "seguro"
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
        "conversacion": mensajes,
    }


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
        "tiempo_turno_medio_ms": int(statistics.mean(turnos)) if turnos else 0,
        "tiempo_turno_p95_ms": percentil(turnos, 0.95),
        "tiempo_ia_medio_ms": int(statistics.mean(ia)) if ia else None,
        "tiempo_ia_p95_ms": percentil(ia, 0.95) if ia else None,
        "sin_verificacion_por_reglas": [r["id"] for r in resultados if not r["requiere_verificacion"]],
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
        f"| Tiempo medio de respuesta por turno | {seg(s['tiempo_turno_medio_ms'])} (p95: {seg(s['tiempo_turno_p95_ms'])}) |",
    ]
    if s["tiempo_ia_medio_ms"] is not None:
        lineas.append(f"| Tiempo medio de Claude por turno | {seg(s['tiempo_ia_medio_ms'])} "
                      f"(p95: {seg(s['tiempo_ia_p95_ms'])}) |")
    if s["sin_verificacion_por_reglas"]:
        lineas.append(f"| Casos que las reglas no mandan a verificar | {', '.join(s['sin_verificacion_por_reglas'])} |")
    lineas += [
        "",
        "Un falso negativo es lo más grave (el dinero se habría ido). Un falso positivo es",
        "reversible: la transferencia queda retenida y un operador del banco la libera tras llamar al cliente.",
        "",
        "## Detalle por caso",
        "",
        "| Caso | Tipo | Descripción | Decisión | Riesgo | Turnos | ¿Acierto? |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in resultados:
        lineas.append(
            f"| {r['id']} | {r['tipo']} | {r['descripcion']} | {r['decision']} | "
            f"{r['nivel_riesgo']} | {r['turnos']} | {'✅' if r['acierto'] else '❌'} |"
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
    parser.add_argument("--solo", help="IDs de casos separados por comas (por ejemplo E01,L05)")
    parser.add_argument("--paralelo", type=int, default=4,
                        help="conversaciones a la vez (1 = tiempos más fieles, más lento)")
    args = parser.parse_args()

    casos = CASOS
    if args.solo:
        ids = {i.strip().upper() for i in args.solo.split(",")}
        casos = [c for c in CASOS if c["id"] in ids]
    motores = ["local", "claude"] if args.motor == "ambos" else [args.motor]
    CARPETA_RESULTADOS.mkdir(exist_ok=True)

    for motor in motores:
        print(f"\n== Evaluando {len(casos)} casos con el motor «{motor}» ==")
        resumen, resultados = asyncio.run(evaluar(motor, casos, args.paralelo))
        nombre = f"resultados_{config.CLAUDE_MODEL}" if motor == "claude" else "resultados_local"
        (CARPETA_RESULTADOS / f"{nombre}.md").write_text(
            informe_markdown(motor, resumen, resultados), encoding="utf-8")
        (CARPETA_RESULTADOS / f"{nombre}.json").write_text(
            json.dumps({"resumen": resumen, "casos": resultados}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        print(f"\nAciertos: {resumen['aciertos']}/{resumen['casos']} · "
              f"falsos negativos: {resumen['falsos_negativos']} · "
              f"falsos positivos: {resumen['falsos_positivos']} · "
              f"tiempo medio por turno: {resumen['tiempo_turno_medio_ms']} ms")
        print(f"Informe: evaluacion/resultados/{nombre}.md")


if __name__ == "__main__":
    main()
