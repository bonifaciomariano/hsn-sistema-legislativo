#!/usr/bin/env python3
"""
scraper_pliegos.py — Lee la ficha de cada pliego (expediente PE tipo "Acuerdos") en el Senado
y la compara con data/pliegos_data.json (el de Mariano). MODO COMPARACIÓN: no escribe nada.

Ficha: https://www.senado.gob.ar/parlamentario/comisiones/verExp/<NRO>.<AA>/PE/AC
De cada ficha se extrae: extracto, fechas de Mesa de Entradas / Dado cuenta / D.A.E.,
ingreso a Comisiones y del dictamen, giro (comisión, ingreso, egreso), archivo,
sanción (fecha y resultado) y Órdenes del Día (número, fecha, estado).

Variables de entorno:
    PLIEGOS_LOCAL   carpeta con HTML guardados "<NRO>.html" (pruebas sin red)
    PLIEGOS_SOLO    lista de números separados por coma (p. ej. "233,312") para limitar
    FORZAR=1        con ACTUALIZAR, relee TODOS los pliegos (por defecto no relee los ya terminados:
                    sancionados/rechazados y archivados, que ya no cambian)
    ACTUALIZAR=1    además de comparar, escribe data/pliegos_senado.json (lo que dice el Senado de
                    cada pliego). La página lo superpone sobre la planilla de Mariano en generar_web.py;
                    la planilla en sí NO se toca.
Una consulta por pliego, con pausa de 1,5 s. User-Agent propio.
"""
import json
import os
import re
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
PLIEGOS_JSON = os.path.join(DATA_DIR, "pliegos_data.json")
URL = "https://www.senado.gob.ar/parlamentario/comisiones/verExp/{nro}.{aa}/PE/AC"
UA = ("HSN-Sistema-Legislativo/1.0 (herramienta interna de la Prosecretaria Parlamentaria; "
      "1 consulta por pliego por corrida)")
PLIEGOS_URL = "https://raw.githubusercontent.com/bonifaciomariano/Pliegos-Poder-Judicial/main/pliegos_data.json"
SALIDA = os.path.join(DATA_DIR, "pliegos_senado.json")
ACTUALIZAR = os.getenv("ACTUALIZAR") == "1"
FORZAR = os.getenv("FORZAR") == "1"
MINIMO_LEIDO = float(os.getenv("PLIEGOS_MINIMO", "0.9"))   # si se leyó menos de este porcentaje de las fichas, NO se escribe nada
LOCAL = os.getenv("PLIEGOS_LOCAL", "").strip()
SOLO = {x.strip() for x in os.getenv("PLIEGOS_SOLO", "").split(",") if x.strip()}


def limpiar(t):
    return " ".join((t or "").replace("\xa0", " ").split())


def fecha(t):
    """'16-07-2026' -> '16/07/2026'; 'SIN FECHA' o vacío -> None."""
    m = re.search(r"(\d{2})-(\d{2})-(\d{4})", t or "")
    return f"{m.group(1)}/{m.group(2)}/{m.group(3)}" if m else None


def tabla_despues_de(soup, titulo):
    h = next((x for x in soup.find_all("h2") if titulo.lower() in x.get_text(" ", strip=True).lower()), None)
    return h.find_next("table") if h else None


def parsear_ficha(html):
    from bs4 import BeautifulSoup
    s = BeautifulSoup(html, "html.parser")
    out = {"extracto": "", "mesa_entradas": None, "dado_cuenta": None, "dae": "",
           "ingreso_comisiones": None, "ingreso_dictamen": None, "giros": [],
           "archivo": None, "sancion_fecha": None, "sancion": "", "aprobado_como": "", "ods": []}
    tabs = s.find_all("table", class_="table-bordered")
    if tabs:
        tds = tabs[0].find_all("td")
        if len(tds) >= 4:
            out["extracto"] = limpiar(tds[3].get_text(" "))
    t = tabla_despues_de(s, "Fechas en Dir. Mesa de Entradas")
    if t:
        td = [limpiar(c.get_text(" ")) for c in t.find_all("td")]
        if len(td) >= 3:
            out["mesa_entradas"], out["dado_cuenta"] = fecha(td[0]), fecha(td[1])
            m = re.search(r"(\d+)\s*/\s*(\d{4})", td[2])
            out["dae"] = f"{m.group(1)}/{m.group(2)[2:]}" if m else ""
    t = tabla_despues_de(s, "Fecha de Ingreso a Dir. Gral. de Comisiones")
    if t:
        td = [limpiar(c.get_text(" ")) for c in t.find_all("td")]
        if len(td) >= 2:
            out["ingreso_comisiones"], out["ingreso_dictamen"] = fecha(td[0]), fecha(td[1])
    t = tabla_despues_de(s, "Giros del Expediente")
    if t:
        for tr in t.find_all("tr")[1:]:
            td = [limpiar(c.get_text(" ")) for c in tr.find_all("td")]
            if len(td) >= 3:
                com = re.sub(r"\s*ORDEN DE GIRO.*$", "", td[0], flags=re.I)
                out["giros"].append({"comision": com, "ingreso": fecha(td[1]), "egreso": fecha(td[2])})
    h = next((x for x in s.find_all("h2") if "ENVIADO AL ARCHIVO" in x.get_text(" ", strip=True).upper()), None)
    if h:
        out["archivo"] = fecha(h.get_text(" "))
    t = tabla_despues_de(s, "Resoluciones")
    if t:
        for c in t.find_all("td"):
            x = limpiar(c.get_text(" "))
            if x.upper().startswith("FECHA DE SANCION"):
                out["sancion_fecha"] = fecha(x)
            elif x.upper().startswith("SANCION:"):
                out["sancion"] = x.split(":", 1)[1].strip()
            elif x.upper().startswith("APROBADO COMO"):
                out["aprobado_como"] = x.split(":", 1)[1].strip()
    t = tabla_despues_de(s, "Órdenes del Día")
    if t:
        for tr in t.find_all("tr")[1:]:
            td = [limpiar(c.get_text(" ")) for c in tr.find_all("td")]
            if len(td) >= 3 and td[0]:
                out["ods"].append({"numero": td[0], "fecha": fecha(td[1]), "estado": td[2]})
    return out


def obtener(nro, aa):
    if LOCAL:
        p = os.path.join(LOCAL, f"{nro}.html")
        return open(p, encoding="utf-8", errors="replace").read() if os.path.exists(p) else None
    import requests
    r = requests.get(URL.format(nro=nro, aa=aa), headers={"User-Agent": UA}, timeout=60)
    r.raise_for_status()
    return r.text


def comparar(p, f):
    """Diferencias entre un pliego de pliegos_data.json y la ficha del Senado."""
    dif = []
    tl = p.get("timeline") or {}
    dc = (tl.get("dado_cuenta") or {})
    if (dc.get("fecha") or None) != f["dado_cuenta"]:
        dif.append(f"dado cuenta: planilla={dc.get('fecha')} | Senado={f['dado_cuenta']}")
    if dc.get("sesion") and f["dae"] and str(dc["sesion"]).split("/")[0] != f["dae"].split("/")[0]:
        dif.append(f"sesión D.A.E.: planilla={dc.get('sesion')} | Senado={f['dae']} (dado cuenta {f['dado_cuenta']})")
    if (tl.get("ingreso") or None) != f["mesa_entradas"]:
        dif.append(f"ingreso: planilla={tl.get('ingreso')} | Senado={f['mesa_entradas']}")
    od = tl.get("orden_del_dia")
    f_od = f["ods"][0]["numero"] if f["ods"] else None
    pl_od = (od or {}).get("numero") if isinstance(od, dict) else od
    n_pl = str(pl_od).split("/")[0].strip() if pl_od else None
    n_f = f_od.split("/")[0].strip() if f_od else None
    if n_pl != n_f:
        dif.append(f"orden del día: planilla={pl_od} | Senado={f_od}")
    sa = tl.get("sancion")
    sa_f = (sa or {}).get("fecha") if isinstance(sa, dict) else sa
    if (sa_f or None) != f["sancion_fecha"]:
        dif.append(f"sanción: planilla={sa_f} | Senado={f['sancion_fecha']} ({f['sancion'] or 's/resultado'}"
                   + (f", archivado {f['archivo']}" if f['archivo'] else "") + ")")
    return dif


# ----------------------------------------------------------------------------------------------
# Detección de pliegos judiciales NUEVOS (que el Senado ya recibió y la planilla de Mariano no tiene).
# Las reglas son las MISMAS que usa data_builder.py de Pliegos-Poder-Judicial (copiadas tal cual),
# para que un pliego nuevo caiga en la misma provincia, rango y fuero que le daría su planilla.
# La lista de acuerdos sale de data/proyectos.json (tipo AC, origen PE), que ya actualiza scraper_proyectos.py.
# ----------------------------------------------------------------------------------------------
import unicodedata
PROYECTOS_JSON = os.path.join(DATA_DIR, "proyectos.json")

PROVINCIAS_CANONICAS = {
    "BUENOS AIRES": "Buenos Aires", "CATAMARCA": "Catamarca", "CHACO": "Chaco", "CHUBUT": "Chubut",
    "CORDOBA": "Córdoba", "CORRIENTES": "Corrientes", "ENTRE RIOS": "Entre Ríos", "FORMOSA": "Formosa",
    "JUJUY": "Jujuy", "LA PAMPA": "La Pampa", "LA RIOJA": "La Rioja", "MENDOZA": "Mendoza",
    "MISIONES": "Misiones", "NEUQUEN": "Neuquén", "RIO NEGRO": "Río Negro", "SALTA": "Salta",
    "SAN JUAN": "San Juan", "SAN LUIS": "San Luis", "SANTA CRUZ": "Santa Cruz", "SANTA FE": "Santa Fe",
    "SANTIAGO DEL ESTERO": "Santiago del Estero", "TIERRA DEL FUEGO": "Tierra del Fuego", "TUCUMAN": "Tucumán",
}
CARGO_KEYWORDS_JUDICIALES = ("JUEZ", "JUEZA", "FISCAL", "DEFENSOR", "DEFENSORA", "VOCAL",
                             "CAMARISTA", "CONJUEZ", "CONJUECES", "PROCURADOR", "PROCURADORA")
DESIGNAR_RE = re.compile(
    r'DESIGNAR\s+(.+?),?\s+(?:AL|A LA)\s+(?:DR\.|DRA\.|DOCTOR|DOCTORA)\s*([^.\n]+)\.?', re.IGNORECASE)
NOMBRAMIENTO_RE = re.compile(
    r'NOMBRAMIENTO\s+(?:DEL|DE LA)\s+(.+?),?\s+(?:AL|A LA)\s+(?:DR\.|DRA\.|DOCTOR|DOCTORA)\s*([^.\n]+)\.?', re.IGNORECASE)
CONJUECES_RE = re.compile(r'DESIGNAR\s+(CONJUECES\s+.+?)\.?\s*$', re.IGNORECASE | re.DOTALL)
RANGO_RULES = [
    ("Corte Suprema", ["CORTE SUPREMA"]), ("Procurador/a General", ["PROCURADOR"]), ("Conjueces", ["CONJUECES"]),
    ("Defensor/a", ["DEFENSOR"]), ("Fiscal", ["FISCAL"]), ("Camarista / Vocal de Cámara", ["CAMARA", "CÁMARA"]),
    ("Juez/a (primera instancia)", ["JUEZ", "JUEZA"]),
]
FUERO_RULES = [
    ("Penal Económico", ["PENAL ECONOMICO", "PENAL ECONÓMICO"]), ("Casación Penal", ["CASACION", "CASACIÓN"]),
    ("Menores", ["MENORES"]), ("Familia", ["FAMILIA"]), ("Seguridad Social", ["SEGURIDAD SOCIAL"]),
    ("Laboral", ["DEL TRABAJO"]), ("Contencioso Administrativo", ["CONTENCIOSO ADMINISTRATIVO"]),
    ("Comercial", ["COMERCIAL"]), ("Civil", ["CIVIL"]),
    ("Ejecuciones Fiscales / Tributario", ["EJECUCIONES FISCALES", "TRIBUTARIA"]),
    ("Penal", ["CRIMINAL", "PENAL", "GARANTIAS", "GARANTÍAS"]),
]


def _sin_acentos(t):
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


def _limpiar_candidato(nombre):
    return re.sub(r'\s*\(.*$', '', nombre).strip()


def extraer_cargo_candidato(caratula):
    texto = " ".join((caratula or "").split())
    if re.search(r'\bCONJUECES\b', texto, re.IGNORECASE):
        m = CONJUECES_RE.search(texto)
        return (m.group(1).strip().rstrip(".") if m else texto), "Conjueces (designación plural)"
    for rx in (DESIGNAR_RE, NOMBRAMIENTO_RE):
        m = rx.search(texto)
        if m:
            return m.group(1).strip().rstrip(","), _limpiar_candidato(m.group(2))
    return None, None


def extraer_provincia(cargo):
    up = cargo.upper()
    if "CAPITAL FEDERAL" in up:
        return "CABA"
    m = re.search(r'PROV(?:INCIA)?\.?\s+DE(L)?\s+([A-ZÁÉÍÓÚÑ ]+?)(?:,|\.|\s+AL\s|\s+A LA\s|$)', up)
    if m:
        nombre = m.group(2).strip()
        return PROVINCIAS_CANONICAS.get(_sin_acentos(nombre), nombre.title())
    m = re.search(r'C[ÁA]MARA FEDERAL DE APELACIONES DE ([A-ZÁÉÍÓÚÑ ]+?)(?:,|\.|$)', up)
    if m:
        k = _sin_acentos(m.group(1).strip())
        if k in PROVINCIAS_CANONICAS:
            return PROVINCIAS_CANONICAS[k]
    return "Nacional / Federal"


def _regla(cargo, reglas, defecto):
    up = cargo.upper()
    for nombre, claves in reglas:
        if any(k in up for k in claves):
            return nombre
    return defecto


def detectar_nuevos(en_planilla):
    """Pliegos judiciales de data/proyectos.json que la planilla todavía no tiene."""
    try:
        proy = json.load(open(PROYECTOS_JSON, encoding="utf-8"))
    except Exception as e:
        print(f"  aviso: no se pudo leer data/proyectos.json ({e}); no se buscan pliegos nuevos")
        return {}
    nuevos = {}
    for pr in proy:
        if pr.get("tipo") != "AC" or pr.get("origen") != "PE":
            continue
        exp = f"PE-{pr['nro']}/{str(pr['anio'])[-2:]}"
        if exp in en_planilla:
            continue
        car = pr.get("extracto") or ""
        admin = bool(re.search(r'ASIGNA SALAS Y VOCAL[IÍ]AS|SOLICITA EL RETIRO', car, re.I))
        cargo, cand = extraer_cargo_candidato(car)
        if cargo is None:
            if not admin:
                continue                       # ascensos, embajadores, Banco Central, etc.: no es judicial
            cargo = " ".join(car.split())
            cand = "Asignación de salas y vocalías" if "ASIGNA SALAS" in car.upper() else "Retiro de mensaje(s) de designación"
        elif not admin and not any(k in cargo.upper() for k in CARGO_KEYWORDS_JUDICIALES):
            continue
        nuevos[exp] = {
            "url": pr.get("url") or URL.format(nro=pr["nro"], aa=str(pr["anio"])[-2:]),
            "candidato": cand, "cargo": cargo, "provincia": extraer_provincia(cargo),
            "rango": _regla(cargo, RANGO_RULES, "Sin rango (mensaje administrativo)"),
            "fuero": _regla(cargo, FUERO_RULES, "Otros"),
        }
    return nuevos


def cargar_planilla():
    """Planilla de Mariano: la última versión de su repo; si no hay red, la copia local."""
    if not LOCAL:
        try:
            import requests
            r = requests.get(PLIEGOS_URL, headers={"User-Agent": UA}, timeout=30)
            r.raise_for_status()
            d = r.json()
            if isinstance(d.get("pliegos"), list) and d["pliegos"]:
                return d
        except Exception as e:
            print(f"  aviso: no se pudo bajar la planilla ({e}); uso la copia local")
    return json.load(open(PLIEGOS_JSON, encoding="utf-8"))


def resumen_senado(f):
    """Lo que se guarda de cada ficha (solo lo que usa la página)."""
    od = f["ods"][0] if f["ods"] else None
    res = (f["sancion"] or "").upper()
    return {
        "ingreso": f["mesa_entradas"],
        "dado_cuenta": f["dado_cuenta"],
        "dae": f["dae"],
        "od": ({"numero": od["numero"].split("/")[0].strip(), "anio": "20" + od["numero"].split("/")[1].strip()
                if "/" in od["numero"] else "", "fecha": od["fecha"], "estado": od["estado"]} if od else None),
        "sancion_fecha": f["sancion_fecha"],
        "sancion": ("aprobada" if res.startswith("APROB") else "rechazada" if res.startswith("RECHAZ") else
                    (res.lower() if res else "")),
        "archivo": f["archivo"],
    }


def cargar_previo():
    """Lo guardado en la corrida anterior (para no releer lo que ya terminó)."""
    try:
        return json.load(open(SALIDA, encoding="utf-8")).get("pliegos", {})
    except Exception:
        return {}


def terminado(z):
    """Un pliego con resolución final y enviado al archivo ya no cambia."""
    return bool(z) and z.get("sancion") in ("aprobada", "rechazada") and bool(z.get("archivo"))


def main():
    d = cargar_planilla()
    previo = cargar_previo() if (ACTUALIZAR and not FORZAR and not SOLO) else {}
    reutilizados = 0
    pliegos = d["pliegos"]
    leidos = fallos = 0
    total_dif = 0
    guardar = {}
    for p in pliegos:
        m = re.match(r"PE-(\d+)/(\d{2})", p.get("expediente", ""))
        if not m:
            continue
        nro, aa = m.group(1), m.group(2)
        if SOLO and nro not in SOLO:
            continue
        if terminado(previo.get(p["expediente"])):
            guardar[p["expediente"]] = previo[p["expediente"]]
            reutilizados += 1
            leidos += 1
            continue
        try:
            html = obtener(nro, aa)
        except Exception as e:
            fallos += 1
            print(f"  ! {p['expediente']}: no se pudo leer ({e})")
            continue
        if html is None:
            continue
        f = parsear_ficha(html)
        leidos += 1
        guardar[p["expediente"]] = resumen_senado(f)
        dif = comparar(p, f)
        if dif:
            total_dif += 1
            print(f"{p['expediente']} ({p.get('candidato')}) [{p.get('categoria')}]")
            for x in dif:
                print("   -", x)
        if not LOCAL:
            time.sleep(1.5)
    print(f"\nFichas leídas: {leidos - reutilizados} | reutilizadas (ya terminadas): {reutilizados} | "
          f"no leídas: {fallos} | pliegos con diferencias: {total_dif}")
    # --- pliegos judiciales nuevos (no están en la planilla) ---
    if not SOLO:
        nuevos = detectar_nuevos({p["expediente"] for p in pliegos})
        previo_n = previo
        for exp, base in sorted(nuevos.items()):
            nro, aa = re.match(r"PE-(\d+)/(\d{2})", exp).groups()
            z = previo_n.get(exp)
            if not terminado(z):
                try:
                    html = obtener(nro, aa)
                except Exception as e:
                    print(f"  ! {exp}: no se pudo leer ({e})")
                    continue
                if html is None:
                    continue
                z = resumen_senado(parsear_ficha(html))
                if not LOCAL:
                    time.sleep(1.5)
            z["nuevo"] = base
            guardar[exp] = z
            print(f"NUEVO {exp} ({base['candidato']}) [{base['rango']} · {base['provincia']}] - no está en la planilla")
        print(f"Pliegos judiciales nuevos detectados: {len(nuevos)}")
    if ACTUALIZAR and not SOLO:
        if leidos < MINIMO_LEIDO * len(pliegos):
            sys.exit(f"Se leyeron solo {leidos} de {len(pliegos)} fichas: NO se escribe nada (posible corte del Senado).")
        salida = {"generado": time.strftime("%Y-%m-%d %H:%M"), "pliegos": guardar}
        with open(SALIDA, "w", encoding="utf-8") as fh:
            json.dump(salida, fh, ensure_ascii=False, indent=1, sort_keys=True)
        print(f"Escrito {SALIDA} ({len(guardar)} pliegos).")
    else:
        print("(modo comparación: no se escribió nada)")


if __name__ == "__main__":
    main()
