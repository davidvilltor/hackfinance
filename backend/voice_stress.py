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
    
    # Si hay volumen alto pero el texto es completamente normal, un 25% o 50% de nerviosismo, no pánico directo
    if volumen_alto and len(coincidencias) == 0:
        nivel_estres = max(nivel_estres, 35) # Se queda en Nerviosismo, no salta a Pánico
    elif volumen_alto:
        nivel_estres = max(nivel_estres, 75)
    
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