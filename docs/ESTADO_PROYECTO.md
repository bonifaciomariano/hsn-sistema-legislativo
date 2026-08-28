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
| `tipo` | str | 19 tipos oficiales (`AC,CA,CC,CD,CE,CM,CO,CV,DC,MS,MD,PP,PC,PD,DE,PL,PR,RC,RP`) |
| `tipo_label` | str | ej. "Proyecto de Ley" |
| `extracto` | str | texto (mayúsculas) |
| `autores` | list[str] | "APELLIDO, NOMBRE" |
| `coautores` | list[str] | casi siempre vacío |
| `bloques` | list[str] | bloque(s) político(s); `bloques[0]` = principal |
| `provincias` | list[str] | |
| `comisiones` | list[str] | nombres de comisión, un giro por elemento, en orden |
| `fecha` | str | `dd/mm/yyyy` |
| `dae` | str | `"nro/año"` |
| `origen` | str | `S, PE, CD, OV, P, JGM, OVD` |
| `url` | str | link al expediente en senado.gob.ar |
| `sancionado` | bool | **(2026-08)** ahora real: `true` sólo si el expediente se convirtió en ley (no confundir con los badges de sanciones HSN, §5.5, que sí distinguen aprobación parcial) |
| `ley_numero` | str\|null | **(2026-08)** número de ley, sólo si `sancionado` |
| `fecha_ley` | str\|null | **(2026-08)** `dd/mm/yyyy` de la sanción de ley |
| `archivado` | bool | **(2026-08)** ahora real: expediente enviado al archivo (incluye caducidad) |
| `fecha_archivo` | str\|null | **(2026-08)** `dd/mm/yyyy` |
| `caduca` | bool | **(2026-08)** subcaso de `archivado`: el expediente caducó por plazo (no toda archivación es por caducidad) |
| `fecha_caduca` | str\|null | **(2026-08)** `dd/mm/yyyy` |

Fuente de estos campos: migración inicial desde `2025.xlsx`/`2026.xlsx`
(`scripts/importar_proyectos_xlsx.py`, one-shot) y de ahí en más `scraper_proyectos.py`
los sigue actualizando en cada corrida — ver §5.7.

Campos que `generar_web.py` agrega **in place** al cruzar con otras fuentes:
`reuniones` (agenda), `od` (órdenes del día), `badge_preferencia`, `badge_sancionado`,
`badge_diputados` (sanciones HSN, ver §5.5).

### `data/od.json` (scraper_od.py)
`{nro_od, anio_od, tipo_od (N/A), expedientes:[{nro,anio,tipo,origen,url}], url_pdf, fecha}`.

### `data/acuerdos.json`
Lista plana de expedientes AC (Acuerdos del PE al Senado):
`{nro, anio, caratula, dado_cuenta (bool), fecha_dado_cuenta (str dd/mm/aaaa|null),
dae (int|null), aprobado (bool), fecha_aprobacion (str|null), nro_od (int|null), origen}`.
**(2026-08)** Ya no depende sólo del CSV manual: la migración inicial lo pobló desde
la columna `NRO. DAE / DADO CUENTA` de los xlsx, y `scraper_proyectos.py` actualiza
`dado_cuenta`/`fecha_dado_cuenta`/`dae` en cada corrida leyendo la tabla "Fechas en
Mesa de Entradas" de cada expediente AC (ver §5.7). `importar_acuerdos.py`/el CSV
manual quedan como fallback, no se usan de forma automática.

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

**(2026-08) Badge "Suspendida":** `scraper_agenda.py` marca `suspendida: true` en
`data/agenda.json` cuando una reunión ya acumulada de un boletín anterior no
reaparece para la misma fecha en un boletín más nuevo (`marcar_suspendidas()`).
No distingue de una reprogramación (se ve igual: desaparece de su fecha
original). Si reaparece más adelante con la misma clave, deja de estar
suspendida automáticamente.

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

### 5.6 Acuerdos (expedientes AC)
Los expedientes AC (mensajes del PE solicitando acuerdo del Senado para designaciones)
tienen 2 estados adicionales en `data/acuerdos.json` (ver §3). `cruzar_proyectos_acuerdos()`
en `generar_web.py` cruza por `nro`+`anio` y agrega in-place `dado_cuenta`,
`fecha_dado_cuenta`, `aprobado_ac`, `fecha_aprobacion_ac` a los proyectos tipo AC.

**Cruce con tarjetas de Proyectos** — 2 badges nuevos en `cardFooterHtml()`:
- **Dado cuenta** (verde `#E8F5E9`/`#1B5E20`): `dado_cuenta === true`.
- **Pendiente de dar cuenta** (ámbar `#FFF8E1`/`#F57F17`): `dado_cuenta === false`.

**Filtro en el Buscador:** cuando el filtro de Tipo activo es exclusivamente `AC`,
aparece un filtro adicional "Estado del acuerdo" (Todos / Dado cuenta / Pendiente de
dar cuenta), implementado con `activeAcuerdoEstado` + chips en `#acuerdo-estado-filter`.

**(2026-08) Resuelto — ya no depende del CSV manual:** `scripts/scraper_proyectos.py`
lee la tabla "Fechas en Mesa de Entradas" de cada expediente AC que visita (columna
DADO CUENTA) y actualiza `data/acuerdos.json` directamente (`actualizar_acuerdo()`).
`scripts/importar_acuerdos.py` + el CSV quedan como fallback manual, no se usan de
forma automática.

### 5.7 Trazabilidad continua de proyectos (2026-08)
`data/proyectos.json` se migró por completo desde `2025.xlsx`/`2026.xlsx`
(`scripts/importar_proyectos_xlsx.py`, one-shot — ver §3 para los campos nuevos). De
ahí en más, `scripts/scraper_proyectos.py` sigue completando esos mismos campos en
cada corrida, en dos pasos:

1. **Expedientes nuevos** (`scrape_incremental()`, sin cambios de fondo): al visitar
   el detalle de cada expediente nuevo, además de autores/comisiones ya calcula
   `archivado`/`caduca`/`sancionado` y, si es tipo AC,
   `dado_cuenta` — usando las mismas tablas del HTML del expediente que se
   confirmaron contra la web real (`ENVIADO AL ARCHIVO`, `EL EXPEDIENTE CADUCO`,
   tabla `summary="SANCION DE LEY"`, tabla `summary="Fechas en Mesa de Entradas"`).
2. **`revisar_expedientes_abiertos()`** (nuevo): en cada corrida re-visita un lote
   acotado (`LOTE_REVISION`, default 200) de expedientes ya existentes que sigan
   "abiertos" (no archivados/sancionados, o AC sin dar cuenta), priorizando los
   menos revisados recientemente (`_ultima_revision`, campo interno). Así, con el
   tiempo, todos los expedientes abiertos se van revisando sin tener que
   re-scrapear las ~4000 filas dos veces por día.

**Límite conocido:** no hay forma de saber por adelantado cuándo un expediente va a
cambiar de estado, así que un expediente puede tardar varios días en ser
re-revisado si la base de "abiertos" es grande. Si hace falta forzar la revisión de
uno puntual, correr con `LOTE_REVISION` más alto o filtrar manualmente.

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
- **Ayuda Memoria — actualizar tras cada Boletín de Novedades:** `data/ayuda_memoria.json`
  no se depura solo. Cuando `scraper_sanciones.py` procesa un boletín nuevo, hay que
  sacar de `ordenes_dia_2026.xlsx` (y re-correr `parse_ayuda_memoria.py`) los OD que
  ese boletín trató, o quedan "pendientes" en la web órdenes que ya se votaron.
  Cruzar por `od_nro` contra `data/sanciones.json` (filtrando por `nro_boletin`) cubre
  la mayoría, pero **el regex de expedientes de `scraper_sanciones.py` (`RE_EXP`) no
  reconoce citas combinadas del boletín tipo "S-252 y 308/26"** (dos números
  compartiendo el "/año" final) — esas filas quedan sin expediente y su OD no se
  marca como tratado. Hay que revisarlas a mano contra el texto del boletín (buscar
  " y \d+/\d\d" en el PDF) antes de dar por completo el barrido. Visto por primera vez
  con el boletín 7/26 (OD 150, 165 y 275 se escapaban así).

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
  Enviado a Diputados).
- **Fase 5c — Acuerdos (AC):** importación manual de `data/acuerdos.json` desde CSV
  (`importar_acuerdos.py`), cruce `cruzar_proyectos_acuerdos()`, 2 badges (Dado cuenta /
  Pendiente de dar cuenta) y filtro "Estado del acuerdo" en el Buscador cuando el tipo
  activo es exclusivamente AC. Scraping automático queda pendiente (ver §5.6). ← estado
  actual
