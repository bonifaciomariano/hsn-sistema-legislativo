#!/usr/bin/env python3
"""
scraper_dpp.py — Decretos de Presidencia Parlamentaria (DPP) → data/comisiones.json
====================================================================================
Consulta la tabla de decretos del Senado, descarga los DPP nuevos cuyo tema refiere
a comisiones, parsea los reemplazos de integración y actualiza data/comisiones.json.

Ajuste de diseño: el texto del DPP no trae roles. Cuando se designa a alguien "en
reemplazo de" otro, el nuevo HEREDA el rol que el reemplazado tenía en comisiones.json.

La integración vigente se siembra desde el índice del repo comisiones-senado
(comisiones_state.json → data/comisiones.json), que ya refleja todos los DPP
históricos. Por eso se corre una vez en modo BASELINE para marcar los DPP actuales
como preexistentes; a partir de ahí el scraper solo aplica decretos nuevos.

Variables de entorno:
    BASELINE   "1" para marcar los DPP actuales como preexistentes sin aplicarlos.

Tolerante a fallos: si un DPP falla, se registra el error y se continúa con el resto.
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
COMISIONES_JSON = os.path.join(DATA_DIR, "comisiones.json")
SENADORES_JSON = os.path.join(DATA_DIR, "senadores.json")
DPP_PROCESADOS_JSON = os.path.join(DATA_DIR, "dpp_procesados.json")

BASELINE = os.getenv("BASELINE", "") == "1"

BASE_URL = "https://www.senado.gob.ar"
URL_DECRETOS = f"{BASE_URL}/parlamentario/parlamentaria/decreto"

HEADERS = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36")}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


# ─────────────────────────────── Utilidades ──────────────────────────────────

def sin_tildes(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto)
                   if unicodedata.category(c) != "Mn")


def norm_comision(nombre):
    """'De Legislación General' / 'Legislación General' → 'LEGISLACION GENERAL'"""
    n = sin_tildes(nombre or "").upper().strip()
    n = re.sub(r"^DE\s+(LA\s+|LOS\s+|LAS\s+|EL\s+)?", "", n)
    n = re.sub(r"\s+", " ", n)
    return n.strip()


def norm_apellido(apellido):
    return re.sub(r"\s+", " ", sin_tildes(apellido or "").upper()).strip()


def nombre_dpp_a_formato(texto):
    """
    'Enrique Martín GOERLING LARA' → ('GOERLING LARA', 'GOERLING LARA, Enrique Martín')
    El apellido es la secuencia FINAL de tokens en MAYÚSCULAS.
    """
    tokens = texto.split()
    if not tokens:
        return "", ""
    # Apellido: tokens finales en mayúsculas (token == su versión upper, con tildes)
    n = len(tokens)
    i = n
    while i > 0:
        t = tokens[i - 1]
        letras = sin_tildes(t)
        if letras.isupper() and any(c.isalpha() for c in letras):
            i -= 1
        else:
            break
    if i == n:  # no detectó apellido en mayúsculas; usar último token
        i = n - 1
    apellido = " ".join(tokens[i:]).strip()
    nombre = " ".join(tokens[:i]).strip().title()
    apellido_fmt = apellido.title() if apellido.isupper() else apellido
    completo = f"{apellido}, {nombre}".strip(", ").strip()
    return apellido, completo


# ─────────────────────────────── Padrón senadores ────────────────────────────

def cargar_padron():
    if not os.path.exists(SENADORES_JSON):
        return {}, {}
    padron = json.load(open(SENADORES_JSON, encoding="utf-8"))
    indice = {}
    for nombre_norm, info in padron.items():
        apellido = nombre_norm.split(",")[0].strip()
        indice.setdefault(norm_apellido(apellido), info)
    return padron, indice


def bloque_de(apellido, padron, indice):
    info = indice.get(norm_apellido(apellido))
    return info.get("bloque", "Sin datos") if info else "Sin datos"


# ─────────────────────────────── Listado de DPP ──────────────────────────────

def listar_decretos(session):
    """Devuelve [{numero, fecha, tema, url}] de la tabla de decretos."""
    resp = session.get(URL_DECRETOS, timeout=45)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tablas = soup.find_all("table")
    if not tablas:
        return []
    tabla = max(tablas, key=lambda t: len(t.find_all("tr")))
    decretos = []
    for tr in tabla.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 5:
            continue
        fecha = tds[0].get_text(strip=True)
        tema = tds[1].get_text(" ", strip=True)
        numero = tds[3].get_text(strip=True)
        link = tds[4].find("a", href=True)
        if not link or not numero:
            continue
        url = link["href"]
        if not url.startswith("http"):
            url = BASE_URL + url
        decretos.append({"numero": numero, "fecha": fecha, "tema": tema, "url": url})
    return decretos


def descargar_texto_pdf(session, url):
    resp = session.get(url, timeout=60)
    resp.raise_for_status()
    partes = []
    with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                partes.append(t)
    return "\n".join(partes)


# ─────────────────────────────── Parseo del DPP ──────────────────────────────

_RE_NUM = re.compile(r"DPP[-\s]*(\d+/\d+)", re.IGNORECASE)
# Artículos: 'Artículo 1°-', 'Artículo 30_', 'Artículo 40' (con ruido OCR)
_RE_ART = re.compile(r"Art[íi]culo\s+\d+\s*[°ºoO]?\s*[-_.]?", re.IGNORECASE)
_RE_COMISION = re.compile(r"en\s+la\s+Comisi[óo]n\s+de\s+(.+?)(?:,|\.|$)", re.IGNORECASE | re.DOTALL)


def extraer_numero(texto):
    m = _RE_NUM.search(texto)
    return m.group(1) if m else None


def _separar_nombres(bloque):
    """
    'los señores Senadores Enrique Martín GOERLING LARA y Eduardo Horacio GALARETTO
     y a las señoras Senadoras Mariana JURI y Carmen ALVAREZ RIVERO'
    → lista de nombres crudos ['Enrique Martín GOERLING LARA', ...]
    """
    # Quitar fórmulas de tratamiento
    t = re.sub(r"\b(a\s+)?(los|las)\s+(señores?|señoras?)\s+Senador(?:es|as|a)?\b",
               "|", bloque, flags=re.IGNORECASE)
    t = re.sub(r"\b(al|a\s+la)\s+(señor|señora)\s+Senador(?:a)?\b", "|",
               t, flags=re.IGNORECASE)
    t = re.sub(r"\b(el|la)\s+(señor|señora)\s+Senador(?:a)?\b", "|",
               t, flags=re.IGNORECASE)
    # Separar por ' y ' y por '|' y por comas
    t = t.replace("|", " ")
    partes = re.split(r"\s+y\s+|,\s*", t, flags=re.IGNORECASE)
    nombres = []
    for p in partes:
        p = p.strip(" .;")
        # Debe contener al menos un token en mayúsculas (apellido)
        if p and any(sin_tildes(tok).isupper() and tok.isalpha() for tok in p.split()):
            nombres.append(re.sub(r"\s+", " ", p))
    return nombres


def parsear_articulos(texto):
    """
    Devuelve lista de cambios:
    [{comision, designados:[crudo...], reemplazados:[crudo...]}]
    """
    cambios = []
    # Cortar por artículos
    marcas = [m.start() for m in _RE_ART.finditer(texto)]
    if not marcas:
        return cambios
    segmentos = []
    for i, ini in enumerate(marcas):
        fin = marcas[i + 1] if i + 1 < len(marcas) else len(texto)
        segmentos.append(texto[ini:fin])

    for seg in segmentos:
        if "Comisi" not in seg:
            continue
        if not re.search(r"Des[íi]gn", seg, re.IGNORECASE):
            continue
        m_com = _RE_COMISION.search(seg)
        if not m_com:
            continue
        comision = re.sub(r"\s+", " ", m_com.group(1)).strip()

        # Dividir en parte designados / reemplazados
        m_reemp = re.search(r"en\s+reemplazo\s+de", seg, re.IGNORECASE)
        if m_reemp:
            # 'Desígnase a ... en la Comisión de Z, en reemplazo de ...'
            parte_des = seg[:m_reemp.start()]
            parte_reemp = seg[m_reemp.end():]
        else:
            parte_des = seg
            parte_reemp = ""

        # En parte_des, quedarse con lo que está entre 'Design...' y 'en la Comisión'
        m_des_ini = re.search(r"Des[íi]gn[ae]se?", parte_des, re.IGNORECASE)
        ini = m_des_ini.end() if m_des_ini else 0
        m_com_in = re.search(r"en\s+la\s+Comisi[óo]n", parte_des, re.IGNORECASE)
        fin = m_com_in.start() if m_com_in else len(parte_des)
        bloque_des = parte_des[ini:fin]

        # En parte_reemp, cortar antes de 'respectivamente' / fin de oración
        m_resp = re.search(r"respectivamente", parte_reemp, re.IGNORECASE)
        bloque_reemp = parte_reemp[:m_resp.start()] if m_resp else parte_reemp.split(".")[0]

        designados = _separar_nombres(bloque_des)
        reemplazados = _separar_nombres(bloque_reemp)
        if designados:
            cambios.append({
                "comision": comision,
                "designados": designados,
                "reemplazados": reemplazados,
            })
    return cambios


# ─────────────────────────────── Aplicar a comisiones.json ───────────────────

def _buscar_miembro_idx(miembros, apellido):
    objetivo = norm_apellido(apellido)
    for i, m in enumerate(miembros):
        ap_m = norm_apellido(m["nombre"].split(",")[0])
        if ap_m == objetivo or objetivo in ap_m or ap_m in objetivo:
            return i
    return None


def _buscar_comision(comisiones, nombre):
    objetivo = norm_comision(nombre)
    for com in comisiones:
        if norm_comision(com["nombre"]) == objetivo:
            return com
    # match parcial (ej. nombres largos de bicamerales)
    for com in comisiones:
        nc = norm_comision(com["nombre"])
        if objetivo and (objetivo in nc or nc in objetivo):
            return com
    return None


def aplicar_cambios(comisiones, cambios, padron, indice):
    aplicados, advertencias = 0, []
    for cambio in cambios:
        com = _buscar_comision(comisiones, cambio["comision"])
        if com is None:
            advertencias.append(f"comisión no encontrada: '{cambio['comision']}'")
            continue
        miembros = com.setdefault("miembros", [])

        designados = cambio["designados"]
        reemplazados = cambio["reemplazados"]

        for i, crudo_nuevo in enumerate(designados):
            apellido_nuevo, nombre_nuevo = nombre_dpp_a_formato(crudo_nuevo)
            rol_heredado = ""
            # Emparejar con el reemplazado en la misma posición ('respectivamente')
            if i < len(reemplazados):
                apellido_viejo, _ = nombre_dpp_a_formato(reemplazados[i])
                idx = _buscar_miembro_idx(miembros, apellido_viejo)
                if idx is not None:
                    rol_heredado = miembros[idx].get("rol", "")
                    miembros.pop(idx)
                else:
                    advertencias.append(
                        f"[{com['nombre']}] reemplazado no hallado: '{apellido_viejo}'")
            # Evitar duplicar si ya está
            if _buscar_miembro_idx(miembros, apellido_nuevo) is None:
                miembros.append({
                    "nombre": nombre_nuevo,
                    "bloque": bloque_de(apellido_nuevo, padron, indice),
                    "rol": rol_heredado,
                })
            aplicados += 1
    return aplicados, advertencias


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


# ─────────────────────────────── Main ─────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("scraper_dpp iniciado")

    comisiones = cargar_json(COMISIONES_JSON, [])
    if not comisiones:
        log.warning("comisiones.json vacío o inexistente; no hay base que actualizar.")
    procesados = cargar_json(DPP_PROCESADOS_JSON, {})
    if isinstance(procesados, list):  # tolerar formato lista
        procesados = {n: {} for n in procesados}
    padron, indice = cargar_padron()

    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        decretos = listar_decretos(session)
    except Exception as exc:
        log.error(f"No se pudo listar decretos: {exc}")
        return
    log.info(f"  → {len(decretos)} decretos en la tabla")

    # Modo baseline: la integración vigente ya está en comisiones.json (índice del
    # repo comisiones-senado). Marcamos los DPP actuales como preexistentes SIN
    # aplicarlos, para que el scraper solo procese decretos nuevos en adelante.
    if BASELINE:
        marcados = 0
        for dec in decretos:
            if dec["numero"] not in procesados:
                procesados[dec["numero"]] = {"fecha": dec["fecha"], "tema": dec["tema"],
                                             "status": "baseline"}
                marcados += 1
        guardar_json(DPP_PROCESADOS_JSON, procesados)
        log.info(f"  → BASELINE: {marcados} DPP marcados como preexistentes "
                 f"(sin aplicar); {len(procesados)} registrados")
        log.info("scraper_dpp finalizado (baseline).")
        log.info("=" * 60)
        return

    total_aplicados = 0
    for dec in decretos:
        numero = dec["numero"]
        tema_upper = sin_tildes(dec["tema"]).upper()
        if numero in procesados:
            continue
        if "COMISION" not in tema_upper:
            continue
        log.info(f"  DPP {numero} — {dec['tema'][:70]}")
        try:
            texto = descargar_texto_pdf(session, dec["url"])
            if len(texto.strip()) < 40:
                # PDF escaneado sin capa de texto (requiere OCR, fuera de alcance)
                log.warning(f"    ⚠ DPP {numero} sin texto extraíble (PDF escaneado)")
                procesados[numero] = {"fecha": dec["fecha"], "tema": dec["tema"],
                                      "status": "sin_texto"}
                continue
            num_pdf = extraer_numero(texto) or numero
            cambios = parsear_articulos(texto)
            aplicados, advertencias = aplicar_cambios(comisiones, cambios, padron, indice)
            for w in advertencias:
                log.warning(f"    ⚠ {w}")
            log.info(f"    → {len(cambios)} artículo(s), {aplicados} designación(es) aplicadas")
            total_aplicados += aplicados
            procesados[numero] = {
                "fecha": dec["fecha"],
                "tema": dec["tema"],
                "articulos": len(cambios),
                "designaciones": aplicados,
            }
        except Exception as exc:
            log.error(f"    ✗ Error procesando DPP {numero}: {exc}")
            continue

    guardar_json(COMISIONES_JSON, comisiones)
    guardar_json(DPP_PROCESADOS_JSON, procesados)
    log.info(f"  → {total_aplicados} designaciones aplicadas en total; "
             f"{len(procesados)} DPP registrados")
    log.info("scraper_dpp finalizado.")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
