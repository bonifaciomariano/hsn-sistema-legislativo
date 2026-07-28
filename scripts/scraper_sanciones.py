#!/usr/bin/env python3
"""
scraper_sanciones.py — Boletines de Novedades del HSN → data/sanciones.json
=============================================================================
Consulta el endpoint de datos abiertos con el listado de Boletines de
Novedades (uno por sesión), descarga en memoria el PDF de cada boletín nuevo
y extrae, por tabla (pdfplumber `extract_tables`), los ítems de las secciones:
  - PROYECTOS DE LEY                                          -> "ley"
  - PROYECTOS DE DECRETO, RESOLUCIÓN, COMUNICACIÓN Y DECLARACIÓN
                                                    -> "decreto_res_com_dec"
  - ACUERDOS CONSIDERADOS                                      -> "acuerdo"
  - MOCIONES DE PREFERENCIA (solo resultado APROBADA)          -> "preferencia"
Las demás secciones (Cuestiones de privilegio, Ingreso acuerdos, Cambio de
giro, Homenajes, Diarios de sesiones, Elección de autoridades) se ignoran.

Es incremental: lee data/sanciones_procesados.json (lista de números de
boletín ya procesados, ej. "3/26") y sólo baja/parsea los boletines nuevos.
Acumula los ítems extraídos en data/sanciones.json.

Tolerante a fallos: si falla la descarga o el parseo de un boletín (o de una
fila puntual), se registra el error y se continúa con lo demás.

Variables de entorno opcionales:
    TEST               "1" para modo de prueba: procesa un único boletín
                        (el más reciente no procesado), imprime resultados
                        y no toca data/sanciones.json ni sanciones_procesados.json.
    SANCIONES_MIN_ANIO  año mínimo (de la fecha de sesión) a considerar;
                        default 2025 (el listado completo va hasta 2004).
"""

import json
import logging
import os
import re
import sys
import time
from io import BytesIO

try:
    import requests
    import pdfplumber
except ImportError:
    print("ERROR: faltan dependencias. Ejecutá: pip install -r requirements.txt")
    sys.exit(1)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
SANCIONES_JSON = os.path.join(DATA_DIR, "sanciones.json")
PROCESADOS_JSON = os.path.join(DATA_DIR, "sanciones_procesados.json")

TEST = os.getenv("TEST", "") == "1"
MIN_ANIO = int(os.getenv("SANCIONES_MIN_ANIO", "2025"))

URL_LISTADO = "https://www.senado.gob.ar/micrositios/DatosAbiertos/ExportarListadoBoletinNovedades/json"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "application/json,text/html,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
}

PAUSA_ENTRE_REQUESTS = 1.0

# Expediente: "S-289/26", "PE-98/26", "CD-20/24" (origen puede traer puntos: "P.E-133/26")
RE_EXP = re.compile(r"\b([A-ZÑ.]{1,5}-\d+/\d{2})\b")

# Encabezados de secciones a ignorar por completo (título de sección, no de columnas)
HEADERS_IGNORAR = (
    "CUESTIONES DE PRIVILEGIO",
    "INGRESO ACUERDOS",
    "CAMBIO DE GIRO",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


def obtener_listado_boletines():
    """Descarga y parsea el listado de boletines. El JSON del endpoint trae
    comas colgantes (no es JSON estricto) -> se limpia con regex antes de
    parsear."""
    r = requests.get(URL_LISTADO, headers=HEADERS, timeout=30)
    r.raise_for_status()
    limpio = re.sub(r",(\s*[}\]])", r"\1", r.text)
    data = json.loads(limpio)
    filas = data.get("table", {}).get("rows", [])

    boletines = []
    for fila in filas:
        nro_raw = (fila.get("NUMERO BOLETIN") or "").strip()
        fecha = (fila.get("FECHA SESION") or "").strip()
        url = (fila.get("URL") or "").strip()
        if not nro_raw or not url:
            continue
        nro_boletin = nro_raw.replace("-", "/", 1)
        try:
            anio = int(fecha.split("-")[0])
        except (ValueError, IndexError):
            anio = None
        if anio is not None and anio < MIN_ANIO:
            continue
        boletines.append({"nro_boletin": nro_boletin, "fecha_sesion": fecha, "url": url})
    return boletines


def cargar_procesados():
    if not os.path.exists(PROCESADOS_JSON):
        return set()
    with open(PROCESADOS_JSON, "r", encoding="utf-8") as f:
        return set(json.load(f))


def guardar_procesados(procesados):
    with open(PROCESADOS_JSON, "w", encoding="utf-8") as f:
        json.dump(sorted(procesados), f, ensure_ascii=False, indent=2)


def cargar_sanciones():
    if not os.path.exists(SANCIONES_JSON):
        return []
    with open(SANCIONES_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_sanciones(items):
    with open(SANCIONES_JSON, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def norm_celda(c):
    return " ".join((c or "").split())


def extraer_expedientes(texto):
    encontrados = []
    for m in RE_EXP.finditer(texto or ""):
        origen, resto = m.group(1).split("-", 1)
        encontrados.append(f"{origen.replace('.', '')}-{resto}")
    return encontrados


def parsear_od_nro(celda):
    m = re.match(r"\s*(\d+)", celda or "")
    return int(m.group(1)) if m else None


def detectar_header(celdas):
    """Devuelve ('section', nombre_o_None) si la fila es un encabezado de
    sección o de columnas; None si es una fila de datos a procesar."""
    c0 = celdas[0].upper() if celdas else ""

    if celdas == ["OD", "ACUERDOS CONSIDERADOS", "RESULTADO", "OBSERVACIONES"]:
        return ("section", "acuerdo")
    if c0.startswith("MOCIONES DE PREFERENCIA"):
        return ("section", "preferencia")
    if c0 == "PROYECTOS DE LEY":
        return ("section", "ley")
    if c0.startswith("PROYECTOS DE DECRETO"):
        return ("section", "decreto_res_com_dec")
    if any(c0.startswith(h) for h in HEADERS_IGNORAR):
        return ("section", None)
    if c0 in ("OD", "N° DE EXPEDIENTE", "NRO DE EXPEDIENTE", "N DE EXPEDIENTE"):
        return ("col_header", None)
    return None


def procesar_fila(celdas, seccion, nro_boletin, fecha_sesion):
    if seccion == "preferencia":
        if len(celdas) < 3:
            return []
        texto, resultado, observaciones = celdas[0], celdas[1], celdas[2]
        if resultado.strip().upper() != "APROBADA":
            return []
        od_nro = None
    else:
        if len(celdas) < 4:
            return []
        od_celda, texto, resultado, observaciones = celdas[0], celdas[1], celdas[2], celdas[3]
        od_nro = None if od_celda.strip().upper() == "S/T" else parsear_od_nro(od_celda)

    items = []
    for exp in extraer_expedientes(texto):
        items.append({
            "expediente": exp,
            "od_nro": od_nro,
            "resultado": resultado,
            "observaciones": observaciones,
            "seccion": seccion,
            "fecha_sesion": fecha_sesion,
            "nro_boletin": nro_boletin,
        })
    return items


def parsear_boletin(pdf_bytes, nro_boletin, fecha_sesion):
    items = []
    errores = []
    seccion_actual = None
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for pagina in pdf.pages:
                try:
                    tablas = pagina.extract_tables()
                except Exception as e:
                    errores.append(f"extract_tables falló en una página: {e}")
                    continue
                for tabla in tablas:
                    for fila in tabla:
                        try:
                            celdas = [norm_celda(c) for c in fila]
                            marca = detectar_header(celdas)
                            if marca is not None:
                                if marca[0] == "section":
                                    seccion_actual = marca[1]
                                continue
                            if not seccion_actual:
                                continue
                            items.extend(procesar_fila(celdas, seccion_actual, nro_boletin, fecha_sesion))
                        except Exception as e:
                            errores.append(f"fila en sección {seccion_actual}: {e}")
    except Exception as e:
        errores.append(f"apertura/lectura del PDF falló: {e}")
    return items, errores


def descargar_boletin(url):
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.content


def main():
    log.info("=" * 60)
    log.info("scraper_sanciones iniciado" + (" (TEST)" if TEST else ""))

    try:
        boletines = obtener_listado_boletines()
    except Exception as e:
        log.error(f"ERROR al obtener listado de boletines: {e}")
        return
    log.info(f"  -> {len(boletines)} boletines disponibles (anio >= {MIN_ANIO})")

    procesados = cargar_procesados()
    pendientes = [b for b in boletines if b["nro_boletin"] not in procesados]
    log.info(f"  -> {len(pendientes)} boletines pendientes de procesar")

    if TEST:
        pendientes = pendientes[:1]

    sanciones = cargar_sanciones()
    total_nuevos = {"ley": 0, "decreto_res_com_dec": 0, "acuerdo": 0, "preferencia": 0}

    for b in pendientes:
        nro_boletin = b["nro_boletin"]
        log.info(f"  Procesando boletín {nro_boletin} ({b['fecha_sesion']})...")
        try:
            pdf_bytes = descargar_boletin(b["url"])
        except Exception as e:
            log.error(f"    ERROR al descargar {nro_boletin}: {e}")
            continue

        items, errores = parsear_boletin(pdf_bytes, nro_boletin, b["fecha_sesion"])
        for err in errores:
            log.warning(f"    [{nro_boletin}] {err}")

        for it in items:
            total_nuevos[it["seccion"]] = total_nuevos.get(it["seccion"], 0) + 1
        log.info(f"    -> {len(items)} items extraidos")

        if TEST:
            print(json.dumps(items, ensure_ascii=False, indent=2))
        else:
            sanciones.extend(items)
            procesados.add(nro_boletin)

        time.sleep(PAUSA_ENTRE_REQUESTS)

    if TEST:
        log.info("TEST: no se escribió data/sanciones.json ni sanciones_procesados.json")
        return

    guardar_sanciones(sanciones)
    guardar_procesados(procesados)
    log.info(f"  -> nuevos por seccion: {total_nuevos}")
    log.info(f"  -> TOTAL en sanciones.json: {len(sanciones)}")
    log.info("scraper_sanciones finalizado.")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
