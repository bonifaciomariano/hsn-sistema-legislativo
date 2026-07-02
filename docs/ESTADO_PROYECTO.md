# HSN — Sistema Legislativo · Estado del proyecto

Documento de traspaso para retomar en una sesión nueva. Resume arquitectura, lo
construido, convenciones y pendientes.

---

## 1. Ubicación y repo

- **Repo:** `hsn-sistema-legislativo`
- **Ruta local (Windows):** `C:\Users\m_bon\Documents\Mail diario\hsn-sistema-legislativo`
- **GitHub:** https://github.com/bonifaciomariano/hsn-sistema-legislativo (rama `main`)
- Contexto institucional: Prosecretaría Parlamentaria — Senado de la Nación Argentina.
- Python local: usar `py` (no `python`) en esta máquina.

> Nota: la carpeta de trabajo `C:\Users\m_bon\Documents\Web integral HSN` está vacía;
> el repo real vive en `Mail diario\hsn-sistema-legislativo`.

---

## 2. Arquitectura

- **Fase 1 (completa):** scrapers pueblan las bases en `data/`:
  - `data/proyectos.json` — lista plana de expedientes (hoy ~2021 registros, crece solo).
  - `data/comisiones.json`, `data/agenda.json`, `data/senadores.json`, etc.
- **Fase 2 (en curso):** `scripts/generar_web.py` lee `data/proyectos.json` y genera un
  **`index.html` autosuficiente** con los datos embebidos como `var DATA = [...]`
  (sin fetch en runtime; funciona abriendo el archivo).
  - Todo el front es **vanilla JS + SVG nativo, sin librerías** (excepto SheetJS por CDN
    para exportar Excel).
  - El HTML pesa ~1.3 MB (límite 15 MB; no hace falta paginación aún).
  - `generar_web.py` está estructurado como: `CSS` (string), `JS` (string raw), 
    `HTML_TEMPLATE` (con placeholders `{css} {js} {datos} {fecha} ...`), y `main()`.

- **Deploy:** un GitHub Action (`.github/workflows/actualizar.yml`) corre periódicamente,
  regenera `index.html` y commitea ("Actualización automática ..."). 
  - **Implicancia al pushear:** el remoto suele estar adelantado. El patrón que usamos:
    `git pull --rebase`, y si `index.html` entra en conflicto (siempre, es artefacto),
    se **regenera** con `py scripts/generar_web.py`, `git add`, `git rebase --continue`,
    y push. `proyectos.json` no suele chocar.
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
| `sancionado` | bool | hoy todos `false` |
| `archivado` | bool | hoy todos `false` |

**Campos que NO existen todavía** (se pidió omitirlos hasta tener datos):
`con_od` (orden del día). El toggle "Sancionados" también se quitó por ahora.

---

## 4. Sistema de diseño

- Fuente **Poppins** (Google Fonts).
- Paleta: azul institucional `#1B5EA2`, azul medio `#2E75B6`, azul oscuro `#0d3f73`,
  azul claro `#D6E4F0`; gris texto `#4A4A4A`, fondo `#F5F7FA`.
- Colores por **tipo** (`TIPO_FG` / `TIPO_BG` en el JS).
- Colores por **bloque**: paleta `BC` + `getBloqueColor()` (índice en `ALL_BLOQUES`,
  con hash de respaldo para claves no listadas). **PENDIENTE:** ver §7.
- Mobile-first, responsive. Header institucional fijo + nav principal.

---

## 5. Estructura de la web (lo construido)

### Navegación principal (4 pestañas)
`Proyectos` (activa) · `Comisiones` · `Agenda` · `Ayuda Memoria`
→ las últimas 3 son **placeholders** ("en construcción").

### Dentro de Proyectos — 3 sub-secciones
Orden y default: **Buscador (por defecto) · Tabla dinámica · Dashboard**.
(Se eligió Buscador primero porque es lo primero que busca el usuario.)

#### 5.1 Buscador (`#sub-buscador`)
- Panel izq sticky de filtros: Año (Todos/2025/2026), texto libre, Tipo (chips
  multi-select), Bloque (select), Provincia (select), Origen (chips), rango de fechas,
  Comisión 1er giro (select), Comisión giros adicionales (select), Autor (select).
- Panel der: contador + **Exportar Excel** (SheetJS) + tarjetas con link al Senado.
- Funciones clave JS: `getFiltered()`, `renderList()`, `buildCard()`, `exportarExcel()`,
  estado `activeAnio`, `activeTipos`, `activeBloque`, `activeOrigen`, `activeProvincia`.

#### 5.2 Tabla dinámica / pivot (`#sub-tabla`)
- Pivot real configurable: **Filas × Columnas × Valores**, dimensiones en `DIMS`
  (tipo, anio, origen, bloque, com1, provincia, sancionado, mes).
- Modos de valor: Conteo, % del total, % de la fila, % de la columna.
- Heatmap en celdas; totales por fila/columna/general.
- **Drill:** clic en celda → aplica filtros al Buscador y **salta a la sub-pestaña
  Buscador** (`drillPivot()` → `applyDimToFilter()` + `switchSub('buscador')`).
- Funciones: `renderPivot()`, `setPivot()`, `drillPivot()`, `applyDimToFilter()`.

#### 5.3 Dashboard (`#sub-dashboard`) — 5 visualizaciones SVG
Selector de **año fijo arriba** (2026 por defecto, luego 2025). Layout tipo **tablero**
(grid 2 columnas, `max-width:1500px`, responsive a 1 col en <900px). Estado: `dashAnio`,
`dashEvoMode`, `dashCross`. Maestro: `renderDashboard()` → filtra por año (`dashData()`)
y llama a las 5 sub-render.

1. **Evolución temporal** (`renderEvolucion`) — líneas por mes; toggle Por tipo / Por
   bloque; top 5 series + "Resto"; tooltip flotante por mes con línea guía.
2. **Treemap de bloques** (`renderTreemap`, `treemapLayout` = squarified) — reemplazó al
   heatmap. **Solo origen `S` (Senado), TODOS los bloques (sin agrupar), área = cantidad,
   subdividido por tipo** con leyenda de tipos. Tiles casi cuadrados.
3. **Barras apiladas Tipo × Bloque** (`renderStacked`) — una barra por tipo, segmentos por
   bloque (top 6 + Resto), leyenda.
4. **Top 10 comisiones + sparkline** (`renderTopComs`, `sparkline`) — tendencia últimas 8
   semanas con referencias (base cero, punto final, tooltip por semana, período en el
   encabezado).
5. **Donut por tipo** (`renderDonut`) — anillo, centro con total, leyenda con %.

**Cross-filtering del Dashboard** (`crossClick`, `crossMatch`, `dashData`, indicador
`#dash-cross`): clic en un bloque/tipo/comisión en cualquier viz filtra **las 5 a la vez**
(incluida la que originó). Indicador "Filtrando por: X (dimensión) ✕"; se limpia con clic
en el indicador o re-clic en el mismo elemento; cambiar de año resetea.

> Sincronización: los filtros Año/Tipo/Origen se comparten entre pivot y buscador vía
> `applyAll()` / `syncFilterUI()` (mismo estado `activeAnio/activeTipos/activeOrigen`).
> El cross-filter del Dashboard es un estado **aparte** (`dashCross`, `dashAnio`).

---

## 6. Convenciones técnicas y aprendizajes

- Validar siempre `python -c "import ast; ast.parse(...)"` antes de generar.
- **Cuidado con separadores de claves en JS**: usar `'~|~'`, nunca un char que pueda
  volverse byte nulo (rompió el `.py` una vez).
- **Sizing de SVG full-width**: un `<svg>` inline con `viewBox` y sin `width` se estira al
  100% del contenedor y la altura explota (bug del heatmap gigante). Usar
  `width:100%;height:auto;max-height:NNNpx` o ancho fijo + `max-width:100%`.
- Escapar valores en handlers inline con `jsStr()` (backslash y comilla) y `esc()`/`escAttr()`.
- El buscador renderiza ~2000 tarjetas → la página se vuelve muy alta; el capturador de
  screenshots del preview a veces se cuelga (no es bug del código). Para verificar,
  filtrar a pocos resultados o inspeccionar el DOM por eval.

---

## 7. Pendientes / próximos pasos sugeridos

- **Colores de bloques (transversal):** unificar la paleta por bloque según la
  especificación del **repo de comisiones**, aplicándolo a TODO el proyecto de una vez
  (buscador `btag`, dashboard, etc.). Confirmar dónde está esa especificación de colores.
- **Secciones placeholder a construir:** `Comisiones`, `Agenda`, `Ayuda Memoria`
  (hay datos en `data/comisiones.json`, `data/agenda.json`, `data/senadores.json`).
- Reincorporar toggles **Sancionados** y **Con OD** cuando existan los datos.
- Eventual **paginación / lazy-render** del buscador si el volumen sigue creciendo.

---

## 8. Historial de commits de Fase 2 (referencia)

- Sección Proyectos inicial (dashboard 3 barras + tabla + buscador).
- Tabla dinámica → pivot table real.
- Unificar tabla + buscador en "Expedientes" (estado compartido + drill).
- Rediseño del Dashboard: 5 visualizaciones SVG.
- Layout compacto tipo tablero.
- Cross-filtering entre las 5 vizs + fix heatmap.
- Treemap squarified (solo Senado, todos los bloques, por tipo) + volver a separar en
  Buscador / Tabla dinámica / Dashboard (Buscador por defecto). ← estado actual
