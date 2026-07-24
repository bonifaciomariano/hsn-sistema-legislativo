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

Dos formatos de boletín conviven (el sitio cambió de formato en julio de 2026):
  - "Tabular" (histórico): tablas FECHA|HORA|COMISIÓN|SALÓN. El encabezado de
    sección ("REUNIONES DE ASESORES", etc.) NO forma parte de ninguna tabla —
    pdfplumber lo descarta si sólo se leen extract_tables(). Por eso se resuelve
    la sección de cada tabla por posición vertical (ver extraer_filas_con_seccion).
  - "Texto libre" (actual): sin tablas, con marcadores 🗓/🕑/📍/📋 y secciones
    "AGENDA DE SENADORES" / "AGENDA DE ASESORES".

Tolerante a fallos: si un boletín falla, se registra el error y se continúa.
"""

import io
import json
import logging
import os
import re
import sys
import unicodedata

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
COMISIONES_JSON = os.path.join(DATA_DIR, "comisiones.json")

BASE_URL = "https://www.senado.gob.ar"
URL_BOLETINES = f"{BASE_URL}/parlamentario/boletines/"

HEADERS = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36")}

DIAS_SEMANA = re.compile(
    r"\b(LUNES|MARTES|MI[EÉ]RCOLES|JUEVES|VIERNES|S[AÁ]BADO|DOMINGO)\b", re.IGNORECASE)

# Encabezados de sección (formato tabular)
SEC_SENADORES = re.compile(r"REUNIONES\s+DE\s+SENADORES", re.IGNORECASE)
SEC_ASESORES = re.compile(r"REUNIONES\s+DE\s+ASESORES", re.IGNORECASE)
SEC_BICAMERAL = re.compile(r"REUNIONES\s+BICAMERAL", re.IGNORECASE)

# Encabezados de sección (formato texto libre)
RE_AGENDA_SEC = re.compile(r"^AGENDA\s+DE\s+(SENADORES|ASESORES)\s*$", re.IGNORECASE)

# Número de expediente: S-565/25, P.E-121/26, CD-12/26, O.V-3/26, etc.
RE_EXPTE_NUM = re.compile(r"EXPTE\.?\s*([A-ZÑ]{1,3}(?:\.[A-ZÑ]{1,2})?-?\s*\d+/\d+)", re.IGNORECASE)
# Igual, pero sin exigir el prefijo "EXPTE." (el formato nuevo no lo trae)
RE_EXP_TOKEN = re.compile(r"\b([A-ZÑ]{1,3}(?:\.[A-ZÑ]{1,2})?-\d+/\d+)\b")

MESES_NOMBRE = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
    "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12,
}
RE_FECHA_LINEA = re.compile(
    r"🗓\s*([A-ZÁÉÍÓÚÑ]+)\s+(\d{1,2})\s+DE\s+([A-ZÁÉÍÓÚÑ]+)\s*🕑\s*(.+?)\s*📍\s*(.+)$")

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


def _norm_com(s):
    """Normaliza nombre de comisión: mayúsculas, sin tildes, sin prefijo 'DE '."""
    if not s:
        return ""
    s = unicodedata.normalize("NFD", s.upper().strip())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"^DE\s+", "", s)
    s = re.sub(r"[^A-Z0-9, ]", "", s)
    return s


def cargar_comisiones_norm():
    """Nombres normalizados de las comisiones permanentes (data/comisiones.json),
    usados para reconocer líneas de nombre de comisión en el formato de texto libre."""
    try:
        data = json.load(open(COMISIONES_JSON, encoding="utf-8"))
        return {_norm_com(c["nombre"]) for c in data}
    except Exception:
        return set()


def _mapear_columnas(row):
    """Mapea las columnas FECHA/HORA/COMISIÓN/SALÓN a su índice real dentro de
    la fila. pdfplumber a veces intercala columnas vacías (tablas de 5-6 celdas
    en vez de 4), así que no se puede asumir posición fija 0/1/2/3."""
    cmap = {}
    for i, cell in enumerate(row):
        if not isinstance(cell, str):
            continue
        u = cell.upper()
        if "FECHA" in u and "fecha" not in cmap:
            cmap["fecha"] = i
        elif "HORA" in u and "hora" not in cmap:
            cmap["hora"] = i
        elif "COMISI" in u and "comision" not in cmap:
            cmap["comision"] = i
        elif ("SALÓN" in u or "SALON" in u) and "salon" not in cmap:
            cmap["salon"] = i
    return cmap


def _es_fila_encabezado(row):
    cmap = _mapear_columnas(row)
    return "fecha" in cmap and "hora" in cmap


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
    """Divide el texto de temario (formato tabular) en expedientes
    [{numero, extracto}]. Si no hay EXPTE., devuelve un único item de tipo texto."""
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


def parsear_temario_texto_libre(texto):
    """Divide el texto de temario (formato texto libre, sin 'EXPTE.') en
    expedientes [{numero, extracto}], separando por el patrón S-123/25 /
    P.E-123/26 / etc. donde aparezca. Sin expedientes -> un único item de texto."""
    texto = _limpiar(texto)
    if not texto:
        return []
    matches = list(RE_EXP_TOKEN.finditer(texto))
    if not matches:
        return [{"numero": "", "extracto": texto}]
    items = []
    if matches[0].start() > 0:
        pre = texto[:matches[0].start()].strip(" ,:.-")
        # descartar preámbulos que son sólo una etiqueta de grupo (ej. "PROYECTO DE LEY:")
        if pre and not re.match(r"^[A-ZÁÉÍÓÚÑ ,]+$", pre):
            items.append({"numero": "", "extracto": pre})
    for i, m in enumerate(matches):
        numero = m.group(1).upper()
        inicio = m.end()
        fin = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
        extracto = texto[inicio:fin]
        # limpiar una etiqueta de grupo que haya quedado pegada al final (ej. "... PROYECTOS DE COMUNICACIÓN:")
        # antes de recortar los separadores, porque el ':' de la etiqueta es la pista.
        extracto = re.sub(r"\s*[A-ZÁÉÍÓÚÑ ,]{6,}:\s*$", "", extracto)
        extracto = extracto.strip(" ,:.-")
        items.append({"numero": numero, "extracto": extracto})
    return items


def tipo_reunion(seccion, comisiones):
    """Tipifica según sección, salvo que alguna comisión contenga BICAMERAL."""
    if any("BICAMERAL" in c.upper() for c in comisiones):
        return "bicameral"
    return seccion


# ─────────────────────────────── Parseo del boletín (formato tabular) ────────

def _lineas_de_pagina(page):
    """Agrupa las palabras de una página por línea (mismo 'top' aproximado),
    devolviendo [(top, texto_línea), ...] de arriba hacia abajo. Sirve para
    encontrar encabezados de sección que no forman parte de ninguna tabla."""
    palabras = page.extract_words(use_text_flow=False, keep_blank_chars=False) or []
    por_top = {}
    for w in palabras:
        top = round(w["top"])
        por_top.setdefault(top, []).append(w)
    fusionados = []
    for top in sorted(por_top.keys()):
        if fusionados and top - fusionados[-1][0] <= 2:
            fusionados[-1] = (fusionados[-1][0], fusionados[-1][1] + por_top[top])
        else:
            fusionados.append((top, list(por_top[top])))
    resultado = []
    for top, ws in fusionados:
        ws.sort(key=lambda w: w["x0"])
        resultado.append((top, " ".join(w["text"] for w in ws)))
    return resultado


def extraer_filas_con_seccion(pdf):
    """Recorre página por página y asigna a cada fila de cada tabla la sección
    vigente (senadores/asesores/bicameral), determinada por el encabezado de
    sección más cercano por encima en la misma página (o el de la página
    anterior si no hay ninguno en ésta) — el encabezado vive como texto suelto,
    no como fila de tabla, así que no puede detectarse fila por fila."""
    filas = []
    seccion_actual = "senadores"
    for page in pdf.pages:
        eventos = []
        for top, texto_linea in _lineas_de_pagina(page):
            up = texto_linea.upper()
            if SEC_ASESORES.search(up):
                eventos.append((top, "header", "asesores"))
            elif SEC_BICAMERAL.search(up):
                eventos.append((top, "header", "bicameral"))
            elif SEC_SENADORES.search(up):
                eventos.append((top, "header", "senadores"))
        for tabla in page.find_tables():
            eventos.append((tabla.bbox[1], "table", tabla.extract()))
        eventos.sort(key=lambda e: e[0])
        for _, kind, payload in eventos:
            if kind == "header":
                seccion_actual = payload
            else:
                for fila in payload:
                    filas.append((seccion_actual, fila))
    return filas


def parsear_reuniones_tabular(filas_con_seccion):
    """Igual que la versión anterior, pero la sección de cada reunión viene
    resuelta de antemano por posición (ver extraer_filas_con_seccion), en vez
    de inferirse leyendo el texto de la propia fila."""
    reuniones = []
    reunion = None
    esperando_datos = False
    seccion_reunion_actual = "senadores"
    col_map = {"fecha": 0, "hora": 1, "comision": 2, "salon": 3}

    def cerrar():
        nonlocal reunion
        if reunion is not None:
            raw = reunion.pop("_temario_raw", "")
            reunion["temario"] = parsear_temario(raw)
            reunion["tipo"] = tipo_reunion(reunion["seccion"], reunion["comisiones"])
            reuniones.append(reunion)
            reunion = None

    def celda(row, key, default=""):
        idx = col_map.get(key)
        if idx is None or idx >= len(row):
            return default
        return row[idx] if row[idx] is not None else default

    for seccion, row in filas_con_seccion:
        if not row:
            continue
        col0 = _limpiar(row[0] or "")
        up = col0.upper()

        cmap_row = _mapear_columnas(row)
        if "fecha" in cmap_row and "hora" in cmap_row:
            cerrar()
            esperando_datos = True
            seccion_reunion_actual = seccion
            col_map = cmap_row
            continue

        hora_cell = celda(row, "hora", None)
        if esperando_datos and hora_cell and re.match(r"^\d{1,2}:\d{2}$", _limpiar(hora_cell)):
            dia, fecha = parsear_celda_fecha(celda(row, "fecha"))
            comisiones, modalidad = parsear_celda_comisiones(celda(row, "comision"))
            salon, salon_completo = parsear_celda_salon(celda(row, "salon"))
            reunion = {
                "seccion": seccion_reunion_actual,
                "dia": dia,
                "fecha": fecha,
                "hora": _limpiar(hora_cell),
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

        # Fila de contenido del temario: no es encabezado ni fila de datos, y ya
        # hay una reunión abierta a la que pertenece.
        if reunion is not None:
            reunion["_temario_raw"] += "\n" + (row[0] or "")

    cerrar()
    return reuniones


# ─────────────────────────────── Parseo del boletín (formato texto libre) ────

def _es_texto_formato_libre(texto):
    return bool(re.search(r"AGENDA\s+DE\s+SENADORES", texto or "", re.IGNORECASE))


def _parece_nombre_comision(linea, comisiones_norm):
    """¿Esta línea es el nombre de una comisión (y no texto de temario)?
    Las comisiones bicamerales ad-hoc no están en comisiones.json, pero su
    nombre siempre empieza con la palabra BICAMERAL."""
    up = linea.strip().upper()
    if not up:
        return False
    if up.startswith("BICAMERAL"):
        return True
    return _norm_com(up) in comisiones_norm


def parsear_reuniones_texto_libre(texto, comisiones_norm):
    """Parsea el formato de texto libre (AGENDA DE SENADORES / AGENDA DE
    ASESORES, marcadores 🗓🕑📍📋). Como no hay separador explícito entre el
    temario de una reunión y el nombre de la siguiente comisión cuando dos
    reuniones de la misma sección van seguidas, se reconoce el nombre de la
    próxima comisión contra la lista oficial (o el prefijo BICAMERAL)."""
    lineas = [l.strip() for l in (texto or "").split("\n") if l.strip()]
    reuniones = []
    seccion = None
    comision_buffer = []
    reunion = None

    def cerrar():
        nonlocal reunion
        if reunion is not None:
            raw = reunion.pop("_temario_raw", "")
            reunion["temario"] = parsear_temario_texto_libre(raw)
            reunion["tipo"] = tipo_reunion(reunion["seccion"], reunion["comisiones"])
            reuniones.append(reunion)
            reunion = None

    for linea in lineas:
        up = linea.upper()

        m_sec = RE_AGENDA_SEC.match(up)
        if m_sec:
            cerrar()
            comision_buffer = []
            seccion = "senadores" if m_sec.group(1).upper() == "SENADORES" else "asesores"
            continue
        if seccion is None:
            continue  # encabezado del boletín (N°, INFORMACIÓN AL...)
        if up.startswith("NO HAY REUNIONES"):
            cerrar()
            comision_buffer = []
            continue
        if up.startswith("*SE ACTUALIZAR"):
            cerrar()
            continue
        if re.match(r"^\d+$", up):
            continue  # número de página suelto

        m_fecha = RE_FECHA_LINEA.search(linea)
        if m_fecha:
            cerrar()
            dia_txt, dd, mes_txt, hora_txt, salon_txt = m_fecha.groups()
            mes_num = MESES_NOMBRE.get(mes_txt.upper())
            fecha = f"{int(dd):02d}/{mes_num:02d}" if mes_num else ""
            hora_txt = re.sub(r"\s*H$", "", hora_txt.strip(), flags=re.IGNORECASE).strip().upper()
            if "CONTINUACI" in hora_txt:
                hora = "A continuación"
            else:
                hm = re.match(r"(\d{1,2}):(\d{2})", hora_txt)
                hora = f"{hm.group(1)}:{hm.group(2)}" if hm else hora_txt
            salon_txt = salon_txt.strip()
            salon = re.sub(r"^SAL[OÓ]N\s+", "", salon_txt, flags=re.IGNORECASE)
            reunion = {
                "seccion": seccion,
                "dia": dia_txt.upper(),
                "fecha": fecha,
                "hora": hora,
                "modalidad": "",
                "comisiones": comision_buffer,
                "salon": salon,
                "salon_completo": salon_txt,
                "_temario_raw": "",
                "temario": [],
            }
            comision_buffer = []
            continue

        if linea.startswith("📋"):
            continue  # marcador "TEMARIO"

        if reunion is not None and _parece_nombre_comision(linea, comisiones_norm):
            cerrar()
            comision_buffer = [linea]
            continue

        if reunion is None:
            comision_buffer.append(linea)
        else:
            reunion["_temario_raw"] += " " + linea

    cerrar()
    return reuniones


# ─────────────────────────────── Orquestación del parseo ─────────────────────

def extraer_tablas_y_texto(contenido_pdf):
    """Se mantiene por compatibilidad (usado en el histórico de este script);
    no se usa en el flujo principal, que ahora pasa por parsear_boletin()."""
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


def parsear_boletin(contenido_pdf, comisiones_norm):
    """Detecta el formato del boletín (tabular vs. texto libre) y devuelve
    (reuniones, texto_completo)."""
    with pdfplumber.open(io.BytesIO(contenido_pdf)) as pdf:
        texto_completo = "\n".join(
            (p.extract_text(x_tolerance=3, y_tolerance=3) or "") for p in pdf.pages)
        if _es_texto_formato_libre(texto_completo):
            reuniones = parsear_reuniones_texto_libre(texto_completo, comisiones_norm)
        else:
            filas = extraer_filas_con_seccion(pdf)
            reuniones = parsear_reuniones_tabular(filas)
    return reuniones, texto_completo


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
    # No incluye 'tipo': si una corrección de clasificación cambia el tipo de
    # una reunión ya guardada, debe reemplazarla en vez de duplicarla.
    return (r.get("fecha", ""), r.get("hora", ""), tuple(r.get("comisiones", [])))


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
    comisiones_norm = cargar_comisiones_norm()

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
            reuniones, texto = parsear_boletin(contenido, comisiones_norm)
            numero_pdf = extraer_numero_boletin(texto) or bol["numero"]
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
