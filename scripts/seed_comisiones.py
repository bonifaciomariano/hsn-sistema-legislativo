#!/usr/bin/env python3
"""
seed_comisiones.py — Siembra inicial de data/comisiones.json (one-shot)
=======================================================================
Toma el índice de integración del repo comisiones-senado (comisiones_state.json),
que ya refleja la integración vigente, y le agrega un campo `rol` vacío por miembro
(el scraper de DPP lo usa para heredar el rol del reemplazado).

Ruta del índice configurable por env COMISIONES_STATE; default apunta al clon local.
"""

import json
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(REPO_ROOT, "data", "comisiones.json")
DEFAULT_SRC = os.path.join(os.path.dirname(REPO_ROOT), "comisiones-senado", "data",
                           "comisiones_state.json")
SRC = os.getenv("COMISIONES_STATE", DEFAULT_SRC)


def main():
    if not os.path.exists(SRC):
        raise SystemExit(f"No se encontró el índice: {SRC}")
    data = json.load(open(SRC, encoding="utf-8"))
    for com in data:
        for m in com.get("miembros", []):
            m.setdefault("rol", "")
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    json.dump(data, open(DST, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"comisiones.json sembrado: {len(data)} comisiones, "
          f"{sum(len(c.get('miembros', [])) for c in data)} miembros")


if __name__ == "__main__":
    main()
