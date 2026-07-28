# HSN — Sistema Legislativo · Estado del proyecto

Documento de traspaso para retomar en una sesión nueva. Resume arquitectura, lo
construido, convenciones y pendientes.

---

## 1. Ubicación y repo

- **Repo:** `hsn-sistema-legislativo`
- **Ruta local (Windows):** `C:\Users\m_bon\Documents\Web integral HSN`
- **GitHub:** https://github.com/bonifaciomariano/hsn-sistema-legislativo (rama `main`)
- Contexto institucional: Prosecretaría Parlamentaria — Senado de la Nación Argentina.
- Python local: usar `py` (no `python`) en esta máquina.

---

## 2. Arquitectura

- **Fase 1 (completa):** scrapers pueblan las bases en `data/`:
  - `data/proyectos.json` — lista plana de expedientes (~2180 registros, crece solo).
  - `data/comisiones.json`, `data/agenda.json`, `data/senadores.json`, `data/dpp_cambios.json`.
  - `data/od.json` — Órdenes del Día (`scripts/scraper_od.py`).
  - `data/sanciones.json` + `data/sanciones_procesados.json` — Boletines de Novedades del
    HSN (`scripts/scraper_sanciones.py`).
- **Fase 2 (en curso):** `scripts/generar_web.py` lee todo lo anterior y genera un
  **`index.html` autosuficiente** con los datos embebidos como `var DATA/COMISIONES/
  AGENDA/OD_DATA/SANCIONES_DATA/BLOQUE_TOTALES = [...]` (sin fetch en runtime; funciona
  abriendo el archivo).
  - Todo el front es **vanilla JS + SVG nativo, sin librerías** (excepto SheetJS y
    jsPDF por CDN, para exportar Excel/PDF).
  - El HTML pesa ~2.2 MB (límite 15 MB; no hace falta paginación aún).
  - `generar_web.py` está estructurado como: `CSS` (string), `JS` (string raw),
    `HTML_TEMPLATE` (con placeholders `{css} {js} {datos} {comisiones} {agenda} {od}
    {sanciones} {fecha} ...`), y `main()`.

- **Deploy:** un GitHub Action (`.github/workflows/actualizar.yml`) corre dos veces por
  día hábil, corre todos los scrapers (los incrementales con `continue-on-error: true`),
  regenera `index.html` y commitea ("Actualización automática ...").
  - **Implicancia al pushear:** el remoto suele estar adelantado. El patrón que usamos:
    `git pull --rebase`, y si `index.html` entra en conflicto (siempre, es artefacto),
    se **regenera** con `py scripts/generar_web.py`, `git add`, `git rebase --continue`,
    y push. Los `data/*.json` no suelen chocar.
  - Identidad git local del repo: `bonifaciomariano <bonifaciomariano@users.noreply.github.com>`.

---

## 3. Esquema de datos — `proyectos.json`

Lista de objetos con estos campos:

| Campo | Tipo | Notas |
|---|---|---|
| `nro` | int | número de expediente |
| `anio` | int | 2025 / 2026 |
| `tipo` | str | `PL, PD, PC, PR, AC, CV, CA` |
| `tipo_label` | str | ej. "Proyecto de Ley" |
| `extracto` | str | texto (mayúsculas) |
| `autores` | list[str] | "APELLIDO, NOMBRE" |
| `coautores` | list[str] | casi siempre vacío |
| `bloques` | list[str] | bloque(s) político(s); `bloques[0]` = principal |
| `provincias` | list[str] | |
| `comisiones` | list[str] | `comisiones[0]` = 1er giro |
| `fecha` | str | `dd/mm/yyyy` |
| `dae` | str | |
| `origen` | str | **S=Senado, PE=Poder Ejecutivo, CD=Diputados, OV=Otros** |
| `url` | str | link al expediente en senado.gob.ar |
| `sancionado` | bool | hoy todos `false` (no confundir con los badges de sanciones, §5.5) |
| `archivado` | bool | hoy todos `false` |

Campos que `generar_web.py` agrega **in place** al cruzar con otras fuentes:
`reuniones` (agenda), `od` (órdenes del día), `badge_preferencia`, `badge_sancionado`,
`badge_diputados` (sanciones HSN, ver §5.5).

### `data/od.json` (scraper_od.py)
`{nro_od, anio_od, tipo_od (N/A), expedientes:[{nro,anio,tipo,origen,url}], url_pdf, fecha}`.

### `data/sanciones.json` (scraper_sanciones.py)
Lista plana de ítems extraídos del Boletín de Novedades (uno por expediente aprobado):
`{expediente (ej. "S-289/26"), od_nro (int|null), resultado ("APROBADO"/"APROBADA"/otro),
observaciones, seccion ("ley"|"decreto_res_com_dec"|"acuerdo"|"preferencia"), fecha_sesion
(ISO), nro_boletin (ej. "3/26")}`. Sólo se guardan mociones de preferencia con resultado
`APROBADA`; las demás secciones se guardan tal cual (incluye resultados no aprobados,
p.ej. "Vuelve a comisión", para no perder trazabilidad).
`data/sanciones_procesados.json` — lista de números de boletín ya scrapeados (incremental).

---

## 4. Sistema de diseño

- Fuente **Poppins** (Google Fonts).
- Paleta: azul institucional `#1B5EA2`, azul medio `#2E75B6`, azul oscuro `#0d3f73`,
  azul claro `#D6E4F0`; gris texto `#4A4A4A`, fondo `#F5F7FA`.
- Colores por **tipo** (`TIPO_FG` / `TIPO_BG` en el JS).
- Colores por **bloque**: paleta `BC` + `getBloqueColor()` (índice en `ALL_BLOQUES`,
  con hash de respaldo para claves no listadas).
- Mobile-first, responsive. Header institucional fijo + nav principal.

---

## 5. Estructura de la web (lo construido)

### Navegación principal (5 pestañas)
`Proyectos` (activa por defecto) · `Comisiones` · `Agenda` · `Ayuda Memoria` ·
`Sanciones HSN`. Las 5 están implementadas (ninguna es placeholder).

### 5.1 Proyectos — 3 sub-secciones
Orden y default: **Buscador (por defecto) · Tabla dinámica · Dashboard**.

- **Buscador** (`#sub-buscador`): panel izq. sticky de filtros (Año, texto libre, Tipo,
  Bloque, Provincia, Origen, rango de fechas, Comisión 1er giro/adicional, Autor); panel
  der. con contador + Exportar Excel + tarjetas (`buildCard()`/`cardFooterHtml()`, con
  badges de reunión/OD/sanciones — ver §5.5).
- **Tabla dinámica** (`#sub-tabla`): pivot Filas×Columnas×Valores configurable
  (`DIMS`: tipo, anio, origen, bloque, com1, provincia, sancionado, mes), heatmap,
  drill-down a Buscador.
- **Dashboard** (`#sub-dashboard`): 5 visualizaciones SVG (evolución temporal, treemap
  de bloques, barras apiladas tipo×bloque, top 10 comisiones + sparkline, donut por
  tipo) con cross-filtering entre las 5 y selector de año.

### 5.2 Comisiones
Nivel 1: grilla de comisiones permanentes + representación por bloques (global y
cruzada). Nivel 2 (detalle): integrantes (con historial de DPP por senador, modal),
proyectos en trámite, próxima reunión, exportar PDF (jsPDF).

### 5.3 Agenda
Nivel 1: lista de reuniones de comisiones (boletines de agenda), buscador por comisión,
badge PLENARIA, reuniones pasadas colapsadas, sección separada para reuniones de
asesores. Nivel 2 (detalle): metadatos de la reunión + temario clickeable (salta al
expediente en el Buscador de Proyectos vía `irAExpediente()`).

### 5.4 Ayuda Memoria
Órdenes del Día del HSN, agrupadas en 4 sub-pestañas (`switchOdTab()`): OD de Ley,
Anexo 1, OD de Acuerdos, Otros (clasificación por `odCategoria()` según el tipo del
primer expediente). Buscador por número de OD o extracto.

### 5.5 Sanciones HSN
Boletín de Novedades del HSN, 3 sub-pestañas (`switchSancTab()`): **Leyes sancionadas**
(sección `ley` + resultado APROBADO), **Acuerdos aprobados** (sección `acuerdo` +
APROBADO), **Otros** (sección `decreto_res_com_dec` + APROBADO, o `preferencia` — ya
viene pre-filtrada a APROBADA). Buscador por expediente o extracto. Cada tarjeta cruza
con `DATA` (vía `claveExp()`/`parseExpNumero()`) para mostrar link al Senado y extracto
cuando el expediente está en `proyectos.json` (los de origen Diputados de años previos
suelen no estarlo).

**Cruce con tarjetas de Proyectos** (`cruzar_proyectos_sanciones()` en Python +
`cardFooterHtml()` en JS) — 3 badges nuevos, en `cardFooterHtml()`:
- **Preferencia solicitada** (ámbar `#FFF8E1`/`#F57F17`): expediente en sección
  `preferencia`.
- **Sancionado** (verde `#E8F5E9`/`#1B5E20`, clickeable → `irASanciones()` salta a
  Sanciones HSN con el expediente pre-filtrado): expediente en `ley`/`acuerdo`/
  `decreto_res_com_dec` con resultado aprobado. Si las observaciones traen "Ley N° ...",
  se muestra ese texto en vez de la fecha.
- **Enviado a Diputados** (azul `#E3F2FD`/`#0D47A1`): observaciones contienen
  "Se comunica a la H. Cámara de Diputados".

---

## 6. Convenciones técnicas y aprendizajes

- Validar siempre `py -c "import ast; ast.parse(...)"` antes de generar.
- **Cuidado con separadores de claves en JS**: usar `'~|~'`, nunca un char que pueda
  volverse byte nulo (rompió el `.py` una vez).
- **Sizing de SVG full-width**: un `<svg>` inline con `viewBox` y sin `width` se estira al
  100% del contenedor y la altura explota (bug del heatmap gigante). Usar
  `width:100%;height:auto;max-height:NNNpx` o ancho fijo + `max-width:100%`.
- Escapar valores en handlers inline con `jsStr()` (backslash y comilla) y `esc()`/`escAttr()`.
- El buscador renderiza ~2000 tarjetas → la página se vuelve muy alta; el capturador de
  screenshots del preview a veces se cuelga (no es bug del código). Para verificar,
  usar `preview_eval` para inspeccionar el DOM en vez de `preview_screenshot`.
- **Parseo de PDFs de boletines** (Boletín de Novedades / Órdenes del Día): usar
  `pdfplumber.page.extract_tables()`, no el texto plano — en tablas multi-columna el
  texto plano intercala mal las columnas (RESULTADO/OBSERVACIONES quedan pegados a
  líneas de TEMA que no les corresponden); `extract_tables()` recupera las celdas
  correctamente alineadas por geometría.
- El endpoint de datos abiertos de boletines de novedades
  (`ExportarListadoBoletinNovedades/json`) devuelve JSON con comas colgantes (no es
  JSON estricto) — hay que limpiarlo con regex (`re.sub(r",(\s*[}\]])", r"\1", texto)`)
  antes de `json.loads`.

---

## 7. Pendientes / próximos pasos sugeridos

- **Colores de bloques (transversal):** unificar la paleta por bloque según la
  especificación del **repo de comisiones**, aplicándolo a TODO el proyecto de una vez
  (buscador `btag`, dashboard, etc.). Confirmar dónde está esa especificación de colores.
- Reincorporar el toggle **Sancionados** genérico (`proyecto.sancionado`) si se decide
  usarlo además de los badges específicos de Sanciones HSN.
- Eventual **paginación / lazy-render** del buscador si el volumen sigue creciendo.
- `SANCIONES_MIN_ANIO` (env var de `scraper_sanciones.py`, default 2025) limita los
  boletines procesados; el listado completo del endpoint llega hasta 2004 por si en
  algún momento se quiere backfillear años previos.

---

## 8. Historial de fases (referencia)

- Sección Proyectos inicial (dashboard 3 barras + tabla + buscador).
- Tabla dinámica → pivot table real; unificar tabla + buscador (estado compartido + drill).
- Rediseño del Dashboard: 5 visualizaciones SVG, cross-filtering, layout tipo tablero.
- Treemap squarified (solo Senado, todos los bloques, por tipo).
- Secciones Comisiones y Agenda (con DPP, badge PLENARIA, asesores).
- Ayuda Memoria (Órdenes del Día) + badge OD en tarjetas de Proyectos.
- **Fase 5b — Sanciones HSN:** scraper de Boletines de Novedades (`scraper_sanciones.py`,
  vía `pdfplumber.extract_tables()`), pestaña Sanciones HSN (Leyes/Acuerdos/Otros), y
  3 badges de cruce en tarjetas de Proyectos (Preferencia solicitada, Sancionado,
  Enviado a Diputados). ← estado actual
