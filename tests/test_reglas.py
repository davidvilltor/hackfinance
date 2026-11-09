import pytest

from backend.reglas_riesgo import (
    IbanInvalido, euros_hablados, evaluar_transferencia, formatear_euros, validar_iban,
)

IBAN_ES = "ES9121000418450200051332"
IBAN_VG = "VG96VPVG0000012345678901"    # Islas Vírgenes Británicas (alto riesgo)
IBAN_PT = "PT50000201231234567890154"   # Portugal (extranjero, no alto riesgo)
SALDO = 12450.0


def codigos(evaluacion):
    return {m["codigo"] for m in evaluacion["motivos"]}


def test_iban_valido_con_espacios():
    assert validar_iban("es91 2100 0418 4502 0005 1332") == IBAN_ES


@pytest.mark.parametrize("iban", [
    "ES9121000418450200051333",   # dígito de control incorrecto
    "ES912100041845020005133",    # longitud incorrecta para España
    "1234",                       # formato
])
def test_iban_invalido(iban):
    with pytest.raises(IbanInvalido):
        validar_iban(iban)


def test_importe_pequeno_a_conocido_no_requiere_confirmacion():
    ev = evaluar_transferencia(120, IBAN_ES, "Cumpleaños", True, SALDO)
    assert ev["requiere_confirmacion"] is False
    assert ev["motivos"] == []


def test_importe_pequeno_a_nuevo_nacional_no_requiere_confirmacion():
    ev = evaluar_transferencia(100, IBAN_ES, "", False, SALDO)
    assert ev["requiere_confirmacion"] is False


@pytest.mark.parametrize("importe,requiere", [(499.99, False), (500, True), (2500, True)])
def test_umbral_500(importe, requiere):
    ev = evaluar_transferencia(importe, IBAN_ES, "Reforma baño", True, SALDO)
    assert ev["requiere_confirmacion"] is requiere
    assert ("IMPORTE_ELEVADO" in codigos(ev)) is requiere


def test_pais_alto_riesgo_por_debajo_del_umbral():
    ev = evaluar_transferencia(300, IBAN_VG, "Pago", False, SALDO)
    assert ev["requiere_confirmacion"] is True
    assert {"PAIS_ALTO_RIESGO", "EXTRANJERO_NUEVO"} <= codigos(ev)
    assert ev["nivel"] == "alto"
    assert ev["pais_nombre"] == "Islas Vírgenes Británicas"


def test_extranjero_nuevo_por_debajo_del_umbral():
    ev = evaluar_transferencia(200, IBAN_PT, "Regalo", False, SALDO)
    assert ev["requiere_confirmacion"] is True
    assert codigos(ev) == {"EXTRANJERO_NUEVO"}


def test_extranjero_conocido_no_requiere_confirmacion():
    ev = evaluar_transferencia(200, IBAN_PT, "Alquiler", True, SALDO)
    assert ev["requiere_confirmacion"] is False


def test_concepto_sospechoso_con_tildes():
    ev = evaluar_transferencia(150, IBAN_ES, "Soporte Técnico Microsoft", False, SALDO)
    assert "CONCEPTO_SOSPECHOSO" in codigos(ev)


def test_mas_de_la_mitad_del_saldo():
    ev = evaluar_transferencia(400, IBAN_ES, "", True, 600)
    assert codigos(ev) == {"PORCENTAJE_SALDO"}


def test_formatos_de_importe():
    assert formatear_euros(1234.5) == "1.234,50 €"
    assert euros_hablados(2500) == "2.500 euros"
    assert euros_hablados(300.5) == "300,50 euros"
