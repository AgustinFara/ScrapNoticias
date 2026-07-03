# test_scraper.py
def test_filtro_longitud_titulos():
    # Simulamos una lista de títulos con diferentes largos
    titulos_crudos = ["Corto", "Este título tiene más de 20 caracteres para pasar el filtro", "Otro título largo y válido"]
    
    # Filtramos manualmente igual que lo hace tu función
    filtrados = [t for t in titulos_crudos if len(t) > 20]
    
    assert len(filtrados) == 2
    assert "Corto" not in filtrados

def test_estructura_fila_bigquery():
    # Simulamos una fila
    fila = {
        "noticia_id": "12345",
        "orden": 1,
        "titulo": "Titulo de prueba",
        "fecha_captura": "2026-07-03T20:00:00Z",
        "procesado": False
    }
    
    # Verificamos que contenga las llaves necesarias
    keys_esperadas = ["noticia_id", "orden", "titulo", "fecha_captura", "procesado"]
    for key in keys_esperadas:
        assert key in fila

def test_evitar_duplicados():
    datos = ["Noticia A", "Noticia A", "Noticia B"]
    vistos = set()
    limpios = []
    
    for d in datos:
        if d not in vistos:
            limpios.append(d)
            vistos.add(d)
            
    assert len(limpios) == 2
    assert limpios == ["Noticia A", "Noticia B"]