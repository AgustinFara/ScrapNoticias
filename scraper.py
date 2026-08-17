
import os
import uuid
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from google.cloud import bigquery


class GestorNoticias:
    def __init__(self):
        load_dotenv()
        try:
            self.bq_client = bigquery.Client()
            print("Conexión con BigQuery establecida con éxito.")
        except Exception as error:
            print(f"Error al conectar con BigQuery: {error}")
            raise SystemExit("No se pudo inicializar la conexión. Revisa tus credenciales.")

    def guardar_noticias_en_bigquery(self, rows_to_insert, portal_nombre):
        for row in rows_to_insert:
            row['portal'] = portal_nombre

        table_id = "scrapnoticias-499802.news_analytics.raw_noticias"
        errors = self.bq_client.insert_rows_json(table_id, rows_to_insert)
            
        if not errors:
            print(f"¡Lote de {len(rows_to_insert)} noticias de {portal_nombre} insertado con éxito!")
        else:
            print(f"Errores en el lote de {portal_nombre}: {errors}")


def configurar_interceptores(page):
    """Bloquea ads y recursos pesados una sola vez por pestaña."""
    dominios_ads = [
        "adclick", "doubleclick", "googleads", "pagead", 
        "adnxs", "taboola", "smartadserver", "outbrain",
        "eplanning", "rubiconproject", "analytics", "googletagmanager"
    ]
    
    def interceptar(route):
        req = route.request
        url = req.url.lower()
        # Bloquear por tipo de recurso pesado (ahorra 80% de RAM/Ancho de banda)
        if req.resource_type in ["image", "media", "font", "stylesheet"]:
            return route.abort()
        # Bloquear por dominio publicitario
        if any(ad in url for ad in dominios_ads):
            return route.abort()
        return route.continue_()

    page.route("**/*", interceptar)


def tomar_titulos(page, url, selector, limit=20):
    print(f"Scrapeando {url}...")
    
    try:
        # NAVEGACIÓN: 'commit' libera rapido, ideal si bloqueamos recursos pesados arriba
        page.goto(url, wait_until="commit", timeout=15000) 
    except Exception:
        print(f"Aviso: Timeout de navegación en {url}, intentando extraer con el HTML presente...")

    try:
        page.wait_for_selector(selector, timeout=10000)
    except Exception:
        print(f"Error: No se encontró el selector {selector} en {url}")
        return []

    # EXTRAER TEXTO VÍA ETIQUETA JS (Mucho más rápido y seguro contra elementos detached)
    textos_raw = page.eval_on_selector_all(selector, "elements => elements.map(e => e.innerText)")

    lista_noticias = []
    vistos = set()

    for txt in textos_raw:
        if len(lista_noticias) >= limit:
            break

        titulo = txt.strip()
        if len(titulo) > 20 and titulo not in vistos:
            lista_noticias.append(titulo)
            vistos.add(titulo)

    print(f"Obtenidos {len(lista_noticias)} títulos de {url}")
    return lista_noticias


def main():
    gestor = GestorNoticias()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",  # Crucial para Cloud Run (usa /tmp)
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
                "--no-zygote",
            ]
        )

        try:
            page = browser.new_page()
            # Interceptamos solicitudes pesadas y trackers en la pestaña
            configurar_interceptores(page)

            titulos_infobae = tomar_titulos(page, "https://www.infobae.com/", "h2", 20)
            titulos_destape = tomar_titulos(page, "https://www.eldestapeweb.com/", "h2", 20)

            for lista, portal in [(titulos_infobae, "Infobae"), (titulos_destape, "El Destape")]:
                if not lista:
                    continue
                rows = [
                    {
                        "noticia_id": str(uuid.uuid4()),
                        "orden": i,
                        "titulo": titulo,
                        "fecha_captura": datetime.now(timezone.utc).isoformat(),
                        "procesado": False
                    }
                    for i, titulo in enumerate(lista, 1)
                ]
                gestor.guardar_noticias_en_bigquery(rows, portal)

        finally:
            # Garantiza liberar la RAM de Chromium pase lo que pase
            browser.close()


if __name__ == "__main__":
    main()


'''
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

# def tomar_titulos(page, url, selector, limit=20):
#     print(f"Scrapeando {url}...")
#     #Abre pagina de portal a scrapear
#     page.goto(url, wait_until="domcontentloaded")
#     #Espera a que cargue el javaScript del portal que genera los tags HTML
#     page.wait_for_selector(selector, timeout=5000)

#     #Recoge todos los titulos del portal    
#     elementos = page.query_selector_all(selector)
#     lista_noticias = []
    
#     # Usamos un set temporal solo para verificar duplicados mientras filtramos
#     vistos = set()
    
#     for el in elementos:
#         if len(lista_noticias) >= limit:
#             break

#         # Extraigo solo el texto, elimino espacios en blanco redundantes    
#         titulo = el.inner_text().strip()
        
#         # Filtros: largo y que no esté en 'vistos'
#         if (len(titulo) > 20 and 
#             titulo not in vistos):
            
#             lista_noticias.append(titulo)
#             vistos.add(titulo)
            
#     return lista_noticias

def tomar_titulos(page, url, selector, limit=20):
    print(f"Scrapeando {url}...")

# Intercepta y bloquea llamadas a AdClick y similares
    page.route("**/*", lambda route: route.abort() if any(
        ad in route.request.url.lower() for ad in [
            "adclick", "doubleclick", "googleads", "pagead", 
            "adnxs", "taboola", "smartadserver", "eplanning"
        ]
    ) else route.continue_())
    
    try:
        page.goto(url, wait_until="commit", timeout=30000) 
    except Exception as e:
        print(f"Aviso: Tiempo de carga excedido en {url}, intentando extraer títulos igual...")

    try:
        page.wait_for_selector(selector, timeout=10000)
    except Exception as e:
        print(f"Error: No se encontró el selector {selector} en {url}")
        return []
 
    elementos = page.query_selector_all(selector)
    lista_noticias = []
    
    vistos = set()
    
    for el in elementos:
        if len(lista_noticias) >= limit:
            break

        titulo = el.inner_text().strip()
        
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


def bloquear_publicidad(route):
    url = route.request.url.lower()
    # Dominios y redes de publicidad a interceptar
    dominios_ads = [
        "adclick", "doubleclick", "googleads", "pagead", 
        "adnxs", "taboola", "smartadserver", "outbrain",
        "eplanning", "rubiconproject"
    ]
    if any(ad in url for ad in dominios_ads):
        route.abort()
    else:
        route.continue_()

#Proceso Principal
def main():

    gestor = GestorNoticias()

    with sync_playwright() as p:
        #Lanza navegador "Headlesss"
        #Headless=True significa que el navegador no se abrirá visualmente (ahorra RAM)
        #browser = p.chromium.launch(headless=True)
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",  # Crucial: usa /tmp para no saturar memoria RAM
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
                "--no-zygote",
            ]
        )
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

'''
