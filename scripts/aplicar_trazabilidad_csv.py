#!/usr/bin/env python3
"""
aplicar_trazabilidad_csv.py — Concilia data/proyectos.json con la planilla de trazabilidad
==========================================================================================
Script ADITIVO e IDEMPOTENTE. No reemplaza proyectos.json (a diferencia de
importar_proyectos_xlsx.py, que lo pisa entero): lee los CSV de trazabilidad exportados de
la planilla oficial y, para los expedientes de origen S de 2025 y 2026:

  a) Calcula la autoría por el prefijo de la carátula (ver scripts/autoria_caratula.py) y
     guarda `autores_caratula` y `bloques_caratula`. No toca autores / bloques / coautores.
  b) Agrega los expedientes que faltan en la fuente (la clave de deduplicación antigua
     ignoraba el origen y descartaba, por ejemplo, el S-94/26 por existir el PE-94/26),
     y completa los que están sin autor (ej. S-1693/26).
  c) Concilia estado contra el CSV (el CSV manda): archivado/fecha_archivo, ley, fecha de
     ingreso y comisiones. Cada cambio queda listado.
  d) Guarda `od_trazabilidad`, `fecha_dictamen` y `sanciones_trazabilidad` (sirven para
     inferir reuniones de comisión y aprobaciones).

Uso:
    python scripts/aplicar_trazabilidad_csv.py [--dry-run] [--informe ruta.json]
Variables opcionales: CSV_2026, CSV_2025 (rutas), PROYECTOS_JSON (ruta de salida).
Corrido por segunda vez no produce cambios.
"""
import argparse
import copy
import csv
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from autoria_caratula import calcular_autoria, es_vigente, parsear_prefijo, sin_tildes  # noqa: E402
from scraper_proyectos import (  # noqa: E402
    TIPOS,
    cargar_padron,
    clasificar_autores,
    construir_url_expediente,
    get_bloques,
    get_provincias,
    normalizar_autor,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
PROYECTOS_JSON = os.getenv("PROYECTOS_JSON", os.path.join(DATA_DIR, "proyectos.json"))
SENADORES_JSON = os.path.join(DATA_DIR, "senadores.json")
CSVS = [
    os.getenv("CSV_2026", os.path.join(DATA_DIR, "trazabilidad_2026_21-10-2026.csv")),
    os.getenv("CSV_2025", os.path.join(DATA_DIR, "trazabilidad_2025.csv")),
]

RE_FECHA = re.compile(r"^\d{2}/\d{2}/\d{4}$")
RE_FECHAS = re.compile(r"\d{2}/\d{2}/\d{4}")
RE_OD = re.compile(r"(\d+)\s+(\d{4})\s+([A-Z]{2})\s*-")
RE_SANCION = re.compile(r"([A-Z]{2})\s+(\d{2}/\d{2}/\d{4})")
RE_CONOC = re.compile(r"\s*solo\s+para\s+conocimiento.*$", re.I | re.S)


# ─────────────────────────────── Lectura del CSV ─────────────────────────────

def _fecha_o_none(v):
    v = (v or "").strip()
    return v if RE_FECHA.match(v) else None


def _partes(campo):
    s = (campo or "").strip()
    if s.endswith("-"):
        s = s[:-1]
    return s.split()


def leer_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.DictReader(f) if (r.get("ORIGEN") or "").strip() == "S"]


def firmantes(row):
    out = []
    for a in (row.get("AUTOR") or "").split(" - "):
        a = a.strip().rstrip("-").strip()
        if a:
            out.append(normalizar_autor(a))
    return out


def datos_csv(row):
    """Campos de estado de una fila del CSV, en el formato de proyectos.json."""
    fecha_archivo = _fecha_o_none(row.get("FECHA_ARCHIVO")) or _fecha_o_none(row.get("ARCHIVO"))
    m = re.match(r"^(\d+)\s*-\s*(\d{2}/\d{2}/\d{4})$", (row.get("LEY – FECHA") or "").strip())
    ley_numero, fecha_ley = (m.group(1), m.group(2)) if m else (None, None)
    mesa = _partes(row.get("MESA DE ENTRADAS"))
    fecha_caduca = _fecha_o_none(row.get("CADUCA"))
    dae_partes = _partes(row.get("NRO. DAE / DADO CUENTA"))
    anio = int(row["AÑO"])
    comisiones = [(row.get(f"COMISION{i}") or "").strip() for i in range(1, 6)]
    return {
        "fecha": mesa[0] if mesa and _fecha_o_none(mesa[0]) else "",
        "dae": f"{dae_partes[0]}/{anio}" if dae_partes else "",
        "comisiones": [c for c in comisiones if c],
        "archivado": bool(fecha_archivo),
        "fecha_archivo": fecha_archivo,
        "sancionado": bool(ley_numero),
        "ley_numero": ley_numero,
        "fecha_ley": fecha_ley,
        "caduca": bool(fecha_caduca),
        "fecha_caduca": fecha_caduca,
        "od_trazabilidad": [{"nro": int(n), "anio": int(a), "resultado": r}
                            for n, a, r in RE_OD.findall(row.get("ORDEN DEL DÍA") or "")],
        "fecha_dictamen": (RE_FECHAS.findall(row.get("FECHA INGRESO DICTAMEN") or "") or [None])[-1],
        "sanciones_trazabilidad": [{"codigo": c, "fecha": f}
                                   for c, f in RE_SANCION.findall(row.get("SANCIONES/SITUACIÓN EXP") or "")],
    }


def _norm_com(c):
    return re.sub(r"\s+", " ", RE_CONOC.sub("", c or "")).strip().upper()


# ─────────────────────────────── Aplicación ──────────────────────────────────

def extracto_sin_prefijo(caratula, autores_car):
    """CARÁTULA sin el prefijo de autor, sólo si el prefijo nombra a senadores identificados."""
    caratula = (caratula or "").strip()
    if autores_car and ":" in caratula and parsear_prefijo(caratula):
        return caratula.split(":", 1)[1].strip()
    return caratula


def registro_nuevo(row, d, padron, indice):
    nro, anio, tipo = int(row["NRO."]), int(row["AÑO"]), row["TIPO"].strip()
    caratula = (row.get("CARÁTULA") or "").strip()
    todos = firmantes(row)
    autores, coautores = clasificar_autores(caratula, todos)
    aut_car, blo_car, info = calcular_autoria(caratula, todos, padron)
    p = {
        "nro": nro,
        "anio": anio,
        "tipo": tipo,
        "tipo_label": TIPOS.get(tipo, tipo),
        "extracto": extracto_sin_prefijo(caratula, aut_car),
        "autores": autores,
        "coautores": coautores,
        "bloques": get_bloques(autores, padron, indice),
        "provincias": get_provincias(autores, padron, indice),
        "comisiones": d["comisiones"],
        "fecha": d["fecha"],
        "dae": d["dae"],
        "origen": "S",
        "url": construir_url_expediente(nro, anio, "S", tipo),
        "sancionado": d["sancionado"],
        "ley_numero": d["ley_numero"],
        "fecha_ley": d["fecha_ley"],
        "archivado": d["archivado"],
        "fecha_archivo": d["fecha_archivo"],
        "caduca": d["caduca"],
        "fecha_caduca": d["fecha_caduca"],
    }
    return p, aut_car, blo_car, info


def conciliar(p, d, cambios):
    """El CSV manda sobre archivado/ley/fecha/comisiones. Sólo se pisa con valores del CSV
    (un valor vacío en el CSV frente a uno cargado en la fuente se informa, no se borra)."""
    idp = f"S-{p['nro']}/{str(p['anio'])[-2:]} {p['tipo']}"

    def poner(campo, nuevo):
        viejo = p.get(campo)
        if viejo != nuevo:
            cambios.append({"id": idp, "campo": campo, "anterior": viejo, "nuevo": nuevo})
            p[campo] = nuevo

    for campo in ("archivado", "fecha_archivo", "sancionado", "ley_numero", "fecha_ley", "fecha"):
        nuevo = d[campo]
        viejo = p.get(campo)
        if nuevo in (None, "", False) and viejo not in (None, "", False):
            cambios.append({"id": idp, "campo": campo, "anterior": viejo, "nuevo": f"(CSV vacío, no se pisa)"})
            continue
        poner(campo, nuevo)
    # comisiones: se comparan sin el marcador 'Solo para conocimiento' que agrega el scraper
    # y sin importar el orden; si difieren, el CSV manda pero se conserva el texto original
    # (con su marcador) de las que ya estaban.
    actual = {_norm_com(c): c for c in p.get("comisiones", [])}
    nuevas = {_norm_com(c): c for c in d["comisiones"]}
    if set(actual) != set(nuevas) and nuevas:
        resultado = [actual.get(_norm_com(c), c) for c in d["comisiones"]]
        cambios.append({"id": idp, "campo": "comisiones", "anterior": p.get("comisiones"), "nuevo": resultado})
        p["comisiones"] = resultado


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--informe", help="ruta de un JSON con el detalle (agregados, cambios, etc.)")
    args = ap.parse_args()

    padron, indice = cargar_padron()
    with open(PROYECTOS_JSON, encoding="utf-8") as f:
        crudo = f.read()
    proyectos = json.loads(crudo)
    antes = copy.deepcopy(proyectos)
    idx = {(p["nro"], p["anio"], p["tipo"], p["origen"]): p for p in proyectos}

    informe = {"agregados": [], "completados": [], "cambios_estado": [], "autoria_nueva": 0,
               "autoria_cambiada": 0, "sin_prefijo": [], "ambiguos": [], "sin_vincular": [],
               "con_od": 0, "con_dictamen": 0, "varios": []}

    for path in CSVS:
        if not os.path.exists(path):
            print(f"ERROR: no se encontró {path}")
            sys.exit(1)
        for row in leer_csv(path):
            if row["TIPO"].strip() not in TIPOS:
                continue
            clave = (int(row["NRO."]), int(row["AÑO"]), row["TIPO"].strip(), "S")
            d = datos_csv(row)
            caratula = (row.get("CARÁTULA") or "").strip()
            idp = f"S-{clave[0]}/{str(clave[1])[-2:]}"
            p = idx.get(clave)
            if p is None:
                p, aut_car, blo_car, info = registro_nuevo(row, d, padron, indice)
                proyectos.append(p)
                idx[clave] = p
                informe["agregados"].append({
                    "id": idp, "anio": p["anio"], "tipo": p["tipo"],
                    "autor": ", ".join(aut_car) or ", ".join(p["autores"]),
                    "bloque": ", ".join(dict.fromkeys(blo_car)) or ", ".join(p["bloques"]),
                    "extracto": p["extracto"][:90]})
            else:
                todos = firmantes(row) + [a for a in p.get("autores", []) + p.get("coautores", [])
                                          if a not in firmantes(row)]
                if not p.get("autores") and firmantes(row):
                    f_ = firmantes(row)
                    autores, coautores = clasificar_autores(caratula, f_)
                    p["autores"], p["coautores"] = autores, coautores
                    p["bloques"] = get_bloques(autores, padron, indice)
                    p["provincias"] = get_provincias(autores, padron, indice)
                    informe["completados"].append({"id": idp, "autores": autores, "bloques": p["bloques"]})
                aut_car, blo_car, info = calcular_autoria(
                    caratula, todos, padron, p.get("autores"), p.get("bloques"))
                conciliar(p, d, informe["cambios_estado"])

            if info["varios"]:
                informe["varios"].append(idp)
            elif not aut_car and clave[2] in ("PL", "PD", "PC", "PR", "CO", "DE"):
                informe["sin_prefijo"].append({"id": idp, "tipo": clave[2], "caratula": caratula[:70]})
            if info["ambiguos"]:
                informe["ambiguos"].append({"id": idp, "apellidos": info["ambiguos"], "elegido": aut_car})
            if info["sin_vincular"] and aut_car:
                informe["sin_vincular"].append({"id": idp, "apellidos": info["sin_vincular"]})

            if aut_car:
                if p.get("autores_caratula") != aut_car or p.get("bloques_caratula") != blo_car:
                    informe["autoria_cambiada" if "autores_caratula" in p else "autoria_nueva"] += 1
                    p["autores_caratula"], p["bloques_caratula"] = aut_car, blo_car
            # Si ningún autor del prefijo sigue en el Senado, las páginas por bloque atribuyen el
            # proyecto a los demás firmantes vigentes; el registro puede traer sólo a los autores
            # principales, así que se guardan todos los firmantes de la planilla.
            if aut_car and not any(es_vigente(a, padron) for a in aut_car):
                f_csv = firmantes(row)
                if f_csv and p.get("firmantes_trazabilidad") != f_csv:
                    p["firmantes_trazabilidad"] = f_csv
            for campo in ("od_trazabilidad", "fecha_dictamen", "sanciones_trazabilidad"):
                if d[campo] and p.get(campo) != d[campo]:
                    p[campo] = d[campo]
            if d["od_trazabilidad"]:
                informe["con_od"] += 1
            if d["fecha_dictamen"]:
                informe["con_dictamen"] += 1

    proyectos.sort(key=lambda p: (int(p["anio"]), int(p["nro"])), reverse=True)

    # ── Verificación: ningún registro ni campo se pierde ──────────────────────
    idx_antes = {(p["nro"], p["anio"], p["tipo"], p["origen"]): p for p in antes}
    idx_desp = {(p["nro"], p["anio"], p["tipo"], p["origen"]): p for p in proyectos}
    assert set(idx_antes) <= set(idx_desp), "se perdió un registro"
    for k, viejo in idx_antes.items():
        assert set(viejo) <= set(idx_desp[k]), f"se perdió un campo en {k}"

    def resumen(lista):
        c = Counter((p["anio"], p["tipo"]) for p in lista if p["origen"] == "S" and p["anio"] in (2025, 2026))
        return c
    ca, cd = resumen(antes), resumen(proyectos)
    informe["registros_antes"] = len(antes)
    informe["registros_despues"] = len(proyectos)
    informe["desglose"] = {f"{a}-{t}": {"antes": ca.get((a, t), 0), "despues": cd.get((a, t), 0)}
                           for a, t in sorted(set(ca) | set(cd)) if ca.get((a, t), 0) != cd.get((a, t), 0)}

    modificados = sum(1 for k, v in idx_desp.items() if k in idx_antes and v != idx_antes[k])
    print(f"Registros: {len(antes)} -> {len(proyectos)} (agregados: {len(informe['agregados'])})")
    print(f"Agregados por año/tipo: {informe['desglose']}")
    print(f"Registros existentes modificados: {modificados}")
    print(f"Completados sin autor: {[c['id'] for c in informe['completados']]}")
    print(f"autores_caratula nuevos: {informe['autoria_nueva']} | recalculados: {informe['autoria_cambiada']}")
    print(f"Cambios de estado por conciliación: {len(informe['cambios_estado'])}")
    for c in informe["cambios_estado"]:
        print(f"   {c['id']}: {c['campo']}: {c['anterior']!r} -> {c['nuevo']!r}")
    print(f"Con orden del día en el CSV: {informe['con_od']} | con fecha de dictamen: {informe['con_dictamen']}")
    print(f"Sin prefijo de autor (no se calcula): {len(informe['sin_prefijo'])} | 'Varios senadores': {informe['varios']}")
    print(f"Apellidos ambiguos: {len(informe['ambiguos'])} | sin vincular: {len(informe['sin_vincular'])}")

    nuevo_json = json.dumps(proyectos, ensure_ascii=False, indent=2)
    hubo_cambios = nuevo_json != crudo
    print("Sin cambios (idempotente)." if not hubo_cambios else "Hay cambios para guardar.")
    if args.informe:
        with open(args.informe, "w", encoding="utf-8") as f:
            json.dump(informe, f, ensure_ascii=False, indent=2)
    if hubo_cambios and not args.dry_run:
        with open(PROYECTOS_JSON, "w", encoding="utf-8") as f:
            f.write(nuevo_json)
        print(f"Guardado {PROYECTOS_JSON}")


if __name__ == "__main__":
    main()
