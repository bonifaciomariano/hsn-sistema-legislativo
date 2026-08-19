#!/usr/bin/env python3
"""Migra 2025.xlsx + 2026.xlsx (exportación completa de trazabilidad, 39 columnas)
a data/proyectos.json y data/acuerdos.json.

Reemplaza por completo ambos archivos: los xlsx son la fuente más completa y
autoritativa para expedientes 2025/2026 (traen ARCHIVO/CADUCA, giros con fechas de
ingreso/egreso, sanción de ley y "dado cuenta" de Acuerdos — nada de esto lo tiene
hoy scraper_proyectos.py). El scraping incremental normal sigue corriendo después
de esta migración para expedientes fuera de esas dos planillas.

Ejecutar con: python scripts/importar_proyectos_xlsx.py

Variables de entorno opcionales:
    XLSX_2025   Ruta al xlsx 2025 (default: Downloads\\2025.xlsx del usuario actual)
    XLSX_2026   Ruta al xlsx 2026 (default: Downloads\\2026.xlsx del usuario actual)
"""
import json
import os
import re
import sys

import openpyxl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scraper_proyectos import (  # noqa: E402
    TIPOS,
    _sin_tildes,
    cargar_padron,
    clasificar_autores,
    get_bloques,
    get_provincias,
    normalizar_autor,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
PROYECTOS_JSON = os.path.join(DATA_DIR, "proyectos.json")
ACUERDOS_JSON = os.path.join(DATA_DIR, "acuerdos.json")

_DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
XLSX_PATHS = [
    os.getenv("XLSX_2025", os.path.join(_DOWNLOADS, "2025.xlsx")),
    os.getenv("XLSX_2026", os.path.join(_DOWNLOADS, "2026.xlsx")),
]

RE_HYPERLINK = re.compile(r'HYPERLINK\(\s*"([^"]*)"\s*,\s*"([^"]*)"\s*\)', re.IGNORECASE)
RE_FECHA = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def _hyperlink_partes(valor):
    """=HYPERLINK(url, texto) -> (url, texto). Si no es fórmula, (valor, valor)."""
    if not valor:
        return "", ""
    m = RE_HYPERLINK.search(str(valor))
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "", str(valor).strip()


def _partes(campo):
    """Quita el '-' final y devuelve los tokens no vacíos separados por espacio.
    Mismo helper que ya usa importar_acuerdos.py para este formato de celda."""
    s = (campo or "").strip()
    if s.endswith("-"):
        s = s[:-1]
    return s.split()


def _fecha_o_none(valor):
    v = (valor or "").strip()
    return v if RE_FECHA.match(v) else None


def _separar_prefijo_autor(caratula, autores):
    """La CARÁTULA del xlsx trae 'APELLIDO[ Y OTRO]: texto real...' cuando hay
    autores senadores (ej. 'VISCHI Y VALENZUELA: PROYECTO DE...'), redundante con
    `autores` (ya parseado aparte de la columna AUTOR). Comunicaciones sin autor
    senador (PE, AGN, ministerios) también traen ':' pero es el nombre de la
    institución, no debe tocarse. Sólo se recorta cuando TODOS los apellidos antes
    de ':' matchean algún autor ya parseado (mismo criterio de `clasificar_autores`,
    comparando sin tildes para evitar falsos negativos por acentos)."""
    if not autores or ":" not in caratula:
        return caratula
    prefijo, resto = caratula.split(":", 1)
    prefijo_limpio = re.sub(r"\s*\bY\s+OTR[OA]S?\b", "", prefijo.upper()).strip()
    partes = re.split(r"[,]\s*|\s+Y\s+", prefijo_limpio)
    apellidos_prefijo = [p.strip() for p in partes if p.strip()]
    if not apellidos_prefijo:
        return caratula
    apellidos_autores = [_sin_tildes(a.split(",")[0].strip().upper()) for a in autores]
    matchean = all(
        any(_sin_tildes(ap) in apellido or apellido in _sin_tildes(ap) for apellido in apellidos_autores)
        for ap in apellidos_prefijo
    )
    return resto.strip() if matchean else caratula


def _parse_ley_fecha(valor):
    """'27818 - 24/06/2026' -> ('27818', '24/06/2026'); ' - ' o vacío -> (None, None)."""
    v = (valor or "").strip()
    m = re.match(r"^(\d+)\s*-\s*(\d{2}/\d{2}/\d{4})$", v)
    return (m.group(1), m.group(2)) if m else (None, None)


def leer_filas(path):
    wb = openpyxl.load_workbook(path, data_only=False)
    ws = wb.active
    return list(ws.iter_rows(min_row=2, values_only=True))


def parsear_fila(row, padron, indice):
    origen = (row[0] or "").strip()
    _, nro_txt = _hyperlink_partes(row[1])
    url, anio_txt = _hyperlink_partes(row[2])
    nro = int(nro_txt)
    anio = int(anio_txt)
    tipo = (row[3] or "").strip()
    caratula = (row[4] or "").strip()

    dae_partes = _partes(row[5])
    dae = f"{dae_partes[0]}/{anio}" if dae_partes else ""

    autor_raw = row[13] or ""
    autores_todos = []
    for a in autor_raw.split(" - "):
        a = a.strip().rstrip("-").strip()
        if a:
            autores_todos.append(normalizar_autor(a))
    autores, coautores = clasificar_autores(caratula, autores_todos)
    extracto = _separar_prefijo_autor(caratula, autores)

    comisiones = []
    for i in range(5):
        base = 14 + i * 4  # GIRO_i, COMISION_i, FECHA_INGRESO_i, FECHA_EGRESO_i
        com = (row[base + 1] or "").strip()
        if com:
            comisiones.append(com)

    mesa_partes = _partes(row[8])
    fecha = mesa_partes[0] if mesa_partes and _fecha_o_none(mesa_partes[0]) else ""

    fecha_archivo = _fecha_o_none(row[38]) or _fecha_o_none(row[7])
    archivado = bool(fecha_archivo)

    fecha_caduca = _fecha_o_none(row[6])
    caduca = bool(fecha_caduca)

    ley_numero, fecha_ley = _parse_ley_fecha(row[36])
    sancionado = bool(ley_numero)

    return {
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
        "url": url or "",
        "sancionado": sancionado,
        "ley_numero": ley_numero,
        "fecha_ley": fecha_ley,
        "archivado": archivado,
        "fecha_archivo": fecha_archivo,
        "caduca": caduca,
        "fecha_caduca": fecha_caduca,
    }


def parsear_acuerdo(row, url):
    """Sólo para tipo=AC. Misma lógica que importar_acuerdos.py, adaptada a las
    celdas del xlsx (ya resueltas desde HYPERLINK)."""
    origen = (row[0] or "").strip()
    _, nro_txt = _hyperlink_partes(row[1])
    _, anio_txt = _hyperlink_partes(row[2])
    nro = int(nro_txt)
    anio = int(anio_txt)
    caratula = (row[4] or "").strip()

    dae_partes = _partes(row[5])
    dae = int(dae_partes[0]) if dae_partes else None
    dado_cuenta = len(dae_partes) >= 2
    fecha_dado_cuenta = dae_partes[1] if dado_cuenta else None

    _, od_texto = _hyperlink_partes(row[34])
    od_partes = _partes(od_texto)
    nro_od = int(od_partes[0]) if len(od_partes) >= 1 else None
    od_resultado = od_partes[2] if len(od_partes) >= 3 else ""

    sanc_partes = (row[35] or "").split()
    sanc_resultado = sanc_partes[0] if len(sanc_partes) >= 1 else ""
    fecha_aprobacion = sanc_partes[1] if len(sanc_partes) >= 2 else None

    aprobado = "AP" in od_resultado and "AP" in sanc_resultado

    return {
        "nro": nro,
        "anio": anio,
        "caratula": caratula,
        "dado_cuenta": dado_cuenta,
        "fecha_dado_cuenta": fecha_dado_cuenta,
        "dae": dae,
        "aprobado": aprobado,
        "fecha_aprobacion": fecha_aprobacion if aprobado else None,
        "nro_od": nro_od,
        "origen": origen,
    }


def main():
    padron, indice = cargar_padron()
    print(f"  → padrón con {len(padron)} senadores")

    proyectos, acuerdos = [], []
    claves_vistas = set()
    for path in XLSX_PATHS:
        if not os.path.exists(path):
            print(f"ERROR: no se encontró {path}")
            sys.exit(1)
        filas = leer_filas(path)
        print(f"  → {path}: {len(filas)} filas")
        for row in filas:
            tipo = (row[3] or "").strip()
            if tipo not in TIPOS:
                continue
            p = parsear_fila(row, padron, indice)
            clave = (p["nro"], p["anio"], p["tipo"])
            if clave in claves_vistas:
                continue  # el mismo expediente puede aparecer en ambos archivos
            claves_vistas.add(clave)
            proyectos.append(p)
            if tipo == "AC":
                acuerdos.append(parsear_acuerdo(row, p["url"]))

    proyectos.sort(key=lambda p: (int(p["anio"]), int(p["nro"])), reverse=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PROYECTOS_JSON, "w", encoding="utf-8") as f:
        json.dump(proyectos, f, ensure_ascii=False, indent=2)
    with open(ACUERDOS_JSON, "w", encoding="utf-8") as f:
        json.dump(acuerdos, f, ensure_ascii=False, indent=2)

    con_bloque = sum(1 for p in proyectos if p["bloques"] and p["bloques"] != ["Sin datos"])
    archivados = sum(1 for p in proyectos if p["archivado"])
    caducados = sum(1 for p in proyectos if p["caduca"])
    sancionados = sum(1 for p in proyectos if p["sancionado"])
    dados_cuenta = sum(1 for a in acuerdos if a["dado_cuenta"])
    print(f"  → TOTAL proyectos: {len(proyectos)} ({con_bloque} con bloque)")
    print(f"  → archivados: {archivados} (de los cuales caducados: {caducados})")
    print(f"  → sancionados (convertidos en ley): {sancionados}")
    print(f"  → acuerdos: {len(acuerdos)} (dados cuenta: {dados_cuenta})")


if __name__ == "__main__":
    main()
