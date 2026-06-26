#!/usr/bin/env python3
"""
scraper_agenda.py — Boletines de Reuniones de Comisiones → data/agenda.json
============================================================================
Lista los boletines en /parlamentario/boletines/, descarga los nuevos (IDs más
altos que el último procesado), parsea cada reunión (fecha, hora, comisión, salón,
tipo y temario) y acumula en data/agenda.json (las reuniones pasadas se mantienen).

Tipo de reunión:
  - Por la sección del PDF: REUNIONES DE SENADORES → 'senadores',
    REUNIONES DE ASESORES → 'asesores', REUNIONES BICAMERALES → 'bicameral'.
  - Ajuste: cualquier reunión cuya comisión contenga la palabra BICAMERAL se
    tipifica como 'bicameral', sin importar la sección.

Tolerante a fallos: si un boletín falla, se registra el error y se continúa.
"""

import io
import json
import logging
import os
import re
import sys

try:
    import requests
    from bs4 import BeautifulSoup
    import pdfplumber
except ImportError:
    print("ERROR: faltan dependencias. Ejecutá: pip install -r requirements.txt")
    sys.exit(1)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
AGENDA_JSON = os.path.join(DATA_DIR, "agenda.json")
BOLETINES_PROCESADOS_JSON = os.path.join(DATA_DIR, "boletines_procesados.json")

BASE_URL = "https://www.senado.gob.ar"
URL_BOLETINES = f"{BASE_URL}/parlamentario/boletines/"

HEADERS = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36")}

DIAS_SEMANA = re.compile(
    r"\b(LUNES|MARTES|MI[EÉ]RCOLES|JUEVES|VIERNES|S[AÁ]BADO|DOMINGO)\b", re.IGNORECASE)

# Encabezados de sección
SEC_SENADORES = re.compile(r"REUNIONES\s+DE\s+SENADORES", re.IGNORECASE)
SEC_ASESORES = re.compile(r"REUNIONES\s+DE\s+ASESORES", re.IGNORECASE)
SEC_BICAMERAL = re.compile(r"REUNIONES\s+BICAMERAL", re.IGNORECASE)

# Número de expediente: S-565/25, P.E-121/26, CD-12/26, O.V-3/26, etc.
RE_EXPTE_NUM = re.compile(r"EXPTE\.?\s*([A-ZÑ]{1,3}(?:\.[A-ZÑ]{1,2})?-?\s*\d+/\d+)", re.IGNORECASE)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


# ─────────────────────────────── Helpers ─────────────────────────────────────

def _limpiar(texto):
    if not texto:
        return ""
    return re.sub(r"\s+", " ", texto).strip()


def _es_fila_encabezado(row):
    return (isinstance(row[0], str) and "FECHA" in row[0].upper()
            and len(row) > 1 and isinstance(row[1], str) and "HORA" in row[1].upper())


def parsear_celda_fecha(celda):
    dia, fecha = "", ""
    for l in [l.strip() for l in (celda or "").split("\n") if l.strip()]:
        if DIAS_SEMANA.match(l):
            dia = l.upper()
        elif re.match(r"^\d{1,2}/\d{2}$", l):
            fecha = l
    return dia, fecha


def parsear_celda_comisiones(celda):
    comisiones, modalidad = [], ""
    for l in [l.strip() for l in (celda or "").split("\n") if l.strip()]:
        m = re.match(r"^\((.+)\)$", l)
        if m:
            modalidad = m.group(1).strip()
        else:
            comisiones.append(l)
    return comisiones, modalidad


def parsear_celda_salon(celda):
    lineas = [l.strip() for l in (celda or "").split("\n") if l.strip()]
    salon = lineas[0] if lineas else ""
    resto = " ".join(lineas[1:]) if len(lineas) > 1 else ""
    return salon, _limpiar(f"{salon} {resto}")


def parsear_temario(texto):
    """Divide el texto de temario en expedientes [{numero, extracto}].
    Si no hay EXPTE., devuelve un único item de tipo texto."""
    texto = (texto or "").strip()
    if not texto:
        return []
    # Quitar encabezados de grupo (PROYECTOS DE ...:) — quedan implícitos en el extracto
    if "EXPTE" not in texto.upper():
        return [{"numero": "", "extracto": _limpiar(texto)}]
    partes = re.split(r"(?=EXPTE\.)", texto, flags=re.IGNORECASE)
    items = []
    for parte in partes:
        parte = _limpiar(parte)
        if not parte or "EXPTE" not in parte.upper():
            continue
        m = RE_EXPTE_NUM.search(parte)
        numero = re.sub(r"\s+", "", m.group(1)).upper() if m else ""
        # Extracto: texto tras el número
        if m:
            extracto = parte[m.end():].lstrip(" ,:.-").strip()
        else:
            extracto = parte
        items.append({"numero": numero, "extracto": _limpiar(extracto)})
    return items


def tipo_reunion(seccion, comisiones):
    """Tipifica según sección, salvo que alguna comisión contenga BICAMERAL."""
    if any("BICAMERAL" in c.upper() for c in comisiones):
        return "bicameral"
    return seccion


# ─────────────────────────────── Parseo del boletín ──────────────────────────

def extraer_tablas_y_texto(contenido_pdf):
    all_rows, textos = [], []
    with pdfplumber.open(io.BytesIO(contenido_pdf)) as pdf:
        for page in pdf.pages:
            for tabla in page.extract_tables():
                all_rows.extend(tabla)
            textos.append(page.extract_text(x_tolerance=3, y_tolerance=3) or "")
    return all_rows, "\n".join(textos)


def extraer_numero_boletin(texto):
    m = re.search(r"N[°ºo]\s*(\d+/\d+)", texto[:200])
    return m.group(1) if m else ""


def parsear_reuniones(all_rows):
    """Recorre todas las filas de tablas y extrae todas las reuniones de todas
    las secciones (senadores / asesores / bicameral)."""
    reuniones = []
    seccion = "senadores"  # default: el boletín empieza con senadores
    reunion = None
    esperando_datos = False

    def cerrar():
        nonlocal reunion
        if reunion is not None:
            # Compactar temario crudo en expedientes
            raw = reunion.pop("_temario_raw", "")
            reunion["temario"] = parsear_temario(raw)
            reunion["tipo"] = tipo_reunion(seccion, reunion["comisiones"])
            reuniones.append(reunion)
            reunion = None

    for row in all_rows:
        if not row:
            continue
        col0 = _limpiar(row[0] or "")
        up = col0.upper()

        # Cambio de sección
        if SEC_ASESORES.search(up):
            cerrar(); seccion = "asesores"; continue
        if SEC_BICAMERAL.search(up):
            cerrar(); seccion = "bicameral"; continue
        if SEC_SENADORES.search(up):
            cerrar(); seccion = "senadores"; continue

        # Encabezado de reunión
        if _es_fila_encabezado(row):
            cerrar()
            esperando_datos = True
            continue

        # Fila de datos (hora en col1)
        if esperando_datos and len(row) > 1 and row[1] and re.match(r"^\d{1,2}:\d{2}$", _limpiar(row[1])):
            dia, fecha = parsear_celda_fecha(row[0] or "")
            comisiones, modalidad = parsear_celda_comisiones(row[2] if len(row) > 2 else "")
            salon, salon_completo = parsear_celda_salon(row[3] if len(row) > 3 else "")
            reunion = {
                "seccion": seccion,
                "dia": dia,
                "fecha": fecha,
                "hora": _limpiar(row[1]),
                "modalidad": modalidad,
                "comisiones": comisiones,
                "salon": salon,
                "salon_completo": salon_completo,
                "_temario_raw": "",
                "temario": [],
            }
            esperando_datos = False
            continue

        if up == "TEMARIO" or not col0:
            continue

        # Fila de contenido del temario
        if reunion is not None and (len(row) < 2 or row[1] is None):
            reunion["_temario_raw"] += "\n" + (row[0] or "")

    cerrar()
    return reuniones


# ─────────────────────────────── Listado de boletines ────────────────────────

def listar_boletines(session):
    """Devuelve [{id, numero, url}] ordenados por id descendente."""
    resp = session.get(URL_BOLETINES, timeout=45)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    boletines = []
    for a in soup.find_all("a", href=re.compile(r"descargarBoletinReunion/(\d+)", re.I)):
        m = re.search(r"descargarBoletinReunion/(\d+)", a["href"])
        if not m:
            continue
        bid = int(m.group(1))
        href = a["href"]
        url = href if href.startswith("http") else BASE_URL + href
        # Número de boletín desde la fila (columna 1)
        numero = ""
        tr = a.find_parent("tr")
        if tr:
            tds = tr.find_all("td")
            if tds:
                numero = tds[0].get_text(strip=True)
        boletines.append({"id": bid, "numero": numero, "url": url})
    boletines.sort(key=lambda b: b["id"], reverse=True)
    return boletines


def descargar_pdf(session, url):
    resp = session.get(url, timeout=90)
    resp.raise_for_status()
    return resp.content


# ─────────────────────────────── Persistencia ────────────────────────────────

def cargar_json(path, default):
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except Exception as exc:
            log.warning(f"No se pudo leer {path}: {exc}")
    return default


def guardar_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def clave_reunion(r):
    return (r.get("fecha", ""), r.get("hora", ""), tuple(r.get("comisiones", [])), r.get("tipo", ""))


# ─────────────────────────────── Main ─────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("scraper_agenda iniciado")

    agenda = cargar_json(AGENDA_JSON, {"reuniones": []})
    if isinstance(agenda, list):
        agenda = {"reuniones": agenda}
    reuniones_acum = agenda.get("reuniones", [])
    indice = {clave_reunion(r): i for i, r in enumerate(reuniones_acum)}

    estado = cargar_json(BOLETINES_PROCESADOS_JSON, {"ultimo_id": 0, "procesados": []})
    ultimo_id = estado.get("ultimo_id", 0)
    procesados = set(estado.get("procesados", []))

    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        boletines = listar_boletines(session)
    except Exception as exc:
        log.error(f"No se pudo listar boletines: {exc}")
        return

    nuevos = [b for b in boletines if b["id"] > ultimo_id and b["id"] not in procesados]
    log.info(f"  → {len(boletines)} boletines listados, {len(nuevos)} nuevos (último_id={ultimo_id})")

    nuevas_reuniones = 0
    max_id = ultimo_id
    # Procesar de menor a mayor para que el más nuevo prevalezca en duplicados
    for bol in sorted(nuevos, key=lambda b: b["id"]):
        bid = bol["id"]
        log.info(f"  Boletín id={bid} (N° {bol['numero']})")
        try:
            contenido = descargar_pdf(session, bol["url"])
            all_rows, texto = extraer_tablas_y_texto(contenido)
            numero_pdf = extraer_numero_boletin(texto) or bol["numero"]
            reuniones = parsear_reuniones(all_rows)
            log.info(f"    → {len(reuniones)} reunión(es)")
            for r in reuniones:
                r["boletin_id"] = bid
                r["boletin_numero"] = numero_pdf
                k = clave_reunion(r)
                if k in indice:
                    reuniones_acum[indice[k]] = r  # reemplaza por la versión más nueva
                else:
                    indice[k] = len(reuniones_acum)
                    reuniones_acum.append(r)
                    nuevas_reuniones += 1
            procesados.add(bid)
            max_id = max(max_id, bid)
        except Exception as exc:
            log.error(f"    ✗ Error en boletín {bid}: {exc}")
            continue

    agenda["reuniones"] = reuniones_acum
    guardar_json(AGENDA_JSON, agenda)
    guardar_json(BOLETINES_PROCESADOS_JSON,
                 {"ultimo_id": max_id, "procesados": sorted(procesados)})
    log.info(f"  → {nuevas_reuniones} reuniones nuevas; {len(reuniones_acum)} en agenda.json; "
             f"último_id={max_id}")
    log.info("scraper_agenda finalizado.")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
