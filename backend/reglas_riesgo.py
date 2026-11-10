"""Motor de reglas determinista que decide si una transferencia necesita una
confirmación extra antes de enviarse.

Es la primera barrera (rápida, explicable y sin coste de IA). Solo cuando salta
alguna regla se ofrece al cliente la verificación conversacional con SilverShield.
"""
import re
import unicodedata

from backend import config

# Longitud oficial del IBAN por país (registro SWIFT) para los países más habituales.
LONGITUD_IBAN = {
    "AD": 24, "AE": 23, "AT": 20, "BE": 16, "BG": 22, "CH": 21, "CY": 28, "CZ": 24,
    "DE": 22, "DK": 18, "EE": 20, "ES": 24, "FI": 18, "FR": 27, "GB": 22, "GI": 23,
    "GR": 27, "HR": 21, "HU": 28, "IE": 22, "IR": 26, "IT": 27, "LB": 28, "LT": 20,
    "LU": 20, "LV": 21, "MA": 28, "MC": 27, "MT": 31, "NL": 18, "NO": 15, "PL": 28,
    "PT": 25, "RO": 24, "SE": 24, "SI": 19, "SK": 24, "TR": 26, "UA": 29, "VG": 24,
    "PK": 24, "BR": 29, "DO": 28, "EG": 29, "TN": 24, "SA": 24, "IL": 23, "GE": 22,
}

NOMBRE_PAIS = {
    "AD": "Andorra", "AE": "Emiratos Árabes Unidos", "AT": "Austria", "BE": "Bélgica",
    "BG": "Bulgaria", "CH": "Suiza", "CY": "Chipre", "CZ": "Chequia", "DE": "Alemania",
    "DK": "Dinamarca", "EE": "Estonia", "ES": "España", "FI": "Finlandia",
    "FR": "Francia", "GB": "Reino Unido", "GH": "Ghana", "GI": "Gibraltar",
    "GR": "Grecia", "HR": "Croacia", "HT": "Haití", "HU": "Hungría", "IE": "Irlanda",
    "IR": "Irán", "IT": "Italia", "KE": "Kenia", "KP": "Corea del Norte",
    "LB": "Líbano", "LT": "Lituania", "LU": "Luxemburgo", "LV": "Letonia",
    "MA": "Marruecos", "PK": "Pakistán", "BR": "Brasil", "DO": "República Dominicana",
    "EG": "Egipto", "TN": "Túnez", "SA": "Arabia Saudí", "IL": "Israel", "GE": "Georgia", "MC": "Mónaco", "MM": "Myanmar", "MT": "Malta", "NG": "Nigeria",
    "NL": "Países Bajos", "NO": "Noruega", "PH": "Filipinas", "PL": "Polonia",
    "PT": "Portugal", "RO": "Rumanía", "SE": "Suecia", "SI": "Eslovenia",
    "SK": "Eslovaquia", "SY": "Siria", "TR": "Turquía", "UA": "Ucrania",
    "VE": "Venezuela", "VG": "Islas Vírgenes Británicas", "YE": "Yemen",
}

# Conceptos que aparecen con frecuencia en estafas a personas mayores
# (fuentes: guías OSI/INCIBE, CFPB, UK Finance Fraud Report).
PALABRAS_CONCEPTO_SOSPECHOSO = [
    "bitcoin", "btc", "cripto", "crypto", "inversion", "rentabilidad", "hacienda",
    "agencia tributaria", "multa", "aduana", "premio", "loteria", "herencia",
    "rescate", "fianza", "desbloqueo", "desbloquear", "cuenta segura",
    "soporte tecnico", "servicio tecnico", "microsoft", "anydesk", "teamviewer",
    "urgente", "policia", "guardia civil", "prestamo", "tarjeta regalo",
    "western union",
]

# Códigos de regla que, por sí solos, obligan a mostrar la pantalla de confirmación.
REGLAS_QUE_ACTIVAN = {
    "IMPORTE_ELEVADO", "PAIS_ALTO_RIESGO", "EXTRANJERO_NUEVO",
    "CONCEPTO_SOSPECHOSO", "PORCENTAJE_SALDO",
    "IMPORTE_INUSUAL_DESTINATARIO", "CUENTA_CON_ALERTA",
}
# Reglas que impiden saltarse la verificación aunque el destino sea habitual.
REGLAS_SIEMPRE_VERIFICAR = {"CONCEPTO_SOSPECHOSO", "PAIS_ALTO_RIESGO", "PORCENTAJE_SALDO",
                            "IMPORTE_INUSUAL_DESTINATARIO", "CUENTA_CON_ALERTA"}

PESOS = {
    "IMPORTE_ELEVADO": 30,
    "PAIS_ALTO_RIESGO": 50,
    "EXTRANJERO_NUEVO": 30,
    "CONCEPTO_SOSPECHOSO": 30,
    "PORCENTAJE_SALDO": 20,
    "BENEFICIARIO_NUEVO": 10,
    "IMPORTE_INUSUAL_DESTINATARIO": 30,
    "CUENTA_CON_ALERTA": 60,
}


class IbanInvalido(ValueError):
    pass


def normalizar_texto(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar palabras clave de forma robusta."""
    sin_tildes = unicodedata.normalize("NFKD", texto or "")
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return sin_tildes.lower()


def normalizar_iban(iban: str) -> str:
    return re.sub(r"[\s\-]", "", iban or "").upper()


def validar_iban(iban: str) -> str:
    """Devuelve el IBAN normalizado o lanza IbanInvalido con un mensaje claro."""
    limpio = normalizar_iban(iban)
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", limpio):
        raise IbanInvalido(
            "El número de cuenta no tiene el formato correcto. "
            "Debe empezar por dos letras (por ejemplo ES) seguidas de números."
        )
    pais = limpio[:2]
    esperado = LONGITUD_IBAN.get(pais)
    if esperado and len(limpio) != esperado:
        raise IbanInvalido(
            f"Un número de cuenta de {NOMBRE_PAIS.get(pais, pais)} debe tener "
            f"{esperado} caracteres y este tiene {len(limpio)}. Revíselo, por favor."
        )
    reordenado = limpio[4:] + limpio[:4]
    numerico = "".join(str(int(c, 36)) for c in reordenado)
    if int(numerico) % 97 != 1:
        raise IbanInvalido(
            "El número de cuenta no es correcto: puede que falte o sobre algún dígito. "
            "Revíselo con calma."
        )
    return limpio


def formatear_euros(importe: float) -> str:
    """1234.5 -> '1.234,50 €' (formato español)."""
    texto = f"{importe:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{texto} €"


def euros_hablados(importe: float) -> str:
    """Formato pensado para ser leído en voz alta: '2.500 euros', '300,50 euros'."""
    if float(importe).is_integer():
        texto = f"{int(importe):,}".replace(",", ".")
    else:
        texto = f"{importe:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{texto} euros"


def nombre_pais(codigo: str) -> str:
    return NOMBRE_PAIS.get(codigo, codigo)


def evaluar_transferencia(
    importe: float,
    iban: str,
    concepto: str,
    beneficiario_conocido: bool,
    saldo: float,
    perfil: dict | None = None,
) -> dict:
    """Aplica las reglas y devuelve un dict serializable con la evaluación.

    `perfil` es la memoria de SilverShield sobre este destinatario (ver
    database.perfil_destinatario): si ya se verificó antes, cuánto se le envió
    como máximo tras verificar y si la cuenta apareció en un intento de estafa.

    - Importe >= umbral (500 € por defecto) -> siempre se pide confirmación.
    - Por debajo del umbral, se pide confirmación si la cuenta es de un país de
      alto riesgo, si es una cuenta extranjera nueva, si el concepto es típico de
      estafa o si se envía más de la mitad del saldo.
    """
    pais = normalizar_iban(iban)[:2]
    extranjero = pais != config.PAIS_LOCAL
    motivos: list[dict] = []

    def anadir(codigo: str, texto: str) -> None:
        motivos.append({"codigo": codigo, "texto": texto})

    if importe >= config.UMBRAL_VERIFICACION_EUR:
        anadir(
            "IMPORTE_ELEVADO",
            f"Es una cantidad importante: {formatear_euros(importe)}.",
        )
    if pais in config.PAISES_ALTO_RIESGO:
        anadir(
            "PAIS_ALTO_RIESGO",
            f"La cuenta está en {nombre_pais(pais)}, un destino que el banco vigila "
            "especialmente porque allí acaba el dinero de muchas estafas.",
        )
    if extranjero and not beneficiario_conocido:
        anadir(
            "EXTRANJERO_NUEVO",
            f"Es la primera vez que envía dinero a esta cuenta de {nombre_pais(pais)}.",
        )
    concepto_norm = normalizar_texto(concepto)
    palabras = sorted({p for p in PALABRAS_CONCEPTO_SOSPECHOSO if p in concepto_norm})
    if palabras:
        anadir(
            "CONCEPTO_SOSPECHOSO",
            f"El concepto «{concepto.strip()}» aparece a menudo en intentos de estafa.",
        )
    if saldo > 0 and importe > saldo * config.PORCENTAJE_SALDO_INUSUAL:
        anadir("PORCENTAJE_SALDO", "Es más de la mitad del dinero que tiene en la cuenta.")
    if not beneficiario_conocido and not extranjero:
        anadir("BENEFICIARIO_NUEVO", "Es la primera vez que envía dinero a esta persona.")

    # --- Parámetros personalizados (memoria por cliente) ---
    perfil = perfil or {}
    maximo = perfil.get("importe_max_verificado")
    limite_habitual = maximo * config.MARGEN_IMPORTE_HABITUAL if maximo else None
    if perfil.get("alerta"):
        anadir("CUENTA_CON_ALERTA",
               "Esta cuenta ya apareció en un intento de estafa anterior.")
    if limite_habitual and importe > limite_habitual:
        anadir("IMPORTE_INUSUAL_DESTINATARIO",
               f"Es bastante más de lo que suele enviar a esta persona "
               f"(hasta ahora, como mucho {formatear_euros(maximo)}).")

    codigos = {m["codigo"] for m in motivos}
    requiere = bool(codigos & REGLAS_QUE_ACTIVAN)
    # Lo de siempre: destinatario ya verificado por SilverShield e importe dentro de
    # lo habitual. No se vuelve a molestar a la persona.
    destino_habitual = bool(
        perfil.get("verificado") and limite_habitual and importe <= limite_habitual
        and not codigos & REGLAS_SIEMPRE_VERIFICAR
    )
    if destino_habitual:
        requiere = False
    puntuacion = min(100, sum(PESOS[c] for c in codigos))
    if puntuacion >= 60 or codigos & {"PAIS_ALTO_RIESGO", "CUENTA_CON_ALERTA"}:
        nivel = "alto"
    elif puntuacion >= 30:
        nivel = "medio"
    else:
        nivel = "bajo"

    nivel_final = nivel if requiere else "bajo"
    return {
        "requiere_confirmacion": requiere,
        "nivel": nivel_final,
        # "Conozco al destinatario" (enviar sin verificar) solo se permite si ya le ha
        # enviado dinero antes y no hay señales graves. En las estafas el dinero va
        # siempre a una cuenta nueva: ahí la verificación con SilverShield es obligatoria.
        "permite_autorizacion_directa": beneficiario_conocido and nivel_final != "alto",
        "puntuacion": puntuacion,
        # El motivo "beneficiario nuevo" solo se muestra si acompaña a otro motivo.
        "motivos": motivos if requiere else [],
        "pais": pais,
        "pais_nombre": nombre_pais(pais),
        "extranjero": extranjero,
        "beneficiario_nuevo": not beneficiario_conocido,
        "palabras_concepto": palabras,
        "destino_habitual_verificado": destino_habitual,
        "importe_habitual_max": maximo,
    }
