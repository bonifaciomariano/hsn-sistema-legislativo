#!/usr/bin/env python3
"""
scraper_noticias.py — Noticias (gacetillas de prensa) del Senado sobre reuniones de comisión.

Lee el listado https://www.senado.gob.ar/prensa/eventos?page=N (título + fecha + link
/prensa/<ID>/noticias), y de cada noticia nueva lee el comienzo del texto para saber a qué
comisiones se refiere. Guarda data/noticias.json:

    [{"id": 24565, "url": "...", "fecha": "2026-10-28", "titulo": "...", "comisiones": ["EDUCACION Y CULTURA"]}]

La página cruza cada reunión de la Agenda con la noticia de la misma fecha (o del día
siguiente) que nombra a esa comisión, y muestra un botón "Ver noticia".

Resguardos: una consulta por noticia nueva y pausa entre consultas; las noticias ya leídas no
se vuelven a pedir; si el listado no trae ningún ítem no se toca el archivo.

Variables de entorno:
    PAGINAS     cantidad de páginas de listado a leer (por defecto 8, unas 80 noticias)
    DIAS        antigüedad máxima de noticias a guardar (por defecto 120)
    PAUSA       segundos entre consultas (por defecto 1.0)
    TEST        "1" = no escribe, solo informa
    NOTICIAS_LOCAL  carpeta con HTML guardados (listado_<N>.html, <ID>.html) para pruebas sin red
"""
import datetime
import json
import os
import re
import sys
import time
import unicodedata

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
OUT = os.path.join(DATA_DIR, "noticias.json")
COMISIONES_JSON = os.path.join(DATA_DIR, "comisiones.json")
BASE = "https://www.senado.gob.ar"
LISTADO = BASE + "/prensa/eventos?page={n}"
UA = ("HSN-Sistema-Legislativo/1.0 (herramienta interna de la Prosecretaria Parlamentaria; "
      "1 consulta por noticia nueva)")
PAGINAS = int(os.getenv("PAGINAS", "8"))
DIAS = int(os.getenv("DIAS", "120"))
PAUSA = float(os.getenv("PAUSA", "1.0"))
TEST = os.getenv("TEST", "") == "1"
LOCAL = os.getenv("NOTICIAS_LOCAL", "").strip()
PRESUPUESTO = float(os.getenv("PRESUPUESTO", "240"))  # segundos máximos en total
INICIO = time.time()


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").upper())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", s)).strip()


def nombre_core(n):
    """'De Minería, Energía y Combustibles' -> 'MINERIA ENERGIA Y COMBUSTIBLES'"""
    n = norm(n)
    return re.sub(r"^(DE LA |DE LOS |DE LAS |DE |DEL )", "", n).strip()


def pedir(url, local=None):
    if LOCAL and local:
        p = os.path.join(LOCAL, local)
        return open(p, encoding="utf-8").read() if os.path.exists(p) else ""
    import requests
    r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text


RE_ID = re.compile(r"/prensa/(\d+)/noticias")
RE_FECHA = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")


def parsear_listado(html):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    items = {}
    for a in soup.find_all("a", href=RE_ID):
        m = RE_ID.search(a["href"])
        nid = int(m.group(1))
        titulo = " ".join(a.get_text(" ", strip=True).split())
        fecha = None
        nodo = a
        for _ in range(5):
            nodo = nodo.parent
            if nodo is None:
                break
            f = RE_FECHA.search(nodo.get_text(" ", strip=True))
            if f:
                fecha = "%04d-%02d-%02d" % (int(f.group(3)), int(f.group(2)), int(f.group(1)))
                break
        it = items.setdefault(nid, {"id": nid, "titulo": "", "fecha": fecha})
        if len(titulo) > len(it["titulo"]):
            it["titulo"] = titulo
        if fecha and not it["fecha"]:
            it["fecha"] = fecha
    return [v for v in items.values() if v["titulo"]]


def texto_noticia(html):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "nav", "header", "footer"]):
        t.decompose()
    ps = [" ".join(p.get_text(" ", strip=True).split()) for p in soup.find_all("p")]
    ps = [p for p in ps if len(p) > 40]
    return " ".join(ps)[:1800]


def nombres_comisiones():
    try:
        com = json.load(open(COMISIONES_JSON, encoding="utf-8"))
    except Exception:
        return []
    lista = com if isinstance(com, list) else com.get("comisiones", [])
    return [c.get("nombre") for c in lista if isinstance(c, dict) and c.get("nombre")]


def comisiones_en(texto, cores):
    t = " " + norm(texto) + " "
    return sorted({c for c in cores if c and (" " + c + " ") in t})


def main():
    cores = [nombre_core(n) for n in nombres_comisiones()]
    previas = {}
    if os.path.exists(OUT):
        try:
            for it in json.load(open(OUT, encoding="utf-8")):
                previas[it["id"]] = it
        except Exception:
            pass

    listado = []
    for n in range(1, PAGINAS + 1):
        try:
            html = pedir(LISTADO.format(n=n), "listado_%d.html" % n)
        except Exception as e:
            print("  AVISO pagina %d del listado: %s" % (n, e))
            break
        its = parsear_listado(html) if html else []
        print("  listado pagina %d: %d noticias" % (n, len(its)))
        if not its:
            break
        listado += its
        time.sleep(PAUSA if not LOCAL else 0)

    if not listado:
        print("Sin noticias en el listado: no se modifica nada.")
        return 0

    limite = (datetime.date.today() - datetime.timedelta(days=DIAS)).isoformat()
    nuevos = leidos = 0
    res = {}
    for it in sorted(listado, key=lambda x: -x["id"]):
        if not it["fecha"] or it["fecha"] < limite:
            continue
        if time.time() - INICIO > PRESUPUESTO:
            print("  Se alcanzo el tiempo maximo (%d s); el resto queda para la proxima corrida." % PRESUPUESTO)
            break
        previa = previas.get(it["id"])
        if previa and "comisiones" in previa:
            res[it["id"]] = previa
            continue
        texto = ""
        try:
            texto = texto_noticia(pedir(BASE + "/prensa/%d/noticias" % it["id"], "%d.html" % it["id"]))
            leidos += 1
        except Exception as e:
            print("  AVISO noticia %s: %s" % (it["id"], e))
        time.sleep(PAUSA if not LOCAL else 0)
        # el título y el comienzo del texto son lo que importa (el resto puede nombrar otras comisiones)
        com = comisiones_en(it["titulo"] + " . " + texto, cores)
        res[it["id"]] = {"id": it["id"], "url": BASE + "/prensa/%d/noticias" % it["id"],
                         "fecha": it["fecha"], "titulo": it["titulo"], "comisiones": com}
        nuevos += 1

    salida = sorted(res.values(), key=lambda x: (x["fecha"], x["id"]), reverse=True)
    con_com = sum(1 for x in salida if x["comisiones"])
    print("Noticias guardadas: %d (%d nuevas, %d con comision identificada)" % (len(salida), nuevos, con_com))
    for x in salida[:12]:
        print("   %s  %s  %s" % (x["fecha"], ",".join(x["comisiones"]) or "-", x["titulo"][:70]))
    if TEST:
        print("TEST: no se escribe.")
        return 0
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
