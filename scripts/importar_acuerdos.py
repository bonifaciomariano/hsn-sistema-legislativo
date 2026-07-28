"""Migra data/AC_2026_acuerdos.csv (export manual de Acuerdos) a data/acuerdos.json.

Ejecutar con: py scripts/importar_acuerdos.py

Nota para automatización futura: el campo "dado cuenta" está disponible en la
página de cada expediente AC del Senado, en la tabla "Fechas en Dir. Mesa de
Entradas". Cuando se automatice, scraper_proyectos.py debería leer esa celda
al visitar un expediente de tipo AC y actualizar data/acuerdos.json
directamente, sin depender de este CSV manual.
"""
import csv
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE, "data", "AC_2026_acuerdos.csv")
JSON_PATH = os.path.join(BASE, "data", "acuerdos.json")


def _partes(campo):
    """Quita el '-' final y devuelve los tokens no vacíos separados por espacio."""
    s = (campo or "").strip()
    if s.endswith("-"):
        s = s[:-1]
    return s.split()


def parsear_fila(row):
    nro = int(row["NRO."])
    anio = int(row["AÑO"])
    caratula = row["CARÁTULA"].strip()
    origen = row["ORIGEN"].strip()

    dae_partes = _partes(row["NRO. DAE / DADO CUENTA"])
    dae = int(dae_partes[0]) if dae_partes else None
    dado_cuenta = len(dae_partes) >= 2
    fecha_dado_cuenta = dae_partes[1] if dado_cuenta else None

    od_partes = _partes(row["ORDEN DEL DÍA"])
    nro_od = int(od_partes[0]) if len(od_partes) >= 1 else None
    od_resultado = od_partes[2] if len(od_partes) >= 3 else ""

    sanc_partes = (row["SANCIONES/SITUACIÓN EXP"] or "").split()
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
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f))

    acuerdos = [parsear_fila(row) for row in filas]

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(acuerdos, f, ensure_ascii=False, indent=2)

    total = len(acuerdos)
    dados_cuenta = sum(1 for a in acuerdos if a["dado_cuenta"])
    pendientes = total - dados_cuenta
    aprobados = sum(1 for a in acuerdos if a["aprobado"])

    print(f"Total: {total}")
    print(f"Dado cuenta: {dados_cuenta}")
    print(f"Pendientes de dar cuenta: {pendientes}")
    print(f"Aprobados: {aprobados}")


if __name__ == "__main__":
    main()
