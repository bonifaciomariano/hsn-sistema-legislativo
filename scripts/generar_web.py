#!/usr/bin/env python3
"""
generar_web.py — Genera index.html (Fase 2 · sección Proyectos Ingresados)
==========================================================================
Lee data/proyectos.json y construye una web autosuficiente (datos embebidos
como `var DATA = [...]`, sin fetch en runtime) con:

  Navegación principal (4 pestañas):
    Proyectos (activa) · Comisiones · Agenda · Ayuda Memoria (placeholders)

  Dentro de Proyectos (3 sub-pestañas):
    Dashboard · Tabla dinámica · Buscador

Sistema de diseño idéntico al repo anterior (Proyectos-ingresados): Poppins,
azul institucional #1B5EA2, vanilla JS, mobile-first.
"""

import json
import os
import re
import unicodedata
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
INDEX = os.path.join(REPO_ROOT, "index.html")

TIPOS = {
    "PL": "Proyecto de Ley",
    "PD": "Proyecto de Declaración",
    "PC": "Proyecto de Comunicación",
    "PR": "Proyecto de Resolución",
    "CA": "Com. de Auditoría",
    "AC": "Acuerdo",
    "CV": "Com. Varias",
}

# ── Estilos ───────────────────────────────────────────────────────────────────

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Poppins',Calibri,sans-serif;background:#F5F7FA;color:#4A4A4A;font-size:15px;line-height:1.5}

/* ── Topbar: header + navegación principal (sticky en bloque) ──────────── */
.topbar{position:sticky;top:0;z-index:100}
.header{background:#1B5EA2;padding:12px 16px;border-bottom:2px solid #0d3f73}
.header-row{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}
.header-inst{font-size:10px;font-weight:600;color:rgba(255,255,255,0.82);text-transform:uppercase;letter-spacing:2px}
.header-dep{font-size:10px;font-weight:700;color:rgba(255,255,255,0.82);text-transform:uppercase;letter-spacing:2px}
.header-title{font-size:19px;font-weight:700;color:#fff;margin-top:5px}
.header-sub{font-size:11px;color:rgba(255,255,255,0.8);margin-top:1px}

.main-nav{display:flex;background:#0d3f73;padding:0 8px;gap:2px;overflow-x:auto}
.mtab-btn{padding:11px 20px;background:transparent;border:none;color:rgba(255,255,255,0.55);font-family:inherit;font-size:12px;font-weight:600;cursor:pointer;border-bottom:3px solid transparent;transition:all .2s;text-transform:uppercase;letter-spacing:1px;white-space:nowrap}
.mtab-btn.active{color:#fff;border-bottom-color:#fff}
.mtab-btn:hover{color:rgba(255,255,255,0.85)}
.mtab-content{display:none}
.mtab-content.active{display:block}

/* ── Sub-navegación dentro de Proyectos ───────────────────────────────── */
.sub-nav{display:flex;background:#fff;border-bottom:1px solid #D6E4F0;padding:0 12px;gap:4px;overflow-x:auto;box-shadow:0 1px 3px rgba(0,0,0,0.04)}
.sub-btn{padding:10px 18px;background:transparent;border:none;color:#888;font-family:inherit;font-size:12px;font-weight:600;cursor:pointer;border-bottom:3px solid transparent;transition:all .2s;white-space:nowrap}
.sub-btn.active{color:#1B5EA2;border-bottom-color:#1B5EA2}
.sub-btn:hover{color:#2E75B6}
.sub-content{display:none}
.sub-content.active{display:block}

/* ── Placeholders ─────────────────────────────────────────────────────── */
.placeholder{text-align:center;padding:80px 20px;color:#9aacbd}
.placeholder-icon{font-size:42px;margin-bottom:14px;opacity:.5}
.placeholder h3{color:#2E75B6;font-size:18px;margin-bottom:6px;font-weight:600}
.placeholder p{font-size:13px;color:#9aacbd}

/* ── Bloques de sección ───────────────────────────────────────────────── */
.section-block{background:#fff;margin:12px;border-radius:10px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.08)}
.section-header{background:#1B5EA2;padding:10px 16px;display:flex;justify-content:space-between;align-items:center}
.section-header h2{font-size:11px;font-weight:700;color:#fff;text-transform:uppercase;letter-spacing:1.5px}
.section-hint{font-size:10px;color:rgba(255,255,255,0.65)}
.section-body{padding:16px}

/* ── Dashboard de análisis ────────────────────────────────────────────── */
.dash-toolbar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:0 auto 14px;max-width:1500px}
.dash-anio-label{font-size:10px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:1px;margin-right:2px}
.dash-total{margin-left:auto;font-size:12px;color:#888}
.dash-total strong{color:#1B5EA2;font-size:16px}
.dash-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;max-width:1500px;margin:0 auto;align-items:start}
.dash-grid .span2{grid-column:1 / -1}
@media(max-width:900px){.dash-grid{grid-template-columns:1fr}.dash-grid .span2{grid-column:auto}}
.viz-card{background:#fff;border:1px solid #D6E4F0;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,0.06);padding:14px}
.viz-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px;flex-wrap:wrap}
.viz-title{font-size:12px;font-weight:700;color:#1B5EA2;text-transform:uppercase;letter-spacing:.8px}
.viz-svg{width:100%;height:auto;display:block;overflow:visible}
.viz-legend{display:flex;flex-wrap:wrap;gap:7px 14px;margin-top:10px}
.legend-item{display:flex;align-items:center;gap:5px;font-size:11px;color:#4A4A4A}
.legend-swatch{width:11px;height:11px;border-radius:3px;flex-shrink:0}
.viz-toggle{display:flex;gap:4px}
.viz-toggle button{padding:4px 12px;border-radius:14px;border:1.5px solid #D6E4F0;background:#fff;font-family:inherit;font-size:11px;color:#4A4A4A;cursor:pointer;transition:all .15s}
.viz-toggle button.on{background:#1B5EA2;border-color:#1B5EA2;color:#fff;font-weight:600}
.viz-empty{font-size:12px;color:#aaa;text-align:center;padding:30px 10px}
.dash-cross{display:none}
.dash-cross.active{display:inline-flex;align-items:center;gap:6px;cursor:pointer;background:#EAF0FA;color:#1B5EA2;border:1px solid #c8daf0;border-radius:14px;padding:4px 12px;font-size:11px;font-weight:600}
.dash-cross.active:hover{background:#D6E4F0}
.legend-item.clk{cursor:pointer}
.legend-item.clk:hover{text-decoration:underline}
.topcom-row.clk{cursor:pointer}
.topcom-row.clk:hover{background:#F0F4FA}
/* SVG text helpers */
.viz-axis{font-size:10px;fill:#999}
.viz-gridline{stroke:#EEF2F8;stroke-width:1}
.hm-label{font-size:10px;fill:#4A4A4A}
/* tooltip flotante compartido */
.dash-tooltip{position:fixed;pointer-events:none;background:#0d3f73;color:#fff;font-size:11px;line-height:1.5;padding:7px 10px;border-radius:7px;box-shadow:0 4px 14px rgba(0,0,0,0.28);z-index:300;opacity:0;transition:opacity .1s;max-width:260px}
.dash-tooltip.show{opacity:1}
.dash-tt-title{font-weight:700;margin-bottom:4px;border-bottom:1px solid rgba(255,255,255,0.25);padding-bottom:3px}
.dash-tt-row{display:flex;align-items:center;gap:6px;white-space:nowrap}
.dash-tt-dot{width:8px;height:8px;border-radius:2px;flex-shrink:0}
.dash-tt-row .v{margin-left:auto;font-weight:700;padding-left:10px}
/* top comisiones + sparkline */
.topcom-row{display:flex;align-items:center;gap:10px;padding:7px 2px;border-bottom:1px solid #EEF2F8}
.topcom-row:last-child{border-bottom:none}
.topcom-rank{font-size:11px;font-weight:700;color:#9aacbd;width:18px;text-align:right;flex-shrink:0}
.topcom-name{font-size:12px;color:#4A4A4A;flex:1;line-height:1.25}
.topcom-count{font-size:14px;font-weight:700;color:#1B5EA2;width:36px;text-align:right;flex-shrink:0}
.topcom-spark{width:92px;height:26px;flex-shrink:0}

/* ── Tabla dinámica (pivot) ───────────────────────────────────────────── */
.pivot-wrap{padding:12px}
.pivot-config{background:#fff;border:1px solid #D6E4F0;border-radius:10px;padding:12px 14px;margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,0.05)}
.pivot-axes{display:flex;gap:14px;flex-wrap:wrap}
.pivot-field{display:flex;flex-direction:column;gap:3px;min-width:170px;flex:1}
.pivot-field .filter-label{margin:0}
.pivot-field .select-wrapper{margin-bottom:0}
.pivot-filters{display:flex;gap:10px;flex-wrap:wrap;align-items:center;border-top:1px dashed #D6E4F0;margin-top:12px;padding-top:11px}
.pivot-filters .filter-label{margin:0}
.pivot-filters .select-wrapper{min-width:140px;margin-bottom:0;flex:0 1 200px}
.pivot-clear{background:none;border:none;color:#1B5EA2;font-family:inherit;font-size:11px;font-weight:700;cursor:pointer;padding:4px 6px}
.pivot-clear:hover{text-decoration:underline}
.pivot-meta{font-size:11px;color:#888;margin-bottom:8px;padding:0 2px}
.pivot-meta strong{color:#1B5EA2}
.pivot-scroll{overflow:auto;max-height:calc(100vh - 250px);border:1px solid #D6E4F0;border-radius:10px;background:#fff}
.pivot-table{border-collapse:separate;border-spacing:0;font-size:12px;width:100%}
.pivot-table th,.pivot-table td{border-right:1px solid #EEF2F8;border-bottom:1px solid #EEF2F8;padding:6px 10px;text-align:center;white-space:nowrap}
.pivot-table thead th{position:sticky;top:0;background:#1B5EA2;color:#fff;font-weight:600;font-size:11px;z-index:2}
.pivot-table .pv-corner{position:sticky;left:0;top:0;z-index:3;background:#0d3f73;text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:.5px}
.pivot-table .pv-rowhead{position:sticky;left:0;background:#F5F8FC;color:#1B5EA2;font-weight:600;text-align:left;z-index:1;max-width:260px;overflow:hidden;text-overflow:ellipsis}
.pv-cell{color:#4A4A4A;transition:outline .1s}
.pv-click{cursor:pointer}
.pv-click:hover{outline:2px solid #2E75B6;outline-offset:-2px}
.pv-empty{color:#cfd8e3}
.pv-tot{font-weight:700;background:#EAF0FA;color:#1B5EA2}
.pivot-table .pv-totrow th,.pivot-table .pv-totrow td{background:#D6E4F0;border-top:2px solid #1B5EA2}
.pv-grand{font-weight:700;background:#1B5EA2!important;color:#fff!important}
@media(max-width:760px){.pivot-field{min-width:130px}.pivot-filters .select-wrapper{flex-basis:140px}}


/* ── Buscador: layout dos columnas ────────────────────────────────────── */
.detalle-layout{display:flex;gap:16px;padding:12px;align-items:flex-start}
.filters-panel{width:280px;flex-shrink:0;background:#fff;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,0.08);overflow-y:auto;max-height:calc(100vh - 130px);position:sticky;top:112px}
.filters-panel .section-header{border-radius:0}
.filters-body{padding:14px}
.results-panel{flex:1;min-width:0}
@media(max-width:900px){
  .detalle-layout{flex-direction:column}
  .filters-panel{width:100%;position:static;max-height:none}
}

.search-box{width:100%;padding:10px 12px;border:1.5px solid #D6E4F0;border-radius:8px;font-family:inherit;font-size:13px;color:#4A4A4A;outline:none;margin-bottom:10px;background:#fff}
.search-box:focus{border-color:#1B5EA2}
.filter-label{font-size:10px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:5px;margin-top:10px}
.filter-label:first-child{margin-top:0}
.filter-row{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:4px}
.chip{padding:6px 11px;border-radius:20px;border:1.5px solid #D6E4F0;background:#fff;font-family:inherit;font-size:11px;color:#4A4A4A;cursor:pointer;transition:all .15s;white-space:nowrap;-webkit-appearance:none;line-height:1.2}
.chip.on{background:#1B5EA2;border-color:#1B5EA2;color:#fff;font-weight:600}
.results-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:8px}
.results-count{font-size:12px;color:#888}
.btn-export{padding:7px 14px;border-radius:8px;border:1.5px solid #1B5EA2;background:#fff;color:#1B5EA2;font-family:inherit;font-size:11px;font-weight:600;cursor:pointer;transition:all .15s}
.btn-export:hover{background:#1B5EA2;color:#fff}
.select-wrapper{position:relative;display:block;margin-bottom:4px}
.filter-select{width:100%;padding:8px 32px 8px 11px;border:1.5px solid #D6E4F0;border-radius:8px;font-family:inherit;font-size:12px;color:#4A4A4A;background:#fff;outline:none;cursor:pointer;-webkit-appearance:none;appearance:none;transition:border-color .15s}
.filter-select:focus,.filter-select.on{border-color:#1B5EA2;background:#EAF0FA;color:#1B5EA2;font-weight:600}
.select-arrow{position:absolute;right:10px;top:50%;transform:translateY(-50%);pointer-events:none;color:#888;font-size:12px}
.date-range{display:flex;flex-direction:column;gap:5px;margin-bottom:4px}
.date-input{width:100%;padding:7px 10px;border:1.5px solid #D6E4F0;border-radius:8px;font-family:inherit;font-size:12px;color:#4A4A4A;background:#fff;outline:none}
.date-input:focus{border-color:#1B5EA2}
.date-sep{font-size:10px;color:#888;font-weight:600;text-transform:uppercase;letter-spacing:1px}

.card{background:#fff;border-radius:10px;margin-bottom:10px;overflow:hidden;border:1px solid #D6E4F0;box-shadow:0 1px 3px rgba(0,0,0,0.05)}
.card-exp{display:flex;align-items:center;justify-content:space-between;padding:9px 14px 7px;border-bottom:1px solid #EEF2F8;background:#F5F8FC}
.exp-id{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.exp-badge{font-size:11px;font-weight:700;padding:4px 9px;border-radius:4px;flex-shrink:0;letter-spacing:.5px}
.exp-nro{font-size:14px;font-weight:700;color:#1B5EA2}
.exp-link{font-size:11px;color:#2E75B6;text-decoration:none;font-weight:600;border:1px solid #2E75B6;padding:3px 9px;border-radius:12px;white-space:nowrap;transition:all .15s}
.exp-link:hover{background:#2E75B6;color:#fff}
.exp-fecha{font-size:11px;color:#888}
.card-body{padding:12px 14px 6px}
.extracto{font-size:14px;font-weight:600;color:#2C2C2C;line-height:1.4;margin-bottom:10px}
.card-meta{display:flex;flex-direction:column;gap:5px;padding-bottom:10px}
.meta-row{display:flex;gap:6px;align-items:flex-start;flex-wrap:wrap}
.meta-bold{font-size:13px;font-weight:600;color:#4A4A4A}
.btag{display:inline-block;font-size:11px;font-weight:600;padding:3px 8px;border-radius:4px;margin-right:4px;margin-bottom:3px}
.ctag{display:inline-block;font-size:11px;padding:3px 8px;border-radius:4px;margin-right:4px;margin-bottom:3px;background:#EAF0FA;color:#1B5EA2;border:1px solid #c8daf0}
.no-results{text-align:center;padding:48px 16px;color:#aaa;font-size:14px}
.footer{text-align:center;padding:20px 16px;font-size:11px;color:#aaa;font-style:italic}

/* ── Comisiones ───────────────────────────────────────────────────────── */
.com-nivel{display:none}
.com-nivel.active{display:block}
.com-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px;margin-top:14px}
.com-card{background:#fff;border:1px solid #D6E4F0;border-radius:10px;padding:14px 16px;cursor:pointer;transition:all .15s;box-shadow:0 1px 3px rgba(0,0,0,0.05)}
.com-card:hover{border-color:#1B5EA2;box-shadow:0 2px 8px rgba(27,94,162,0.15);transform:translateY(-1px)}
.com-card-nombre{font-size:14px;font-weight:700;color:#1B5EA2;line-height:1.3}
.btn-volver{padding:7px 14px;border-radius:8px;border:1.5px solid #fff;background:transparent;color:#fff;font-family:inherit;font-size:11px;font-weight:600;cursor:pointer;transition:all .15s}
.btn-volver:hover{background:#fff;color:#1B5EA2}
.com-detalle-layout{display:flex;gap:16px;align-items:flex-start}
.com-panel{flex:1;min-width:0}
.com-panel-integrantes{flex:0 0 340px}
.com-panel-title{font-size:11px;font-weight:700;color:#1B5EA2;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;padding-bottom:6px;border-bottom:1px solid #D6E4F0}
@media(max-width:800px){.com-detalle-layout{flex-direction:column}.com-panel-integrantes{flex:0 0 auto;width:100%}}
.integrante-row{display:flex;align-items:center;gap:8px;padding:8px 4px;border-bottom:1px solid #EEF2F8}
.integrante-row:last-child{border-bottom:none}
.integrante-nombre{font-size:12.5px;color:#4A4A4A;flex:1;min-width:0}
.rol-badge{font-size:9.5px;font-weight:700;padding:2px 7px;border-radius:10px;text-transform:uppercase;letter-spacing:.4px;white-space:nowrap;flex-shrink:0}
.rol-Presidente{background:#1B5EA2;color:#fff}
.rol-Vicepresidente{background:#D6E4F0;color:#1B5EA2}
.rol-Secretario{background:#EAF0FA;color:#2E75B6}
.rol-Vocal{background:#F5F7FA;color:#9aacbd}
.com-proximareunion{margin-top:16px;background:#D6E4F0;border-left:3px solid #2E75B6;border-radius:6px;padding:12px 16px;font-size:12.5px;color:#0d3f73;display:flex;flex-wrap:wrap;gap:6px 18px;align-items:center}
.com-proximareunion strong{color:#1B5EA2}
.semaforo{display:inline-block;width:9px;height:9px;border-radius:50%;flex-shrink:0}
.sem-verde{background:#1a9c4a}
.sem-amarillo{background:#d9a300}
.sem-rojo{background:#c0392b}
.com-empty{text-align:center;padding:40px 16px;color:#aaa;font-size:13px}

/* ── Representación por bloques ──────────────────────────────────────── */
.repr-titulo{font-size:11px;font-weight:700;color:#1B5EA2;text-transform:uppercase;letter-spacing:1px;margin:18px 0 8px;padding-bottom:5px;border-bottom:1px solid #D6E4F0}
.repr-titulo:first-child{margin-top:0}
.repr-hint{font-size:11px;color:#888;margin-bottom:8px}
.repr-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid #D6E4F0;border-radius:10px}
table.repr-table{width:100%;border-collapse:collapse;font-size:12px}
table.repr-table th{background:#1B5EA2;color:#fff;padding:8px 12px;text-align:left;font-weight:600;font-size:11px;white-space:nowrap}
table.repr-table th.num,table.repr-table td.num{text-align:center}
table.repr-table td{padding:7px 12px;border-bottom:1px solid #EEF2F8;vertical-align:middle}
table.repr-table tr:last-child td{border-bottom:none}
table.repr-table tr:hover td{background:#F5F8FC}
.repr-bloque-cell{display:flex;align-items:center;gap:7px;white-space:nowrap}
.repr-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
table.cross-table{border-collapse:collapse;font-size:11px}
table.cross-table th.blq-col{text-align:left;padding:8px 12px;background:#1B5EA2;color:#fff;white-space:nowrap;position:sticky;left:0;z-index:2;min-width:150px}
table.cross-table th.com-col{background:#1B5EA2;color:#fff;padding:0 3px 8px;width:30px;min-width:30px;max-width:30px;vertical-align:bottom;text-align:center}
table.cross-table th.com-col span{display:block;writing-mode:vertical-rl;transform:rotate(180deg);font-size:9.5px;font-weight:500;line-height:1;white-space:nowrap;max-height:110px;overflow:hidden}
table.cross-table td.blq-name{padding:6px 12px;white-space:nowrap;font-size:11px;font-weight:600;position:sticky;left:0;border-right:1px solid #EEF2F8}
table.cross-table td.val{text-align:center;padding:5px 3px;border-bottom:1px solid #EEF2F8;border-right:1px solid #EEF2F8;font-size:11.5px;width:30px}
table.cross-table tr:last-child td{border-bottom:none}
"""

# ── JavaScript (vanilla) ───────────────────────────────────────────────────────

JS = r"""
var TIPOS={PL:'Proy. de Ley',PD:'Declaración',PC:'Comunicación',PR:'Resolución',CA:'Com. Auditoría',AC:'Acuerdo',CV:'Com. Varias'};
var TIPO_FG={PL:'#1B5EA2',PD:'#2E75B6',PC:'#0d7a4a',PR:'#5B4DA0',CA:'#1a7a4a',AC:'#7a5c1a',CV:'#7a1a3a'};
var TIPO_BG={PL:'#D6E4F0',PD:'#EAF0FA',PC:'#DCF0E8',PR:'#EDE8FA',CA:'#E0F4EC',AC:'#F9F0DA',CV:'#FAE0EA'};
var ORIGEN_LABEL={S:'Senado',PE:'Poder Ejecutivo',CD:'Diputados',OV:'Otros'};
var ORIGEN_CODE={};Object.keys(ORIGEN_LABEL).forEach(function(k){ORIGEN_CODE[ORIGEN_LABEL[k]]=k});
var BC=['#1B5EA2','#2E75B6','#5B4DA0','#1a7a4a','#7a5c1a','#7a1a3a','#2E8B7A','#6B3A2A','#1a4a7a','#4a7a1a','#7a1a5a','#2a7a6a','#5a2a7a','#2a5a2a'];
var ALL_BLOQUES=[];
var dashAnio='2026',dashEvoMode='tipo',dashCross={dim:'',val:''};
var activeTipos={},activeBloque='',activeOrigen='',activeProvincia='',activeAnio='';

/* ── Escapado HTML básico ──────────────────────────────────────────── */
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function escAttr(s){return esc(s).replace(/"/g,'&quot;')}

/* ── Navegación ────────────────────────────────────────────────────── */
function switchMain(id){
  document.querySelectorAll('.mtab-btn').forEach(function(b){b.classList.remove('active')});
  document.querySelectorAll('.mtab-content').forEach(function(c){c.classList.remove('active')});
  document.getElementById('main-'+id).classList.add('active');
  document.querySelector('[data-main="'+id+'"]').classList.add('active');
}
function switchSub(id){
  document.querySelectorAll('.sub-btn').forEach(function(b){b.classList.remove('active')});
  document.querySelectorAll('.sub-content').forEach(function(c){c.classList.remove('active')});
  document.getElementById('sub-'+id).classList.add('active');
  document.querySelector('[data-sub="'+id+'"]').classList.add('active');
  if(id==='tabla')renderPivot();
  if(id==='dashboard')renderDashboard();
}

function init(){
  var bset={};
  DATA.forEach(function(p){p.bloques.forEach(function(b){if(b)bset[b]=1})});
  ALL_BLOQUES=Object.keys(bset).sort();

  var cset1={},csetAdic={};
  DATA.forEach(function(p){
    if(p.comisiones[0])cset1[p.comisiones[0]]=1;
    if(p.comisiones[1])csetAdic[p.comisiones[1]]=1;
    if(p.comisiones[2])csetAdic[p.comisiones[2]]=1;
  });
  fillSelect('com-select-1',Object.keys(cset1).sort());
  fillSelect('com-select-adic',Object.keys(csetAdic).sort());

  var aset={};
  DATA.forEach(function(p){p.autores.forEach(function(a){aset[a]=1})});
  fillSelect('autor-select',Object.keys(aset).sort());

  fillSelect('bloque-select',ALL_BLOQUES);

  var provSet={};
  DATA.forEach(function(p){(p.provincias||[]).forEach(function(pv){if(pv)provSet[pv]=1})});
  fillSelect('provincia-select',Object.keys(provSet).sort());

  initPivot();
  renderDashboard();
  syncFilterUI();
  renderList();
  renderPivot();
  renderComisionesList();
  renderRepresentacion();
}
function fillSelect(id,values){
  var sel=document.getElementById(id);
  values.forEach(function(v){
    var o=document.createElement('option');o.value=v;o.textContent=v;sel.appendChild(o);
  });
}
function getBloqueColor(b){
  var i=ALL_BLOQUES.indexOf(b);
  if(i<0){var h=0;for(var k=0;k<b.length;k++)h=(h*31+b.charCodeAt(k))|0;i=h;}
  return BC[((i%BC.length)+BC.length)%BC.length];
}

/* ── Dashboard de análisis ─────────────────────────────────────── */
var MESES=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
function crossMatch(p){
  if(!dashCross.dim)return true;
  if(dashCross.dim==='tipo')return p.tipo===dashCross.val;
  if(dashCross.dim==='bloque')return p.bloques.indexOf(dashCross.val)>=0||bloqueOf(p)===dashCross.val;
  if(dashCross.dim==='com')return (p.comisiones[0]||'')===dashCross.val;
  return true;
}
function dashData(){return DATA.filter(function(p){return String(p.anio)===dashAnio&&crossMatch(p);})}
function jsStr(s){return String(s).replace(/\\/g,'\\\\').replace(/'/g,"\\'");}
function crossClick(dim,val){
  if(!val)return;
  if(dashCross.dim===dim&&dashCross.val===val)dashCross={dim:'',val:''};
  else dashCross={dim:dim,val:val};
  renderDashboard();
}
function clearCross(){dashCross={dim:'',val:''};renderDashboard();}
function setDashAnio(y){
  dashAnio=y;dashCross={dim:'',val:''};
  ['2026','2025'].forEach(function(a){
    var el=document.getElementById('dash-anio-'+a);
    if(el)el.className='chip'+(dashAnio===a?' on':'');
  });
  renderDashboard();
}
function setEvoMode(m){
  dashEvoMode=m;
  document.getElementById('evo-tipo').className=(m==='tipo'?'on':'');
  document.getElementById('evo-bloque').className=(m==='bloque'?'on':'');
  renderEvolucion(dashData());
}
function renderDashboard(){
  var data=dashData();
  document.getElementById('dash-total').innerHTML='<strong>'+data.length+'</strong> proyectos en '+dashAnio;
  var ci=document.getElementById('dash-cross');
  if(dashCross.dim){
    var dimL={tipo:'tipo',bloque:'bloque',com:'comisión'}[dashCross.dim];
    var valL=dashCross.dim==='tipo'?(TIPOS[dashCross.val]||dashCross.val):dashCross.val;
    ci.innerHTML='Filtrando por: <strong>'+esc(valL)+'</strong> <span style="opacity:.65">('+dimL+')</span> &#x2715;';
    ci.className='dash-cross active';
  }else{ci.className='dash-cross';ci.innerHTML='';}
  renderEvolucion(data);
  renderTreemap(data);
  renderStacked(data);
  renderDonut(data);
  renderTopComs(data);
}
/* tooltip flotante compartido */
function showTip(html,ev){
  var t=document.getElementById('dash-tooltip');
  t.innerHTML=html;t.className='dash-tooltip show';
  var x=ev.clientX,y=ev.clientY,w=t.offsetWidth,h=t.offsetHeight;
  if(x+w+18>window.innerWidth)x=x-w-14;else x=x+14;
  if(y+h+18>window.innerHeight)y=y-h-14;else y=y+14;
  t.style.left=x+'px';t.style.top=y+'px';
}
function hideTip(){document.getElementById('dash-tooltip').className='dash-tooltip';}
/* helpers de agregación */
function topSeries(counts,n){
  /* counts: {clave:total}; devuelve top n claves + 'Otros' si sobra */
  var keys=Object.keys(counts).sort(function(a,b){return counts[b]-counts[a]});
  if(keys.length<=n)return{keys:keys,hasOtros:false};
  return{keys:keys.slice(0,n),hasOtros:true};
}
/* ── Viz 1: Evolución temporal (líneas) ──────────────────────── */
var EVO=null;
function monthOf(p){if(!p.fecha)return -1;var pp=p.fecha.split('/');return pp.length===3?parseInt(pp[1],10)-1:-1;}
function evoKey(p){return dashEvoMode==='tipo'?p.tipo:(p.bloques[0]||(ORIGEN_LABEL[p.origen]||'Otros'));}
function evoColor(k){if(k==='__otros')return '#9aacbd';return dashEvoMode==='tipo'?(TIPO_FG[k]||'#888'):getBloqueColor(k);}
function evoLabel(k){if(k==='__otros')return 'Resto';return dashEvoMode==='tipo'?(TIPOS[k]||k):k;}
function renderEvolucion(data){
  var totals={};
  data.forEach(function(p){var k=evoKey(p);totals[k]=(totals[k]||0)+1;});
  var sel=topSeries(totals,5),keys=sel.keys.slice(),useOtros=sel.hasOtros;
  var lastM=0,any=false;
  data.forEach(function(p){var m=monthOf(p);if(m>=0){any=true;if(m>lastM)lastM=m;}});
  var nM=any?lastM+1:1;
  var series={};keys.forEach(function(k){series[k]=[];for(var j=0;j<nM;j++)series[k].push(0);});
  if(useOtros){series['__otros']=[];for(var j=0;j<nM;j++)series['__otros'].push(0);}
  data.forEach(function(p){
    var m=monthOf(p);if(m<0||m>=nM)return;
    var k=evoKey(p);
    if(keys.indexOf(k)>=0)series[k][m]++;else if(useOtros)series['__otros'][m]++;
  });
  var order=keys.slice();if(useOtros)order.push('__otros');
  var maxY=1;order.forEach(function(k){series[k].forEach(function(v){if(v>maxY)maxY=v;});});

  var W=600,H=240,L=38,R=14,T=12,B=26,pw=W-L-R,ph=H-T-B;
  function X(i){return nM>1?L+i/(nM-1)*pw:L+pw/2;}
  function Y(v){return T+ph-(v/maxY)*ph;}
  var svg='<svg class="viz-svg" viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="xMidYMid meet">';
  [0,0.5,1].forEach(function(f){var v=Math.round(maxY*f),y=Y(v);
    svg+='<line class="viz-gridline" x1="'+L+'" y1="'+y+'" x2="'+(W-R)+'" y2="'+y+'"/>';
    svg+='<text class="viz-axis" x="'+(L-6)+'" y="'+(y+3)+'" text-anchor="end">'+v+'</text>';});
  for(var i=0;i<nM;i++)svg+='<text class="viz-axis" x="'+X(i)+'" y="'+(H-8)+'" text-anchor="middle">'+MESES[i]+'</text>';
  order.forEach(function(k){
    var pts=series[k].map(function(v,i){return X(i).toFixed(1)+','+Y(v).toFixed(1);}).join(' ');
    var c=evoColor(k);
    svg+='<polyline points="'+pts+'" fill="none" stroke="'+c+'" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>';
    series[k].forEach(function(v,i){svg+='<circle cx="'+X(i).toFixed(1)+'" cy="'+Y(v).toFixed(1)+'" r="2.6" fill="'+c+'"/>';});
  });
  svg+='<line id="evo-guide" x1="0" y1="'+T+'" x2="0" y2="'+(T+ph)+'" stroke="#1B5EA2" stroke-width="1" stroke-dasharray="3 3" opacity="0"/>';
  for(var i=0;i<nM;i++){
    var bw=nM>1?pw/(nM-1):pw, bx=nM>1?X(i)-bw/2:L;
    svg+='<rect x="'+bx.toFixed(1)+'" y="'+T+'" width="'+bw.toFixed(1)+'" height="'+ph+'" fill="transparent" onmousemove="evoHover(event,'+i+')" onmouseleave="evoOut()"/>';
  }
  svg+='</svg>';
  document.getElementById('viz-evolucion').innerHTML=svg;
  var leg='';var edim=dashEvoMode==='tipo'?'tipo':'bloque';
  order.forEach(function(k){
    var clk=(k!=='__otros');
    var on=clk&&dashCross.dim===edim&&dashCross.val===k;
    var oc=clk?' class="legend-item clk" onclick="crossClick(\''+edim+'\',\''+jsStr(k)+'\')"':' class="legend-item"';
    leg+='<span'+oc+(on?' style="font-weight:700;color:#1B5EA2"':'')+'><span class="legend-swatch" style="background:'+evoColor(k)+'"></span>'+esc(evoLabel(k))+'</span>';
  });
  document.getElementById('evo-legend').innerHTML=leg;
  EVO={nM:nM,order:order,series:series,xs:[]};for(var i=0;i<nM;i++)EVO.xs.push(X(i));
}
function evoHover(ev,i){
  if(!EVO)return;
  var g=document.getElementById('evo-guide');
  if(g){g.setAttribute('x1',EVO.xs[i]);g.setAttribute('x2',EVO.xs[i]);g.setAttribute('opacity','1');}
  var rows='';
  EVO.order.forEach(function(k){
    rows+='<div class="dash-tt-row"><span class="dash-tt-dot" style="background:'+evoColor(k)+'"></span>'+esc(evoLabel(k))+'<span class="v">'+EVO.series[k][i]+'</span></div>';
  });
  showTip('<div class="dash-tt-title">'+MESES[i]+' '+dashAnio+'</div>'+rows,ev);
}
function evoOut(){var g=document.getElementById('evo-guide');if(g)g.setAttribute('opacity','0');hideTip();}
/* ── Viz 2: Treemap por bloque, subdividido por tipo ─────────── */
function bloqueOf(p){return p.bloques[0]||(ORIGEN_LABEL[p.origen]||'Otros');}
function trunc(s,n){s=String(s);return s.length>n?s.slice(0,n-1)+'…':s;}
/* treemap "squarified" (tiles casi cuadrados, sin librerías) */
function treemapLayout(items,x,y,w,h){
  if(!items.length)return [];
  var total=0;items.forEach(function(it){total+=it.value;});
  if(total<=0)return [];
  var scale=(w*h)/total;
  var rem=items.map(function(it){return {key:it.key,value:it.value,area:it.value*scale};});
  var area={x:x,y:y,w:w,h:h},out=[];
  function worst(row,side){
    var s=0,mx=-Infinity,mn=Infinity;
    row.forEach(function(r){s+=r.area;if(r.area>mx)mx=r.area;if(r.area<mn)mn=r.area;});
    var s2=s*s,l2=side*side;
    return Math.max(l2*mx/s2,s2/(l2*mn));
  }
  while(rem.length){
    var side=Math.min(area.w,area.h),row=[];
    while(rem.length){
      if(row.length===0||worst(row,side)>=worst(row.concat([rem[0]]),side))row.push(rem.shift());
      else break;
    }
    var rs=0;row.forEach(function(r){rs+=r.area;});
    if(area.w>=area.h){
      var dw=rs/area.h,yy=area.y;
      row.forEach(function(r){var rh=r.area/dw;out.push({key:r.key,value:r.value,x:area.x,y:yy,w:dw,h:rh});yy+=rh;});
      area.x+=dw;area.w-=dw;
    }else{
      var dh=rs/area.w,xx=area.x;
      row.forEach(function(r){var rw=r.area/dh;out.push({key:r.key,value:r.value,x:xx,y:area.y,w:rw,h:dh});xx+=rw;});
      area.y+=dh;area.h-=dh;
    }
  }
  return out;
}
function renderTreemap(data){
  var box=document.getElementById('viz-treemap');
  /* solo bloques políticos: expedientes de origen Senado (S) con bloque asignado */
  var dS=data.filter(function(p){return p.origen==='S'&&p.bloques[0];});
  var blTot={};dS.forEach(function(p){var b=p.bloques[0];blTot[b]=(blTot[b]||0)+1;});
  var keys=Object.keys(blTot).sort(function(a,b){return blTot[b]-blTot[a];});
  if(!keys.length){box.innerHTML='<div class="viz-empty">Sin datos para este a&ntilde;o.</div>';document.getElementById('treemap-legend').innerHTML='';return;}
  var items=keys.map(function(k){return {key:k,value:blTot[k]};});
  var tb={};dS.forEach(function(p){var b=p.bloques[0];(tb[b]=tb[b]||{});tb[b][p.tipo]=(tb[b][p.tipo]||0)+1;});
  var W=1000,H=300,pad=3,tipoOrder=['PL','PD','PC','PR','CA','AC','CV'];
  var rects=treemapLayout(items,0,0,W,H);
  var svg='<svg viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="xMidYMid meet" style="display:block;width:100%;height:auto;max-height:380px">';
  rects.forEach(function(r){
    var bl=r.key,label=bl,comp=tb[bl]||{};
    var x=r.x+pad/2,y=r.y+pad/2,w=Math.max(0,r.w-pad),h=Math.max(0,r.h-pad),horiz=w>=h,acc=0;
    var oc=' style="cursor:pointer" onclick="crossClick(\'bloque\',\''+jsStr(bl)+'\')"';
    tipoOrder.forEach(function(t){
      var v=comp[t]||0;if(!v)return;
      var frac=v/r.value,sc=TIPO_FG[t]||'#888';
      if(horiz){var sw=w*frac;svg+='<rect x="'+(x+acc).toFixed(1)+'" y="'+y.toFixed(1)+'" width="'+sw.toFixed(1)+'" height="'+h.toFixed(1)+'" fill="'+sc+'"'+oc+'><title>'+esc(label)+' · '+esc(TIPOS[t]||t)+': '+v+'</title></rect>';acc+=sw;}
      else{var sh=h*frac;svg+='<rect x="'+x.toFixed(1)+'" y="'+(y+acc).toFixed(1)+'" width="'+w.toFixed(1)+'" height="'+sh.toFixed(1)+'" fill="'+sc+'"'+oc+'><title>'+esc(label)+' · '+esc(TIPOS[t]||t)+': '+v+'</title></rect>';acc+=sh;}
    });
    svg+='<rect x="'+x.toFixed(1)+'" y="'+y.toFixed(1)+'" width="'+w.toFixed(1)+'" height="'+h.toFixed(1)+'" fill="none" stroke="#fff" stroke-width="1.5" pointer-events="none"/>';
    if(w>62&&h>28){
      svg+='<text x="'+(x+5).toFixed(1)+'" y="'+(y+15).toFixed(1)+'" style="font-size:11px;font-weight:700;fill:#fff;pointer-events:none">'+esc(trunc(label,Math.floor(w/7)))+'</text>';
      svg+='<text x="'+(x+5).toFixed(1)+'" y="'+(y+30).toFixed(1)+'" style="font-size:12px;font-weight:700;fill:#fff;opacity:.85;pointer-events:none">'+r.value+'</text>';
    }
  });
  svg+='</svg>';
  box.innerHTML=svg;
  var leg='';tipoOrder.forEach(function(t){if(!dS.some(function(p){return p.tipo===t;}))return;leg+='<span class="legend-item"><span class="legend-swatch" style="background:'+(TIPO_FG[t]||'#888')+'"></span>'+esc(TIPOS[t]||t)+'</span>';});
  document.getElementById('treemap-legend').innerHTML=leg;
}
/* ── Viz 3: Barras apiladas horizontales (Tipo por Bloque) ───── */
function renderStacked(data){
  var box=document.getElementById('viz-stacked');
  var tipoTot={};data.forEach(function(p){tipoTot[p.tipo]=(tipoTot[p.tipo]||0)+1;});
  var tipos=Object.keys(tipoTot).sort(function(a,b){return tipoTot[b]-tipoTot[a];});
  if(!tipos.length){box.innerHTML='<div class="viz-empty">Sin datos.</div>';document.getElementById('stacked-legend').innerHTML='';return;}
  var blTot={};data.forEach(function(p){var b=bloqueOf(p);blTot[b]=(blTot[b]||0)+1;});
  var selB=topSeries(blTot,6),topB=selB.keys,useResto=selB.hasOtros;
  var m={};
  data.forEach(function(p){
    var t=p.tipo,b=bloqueOf(p),key=topB.indexOf(b)>=0?b:'__resto';
    (m[t]=m[t]||{});m[t][key]=(m[t][key]||0)+1;
  });
  var order=topB.slice();if(useResto)order.push('__resto');
  var maxT=tipos.reduce(function(mx,t){return Math.max(mx,tipoTot[t]);},1);
  var W=600,L=46,R=46,T=6,rowH=30,barH=18,pw=W-L-R,H=T+tipos.length*rowH+2;
  function sc(c){return c==='__resto'?'#9aacbd':getBloqueColor(c);}
  function sl(c){return c==='__resto'?'Resto':c;}
  var svg='<svg viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="xMidYMid meet" style="width:100%;height:auto;display:block">';
  tipos.forEach(function(t,ti){
    var cy=T+ti*rowH+rowH/2,barY=cy-barH/2,xacc=L;
    var ton=(dashCross.dim==='tipo'&&dashCross.val===t);
    svg+='<text x="0" y="'+(cy+4)+'" style="cursor:pointer;font-size:12px;font-weight:700;fill:'+(ton?'#0d3f73':(TIPO_FG[t]||'#888'))+(ton?';text-decoration:underline':'')+'" onclick="crossClick(\'tipo\',\''+jsStr(t)+'\')">'+esc(t)+'</text>';
    order.forEach(function(b){
      var v=(m[t]&&m[t][b])||0;if(!v)return;
      var w=v/maxT*pw,clk=(b!=='__resto');
      var oc=clk?' style="cursor:pointer" onclick="crossClick(\'bloque\',\''+jsStr(b)+'\')"':'';
      svg+='<rect x="'+xacc.toFixed(1)+'" y="'+barY+'" width="'+w.toFixed(1)+'" height="'+barH+'" fill="'+sc(b)+'"'+oc+'><title>'+esc(sl(b))+' &middot; '+esc(TIPOS[t]||t)+': '+v+' ('+Math.round(v/tipoTot[t]*100)+'%)</title></rect>';
      xacc+=w;
    });
    svg+='<text x="'+(L+tipoTot[t]/maxT*pw+5).toFixed(1)+'" y="'+(cy+4)+'" style="font-size:11px;font-weight:700;fill:#1B5EA2">'+tipoTot[t]+'</text>';
  });
  svg+='</svg>';
  box.innerHTML=svg;
  var leg='';order.forEach(function(b){
    var clk=(b!=='__resto'),on=clk&&dashCross.dim==='bloque'&&dashCross.val===b;
    var oc=clk?' class="legend-item clk" onclick="crossClick(\'bloque\',\''+jsStr(b)+'\')"':' class="legend-item"';
    leg+='<span'+oc+(on?' style="font-weight:700;color:#1B5EA2"':'')+'><span class="legend-swatch" style="background:'+sc(b)+'"></span>'+esc(trunc(sl(b),22))+'</span>';
  });
  document.getElementById('stacked-legend').innerHTML=leg;
}
/* ── Viz 5: Donut — distribución por tipo de proyecto ────────── */
function renderDonut(data){
  var box=document.getElementById('viz-donut');
  var tipoTot={};data.forEach(function(p){tipoTot[p.tipo]=(tipoTot[p.tipo]||0)+1;});
  var tipos=Object.keys(tipoTot).sort(function(a,b){return tipoTot[b]-tipoTot[a];});
  var total=data.length;
  if(!total){box.innerHTML='<div class="viz-empty">Sin datos para este a&ntilde;o.</div>';return;}
  var cx=100,cy=100,R=70,SW=28,C=2*Math.PI*R,cum=0;
  var svg='<svg viewBox="0 0 200 200" style="width:150px;height:150px;flex-shrink:0"><g transform="rotate(-90 '+cx+' '+cy+')">';
  tipos.forEach(function(t){
    var frac=tipoTot[t]/total,dash=frac*C,c=TIPO_FG[t]||'#888';
    svg+='<circle cx="'+cx+'" cy="'+cy+'" r="'+R+'" fill="none" stroke="'+c+'" stroke-width="'+SW+'" stroke-dasharray="'+dash.toFixed(2)+' '+(C-dash).toFixed(2)+'" stroke-dashoffset="'+(-cum*C).toFixed(2)+'" style="cursor:pointer" onclick="crossClick(\'tipo\',\''+jsStr(t)+'\')"><title>'+esc(TIPOS[t]||t)+': '+tipoTot[t]+' ('+Math.round(frac*100)+'%)</title></circle>';
    cum+=frac;
  });
  svg+='</g><text x="'+cx+'" y="'+(cy-1)+'" text-anchor="middle" style="font-size:30px;font-weight:700;fill:#1B5EA2">'+total+'</text>';
  svg+='<text x="'+cx+'" y="'+(cy+17)+'" text-anchor="middle" style="font-size:11px;fill:#888">proyectos</text></svg>';
  var leg='<div class="viz-legend" style="flex:1;margin-top:0;flex-direction:column;gap:5px;min-width:130px">';
  tipos.forEach(function(t){
    var pct=Math.round(tipoTot[t]/total*100),on=dashCross.dim==='tipo'&&dashCross.val===t;
    leg+='<span class="legend-item clk" style="justify-content:flex-start'+(on?';font-weight:700;color:#1B5EA2':'')+'" onclick="crossClick(\'tipo\',\''+jsStr(t)+'\')"><span class="legend-swatch" style="background:'+(TIPO_FG[t]||'#888')+'"></span>'+esc(TIPOS[t]||t)+' &middot; <strong style="margin-left:3px">'+tipoTot[t]+'</strong> ('+pct+'%)</span>';
  });
  leg+='</div>';
  box.innerHTML='<div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap;justify-content:center">'+svg+leg+'</div>';
}
/* ── Viz 4: Top 10 comisiones con sparkline de tendencia ─────── */
function fmtDM(d){return ('0'+d.getDate()).slice(-2)+'/'+('0'+(d.getMonth()+1)).slice(-2);}
function sparkline(vals,bins){
  var w=92,h=26,p=3,n=vals.length,mx=Math.max.apply(null,vals)||1;
  function X(i){return p+(n>1?i/(n-1)*(w-2*p):(w-2*p)/2);}
  function Y(v){return h-p-(v/mx)*(h-2*p);}
  var pts=vals.map(function(v,i){return X(i).toFixed(1)+','+Y(v).toFixed(1);}).join(' ');
  var s='<svg class="topcom-spark" viewBox="0 0 '+w+' '+h+'">';
  s+='<line x1="'+p+'" y1="'+(h-p)+'" x2="'+(w-p)+'" y2="'+(h-p)+'" stroke="#E3EAF3" stroke-width="1"/>';
  s+='<polyline points="'+pts+'" fill="none" stroke="#2E75B6" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>';
  vals.forEach(function(v,i){
    var last=i===n-1;
    s+='<circle cx="'+X(i).toFixed(1)+'" cy="'+Y(v).toFixed(1)+'" r="'+(last?2.4:1.4)+'" fill="'+(last?'#1B5EA2':'#2E75B6')+'"><title>Semana '+fmtDM(bins[i][0])+'–'+fmtDM(bins[i][1])+': '+v+'</title></circle>';
  });
  s+='</svg>';
  return s;
}
function renderTopComs(data){
  var box=document.getElementById('viz-topcoms');
  var comC={};data.forEach(function(p){var c=p.comisiones[0];if(c)comC[c]=(comC[c]||0)+1;});
  var coms=Object.keys(comC).sort(function(a,b){return comC[b]-comC[a];}).slice(0,10);
  if(!coms.length){box.innerHTML='<div class="viz-empty">Sin datos para este a&ntilde;o.</div>';return;}
  var maxD=null;data.forEach(function(p){var d=parseFecha(p.fecha);if(d&&(!maxD||d>maxD))maxD=d;});
  if(!maxD)maxD=new Date();
  var WEEKS=8,MS=7*24*3600*1000;
  var bins=[];for(var i=0;i<WEEKS;i++){var end=new Date(maxD.getTime()-(WEEKS-1-i)*MS);bins.push([new Date(end.getTime()-6*MS),end]);}
  function binOf(d){var idx=WEEKS-1-Math.floor((maxD-d)/MS);return (idx>=0&&idx<WEEKS)?idx:-1;}
  var series={};coms.forEach(function(c){series[c]=[];for(var i=0;i<WEEKS;i++)series[c].push(0);});
  data.forEach(function(p){var c=p.comisiones[0];if(coms.indexOf(c)<0)return;var d=parseFecha(p.fecha);if(!d)return;var b=binOf(d);if(b>=0)series[c][b]++;});
  var rango=fmtDM(bins[0][0])+' &ndash; '+fmtDM(bins[WEEKS-1][1]);
  var html='<div style="font-size:10px;color:#888;margin-bottom:6px">Tendencia &uacute;ltimas 8 semanas ('+rango+') &middot; conteo total por 1er giro</div>';
  coms.forEach(function(c,i){
    var on=dashCross.dim==='com'&&dashCross.val===c;
    html+='<div class="topcom-row clk" onclick="crossClick(\'com\',\''+jsStr(c)+'\')"><span class="topcom-rank">'+(i+1)+'</span><span class="topcom-name"'+(on?' style="font-weight:700;color:#1B5EA2"':'')+'>'+esc(c)+'</span><span class="topcom-count">'+comC[c]+'</span>'+sparkline(series[c],bins)+'</div>';
  });
  box.innerHTML=html;
}

/* ── Tabla dinámica (pivot table) ──────────────────────────────── */
/* Dimensiones disponibles para Filas / Columnas */
var DIMS={
  tipo:{label:'Tipo de proyecto',get:function(p){return p.tipo},disp:function(v){return (TIPOS[v]||v)+' ('+v+')'}},
  anio:{label:'Año',get:function(p){return String(p.anio)}},
  origen:{label:'Origen',get:function(p){return ORIGEN_LABEL[p.origen]||p.origen}},
  bloque:{label:'Bloque político (1°)',get:function(p){return p.bloques[0]||(ORIGEN_LABEL[p.origen]||'(Sin bloque)')}},
  com1:{label:'Comisión (1er giro)',get:function(p){return p.comisiones[0]||'(Sin comisión)'}},
  provincia:{label:'Provincia (1°)',get:function(p){return (p.provincias&&p.provincias[0])||'(Sin provincia)'}},
  sancionado:{label:'Sancionado',get:function(p){return p.sancionado?'Sí':'No'}},
  mes:{label:'Mes (AAAA-MM)',get:function(p){var f=p.fecha?p.fecha.split('/'):null;return (f&&f.length===3)?f[2]+'-'+f[1]:'(Sin fecha)'}}
};
var DIM_ORDER=['bloque','com1','tipo','origen','provincia','anio','mes','sancionado'];
var DISP_NAME={abs:'Conteo de proyectos',ptotal:'% del total general',prow:'% de la fila',pcol:'% de la columna'};
var pvRow='bloque',pvCol='tipo',pvDisp='abs';
var PV_ROWKEYS=[],PV_COLKEYS=[];

function initPivot(){
  var ro=document.getElementById('pv-row'),co=document.getElementById('pv-col');
  DIM_ORDER.forEach(function(k){
    var o=document.createElement('option');o.value=k;o.textContent=DIMS[k].label;ro.appendChild(o);
    var o2=document.createElement('option');o2.value=k;o2.textContent=DIMS[k].label;co.appendChild(o2);
  });
  var none=document.createElement('option');none.value='none';none.textContent='— Ninguna (solo total) —';co.appendChild(none);
  ro.value=pvRow;co.value=pvCol;
  var anios={},tipos={},origs={};
  DATA.forEach(function(p){anios[p.anio]=1;tipos[p.tipo]=1;origs[p.origen]=1});
  Object.keys(anios).sort().forEach(function(a){var o=document.createElement('option');o.value=a;o.textContent=a;document.getElementById('pv-f-anio').appendChild(o)});
  Object.keys(tipos).sort().forEach(function(t){var o=document.createElement('option');o.value=t;o.textContent=t+' · '+(TIPOS[t]||t);document.getElementById('pv-f-tipo').appendChild(o)});
  Object.keys(origs).sort().forEach(function(x){var o=document.createElement('option');o.value=x;o.textContent=ORIGEN_LABEL[x]||x;document.getElementById('pv-f-origen').appendChild(o)});
}
/* Filtra por el estado COMPARTIDO (año/tipo/origen) — mismo que el buscador */
function pvFilteredData(){
  var tk=Object.keys(activeTipos);
  return DATA.filter(function(p){
    if(activeAnio&&String(p.anio)!==activeAnio)return false;
    if(tk.length&&!activeTipos[p.tipo])return false;
    if(activeOrigen&&p.origen!==activeOrigen)return false;
    return true;
  });
}
/* Ejes y modo de cálculo del pivot (no son estado compartido) */
function setPivot(){
  pvRow=document.getElementById('pv-row').value;
  pvCol=document.getElementById('pv-col').value;
  pvDisp=document.getElementById('pv-disp').value;
  renderPivot();
}
function renderPivot(){
  var data=pvFilteredData();
  var cNone=(pvCol==='none');
  var rget=DIMS[pvRow].get,cget=cNone?function(){return 'Conteo'}:DIMS[pvCol].get;
  var cells={},rowTot={},colTot={},grand=0,rowSet={},colSet={};
  data.forEach(function(p){
    var rk=rget(p),ck=cget(p);
    rowSet[rk]=1;colSet[ck]=1;
    cells[rk+'~|~'+ck]=(cells[rk+'~|~'+ck]||0)+1;
    rowTot[rk]=(rowTot[rk]||0)+1;colTot[ck]=(colTot[ck]||0)+1;grand++;
  });
  var rowKeys=Object.keys(rowSet).sort(function(a,b){return rowTot[b]-rowTot[a]});
  var colKeys=Object.keys(colSet).sort(function(a,b){return colTot[b]-colTot[a]});
  PV_ROWKEYS=rowKeys;PV_COLKEYS=colKeys;
  var maxCell=0;
  rowKeys.forEach(function(rk){colKeys.forEach(function(ck){var v=cells[rk+'~|~'+ck]||0;if(v>maxCell)maxCell=v})});

  var dispRow=DIMS[pvRow].disp||function(v){return v};
  var dispCol=cNone?function(v){return v}:(DIMS[pvCol].disp||function(v){return v});
  function fmt(v,rk,ck){
    if(!v)return '';
    if(pvDisp==='abs')return v;
    var d=pvDisp==='ptotal'?grand:(pvDisp==='prow'?rowTot[rk]:colTot[ck]);
    return d?(Math.round(v/d*1000)/10)+'%':'';
  }
  var h='<table class="pivot-table"><thead><tr><th class="pv-corner">'+esc(DIMS[pvRow].label)+(cNone?'':' \\ '+esc(DIMS[pvCol].label))+'</th>';
  colKeys.forEach(function(ck){h+='<th>'+esc(dispCol(ck))+'</th>'});
  h+='<th class="pv-tot">Total</th></tr></thead><tbody>';
  rowKeys.forEach(function(rk,ri){
    h+='<tr><th class="pv-rowhead" title="'+escAttr(dispRow(rk))+'">'+esc(dispRow(rk))+'</th>';
    colKeys.forEach(function(ck,ci){
      var v=cells[rk+'~|~'+ck]||0;
      var style='',cls='pv-cell';
      if(v){
        cls+=' pv-click';
        var intensity=maxCell?v/maxCell:0;
        style='background:rgba(27,94,162,'+(0.06+intensity*0.74).toFixed(3)+')';
        if(intensity>0.55)style+=';color:#fff';
      }else{cls+=' pv-empty'}
      h+='<td class="'+cls+'" style="'+style+'"'+(v?' onclick="drillPivot('+ri+','+ci+')"':'')+'>'+fmt(v,rk,ck)+'</td>';
    });
    h+='<td class="pv-tot">'+rowTot[rk]+'</td></tr>';
  });
  h+='<tr class="pv-totrow"><th class="pv-rowhead">Total general</th>';
  colKeys.forEach(function(ck){h+='<td class="pv-tot">'+colTot[ck]+'</td>'});
  h+='<td class="pv-grand">'+grand+'</td></tr></tbody></table>';
  document.getElementById('pivot-body').innerHTML=grand?h:'<div class="no-results">Sin datos para los filtros seleccionados.</div>';
  document.getElementById('pivot-meta').innerHTML='<strong>'+grand+'</strong> proyectos &middot; '+rowKeys.length+' filas &times; '+colKeys.length+' columna'+(colKeys.length!==1?'s':'')+' &middot; Valor: <strong>'+DISP_NAME[pvDisp]+'</strong> &middot; <span style="color:#aaa">toc&aacute; una celda para filtrar los expedientes de abajo</span>';
}
/* Limpia los filtros propios del buscador (no los compartidos año/tipo/origen) */
function resetBuscadorOnly(){
  activeBloque='';activeProvincia='';
  setSelVal('bloque-select','');setSelVal('provincia-select','');
  setSelVal('com-select-1','');setSelVal('com-select-adic','');setSelVal('autor-select','');
  document.getElementById('search').value='';
  document.getElementById('fecha-desde').value='';
  document.getElementById('fecha-hasta').value='';
}
/* Clic en celda: preserva los filtros compartidos (universo del pivot), resetea
   los del buscador, mapea fila+columna de la celda y salta al Buscador */
function drillPivot(ri,ci){
  resetBuscadorOnly();
  applyDimToFilter(pvRow,PV_ROWKEYS[ri]);
  if(pvCol!=='none')applyDimToFilter(pvCol,PV_COLKEYS[ci]);
  applyAll();
  switchSub('buscador');
  window.scrollTo({top:0,behavior:'smooth'});
}
function setSelVal(id,v){var el=document.getElementById(id);if(el){el.value=v;el.className=v?'filter-select on':'filter-select';}}
function applyDimToFilter(dim,value){
  if(dim==='anio'){activeAnio=value;}
  else if(dim==='tipo'){activeTipos={};activeTipos[value]=1;}
  else if(dim==='origen'){if(ORIGEN_CODE[value])activeOrigen=ORIGEN_CODE[value];}
  else if(dim==='bloque'){
    if(ALL_BLOQUES.indexOf(value)>=0){activeBloque=value;setSelVal('bloque-select',value);}
    else if(ORIGEN_CODE[value]){activeOrigen=ORIGEN_CODE[value];}
  }
  else if(dim==='provincia'){if(value!=='(Sin provincia)'){activeProvincia=value;setSelVal('provincia-select',value);}}
  else if(dim==='com1'){if(value!=='(Sin comisión)'){setSelVal('com-select-1',value);}}
  /* sancionado, mes: sin filtro equivalente en el buscador -> se ignoran */
}

/* ── Estado de filtros compartido (año/tipo/origen) ─────────────── */
function applyAll(){syncFilterUI();renderPivot();renderList();}
function syncFilterUI(){
  ['all','2025','2026'].forEach(function(a){
    var el=document.getElementById('anio-det-'+a);
    if(el)el.className='chip'+(activeAnio===(a==='all'?'':a)?' on':'');
  });
  var pa=document.getElementById('pv-f-anio');if(pa)pa.value=activeAnio;
  var tk=Object.keys(activeTipos);
  var pt=document.getElementById('pv-f-tipo');if(pt)pt.value=(tk.length===1?tk[0]:'');
  var po=document.getElementById('pv-f-origen');if(po)po.value=activeOrigen;
  renderFilters();
}
function setAnioShared(v){activeAnio=v;applyAll();}
function setTipoShared(v){activeTipos={};if(v)activeTipos[v]=1;applyAll();}
function setOrigenShared(v){activeOrigen=v;applyAll();}
function clearSharedFilters(){activeAnio='';activeTipos={};activeOrigen='';applyAll();}

/* ── Buscador: filtros ─────────────────────────────────────────── */
function renderFilters(){
  var tset={};
  DATA.forEach(function(p){tset[p.tipo]=1});
  var anyT=Object.keys(activeTipos).length===0;
  var h='<button class="chip'+(anyT?' on':'')+'" onclick="toggleTipo(\'__all__\')">Todos</button>';
  Object.keys(tset).sort().forEach(function(t){
    h+='<button class="chip'+(activeTipos[t]?' on':'')+'" onclick="toggleTipo(\''+t+'\')">'+t+' &middot; '+(TIPOS[t]||t)+'</button>';
  });
  document.getElementById('tipo-filters').innerHTML=h;

  var ohtml='<button class="chip'+(activeOrigen===''?' on':'')+'" onclick="toggleOrigen(\'\')">Todos</button>';
  var oset={};
  DATA.forEach(function(p){oset[p.origen]=1});
  Object.keys(oset).sort().forEach(function(o){
    ohtml+='<button class="chip'+(activeOrigen===o?' on':'')+'" onclick="toggleOrigen(\''+o+'\')">'+(ORIGEN_LABEL[o]||o)+'</button>';
  });
  document.getElementById('origen-filters').innerHTML=ohtml;
}
function toggleTipo(t){
  if(t==='__all__'){activeTipos={}}else{if(activeTipos[t])delete activeTipos[t];else activeTipos[t]=1}
  applyAll();
}
function toggleOrigen(o){activeOrigen=activeOrigen===o?'':o;applyAll()}
function setBloque(val){
  activeBloque=val;
  var el=document.getElementById('bloque-select');
  if(el)el.className=val?'filter-select on':'filter-select';
  renderList();
}
function setProvincia(val){
  activeProvincia=val;
  var el=document.getElementById('provincia-select');
  if(el)el.className=val?'filter-select on':'filter-select';
  renderList();
}
function parseFecha(s){
  if(!s)return null;
  var p=s.split('/');
  if(p.length!==3)return null;
  return new Date(parseInt(p[2]),parseInt(p[1])-1,parseInt(p[0]));
}
function getFiltered(){
  var q=document.getElementById('search').value.toLowerCase().trim();
  var selCom1=document.getElementById('com-select-1').value;
  var selComAdic=document.getElementById('com-select-adic').value;
  var selAutor=document.getElementById('autor-select').value;
  var dDesde=document.getElementById('fecha-desde').value;
  var dHasta=document.getElementById('fecha-hasta').value;
  var fDesde=dDesde?new Date(dDesde):null;
  var fHasta=dHasta?new Date(dHasta+'T23:59:59'):null;

  return DATA.filter(function(p){
    if(activeAnio&&String(p.anio)!==activeAnio)return false;
    if(Object.keys(activeTipos).length&&!activeTipos[p.tipo])return false;
    if(activeBloque&&p.bloques.indexOf(activeBloque)<0)return false;
    if(activeOrigen&&p.origen!==activeOrigen)return false;
    if(activeProvincia&&(!p.provincias||p.provincias.indexOf(activeProvincia)<0))return false;
    if(selCom1&&p.comisiones[0]!==selCom1)return false;
    if(selComAdic&&p.comisiones.slice(1).indexOf(selComAdic)<0)return false;
    if(selAutor&&p.autores.indexOf(selAutor)<0)return false;
    if(fDesde||fHasta){
      var fp=parseFecha(p.fecha);
      if(fp){
        if(fDesde&&fp<fDesde)return false;
        if(fHasta&&fp>fHasta)return false;
      }
    }
    if(q){
      var hay=(p.extracto+' '+p.autores.join(' ')+' '+p.comisiones.join(' ')).toLowerCase();
      if(hay.indexOf(q)<0)return false;
    }
    return true;
  });
}
function buildCard(p){
  var fg=TIPO_FG[p.tipo]||'#888',bg=TIPO_BG[p.tipo]||'#eee';
  var autoresTxt=p.autores.slice(0,3).join(' · ')+(p.autores.length>3?' +'+(p.autores.length-3)+' más':'');
  var btags='',ctags='';
  p.bloques.forEach(function(b){
    var c=getBloqueColor(b);
    btags+='<span class="btag" style="background:'+c+'22;color:'+c+'">'+esc(b)+'</span>';
  });
  p.comisiones.forEach(function(c){ctags+='<span class="ctag">'+esc(c)+'</span>'});
  var expNro=p.origen+'-'+p.nro+'/'+String(p.anio).slice(-2);
  var linkBtn=p.url?'<a class="exp-link" href="'+escAttr(p.url)+'" target="_blank">Ver en Senado &#8599;</a>':'';
  return '<div class="card"><div class="card-exp"><div class="exp-id"><span class="exp-badge" style="background:'+bg+';color:'+fg+'">'+esc(p.tipo)+'</span><span class="exp-nro">'+esc(expNro)+'</span>'+(p.fecha?'<span class="exp-fecha">'+esc(p.fecha)+'</span>':'')+'</div>'+linkBtn+'</div><div class="card-body"><div class="extracto">'+esc(p.extracto)+'</div><div class="card-meta">'+(autoresTxt?'<div class="meta-row"><span class="meta-bold">'+esc(autoresTxt)+'</span></div>':'')+(btags?'<div class="meta-row">'+btags+'</div>':'')+(ctags?'<div class="meta-row">'+ctags+'</div>':'')+'</div></div></div>';
}
function renderList(){
  var filtered=getFiltered();
  var tot=filtered.length;
  document.getElementById('results-count').innerHTML=tot+' proyecto'+(tot!==1?'s':'')+' encontrado'+(tot!==1?'s':'');
  if(!filtered.length){
    document.getElementById('list').innerHTML='<div class="no-results">Sin resultados para este filtro.</div>';
    return;
  }
  var html='';
  filtered.forEach(function(p){html+=buildCard(p)});
  document.getElementById('list').innerHTML=html;
}

/* ── Exportar a Excel ──────────────────────────────────────────── */
function exportarExcel(){
  var filtered=getFiltered();
  if(!filtered.length){alert('No hay datos para exportar.');return}
  var headers=['Tipo','Nro','Origen','Fecha','Bloque','Autor','Coautor','Extracto','Giro 1','Giro 2','Giro 3'];
  var rows=[headers],urls=[];
  filtered.forEach(function(p){
    rows.push([
      p.tipo,p.nro+'/'+String(p.anio).slice(-2),p.origen,p.fecha,
      p.bloques.join('; '),p.autores.join('; '),(p.coautores||[]).join('; '),
      p.extracto,p.comisiones[0]||'',p.comisiones[1]||'',p.comisiones[2]||''
    ]);
    urls.push(p.url||'');
  });
  var wb=XLSX.utils.book_new();
  var ws=XLSX.utils.aoa_to_sheet(rows);
  for(var i=0;i<filtered.length;i++){
    if(urls[i]){
      var cellRef=XLSX.utils.encode_cell({r:i+1,c:1});
      if(ws[cellRef]){ws[cellRef].l={Target:urls[i]}}
    }
  }
  ws['!cols']=[{wch:6},{wch:10},{wch:8},{wch:12},{wch:28},{wch:35},{wch:35},{wch:60},{wch:30},{wch:30},{wch:30}];
  XLSX.utils.book_append_sheet(wb,ws,'Proyectos');
  XLSX.writeFile(wb,'proyectos_filtrados.xlsx');
}

/* ── Comisiones ────────────────────────────────────────────────── */
function normCom(s){return String(s||'').toUpperCase().trim()}
function nombreCom(s){return String(s||'').replace(/^De\s+/,'')}
function renderComisionesList(){
  var q=(document.getElementById('com-search').value||'').toLowerCase().trim();
  var lista=COMISIONES.filter(function(c){return !q||nombreCom(c.nombre).toLowerCase().indexOf(q)>=0});
  var el=document.getElementById('com-list');
  if(!lista.length){el.innerHTML='<div class="com-empty">Sin comisiones para este filtro.</div>';return}
  var html='';
  lista.forEach(function(c,i){
    var idx=COMISIONES.indexOf(c);
    html+='<div class="com-card" onclick="abrirComision('+idx+')">'
      +'<div class="com-card-nombre">'+esc(nombreCom(c.nombre))+'</div>'
      +'</div>';
  });
  el.innerHTML=html;
}
function abrirComision(idx){
  var c=COMISIONES[idx];
  if(!c)return;
  document.getElementById('com-detalle-nombre').textContent=nombreCom(c.nombre);
  document.getElementById('com-nivel1').classList.remove('active');
  document.getElementById('com-nivel2').classList.add('active');
  renderIntegrantes(c);
  renderProyectosComision(c);
  renderProximaReunion(c);
}
function volverComisiones(){
  document.getElementById('com-nivel2').classList.remove('active');
  document.getElementById('com-nivel1').classList.add('active');
}
function renderIntegrantes(c){
  var html='';
  c.integrantes.forEach(function(m){
    var col=getBloqueColor(m.bloque);
    html+='<div class="integrante-row">'
      +'<span class="integrante-nombre">'+esc(m.nombre)+'</span>'
      +'<span class="btag" style="background:'+col+'22;color:'+col+'">'+esc(m.bloque)+'</span>'
      +'<span class="rol-badge rol-'+m.rol+'">'+esc(m.rol)+'</span>'
      +'</div>';
  });
  document.getElementById('com-integrantes-list').innerHTML=html||'<div class="com-empty">Sin integrantes cargados.</div>';
}
function parseFechaDMY(fecha){
  var parts=(fecha||'').split('/');
  if(parts.length!==3)return null;
  return new Date(+parts[2],+parts[1]-1,+parts[0]);
}
function semaforoAntiguedad(fecha){
  var d=parseFechaDMY(fecha);
  if(!d)return'';
  var dias=Math.floor((Date.now()-d.getTime())/86400000);
  var cls=dias<30?'sem-verde':dias<=90?'sem-amarillo':'sem-rojo';
  return '<span class="semaforo '+cls+'" title="'+dias+' d&iacute;as desde el ingreso"></span>';
}
function renderProyectosComision(c){
  var nom=normCom(c.nombre);
  var lista=DATA.filter(function(p){
    var coms=p.comisiones||[];
    return coms.length&&normCom(coms[0])===nom;
  });
  lista.sort(function(a,b){
    var da=parseFechaDMY(a.fecha),db=parseFechaDMY(b.fecha);
    return (db?db.getTime():0)-(da?da.getTime():0);
  });
  var el=document.getElementById('com-proyectos-list');
  if(!lista.length){el.innerHTML='<div class="com-empty">No hay proyectos en tr&aacute;mite en esta comisi&oacute;n.</div>';return}
  var html='';
  lista.forEach(function(p){
    var fg=TIPO_FG[p.tipo]||'#888',bg=TIPO_BG[p.tipo]||'#eee';
    var expNro=p.origen+'-'+p.nro+'/'+String(p.anio).slice(-2);
    var linkBtn=p.url?'<a class="exp-link" href="'+escAttr(p.url)+'" target="_blank">Ver en Senado &#8599;</a>':'';
    var autorPrincipal=p.autores&&p.autores[0]?p.autores[0]:'';
    var bloquePrincipal=p.bloques&&p.bloques[0]?p.bloques[0]:'';
    var col=getBloqueColor(bloquePrincipal);
    html+='<div class="card"><div class="card-exp"><div class="exp-id">'+semaforoAntiguedad(p.fecha)
      +'<span class="exp-badge" style="background:'+bg+';color:'+fg+'">'+esc(p.tipo)+'</span>'
      +'<span class="exp-nro">'+esc(expNro)+'</span>'
      +(p.fecha?'<span class="exp-fecha">'+esc(p.fecha)+'</span>':'')
      +'</div>'+linkBtn+'</div><div class="card-body"><div class="extracto">'+esc(p.extracto)+'</div>'
      +'<div class="card-meta">'
      +(autorPrincipal?'<div class="meta-row"><span class="meta-bold">'+esc(autorPrincipal)+'</span></div>':'')
      +(bloquePrincipal?'<div class="meta-row"><span class="btag" style="background:'+col+'22;color:'+col+'">'+esc(bloquePrincipal)+'</span></div>':'')
      +'</div></div></div>';
  });
  el.innerHTML=html;
}
var COM_NOMBRE_CORTO={
  'De Economías Regionales, Economía Social, Micro, Pequeña y Mediana Empresa':'Ec. Regionales',
  'De Sistemas, Medios de Comunicación y Libertad de Expresión':'Sistemas y Medios',
  'De Coparticipación Federal de Impuestos':'Coparticipación',
  'De Infraestructura, Vivienda y Transporte':'Infraestructura',
  'De Asuntos Administrativos y Municipales':'Asuntos Adm.',
  'De Asuntos Constitucionales':'Constitucionales',
  'De Seguridad Interior y Narcotráfico':'Seg. Interior',
  'De Relaciones Exteriores y Culto':'RR.EE. y Culto',
  'De Población y Desarrollo Humano':'Pob. y Des. Humano',
  'De Trabajo y Previsión Social':'Trabajo',
  'De Minería, Energía y Combustibles':'Minería',
  'De Agricultura, Ganadería y Pesca':'Agricultura',
  'De Ambiente y Desarrollo Sustentable':'Ambiente',
  'De Economía Nacional e Inversión':'Ec. Nacional',
  'De Derechos y Garantías':'Der. y Garantías',
  'De Defensa Nacional':'Defensa',
  'De Educación y Cultura':'Educación',
  'De Industria y Comercio':'Industria',
  'De Legislación General':'Legislación',
  'De Ciencia y Tecnología':'Ciencia',
  'De Justicia y Asuntos Penales':'Justicia Penal'
};
function nombreComCorto(nombre){return COM_NOMBRE_CORTO[nombre]||nombreCom(nombre)}
function renderRepresentacion(){
  var totalSenadores=0;
  Object.keys(BLOQUE_TOTALES).forEach(function(b){totalSenadores+=BLOQUE_TOTALES[b]});
  var bloques=Object.keys(BLOQUE_TOTALES).sort(function(a,b){return BLOQUE_TOTALES[b]-BLOQUE_TOTALES[a]});

  var globalHtml='<div class="repr-titulo">Resumen global</div>'
    +'<p class="repr-hint">"Com. de 17" y "Com. de 19" son las bancas proporcionales seg&uacute;n el peso de cada bloque en la c&aacute;mara (senadores &divide; '+totalSenadores+' &times; cupo).</p>'
    +'<div class="repr-wrap"><table class="repr-table"><thead><tr>'
    +'<th>Bloque</th><th class="num">Senadores</th><th class="num">% c&aacute;mara</th>'
    +'<th class="num">Com. de 17</th><th class="num">Com. de 19</th>'
    +'</tr></thead><tbody>';
  bloques.forEach(function(b){
    var total=BLOQUE_TOTALES[b];
    var pct=(total/totalSenadores*100).toFixed(2);
    var exp17=(total/totalSenadores*17).toFixed(2);
    var exp19=(total/totalSenadores*19).toFixed(2);
    var col=getBloqueColor(b);
    globalHtml+='<tr><td><div class="repr-bloque-cell"><span class="repr-dot" style="background:'+col+'"></span>'+esc(b)+'</div></td>'
      +'<td class="num">'+total+'</td><td class="num">'+pct+'%</td>'
      +'<td class="num">'+exp17+'</td><td class="num">'+exp19+'</td></tr>';
  });
  globalHtml+='</tbody></table></div>';
  document.getElementById('repr-global').innerHTML=globalHtml;

  var crossHtml='<div class="repr-titulo">Integrantes por bloque y comisi&oacute;n</div>'
    +'<p class="repr-hint">Desplaz&aacute; horizontalmente para ver todas las comisiones.</p>'
    +'<div class="repr-wrap"><table class="cross-table"><thead><tr><th class="blq-col">Bloque</th>';
  COMISIONES.forEach(function(c){crossHtml+='<th class="com-col"><span>'+esc(nombreComCorto(c.nombre))+'</span></th>'});
  crossHtml+='</tr></thead><tbody>';
  bloques.forEach(function(b){
    crossHtml+='<tr><td class="blq-name">'+esc(b)+'</td>';
    COMISIONES.forEach(function(c){
      var n=c.integrantes.filter(function(m){return m.bloque===b}).length;
      crossHtml+='<td class="val" style="color:'+(n>0?'#4A4A4A':'#cfd8e3')+';font-weight:'+(n>0?'600':'400')+'">'+(n>0?n:'&mdash;')+'</td>';
    });
    crossHtml+='</tr>';
  });
  crossHtml+='</tbody></table></div>';
  document.getElementById('repr-cross').innerHTML=crossHtml;
}
function renderProximaReunion(c){
  var el=document.getElementById('com-proxima-reunion');
  var r=c.proximaReunion;
  if(!r){el.innerHTML='';return}
  el.innerHTML='<div class="com-proximareunion">'
    +'<span>&#128197; <strong>Pr&oacute;xima reuni&oacute;n:</strong> '+esc(r.fecha)+' &middot; '+esc(r.hora)+' hs</span>'
    +'<span>&#128205; '+esc(r.salon)+'</span>'
    +'<span>&#128196; '+r.nExpedientes+' expediente'+(r.nExpedientes!==1?'s':'')+' en el temario</span>'
    +'</div>';
}
"""

# ── Plantilla HTML ─────────────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sistema Legislativo &mdash; HSN</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.sheetjs.com/xlsx-0.20.3/package/dist/xlsx.full.min.js"></script>
<style>{css}</style>
</head>
<body>

<div class="topbar">
  <div class="header">
    <div class="header-row">
      <span class="header-inst">Senado de la Naci&oacute;n Argentina</span>
      <span class="header-dep">Prosecretar&iacute;a Parlamentaria</span>
    </div>
    <div class="header-title">Sistema Legislativo</div>
    <div class="header-sub">&Uacute;ltima actualizaci&oacute;n: {fecha}</div>
  </div>
  <div class="main-nav">
    <button class="mtab-btn active" data-main="proyectos" onclick="switchMain('proyectos')">Proyectos</button>
    <button class="mtab-btn" data-main="comisiones" onclick="switchMain('comisiones')">Comisiones</button>
    <button class="mtab-btn" data-main="agenda" onclick="switchMain('agenda')">Agenda</button>
    <button class="mtab-btn" data-main="ayuda" onclick="switchMain('ayuda')">Ayuda Memoria</button>
  </div>
</div>

<!-- ====================== MAIN: PROYECTOS ====================== -->
<div id="main-proyectos" class="mtab-content active">
  <div class="sub-nav">
    <button class="sub-btn active" data-sub="buscador" onclick="switchSub('buscador')">Buscador</button>
    <button class="sub-btn" data-sub="tabla" onclick="switchSub('tabla')">Tabla din&aacute;mica</button>
    <button class="sub-btn" data-sub="dashboard" onclick="switchSub('dashboard')">Dashboard</button>
  </div>

  <!-- SUB: DASHBOARD (análisis político, 5 visualizaciones SVG) -->
  <div id="sub-dashboard" class="sub-content">
    <div class="section-block">
      <div class="section-header">
        <h2>Dashboard de an&aacute;lisis</h2>
        <span class="section-hint">Proyectos ingresados &middot; an&aacute;lisis pol&iacute;tico</span>
      </div>
      <div class="section-body">
        <div class="dash-toolbar">
          <span class="dash-anio-label">A&ntilde;o</span>
          <button class="chip on" id="dash-anio-2026" onclick="setDashAnio('2026')">2026</button>
          <button class="chip" id="dash-anio-2025" onclick="setDashAnio('2025')">2025</button>
          <span class="dash-cross" id="dash-cross" onclick="clearCross()" title="Quitar filtro"></span>
          <span class="dash-total" id="dash-total"></span>
        </div>
        <div class="dash-grid">
          <div class="viz-card">
            <div class="viz-head">
              <span class="viz-title">Evoluci&oacute;n temporal</span>
              <div class="viz-toggle">
                <button id="evo-tipo" class="on" onclick="setEvoMode('tipo')">Por tipo</button>
                <button id="evo-bloque" onclick="setEvoMode('bloque')">Por bloque</button>
              </div>
            </div>
            <div id="viz-evolucion"></div>
            <div class="viz-legend" id="evo-legend"></div>
          </div>
          <div class="viz-card">
            <div class="viz-head"><span class="viz-title">Distribuci&oacute;n por tipo</span></div>
            <div id="viz-donut"></div>
          </div>
          <div class="viz-card span2">
            <div class="viz-head"><span class="viz-title">Bloques pol&iacute;ticos (Senado) &middot; composici&oacute;n por tipo</span></div>
            <div id="viz-treemap"></div>
            <div class="viz-legend" id="treemap-legend"></div>
          </div>
          <div class="viz-card">
            <div class="viz-head"><span class="viz-title">Tipo por bloque</span></div>
            <div id="viz-stacked"></div>
            <div class="viz-legend" id="stacked-legend"></div>
          </div>
          <div class="viz-card">
            <div class="viz-head"><span class="viz-title">Top 10 comisiones &middot; tendencia 8 semanas</span></div>
            <div id="viz-topcoms"></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- SUB: TABLA DINÁMICA (pivot) -->
  <div id="sub-tabla" class="sub-content">
    <div class="section-block">
      <div class="section-header">
        <h2>Tabla din&aacute;mica</h2>
        <span class="section-hint">Toc&aacute; una celda para ver esos expedientes en el Buscador</span>
      </div>
      <div class="section-body">
        <div class="pivot-config">
          <div class="pivot-axes">
            <div class="pivot-field">
              <span class="filter-label">Filas</span>
              <div class="select-wrapper">
                <select class="filter-select" id="pv-row" onchange="setPivot()"></select>
                <span class="select-arrow">&#9660;</span>
              </div>
            </div>
            <div class="pivot-field">
              <span class="filter-label">Columnas</span>
              <div class="select-wrapper">
                <select class="filter-select" id="pv-col" onchange="setPivot()"></select>
                <span class="select-arrow">&#9660;</span>
              </div>
            </div>
            <div class="pivot-field">
              <span class="filter-label">Valores</span>
              <div class="select-wrapper">
                <select class="filter-select" id="pv-disp" onchange="setPivot()">
                  <option value="abs">Conteo de proyectos</option>
                  <option value="ptotal">% del total general</option>
                  <option value="prow">% de la fila</option>
                  <option value="pcol">% de la columna</option>
                </select>
                <span class="select-arrow">&#9660;</span>
              </div>
            </div>
          </div>
          <div class="pivot-filters">
            <span class="filter-label">Filtros</span>
            <div class="select-wrapper">
              <select class="filter-select" id="pv-f-anio" onchange="setAnioShared(this.value)"><option value="">Todos los a&ntilde;os</option></select>
              <span class="select-arrow">&#9660;</span>
            </div>
            <div class="select-wrapper">
              <select class="filter-select" id="pv-f-tipo" onchange="setTipoShared(this.value)"><option value="">Todos los tipos</option></select>
              <span class="select-arrow">&#9660;</span>
            </div>
            <div class="select-wrapper">
              <select class="filter-select" id="pv-f-origen" onchange="setOrigenShared(this.value)"><option value="">Todos los or&iacute;genes</option></select>
              <span class="select-arrow">&#9660;</span>
            </div>
            <button class="pivot-clear" onclick="clearSharedFilters()">Limpiar filtros &#x2715;</button>
          </div>
        </div>
        <div class="pivot-meta" id="pivot-meta"></div>
        <div class="pivot-scroll"><div id="pivot-body"></div></div>
      </div>
    </div>
  </div><!-- /sub-tabla -->

  <!-- SUB: BUSCADOR de expedientes -->
  <div id="sub-buscador" class="sub-content active">
    <div class="detalle-layout">
      <div class="filters-panel">
        <div class="section-header">
          <h2>B&uacute;squeda y filtros</h2>
        </div>
        <div class="filters-body">
          <div class="filter-label" style="margin-top:0">A&ntilde;o</div>
          <div class="filter-row" style="margin-bottom:10px">
            <button class="chip on" id="anio-det-all" onclick="setAnioShared('')">Todos</button>
            <button class="chip" id="anio-det-2025" onclick="setAnioShared('2025')">2025</button>
            <button class="chip" id="anio-det-2026" onclick="setAnioShared('2026')">2026</button>
          </div>

          <input class="search-box" type="text" id="search" placeholder="Buscar por extracto, autor o comisi&oacute;n&hellip;" oninput="renderList()">

          <div class="filter-label">Tipo</div>
          <div class="filter-row" id="tipo-filters"></div>

          <div class="filter-label">Bloque</div>
          <div class="select-wrapper">
            <select class="filter-select" id="bloque-select" onchange="setBloque(this.value)">
              <option value="">Todos los bloques</option>
            </select>
            <span class="select-arrow">&#9660;</span>
          </div>

          <div class="filter-label">Provincia</div>
          <div class="select-wrapper">
            <select class="filter-select" id="provincia-select" onchange="setProvincia(this.value)">
              <option value="">Todas las provincias</option>
            </select>
            <span class="select-arrow">&#9660;</span>
          </div>

          <div class="filter-label">Origen</div>
          <div class="filter-row" id="origen-filters"></div>

          <div class="filter-label">Rango de fechas</div>
          <div class="date-range">
            <input type="date" class="date-input" id="fecha-desde" onchange="renderList()">
            <span class="date-sep">hasta</span>
            <input type="date" class="date-input" id="fecha-hasta" onchange="renderList()">
          </div>

          <div class="filter-label">Comisi&oacute;n (1er giro)</div>
          <div class="select-wrapper">
            <select class="filter-select" id="com-select-1" onchange="renderList()">
              <option value="">Todas las comisiones</option>
            </select>
            <span class="select-arrow">&#9660;</span>
          </div>

          <div class="filter-label">Comisi&oacute;n (giros adicionales)</div>
          <div class="select-wrapper">
            <select class="filter-select" id="com-select-adic" onchange="renderList()">
              <option value="">Todos los giros adicionales</option>
            </select>
            <span class="select-arrow">&#9660;</span>
          </div>

          <div class="filter-label">Autor</div>
          <div class="select-wrapper">
            <select class="filter-select" id="autor-select" onchange="renderList()">
              <option value="">Todos los autores</option>
            </select>
            <span class="select-arrow">&#9660;</span>
          </div>
        </div>
      </div>

      <div class="results-panel">
        <div class="results-header">
          <span class="results-count" id="results-count"></span>
          <button class="btn-export" onclick="exportarExcel()">&#128196; Exportar Excel</button>
        </div>
        <div id="list"></div>
      </div>
    </div>
  </div><!-- /sub-buscador -->
</div><!-- /main-proyectos -->

<!-- ====================== MAIN: COMISIONES ====================== -->
<div id="main-comisiones" class="mtab-content">

  <!-- NIVEL 1: lista de comisiones -->
  <div id="com-nivel1" class="com-nivel active">
    <div class="section-block">
      <div class="section-header">
        <h2>Comisiones permanentes</h2>
        <span class="section-hint">Senado de la Naci&oacute;n</span>
      </div>
      <div class="section-body">
        <input class="search-box" type="text" id="com-search" placeholder="Buscar comisi&oacute;n&hellip;" oninput="renderComisionesList()" style="max-width:360px">
        <div id="com-list" class="com-grid"></div>
      </div>
    </div>

    <div class="section-block">
      <div class="section-header">
        <h2>Representaci&oacute;n por bloques</h2>
        <span class="section-hint">Composici&oacute;n del Senado y de cada comisi&oacute;n</span>
      </div>
      <div class="section-body">
        <div id="repr-global"></div>
        <div id="repr-cross"></div>
      </div>
    </div>
  </div>

  <!-- NIVEL 2: detalle de comisión -->
  <div id="com-nivel2" class="com-nivel">
    <div class="section-block">
      <div class="section-header">
        <h2 id="com-detalle-nombre">&nbsp;</h2>
        <button class="btn-volver" onclick="volverComisiones()">&larr; Volver</button>
      </div>
      <div class="section-body">
        <div class="com-detalle-layout">
          <div class="com-panel com-panel-integrantes">
            <div class="com-panel-title">Integrantes</div>
            <div id="com-integrantes-list"></div>
          </div>
          <div class="com-panel com-panel-proyectos">
            <div class="com-panel-title">Proyectos en tr&aacute;mite</div>
            <div id="com-proyectos-list"></div>
          </div>
        </div>
        <div id="com-proxima-reunion"></div>
      </div>
    </div>
  </div>

</div>

<!-- ====================== MAIN: AGENDA ====================== -->
<div id="main-agenda" class="mtab-content">
  <div class="placeholder">
    <div class="placeholder-icon">&#128197;</div>
    <h3>Agenda</h3>
    <p>Secci&oacute;n en construcci&oacute;n &mdash; pr&oacute;ximamente en Fase 2.</p>
  </div>
</div>

<!-- ====================== MAIN: AYUDA MEMORIA ====================== -->
<div id="main-ayuda" class="mtab-content">
  <div class="placeholder">
    <div class="placeholder-icon">&#128221;</div>
    <h3>Ayuda Memoria</h3>
    <p>Secci&oacute;n en construcci&oacute;n &mdash; pr&oacute;ximamente en Fase 2.</p>
  </div>
</div>

<div id="dash-tooltip" class="dash-tooltip"></div>

<div class="footer">Prosecretar&iacute;a Parlamentaria &middot; Senado de la Naci&oacute;n Argentina<br>Datos al {fecha}</div>

<script>
var DATA = {datos};
var COMISIONES = {comisiones};
var BLOQUE_TOTALES = {bloque_totales};
{js}
init();
</script>
</body>
</html>"""


# Autoridades por comisión (pres/vice/secr) — fuente: repo comisiones-senado
# (no viene en el scraper de comisiones.json; roles no listados = Vocal).
AUTORIDADES = {
    'De Acuerdos': {'pres': 'PAGOTTO, Juan Carlos', 'vice': 'ABAD, Maximiliano', 'secr': 'GOERLING LARA, Enrique Martín'},
    'De Agricultura, Ganadería y Pesca': {'pres': 'BENEGAS LYNCH, Joaquín Alberto', 'vice': 'KRONEBERGER, Daniel Ricardo', 'secr': ''},
    'De Ambiente y Desarrollo Sustentable': {'pres': 'TERENZI, Edith Elizabeth', 'vice': '', 'secr': ''},
    'De Asuntos Administrativos y Municipales': {'pres': 'KRONEBERGER, Daniel Ricardo', 'vice': 'MARKS, Ana Inés', 'secr': ''},
    'De Asuntos Constitucionales': {'pres': 'COTO, Agustín Pedro', 'vice': 'LÓPEZ, María Florencia', 'secr': ''},
    'De Ciencia y Tecnología': {'pres': 'DE PEDRO, Eduardo Enrique', 'vice': 'ALMEIDA, Romina María', 'secr': ''},
    'De Coparticipación Federal de Impuestos': {'pres': 'VISCHI, Eduardo Alejandro', 'vice': 'ROYÓN, Flavia Gabriela', 'secr': ''},
    'De Defensa Nacional': {'pres': 'JUEZ, Luis Alfredo', 'vice': 'LINARES, Carlos Alberto', 'secr': ''},
    'De Deporte': {'pres': 'FERNÁNDEZ SAGASTI, Anabel', 'vice': 'ABAD, Maximiliano', 'secr': 'ABDALA, Bartolomé Esteban'},
    'De Derechos y Garantías': {'pres': 'BENSUSÁN, Daniel Pablo', 'vice': '', 'secr': 'CERVI, Mario Pablo'},
    'De Economía Nacional e Inversión': {'pres': 'GOERLING LARA, Enrique Martín', 'vice': '', 'secr': 'CORROZA, Julieta'},
    'De Economías Regionales, Economía Social, Micro, Pequeña y Mediana Empresa': {'pres': 'CAPITANICH, Jorge Milton', 'vice': '', 'secr': ''},
    'De Educación y Cultura': {'pres': 'ROJAS DECUT, Sonia Elizabeth', 'vice': 'VALENZUELA, Mercedes Gabriela', 'secr': ''},
    'De Industria y Comercio': {'pres': 'LEWANDOWSKI, Marcelo Néstor', 'vice': 'GADANO, Natalia Elena', 'secr': ''},
    'De Infraestructura, Vivienda y Transporte': {'pres': 'ÁVILA, Beatriz Luisa', 'vice': 'FULLONE, Enzo Paolo', 'secr': 'LEWANDOWSKI, Marcelo Néstor'},
    'De Justicia y Asuntos Penales': {'pres': 'GUZMÁN CORAITA, Gonzalo', 'vice': '', 'secr': ''},
    'De Legislación General': {'pres': 'MÁRQUEZ, Nadia Judith', 'vice': 'BENSUSÁN, Daniel Pablo', 'secr': ''},
    'De Minería, Energía y Combustibles': {'pres': 'FAMA, Flavio Sergio', 'vice': '', 'secr': ''},
    'De Población y Desarrollo Humano': {'pres': 'KIRCHNER, Alicia Margarita Antonia', 'vice': 'GODOY, Juan Cruz', 'secr': ''},
    'De Presupuesto y Hacienda': {'pres': 'MONTEVERDE, Agustín Aníbal', 'vice': '', 'secr': 'SCHNEIDER, Silvana Lorena'},
    'De Relaciones Exteriores y Culto': {'pres': 'PAOLTRONI, Francisco Manuel', 'vice': '', 'secr': ''},
    'De Salud': {'pres': 'ARRASCAETA, Ivanna Marcela', 'vice': 'ARCE, Carlos Omar', 'secr': ''},
    'De Seguridad Interior y Narcotráfico': {'pres': 'LOSADA, Carolina', 'vice': '', 'secr': ''},
    'De Sistemas, Medios de Comunicación y Libertad de Expresión': {'pres': 'MOISÉS, María Carolina', 'vice': '', 'secr': ''},
    'De Trabajo y Previsión Social': {'pres': 'ALVAREZ RIVERO, Carmen', 'vice': '', 'secr': ''},
    'De Turismo': {'pres': 'JURI, Mariana', 'vice': '', 'secr': ''},
}


def _cargar(nombre, default):
    path = os.path.join(DATA_DIR, nombre)
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except Exception:
            return default
    return default


def _norm_com(s):
    """Normaliza nombre de comisión: mayúsculas, sin tildes, sin prefijo 'DE '."""
    if not s:
        return ""
    s = unicodedata.normalize("NFD", s.upper().strip())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"^DE\s+", "", s)
    s = re.sub(r"[^A-Z0-9, ]", "", s)
    return s


def _rol_de(nombre_com, nombre_miembro):
    aut = AUTORIDADES.get(nombre_com, {})
    if aut.get("pres") == nombre_miembro:
        return "Presidente"
    if aut.get("vice") == nombre_miembro:
        return "Vicepresidente"
    if aut.get("secr") == nombre_miembro:
        return "Secretario"
    return "Vocal"


def _parse_fecha_agenda(fecha_dd_mm, boletin_numero):
    """'17/06' + boletín '64/26' -> datetime(2026,6,17). Sin año -> None."""
    try:
        dia, mes = fecha_dd_mm.split("/")
        anio_suffix = (boletin_numero or "").split("/")[-1]
        anio = 2000 + int(anio_suffix)
        return datetime(anio, int(mes), int(dia))
    except Exception:
        return None


def construir_bloque_totales():
    """Cantidad de senadores vigentes por bloque, según data/senadores.json."""
    senadores = _cargar("senadores.json", {})
    totales = {}
    for datos in senadores.values():
        if not datos.get("vigente"):
            continue
        bloque = datos.get("bloque", "")
        totales[bloque] = totales.get(bloque, 0) + 1
    return totales


def construir_comisiones(proyectos):
    comisiones = _cargar("comisiones.json", [])
    agenda = _cargar("agenda.json", {})
    reuniones = agenda.get("reuniones", [])

    # Conteo de proyectos en trámite por comisión (comisiones[0], normalizado)
    conteo_proyectos = {}
    for p in proyectos:
        coms = p.get("comisiones") or []
        if coms and coms[0]:
            key = _norm_com(coms[0])
            conteo_proyectos[key] = conteo_proyectos.get(key, 0) + 1

    # Próxima reunión futura por comisión (matching por prefijo normalizado,
    # porque agenda.json trae nombres truncados/mayúsculas del boletín)
    ahora = datetime.now()
    proxima = {}
    for r in reuniones:
        fecha_dt = _parse_fecha_agenda(r.get("fecha", ""), r.get("boletin_numero", ""))
        if not fecha_dt or fecha_dt <= ahora:
            continue
        for c_nombre in r.get("comisiones") or []:
            n_ag = _norm_com(c_nombre)
            if not n_ag:
                continue
            for com in comisiones:
                n_com = _norm_com(com["nombre"])
                if n_com.startswith(n_ag) or n_ag.startswith(n_com):
                    prev = proxima.get(com["nombre"])
                    if not prev or fecha_dt < prev["_dt"]:
                        proxima[com["nombre"]] = {
                            "_dt": fecha_dt,
                            "fecha": r.get("fecha", ""),
                            "hora": r.get("hora", ""),
                            "salon": r.get("salon_completo") or r.get("salon", ""),
                            "nExpedientes": len(r.get("temario") or []),
                        }
                    break

    resultado = []
    for com in comisiones:
        nombre = com["nombre"]
        integrantes = [
            {
                "nombre": m["nombre"],
                "bloque": m.get("bloque", ""),
                "rol": _rol_de(nombre, m["nombre"]),
            }
            for m in com.get("miembros", [])
        ]
        # Presidente/Vice/Secretario primero, luego Vocales
        orden_rol = {"Presidente": 0, "Vicepresidente": 1, "Secretario": 2, "Vocal": 3}
        integrantes.sort(key=lambda x: orden_rol.get(x["rol"], 9))

        pr = proxima.get(nombre)
        resultado.append({
            "nombre": nombre,
            "cupo": com.get("cupo", 0),
            "integrantes": integrantes,
            "nProyectos": conteo_proyectos.get(_norm_com(nombre), 0),
            "proximaReunion": {
                "fecha": pr["fecha"], "hora": pr["hora"],
                "salon": pr["salon"], "nExpedientes": pr["nExpedientes"],
            } if pr else None,
        })
    return resultado


def parse_fecha_sort(fecha_str):
    """Convierte 'DD/MM/AAAA' a 'AAAAMMDD' para orden cronológico."""
    if not fecha_str:
        return "00000000"
    parts = fecha_str.split("/")
    if len(parts) == 3:
        return f"{parts[2]}{parts[1].zfill(2)}{parts[0].zfill(2)}"
    return "00000000"


def main():
    proyectos = _cargar("proyectos.json", [])
    # Orden: fecha ↓, luego año y número (más nuevo a más viejo)
    proyectos = sorted(
        proyectos,
        key=lambda x: (parse_fecha_sort(x.get("fecha", "")), x.get("anio", 0), x.get("nro", 0)),
        reverse=True,
    )

    total = len(proyectos)
    tipos_count = {}
    for p in proyectos:
        tipos_count[p.get("tipo", "")] = tipos_count.get(p.get("tipo", ""), 0) + 1

    datos_js = json.dumps(proyectos, ensure_ascii=False)
    comisiones_js = json.dumps(construir_comisiones(proyectos), ensure_ascii=False)
    bloque_totales_js = json.dumps(construir_bloque_totales(), ensure_ascii=False)
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    html = HTML_TEMPLATE.format(
        css=CSS,
        js=JS,
        datos=datos_js,
        comisiones=comisiones_js,
        bloque_totales=bloque_totales_js,
        fecha=fecha,
        total=total,
        pl=tipos_count.get("PL", 0),
        pd=tipos_count.get("PD", 0),
        otros=total - tipos_count.get("PL", 0) - tipos_count.get("PD", 0),
    )

    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(html)

    mb = len(html.encode("utf-8")) / (1024 * 1024)
    print(f"index.html generado: {len(html):,} bytes ({mb:.2f} MB)")
    print(f"  -> {total} proyectos | {tipos_count.get('PL', 0)} PL | "
          f"{tipos_count.get('PD', 0)} PD | otros {total - tipos_count.get('PL', 0) - tipos_count.get('PD', 0)}")
    if mb > 15:
        print(f"  ADVERTENCIA: el HTML supera 15 MB ({mb:.2f} MB) -- considerar paginacion.")


if __name__ == "__main__":
    main()
