#!/usr/bin/env python3
"""
generar_web.py — Genera index.html (PLACEHOLDER de Fase 1)
==========================================================
Por ahora solo arma un index.html simple con el estado de las cuatro bases de
datos (proyectos, comisiones, agenda, senadores). La web definitiva se construye
en una fase posterior.
"""

import json
import os
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
INDEX = os.path.join(REPO_ROOT, "index.html")


def _cargar(nombre, default):
    path = os.path.join(DATA_DIR, nombre)
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except Exception:
            return default
    return default


def main():
    proyectos = _cargar("proyectos.json", [])
    comisiones = _cargar("comisiones.json", [])
    agenda = _cargar("agenda.json", {"reuniones": []})
    senadores = _cargar("senadores.json", {})

    reuniones = agenda.get("reuniones", []) if isinstance(agenda, dict) else agenda
    n_miembros = sum(len(c.get("miembros", [])) for c in comisiones)
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HSN — Sistema Legislativo</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 760px; margin: 3rem auto;
           padding: 0 1rem; color: #1a1a2e; }}
    h1 {{ font-size: 1.6rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 1rem; margin: 2rem 0; }}
    .card {{ border: 1px solid #ddd; border-radius: 10px; padding: 1.2rem; text-align: center; }}
    .n {{ font-size: 2.2rem; font-weight: 700; color: #0f3460; }}
    .l {{ color: #555; font-size: .9rem; }}
    footer {{ color: #888; font-size: .85rem; margin-top: 2rem; }}
  </style>
</head>
<body>
  <h1>HSN — Sistema Legislativo</h1>
  <p>Web unificada (placeholder de Fase 1). Datos actualizados automáticamente.</p>
  <div class="grid">
    <div class="card"><div class="n">{len(proyectos)}</div><div class="l">Proyectos</div></div>
    <div class="card"><div class="n">{len(comisiones)}</div><div class="l">Comisiones</div></div>
    <div class="card"><div class="n">{n_miembros}</div><div class="l">Integrantes</div></div>
    <div class="card"><div class="n">{len(reuniones)}</div><div class="l">Reuniones</div></div>
    <div class="card"><div class="n">{len(senadores)}</div><div class="l">Senadores</div></div>
  </div>
  <footer>Generado el {ahora}.</footer>
</body>
</html>
"""
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"index.html generado ({len(proyectos)} proyectos, {len(comisiones)} comisiones, "
          f"{len(reuniones)} reuniones, {len(senadores)} senadores)")


if __name__ == "__main__":
    main()
