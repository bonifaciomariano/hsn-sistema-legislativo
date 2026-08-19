# Prompt para la próxima sesión: migrar la base de proyectos a los xlsx completos

Quiero reemplazar la base actual de `data/proyectos.json` por dos planillas
que tengo en `C:\Users\mariano.bonifacio\Downloads\2025.xlsx` y `2026.xlsx`,
con trazabilidad completa de cada expediente (giros con fechas, Orden del
Día, archivo/caducidad, sanción). Después de la carga inicial, quiero que el
scraper diario (`scripts/scraper_proyectos.py` y los que correspondan) siga
actualizando esos mismos campos de trazabilidad de ahí en más — no que la
carga sea un evento único y todo vuelva a quedar congelado.

## Por qué (contexto de la sesión anterior)

Verificando si podíamos adaptar un artefacto de "Pliegos del Poder Judicial
en trámite" a datos propios, encontramos que:
- `proyectos.json` tiene los campos `sancionado` y `archivado`, pero **hoy
  siempre están en `false`** — nunca se completan.
- `data/acuerdos.json` (Acuerdos, importado a mano desde un CSV) tiene
  `nro_od` prácticamente vacío salvo que el expediente YA esté aprobado (es
  decir, no sirve para detectar "tiene OD asignada pero todavía no se
  votó" — llega a ese dato tarde).
- `dado_cuenta` en ese mismo archivo parece desactualizado (muy pocos
  expedientes marcados "sin dar cuenta" comparado con la realidad).

Los dos xlsx parecen resolver esto de raíz: traen ARCHIVO/CADUCA pobladas,
Orden del Día por expediente, y fechas de ingreso/egreso por cada giro a
comisión.

## Los dos archivos (ya inspeccionados)

Mismas 39 columnas en ambos (`Worksheet`, fila 1 = encabezados):

```
ORIGEN, NRO., AÑO, TIPO, CARÁTULA, NRO. DAE / DADO CUENTA, CADUCA, ARCHIVO,
MESA DE ENTRADAS, PRONTO DESPACHO, FECHA INGRESO DICTAMEN, DIR. COMISIONES,
MOCIÓN DE PREFERENCIA, AUTOR,
GIRO1, COMISION1, FECHA_INGRESO1, FECHA_EGRESO1,
GIRO2, COMISION2, FECHA_INGRESO2, FECHA_EGRESO2,
GIRO3, COMISION3, FECHA_INGRESO3, FECHA_EGRESO3,
GIRO4, COMISION4, FECHA_INGRESO4, FECHA_EGRESO4,
GIRO5, COMISION5, FECHA_INGRESO5, FECHA_EGRESO5,
ORDEN DEL DÍA, SANCIONES/SITUACIÓN EXP, LEY – FECHA, COMUNICACIÓN,
FECHA_ARCHIVO
```

Notas del formato (visto en filas de muestra, confirmar con más casos al
armar el parser):
- `NRO. DAE / DADO CUENTA`, `MESA DE ENTRADAS`, `DIR. COMISIONES`,
  `FECHA INGRESO DICTAMEN`: strings tipo `" 59  -"` / `" 12/08/2026 -"` —
  parecen "valor + guion final", a veces con fecha, a veces vacíos.
- `AUTOR`: un solo string con todos los autores juntos, ej.
  `" VISCHI, EDUARDO ALEJANDRO - VALENZUELA, MERCEDES GABRIELA -"` — hay
  que volver a separarlo en lista (similar a `clasificar_autores()` en
  `scraper_proyectos.py`, pero el delimitador acá es " - ", no coma).
- `ORDEN DEL DÍA`: string tipo `" 180 2026 PE -"` (nro, año, tipo,
  separados por espacio). Ojo: el "PE" acá es el ORIGEN del expediente
  referido en esa OD, no necesariamente relevante — confirmar contra
  `data/od.json` si el número solo (180/2026) alcanza para cruzar.
- `GIRO1..5` es el número de orden del giro (float tipo `51.0`), no un
  ID de comisión.
- **Hipervínculos — resuelto.** No son hipervínculos nativos de Excel
  (`cell.hyperlink` da `None`), son fórmulas `=HYPERLINK(url, texto)`.
  Hay que leer el workbook con `data_only=False` y parsear el primer
  argumento de la fórmula (regex sobre `cell.value`, que con
  `data_only=False` es el string de la fórmula, no el resultado).
  - **Columna B** (`NRO.`): siempre trae la URL del expediente, con el
    mismo formato que ya arma `construir_url_expediente()`, ej.
    `=HYPERLINK("https://www.senado.gob.ar/parlamentario/comisiones/verExp/1361.26/S/PD","1361")`.
  - **Columna AI** (`ORDEN DEL DÍA`, columna 35): cuando el expediente
    tiene OD, trae `=HYPERLINK("https://www.senado.gob.ar/parlamentario/parlamentaria/ordenDelDiaResultadoLink/{año}/{nro_od}"," {nro_od} {año} PE -")`;
    cuando no tiene, es `=HYPERLINK("","")`. Ese link es un formato
    nuevo (`ordenDelDiaResultadoLink`) distinto al que ya usamos para
    `od.json` (`downloadOrdenDia`) — confirmar si abre directo el
    resultado en vez del PDF, podría ser mejor que el link actual.

Conteos (para verificar que el parser levantó todo bien):

| | 2025.xlsx | 2026.xlsx |
|---|---|---|
| filas de datos | 2393 | 1595 |
| con ARCHIVO poblado | 169 | 114 |
| con ORDEN DEL DÍA poblado | 355 | 236 |
| tipos presentes | CO,PL,PC,PD,PR,CV,CA,DC,CE,AC,RP,CM,CD,PP | PD,PC,PR,PL,CO,CV,CA,CM,DC,AC,CE |
| orígenes presentes | S,OV,PE,CD,P | S,OV,PE,CD |

**Ojo**: hay tipos que hoy el scraper NO incluye
(`TIPOS_INCLUIR = {"PL","PD","PC","PR","CA","AC","CV"}` en
`scraper_proyectos.py`). Se decidió sumarlos todos.

**Listas oficiales confirmadas por Mariano** (reemplazan el mapeo
tentativo de la vuelta anterior):

Origen de expediente:

| Sigla | Significado |
|---|---|
| CD | Cámara de Diputados |
| JGM | Jefatura de Gabinete de Ministros |
| OVD | Oficiales Varios Cámara de Diputados |
| OV | Oficiales Varios |
| P | Particulares |
| PE | Poder Ejecutivo Nacional |
| S | Senadores |

Nota: en las planillas 2025/2026 sólo aparecieron S, OV, PE, CD, P — JGM y
OVD no salieron en la muestra pero están en la lista oficial, contemplarlos
en el parser igual.

Tipo de expediente:

| Sigla | Significado |
|---|---|
| AC | Acuerdos |
| CA | Comunicaciones de Auditoría |
| CC | Comunicaciones de Comisiones |
| CD | Comunicaciones de Diputados |
| CE | Comunicaciones del Poder Ejecutivo |
| CM | Comunicaciones de Ministerios |
| CO | Comunicaciones de Senadores |
| CV | Comunicaciones Varias |
| DC | Decreto |
| MS | Mensaje de Senado |
| MD | Mensaje de Diputados |
| PP | Peticiones |
| PC | Proyecto de Comunicación |
| PD | Proyecto de Declaración |
| DE | Proyecto de Decreto |
| PL | Proyecto de Ley |
| PR | Proyecto de Resolución |
| RC | Resolución Conjunta |
| RP | Respuesta de Presidencia |

Nota: en las planillas 2025/2026 sólo aparecieron AC, CA, CD, CE, CM, CO,
CV, DC, PP, PC, PD, PL, PR, RP (14 de 19) — CC, MS, MD, DE, RC no salieron
en la muestra pero están en la lista oficial, contemplarlos en el parser
igual (`TIPOS_INCLUIR` debería pasar a ser esta lista completa de 19, no
sólo los que aparecieron).

## Bloques políticos — resuelto esta sesión

Reportaste (con captura) que el filtro de bloques mostraba duplicados como
"UCR - UNIÓN CÍVICA RADICAL" / "UCR - Unión Cívica Radical" /
"Ucr - Unión Cívica Radical" como si fueran 3 bloques distintos. Causa:
`Senadores_2026.xlsx` (vigentes, post recambio del 10/12/2025) y
`Senadores_mandato_cumplido_2025.xlsx` (mandato cumplido, fallback) traen
la misma denominación con distinta grafía, y `construir_senadores.py` la
copiaba tal cual sin normalizar.

**Ya arreglado esta sesión** (no hace falta tocarlo en la migración, solo
tenerlo en cuenta — confirmar en `git log` que ya esté pusheado, si no
avisar): `construir_senadores.py` ahora
canoniza por clave normalizada (mayúsculas + sin tildes), con la grafía de
`Senadores_2026.xlsx` (vigentes) como autoridad; a los bloques que sólo
existen en mandato cumplido (ya disueltos, ej. "Unidad Ciudadana") se les
respeta su propia grafía. Se regeneró `data/senadores.json` y se
reprocesó `data/proyectos.json` para recalcular `bloques`/`provincias` de
los 2373 proyectos existentes con el padrón corregido (18 proyectos
cambiaron). Cuando se migre a los xlsx nuevos, aplicar la misma función
`get_bloques()`/`get_provincias()` sobre los autores re-parseados, como ya
dice el punto 2 de abajo.

## Qué decidir/diseñar en esta sesión (antes de tocar código)

1. **Mapeo de columnas → schema de `proyectos.json`.** El schema actual
   está documentado en `docs/ESTADO_PROYECTO.md` §3. Como mínimo hay que
   sumar: `archivado`/`fecha_archivo` (reales, no siempre `false`),
   `sancionado`/fecha de sanción (ya existen los badges de Sanciones HSN
   que cruzan por otro lado — ver si conviene unificar o mantener
   separado), la Orden del Día por expediente (¿reemplaza o convive con
   el cruce que ya hace `od.json` vía `_parse_exp_numero`?), y los giros
   con fecha de ingreso/egreso (hoy `comisiones` es solo una lista de
   nombres, sin fechas — decidir si vale la pena versionar eso).
2. **No perder el cruce bloques/provincias.** Hoy `scraper_proyectos.py`
   resuelve `bloques`/`provincias` por autor contra `data/senadores.json`
   (`get_bloques`/`get_provincias`). La migración tiene que seguir
   aplicando esa misma lógica sobre los autores re-parseados del xlsx.
3. **Qué hace el scraper diario de ahí en más.** Si el valor de esta
   migración es que ARCHIVO/OD/sanción no vuelvan a congelarse, definir
   qué actualiza cada campo en las corridas normales: ¿el scraper de
   expedientes visita cada proyecto y relee esas columnas equivalentes de
   la web (como ya hace para DAE/comisiones), o se apoya en cruces que ya
   existen (`od.json`, `sanciones.json`, `acuerdos.json`) y esos otros
   scrapers son los que quedan a cargo?
4. **Verificar contra lo que ya sabemos que está mal.** Una vez migrado,
   repetir la comparación de conteos que hicimos esta sesión para
   "Pliegos" (dar_cuenta / en comisión / con OD / sancionado) y ver si
   ahora sí da cerca de los números del artefacto de referencia
   (Pliegos del Poder Judicial: 24 / 19 / 53 / 103 al 14/08/2026 — ojo,
   esos son de hace unos días, van a haber cambiado; usar como orden de
   magnitud, no como target exacto).

## Cómo probar

Igual que siempre en este repo: no hay Python real instalado por defecto
en esta máquina — instalar con
`winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements --silent`
y agregar `C:\Users\mariano.bonifacio\AppData\Local\Programs\Python\Python312`
al PATH de la sesión de PowerShell/Bash antes de correr nada. Regenerar con
`python scripts\generar_web.py` y probar en el navegador antes de pushear
(convención ya establecida: levantar un server estático con
`python -m http.server` vía `.claude/launch.json` + `preview_start`,
nunca abrir el `index.html` como `file://` directo).
