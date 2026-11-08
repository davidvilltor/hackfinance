def analizar_estres(texto_usuario: str, volumen_alto: bool = False) -> dict:
    """
    Analiza el texto y los metadatos acústicos buscando indicadores de estrés.
    """
    texto_min = texto_usuario.lower()
    
    palabras_alerta = [
        "rápido", "rapido", "urgente", "inmediato", "bloqueo", 
        "multa", "peligro", "policía", "policia", "descargar", 
        "cárcel", "carcel", "delito", "juzgado", "consecuencias"
    ]
    
    coincidencias = [palabra for palabra in palabras_alerta if palabra in texto_min]
    nivel_estres = len(coincidencias) * 25  
    
    # EL TRUCO ACÚSTICO: Si la web detectó que el abuelo subió el volumen, forzamos el pánico
    if volumen_alto:
        nivel_estres = max(nivel_estres, 80)
        coincidencias.append("(Tono de voz alterado detectado acústicamente)")
    
    nivel_estres = min(nivel_estres, 100)
    
    estado = "Tranquilo"
    if nivel_estres >= 50:
        estado = "Pánico / Alta Coacción"
    elif nivel_estres > 0:
        estado = "Nerviosismo"
        
    return {
        "nivel_porcentaje": nivel_estres,
        "estado": estado,
        "palabras_detectadas": coincidencias
    }