#!/usr/bin/env python3
"""
scraper_proyectos.py — Proyectos ingresados en el Senado → data/proyectos.json
==============================================================================
Adaptado de scraper_senado.py (repo Proyectos-ingresados). Cambios:
  - Salida a data/proyectos.json (no TSV).
  - Lee data/proyectos.json existente: solo procesa expedientes nuevos.
  - Padrón de senadores desde data/senadores.json (construir_senadores.py), con
    fallback a scraping web si el JSON no existe.
  - Modo migración (MIGRAR_TSV): siembra proyectos.json desde un trazabilidad.tsv.
  - Mantiene la lógica de cruce autores→bloques/provincias y el filtro de
    sancionados/archivados.

Variables de entorno opcionales:
    MIGRAR_TSV       Ruta a un trazabilidad.tsv para sembrar la base (one-shot).
    SCRAPE           "0" para saltar el scraping web (solo migración). Default "1".
    FECHA_DESDE      Fecha de inicio fija DD/MM/YYYY (ignora VENTANA_DIAS).
    VENTANA_DIAS     Días hacia atrás para el scraping (default 30).
"""

import csv
import io
import json
import logging
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, timedelta

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: faltan dependencias. Ejecutá: pip install -r requirements.txt")
    sys.exit(1)

try:
    import pdfplumber
    _PDFPLUMBER_OK = True
except ImportError:
    _PDFPLUMBER_OK = False

# ─────────────────────────────── Configuración ────────────────────────────────

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
PROYECTOS_JSON = os.path.join(DATA_DIR, "proyectos.json")
SENADORES_JSON = os.path.join(DATA_DIR, "senadores.json")

MIGRAR_TSV = os.getenv("MIGRAR_TSV", "")
SCRAPE = os.getenv("SCRAPE", "1") != "0"
FECHA_DESDE_FIJA = os.getenv("FECHA_DESDE", "")
VENTANA_DIAS = int(os.getenv("VENTANA_DIAS", "30"))

BASE_URL = "https://www.senado.gob.ar"
URL_BUSQUEDA = f"{BASE_URL}/parlamentario/parlamentaria/"
URL_FECHA_MESA = f"{BASE_URL}/parlamentario/parlamentaria/fechaMesa"

TIPOS_INCLUIR = {"PL", "PD", "PC", "PR", "CA", "AC", "CV"}

ESTADOS_DESCARTAR = frozenset([
    "SANCION DE LEY",
    "EL EXPEDIENTE CADUCO",
    "ENVIADO AL ARCHIVO",
    "VUELVE A DIP",
])

TIPOS = {
    "PL": "Proyecto de Ley",
    "PD": "Proyecto de Declaración",
    "PC": "Proyecto de Comunicación",
    "PR": "Proyecto de Resolución",
    "CA": "Com. de Auditoría",
    "AC": "Acuerdo",
    "CV": "Com. Varias",
}

PAUSA_ENTRE_REQUESTS = 1.0

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


# ─────────────────────────────── Padrón senadores ────────────────────────────

def _sin_tildes(texto):
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def cargar_padron():
    """Devuelve (padron, indice_apellido). Usa data/senadores.json; si no existe,
    lo construye desde los xlsx via construir_senadores."""
    padron = {}
    if os.path.exists(SENADORES_JSON):
        with open(SENADORES_JSON, "r", encoding="utf-8") as f:
            padron = json.load(f)
    else:
        try:
            from construir_senadores import construir_padron
            padron = construir_padron()
            log.info("senadores.json no existe; padrón construido desde xlsx en memoria")
        except Exception as exc:
            log.warning(f"No se pudo construir el padrón: {exc}")
    indice = {}
    for nombre_norm, info in padron.items():
        apellido = nombre_norm.split(",")[0].strip()
        indice.setdefault(_sin_tildes(apellido).upper(), info)
    log.info(f"  → padrón con {len(padron)} senadores")
    return padron, indice


# ─────────────────────────────── Helpers ─────────────────────────────────────

def normalizar_autor(nombre_sitio):
    if not nombre_sitio:
        return ""
    if "," not in nombre_sitio:
        return nombre_sitio.strip().upper()
    apellido, nombre = nombre_sitio.split(",", 1)
    return f"{apellido.strip()}, {nombre.strip()}".upper()


def buscar_info(nombre_norm, padron, indice_apellido):
    if nombre_norm in padron:
        return padron[nombre_norm]
    apellido = nombre_norm.split(",")[0].strip() if "," in nombre_norm else nombre_norm.strip()
    clave = _sin_tildes(apellido).upper()
    if clave in indice_apellido:
        return indice_apellido[clave]
    return {"bloque": "Sin datos", "provincia": ""}


def get_bloques(autores, padron, indice):
    seen, result = set(), []
    for autor in autores:
        bloque = buscar_info(autor, padron, indice).get("bloque", "Sin datos")
        if bloque and bloque not in seen:
            seen.add(bloque)
            result.append(bloque)
    return result


def get_provincias(autores, padron, indice):
    seen, result = set(), []
    for autor in autores:
        prov = buscar_info(autor, padron, indice).get("provincia", "")
        if prov and prov not in seen:
            seen.add(prov)
            result.append(prov)
    return result


def clasificar_autores(extracto, autores_detalle):
    """Separa autores principales de coautores según 'Y OTROS' en el extracto."""
    if not autores_detalle:
        return [], []
    atrib = extracto.split(":")[0].upper() if ":" in extracto else extracto.upper()
    tiene_y_otros = bool(re.search(r'\bY\s+OTR[OA]S?\b', atrib))
    if not tiene_y_otros:
        return autores_detalle, []
    atrib_limpio = re.sub(r'\s*\bY\s+OTR[OA]S?\b', '', atrib).strip()
    partes = re.split(r'[,]\s*|\s+Y\s+', atrib_limpio)
    apellidos_extracto = [p.strip() for p in partes if p.strip()]
    autores, coautores = [], []
    for autor in autores_detalle:
        apellido = autor.split(",")[0].strip().upper()
        es_principal = any(ap in apellido or apellido in ap for ap in apellidos_extracto)
        (autores if es_principal else coautores).append(autor)
    if not autores and autores_detalle:
        autores = [autores_detalle[0]]
        coautores = autores_detalle[1:]
    return autores, coautores


def construir_url_expediente(nro, anio, origen, tipo):
    anio_short = str(anio)[-2:]
    return f"{BASE_URL}/parlamentario/comisiones/verExp/{nro}.{anio_short}/{origen}/{tipo}"


def clave_proyecto(p):
    return (int(p["nro"]), int(p["anio"]), str(p["tipo"]).strip())


# ─────────────────────────────── Persistencia JSON ───────────────────────────

def cargar_proyectos_existentes():
    if not os.path.exists(PROYECTOS_JSON):
        return [], set()
    with open(PROYECTOS_JSON, "r", encoding="utf-8") as f:
        proyectos = json.load(f)
    claves = {clave_proyecto(p) for p in proyectos}
    return proyectos, claves


def guardar_proyectos(proyectos):
    os.makedirs(DATA_DIR, exist_ok=True)
    # Orden: año desc, nro desc
    proyectos.sort(key=lambda p: (int(p["anio"]), int(p["nro"])), reverse=True)
    with open(PROYECTOS_JSON, "w", encoding="utf-8") as f:
        json.dump(proyectos, f, ensure_ascii=False, indent=2)


# ─────────────────────────────── Migración TSV ───────────────────────────────

def migrar_desde_tsv(tsv_path, padron, indice, claves_existentes):
    """Convierte filas del TSV a dicts de proyecto (formato proyectos.json).
    Solo devuelve los que no estén ya en claves_existentes."""
    if not os.path.exists(tsv_path):
        log.warning(f"  TSV no encontrado: {tsv_path}")
        return []
    nuevos = []
    with open(tsv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            nro_str = (row.get("NRO") or "").strip()
            if not nro_str:
                continue
            nro = int(nro_str)
            anio = int((row.get("ANIO") or "2025").strip() or "2025")
            tipo = (row.get("TIPO") or "PL").strip()
            origen = (row.get("ORIGEN") or "S").strip()
            if (nro, anio, tipo) in claves_existentes:
                continue

            caratula = (row.get("CARATULA") or "").strip()
            extracto = caratula[caratula.index(":") + 1:].strip() if ":" in caratula else caratula

            mesa_raw = (row.get("MESA") or "").strip()
            fecha = ""
            fm = re.search(r"(\d{2}/\d{2}/\d{4})", mesa_raw)
            if fm:
                fecha = fm.group(1)

            dae_raw = (row.get("DAE") or "").strip()
            dae = ""
            md = re.match(r"(\d+)", dae_raw)
            if md:
                ma = re.search(r"(\d{4})", dae_raw)
                if ma:
                    dae = f"{md.group(1)}/{ma.group(1)}"

            autor_raw = (row.get("AUTOR") or "").strip()
            todos = []
            if autor_raw:
                for a in autor_raw.split(" - "):
                    a = a.strip().rstrip("-").strip()
                    if a:
                        todos.append(normalizar_autor(a))

            autores, coautores = clasificar_autores(caratula, todos)
            comisiones = [(row.get(f"COM{i}") or "").strip()
                          for i in range(1, 6) if (row.get(f"COM{i}") or "").strip()]

            nuevos.append({
                "nro": nro,
                "anio": anio,
                "tipo": tipo,
                "tipo_label": TIPOS.get(tipo, tipo),
                "extracto": extracto,
                "autores": autores,
                "coautores": coautores,
                "bloques": get_bloques(autores, padron, indice),
                "provincias": get_provincias(autores, padron, indice),
                "comisiones": comisiones,
                "fecha": fecha,
                "dae": dae,
                "origen": origen,
                "url": construir_url_expediente(nro, anio, origen, tipo),
                "sancionado": False,
                "archivado": False,
            })
            claves_existentes.add((nro, anio, tipo))
    log.info(f"  → migración: {len(nuevos)} proyectos nuevos desde TSV")
    return nuevos


# ─────────────────────────────── Scraping web ────────────────────────────────

def obtener_token(session):
    resp = session.get(URL_BUSQUEDA, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    inp = soup.find("input", {"name": "busqueda_proyectos[_token]"})
    if not inp:
        raise RuntimeError("No se encontró busqueda_proyectos[_token]")
    return inp["value"]


def parsear_tabla_resultados(html):
    soup = BeautifulSoup(html, "html.parser")
    tablas = soup.find_all("table")
    if not tablas:
        return []
    tabla = max(tablas, key=lambda t: len(t.find_all("tr")))
    filas = []
    for tr in tabla.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 6:
            continue
        link = tds[0].find("a", href=True)
        if not link:
            continue
        exp_text = tds[0].get_text(strip=True)
        url = link["href"]
        if url and not url.startswith("http"):
            url = BASE_URL + url
        tipo = tds[1].get_text(strip=True)
        origen = tds[2].get_text(strip=True)
        fecha = tds[4].get_text(strip=True)
        caratula = tds[5].get_text(strip=True)
        if tipo not in TIPOS_INCLUIR:
            continue
        m = re.match(r"(\d+)/(\d+)", exp_text)
        if not m:
            continue
        nro = int(m.group(1))
        anio_str = m.group(2)
        anio = int("20" + anio_str) if len(anio_str) == 2 else int(anio_str)
        extracto = caratula[caratula.index(":") + 1:].strip() if ":" in caratula else caratula
        filas.append({
            "nro": nro, "anio": anio, "tipo": tipo, "origen": origen,
            "fecha": fecha, "extracto": extracto, "url": url, "caratula": caratula,
        })
    return filas


def buscar_por_fechas(session, fecha_desde, fecha_hasta):
    token = obtener_token(session)
    payload = {
        "busqueda_proyectos[fechaDesdeMesa][day]": str(fecha_desde.day),
        "busqueda_proyectos[fechaDesdeMesa][month]": str(fecha_desde.month),
        "busqueda_proyectos[fechaDesdeMesa][year]": str(fecha_desde.year),
        "busqueda_proyectos[fechaHastaMesa][day]": str(fecha_hasta.day),
        "busqueda_proyectos[fechaHastaMesa][month]": str(fecha_hasta.month),
        "busqueda_proyectos[fechaHastaMesa][year]": str(fecha_hasta.year),
        "busqueda_proyectos[_token]": token,
    }
    log.info(f"POST {URL_FECHA_MESA} | {fecha_desde:%d/%m/%Y} → {fecha_hasta:%d/%m/%Y}")
    resp = session.post(URL_FECHA_MESA, data=payload, timeout=30)
    resp.raise_for_status()
    todos, pagina, html = [], 1, resp.text
    while True:
        filas = parsear_tabla_resultados(html)
        log.info(f"  Página {pagina}: {len(filas)} expedientes de interés")
        todos.extend(filas)
        soup = BeautifulSoup(html, "html.parser")
        next_link = soup.find("a", href=re.compile(rf"[?&]page={pagina + 1}"))
        if not next_link:
            break
        pagina += 1
        url_sig = next_link["href"]
        if not url_sig.startswith("http"):
            url_sig = BASE_URL + url_sig
        time.sleep(PAUSA_ENTRE_REQUESTS)
        resp = session.get(url_sig, timeout=30)
        resp.raise_for_status()
        html = resp.text
    log.info(f"  → {len(todos)} expedientes en total")
    return todos


def obtener_detalle(session, url):
    resultado = {"autores_raw": [], "comisiones": [], "dae": "", "descartar": False}
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for link in soup.select("a[href*='/senadores/senador/']"):
            nombre = link.get("title", "").strip() or link.get_text(strip=True)
            if nombre:
                resultado["autores_raw"].append(nombre)
        for tr in soup.select("table tr"):
            if "ORDEN DE GIRO" in tr.get_text(" ", strip=True):
                celda = tr.find("td")
                if celda:
                    com = re.sub(r"\s*ORDEN DE GIRO:\s*\d+.*$", "", celda.get_text(strip=True)).strip()
                    if com:
                        resultado["comisiones"].append(com)
        texto = soup.get_text()
        dm = re.search(r"D\.A\.E\.\s*(\d+/\d{4})", texto) or re.search(r"(\d+/\d{4})\s*Tipo:", texto)
        if dm:
            resultado["dae"] = dm.group(1)
        texto_upper = soup.get_text(" ", strip=True).upper()
        for estado in ESTADOS_DESCARTAR:
            if estado in texto_upper:
                resultado["descartar"] = True
                break
    except Exception as exc:
        log.warning(f"    Error en detalle {url}: {exc}")
    return resultado


def scrape_incremental(session, padron, indice, claves_existentes):
    hoy = datetime.now()
    if FECHA_DESDE_FIJA:
        try:
            fecha_desde = datetime.strptime(FECHA_DESDE_FIJA, "%d/%m/%Y")
        except ValueError:
            log.error(f"FECHA_DESDE inválido: '{FECHA_DESDE_FIJA}'")
            return [], set()
    else:
        fecha_desde = hoy - timedelta(days=VENTANA_DIAS)

    try:
        expedientes = buscar_por_fechas(session, fecha_desde, hoy)
    except Exception as exc:
        log.error(f"Error en búsqueda principal: {exc}")
        return [], set()

    # Solo procesar expedientes que no estén ya en la base
    pendientes = [e for e in expedientes
                  if (e["nro"], e["anio"], e["tipo"]) not in claves_existentes]
    log.info(f"  → {len(pendientes)}/{len(expedientes)} expedientes nuevos a procesar")

    nuevos, claves_descartar = [], set()
    for i, exp in enumerate(pendientes, 1):
        log.info(f"  [{i:>3}/{len(pendientes)}] {exp['tipo']} {exp['nro']}/{exp['anio']}")
        time.sleep(PAUSA_ENTRE_REQUESTS)
        detalle = obtener_detalle(session, exp["url"]) if exp["url"] else {}
        if detalle.get("descartar"):
            claves_descartar.add((exp["nro"], exp["anio"], exp["tipo"]))
            continue
        autores_norm = [normalizar_autor(a) for a in detalle.get("autores_raw", []) if a.strip()]
        caratula = exp.get("caratula", exp["extracto"])
        autores, coautores = clasificar_autores(caratula, autores_norm)
        nuevos.append({
            "nro": exp["nro"],
            "anio": exp["anio"],
            "tipo": exp["tipo"],
            "tipo_label": TIPOS.get(exp["tipo"], exp["tipo"]),
            "extracto": exp["extracto"],
            "autores": autores,
            "coautores": coautores,
            "bloques": get_bloques(autores, padron, indice),
            "provincias": get_provincias(autores, padron, indice),
            "comisiones": detalle.get("comisiones", []),
            "fecha": exp["fecha"],
            "dae": detalle.get("dae", ""),
            "origen": exp["origen"],
            "url": exp["url"],
            "sancionado": False,
            "archivado": False,
        })
    return nuevos, claves_descartar


# ─────────────────────────────── Main ─────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("scraper_proyectos iniciado")

    padron, indice = cargar_padron()
    proyectos, claves = cargar_proyectos_existentes()
    log.info(f"  → {len(proyectos)} proyectos ya en data/proyectos.json")

    # 1. Migración desde TSV (opcional, one-shot)
    if MIGRAR_TSV:
        migrados = migrar_desde_tsv(MIGRAR_TSV, padron, indice, claves)
        proyectos.extend(migrados)

    # 2. Scraping incremental web
    if SCRAPE:
        session = requests.Session()
        session.headers.update({
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36")
        })
        nuevos, claves_descartar = scrape_incremental(session, padron, indice, claves)
        # Filtrar sancionados/archivados detectados (también de la base existente)
        if claves_descartar:
            antes = len(proyectos)
            proyectos = [p for p in proyectos if clave_proyecto(p) not in claves_descartar]
            log.info(f"  → {antes - len(proyectos)} proyectos eliminados (sancionados/archivados)")
        proyectos.extend(nuevos)
        log.info(f"  → {len(nuevos)} proyectos nuevos del scraping")

    guardar_proyectos(proyectos)
    con_bloque = sum(1 for p in proyectos if p["bloques"] and p["bloques"] != ["Sin datos"])
    log.info(f"  → TOTAL en proyectos.json: {len(proyectos)} ({con_bloque} con bloque)")
    log.info("scraper_proyectos finalizado.")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
