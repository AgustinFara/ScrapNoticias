
# Permite automatización web síncrona
from playwright.sync_api import sync_playwright

# Permite guardar en tablas BigQuery
from google.cloud import bigquery

#Libreria para generar índices irrepetibles
import uuid

#Libreria para manejar las fechas
from datetime import datetime, timezone

#librerias para variables .env
import os
from dotenv import load_dotenv

#Constructor
class GestorNoticias:
    def __init__(self):
            # Carga las variables del archivo .env al entorno del sistema
        load_dotenv()
        #Inicializa Cliente BigQuery
        try:
            # Intentamos crear la conexión
            self.bq_client = bigquery.Client()
            print("Conexión con BigQuery establecida con éxito.")
        except Exception as error:
            # Si falla, capturamos el error y terminamos el programa de forma elegante
            print(f"Error al conectar con BigQuery: {error}")
            # Esto detiene la ejecución para que no intentes usar un cliente que no existe
            raise SystemExit("No se pudo inicializar la conexión. Revisa tus credenciales.")



#Defino funcion para obtener titulares(contiene 4 variables de entrada)
#page: Le paso la "pestaña" que abrí en main
#url: Url de la página a scrapear
#selector: Tipo de etiqueta HTML que quiero scrapear
#limit: Cantidad de noticias a scrapear
def tomar_titulos(page, url, selector, limit=20):
    print(f"Scrapeando {url}...")
    #Abre pagina de portal a scrapear
    page.goto(url, wait_until="domcontentloaded")
    #Espera a que cargue el javaScript del portal que genera los tags HTML
    page.wait_for_selector(selector, timeout=5000)

    #Recoge todos los titulos del portal    
    elementos = page.query_selector_all(selector)
    lista_noticias = []
    
    # Usamos un set temporal solo para verificar duplicados mientras filtramos
    vistos = set()
    
    for el in elementos:
        if len(lista_noticias) >= limit:
            break

        # Extraigo solo el texto, elimino espacios en blanco redundantes    
        titulo = el.inner_text().strip()
        
        # Filtros: largo y que no esté en 'vistos'
        if (len(titulo) > 20 and 
            titulo not in vistos):
            
            lista_noticias.append(titulo)
            vistos.add(titulo)
            
    return lista_noticias

def guardar_noticias_en_bigquery(self,rows_to_insert,portal_nombre):
    
    for row in rows_to_insert:
        row['portal'] = portal_nombre

    #Genero variable con id de tabla    
    table_id = "scrapnoticias-499802.news_analytics.raw_noticias"
    
    # --- Guardar todos los titulos del portal ---
    errors = self.bq_client.insert_rows_json(table_id, rows_to_insert)
        
    if errors == []:
        print("¡Lote de 20 noticias insertado con éxito en BigQuery!")
    else:
        print(f"Errores en el lote: {errors}")


#Proceso Principal
def main():

    gestor = GestorNoticias()

    with sync_playwright() as p:
        #Lanza navegador "Headlesss"
        #Headless=True significa que el navegador no se abrirá visualmente (ahorra RAM)
        browser = p.chromium.launch(headless=True)
        #Abro "Pestaña" (Una página es una pestaña individual dentro del navegador)
        page = browser.new_page()
        
        # Scrapeamos Infobae y El Destape buscando 20 de cada uno
        # (Al final el main seleccionará las mejores 20 del conjunto total)
        titulos_infobae = tomar_titulos(page, "https://www.infobae.com/", "h2", 20)
        titulos_destape = tomar_titulos(page, "https://www.eldestapeweb.com/", "h2", 20)
        

        # Preparamos los lotes
        for lista, portal in [(titulos_infobae, "Infobae"), (titulos_destape, "El Destape")]:
            rows = []
            for i, titulo in enumerate(lista, 1):
                rows.append({
                    "noticia_id": str(uuid.uuid4()),
                    "orden": i,
                    "titulo": titulo,
                    "fecha_captura": datetime.now(timezone.utc).isoformat(),
                    "procesado": False
                })
            # Usamos el método de la clase
            
            guardar_noticias_en_bigquery(gestor,rows, portal)


        # Libero recursos del sistema
        browser.close()

if __name__ == "__main__":
    main()


