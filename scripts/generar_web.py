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

/* ── Dashboard ────────────────────────────────────────────────────────── */
.dash-stats-row{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px}
.dash-panels-row{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
@media(max-width:900px){
  .dash-stats-row{grid-template-columns:repeat(2,1fr)}
  .dash-panels-row{grid-template-columns:1fr}
}
.stat-card{background:#F5F7FA;border-radius:8px;padding:14px 12px;border-left:4px solid #1B5EA2}
.stat-num{font-size:28px;font-weight:700;color:#1B5EA2;line-height:1}
.stat-label{font-size:11px;color:#4A4A4A;margin-top:3px}
.dash-subtitle{font-size:11px;font-weight:600;color:#2E75B6;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;padding-bottom:4px;border-bottom:1px solid #D6E4F0}
.tipo-bar-row{display:flex;align-items:center;gap:8px;margin-bottom:7px;cursor:pointer;padding:3px 6px;border-radius:6px;transition:background .12s}
.tipo-bar-row:hover{background:#F0F4FA}
.tipo-bar-row.on{background:#D6E4F0}
.tipo-pill{font-size:11px;font-weight:700;border-radius:4px;padding:3px 8px;min-width:36px;text-align:center;flex-shrink:0}
.tipo-nombre{font-size:12px;color:#4A4A4A;flex:1}
.bar-track{flex:2;height:7px;background:#D6E4F0;border-radius:4px;overflow:hidden}
.bar-fill{height:100%;border-radius:4px;transition:width .3s}
.tipo-count{font-size:12px;font-weight:700;min-width:28px;text-align:right}
.bloque-row{display:flex;align-items:center;gap:8px;margin-bottom:6px;cursor:pointer;padding:3px 6px;border-radius:6px;transition:background .12s}
.bloque-row:hover,.com-row:hover{background:#F0F4FA}
.bloque-row.on,.com-row.on{background:#D6E4F0}
.bloque-name{font-size:11px;color:#4A4A4A;flex:1;line-height:1.3}
.bloque-bar-track{flex:2;height:6px;background:#D6E4F0;border-radius:3px;overflow:hidden}
.bloque-bar-fill{height:100%;border-radius:3px;transition:width .3s}
.bloque-count{font-size:11px;font-weight:700;color:#2E75B6;min-width:24px;text-align:right}
.com-row{display:flex;align-items:center;gap:8px;margin-bottom:6px;cursor:pointer;padding:3px 6px;border-radius:6px;transition:background .12s}
.com-name{font-size:11px;color:#4A4A4A;flex:1;line-height:1.3}
.com-bar-track{flex:2;height:6px;background:#D6E4F0;border-radius:3px;overflow:hidden}
.com-bar-fill{height:100%;background:#2E75B6;border-radius:3px;transition:width .3s}
.com-count{font-size:11px;font-weight:700;color:#2E75B6;min-width:24px;text-align:right}
.dash-context{font-size:11px;color:#2E75B6;background:#EAF0FA;border-radius:6px;padding:6px 10px;margin-bottom:10px;display:none}
.dash-context.visible{display:block}

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

/* ── Vista unificada Expedientes: panel de análisis colapsable ─────────── */
.analisis-toggle-btn{background:rgba(255,255,255,0.18);border:none;color:#fff;font-family:inherit;font-size:11px;font-weight:600;cursor:pointer;padding:5px 12px;border-radius:6px;transition:background .15s}
.analisis-toggle-btn:hover{background:rgba(255,255,255,0.32)}
#buscador-block{scroll-margin-top:112px}

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
var dashFiltroTipo='',dashFiltroBloque='',dashFiltroCom='',dashActiveAnio='',dashSancionado=false;
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
  if(id==='expedientes')renderPivot();
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
  renderDash(DATA);
  syncFilterUI();
  renderList();
  renderPivot();
}
function fillSelect(id,values){
  var sel=document.getElementById(id);
  values.forEach(function(v){
    var o=document.createElement('option');o.value=v;o.textContent=v;sel.appendChild(o);
  });
}
function getBloqueColor(b){return BC[ALL_BLOQUES.indexOf(b)%BC.length]}

/* ── Dashboard ─────────────────────────────────────────────────── */
function getDashFiltered(){
  return DATA.filter(function(p){
    if(dashActiveAnio&&String(p.anio)!==dashActiveAnio)return false;
    if(dashSancionado&&!p.sancionado)return false;
    if(dashFiltroTipo&&p.tipo!==dashFiltroTipo)return false;
    if(dashFiltroBloque&&p.bloques.indexOf(dashFiltroBloque)<0)return false;
    if(dashFiltroCom&&(p.comisiones[0]||'')!==dashFiltroCom)return false;
    return true;
  });
}
function calcStats(data){
  var t={},b={},c={};
  data.forEach(function(p){
    t[p.tipo]=(t[p.tipo]||0)+1;
    p.bloques.forEach(function(x){b[x]=(b[x]||0)+1});
    if(p.comisiones[0])c[p.comisiones[0]]=(c[p.comisiones[0]]||0)+1;
  });
  return{tipos:t,bloques:b,coms:c};
}
function renderDash(data){
  var s=calcStats(data),total=data.length;
  document.getElementById('stat-total').innerHTML=total;
  document.getElementById('stat-pl').innerHTML=s.tipos['PL']||0;
  document.getElementById('stat-pd').innerHTML=s.tipos['PD']||0;
  document.getElementById('stat-otros').innerHTML=total-(s.tipos['PL']||0)-(s.tipos['PD']||0);

  var partes=[];
  if(dashFiltroTipo)partes.push('Tipo: '+(TIPOS[dashFiltroTipo]||dashFiltroTipo));
  if(dashFiltroBloque)partes.push('Bloque: '+dashFiltroBloque);
  if(dashFiltroCom)partes.push('Comisión: '+dashFiltroCom);
  var ctx=document.getElementById('dash-context');
  if(partes.length){
    ctx.innerHTML='Filtrando: <strong>'+partes.map(esc).join(' &middot; ')+'</strong> &nbsp;<button onclick="clearDash()" style="background:none;border:none;color:#1B5EA2;cursor:pointer;font-size:11px;font-weight:700;padding:0 4px">Limpiar filtro &#x2715;</button>';
    ctx.className='dash-context visible';
  }else{ctx.className='dash-context'}

  var tipoOrder=['PL','PD','PC','PR','CA','AC','CV'],maxT=0;
  tipoOrder.forEach(function(t){if((s.tipos[t]||0)>maxT)maxT=s.tipos[t]||0});
  var tb='';
  tipoOrder.forEach(function(t){
    if(!DATA.some(function(p){return p.tipo===t}))return;
    var n=s.tipos[t]||0,pct=maxT?Math.round(n/maxT*100):0;
    var fg=TIPO_FG[t]||'#888',bg=TIPO_BG[t]||'#eee';
    var on=dashFiltroTipo===t?' on':'';
    tb+='<div class="tipo-bar-row'+on+'" onclick="clickDashTipo(\''+t+'\')"><span class="tipo-pill" style="background:'+bg+';color:'+fg+'">'+t+'</span><span class="tipo-nombre">'+(TIPOS[t]||t)+'</span><div class="bar-track"><div class="bar-fill" style="width:'+pct+'%;background:'+fg+'"></div></div><span class="tipo-count" style="color:'+fg+'">'+n+'</span></div>';
  });
  document.getElementById('tipo-bars').innerHTML=tb;

  var blist=Object.keys(s.bloques).sort(function(a,b){return s.bloques[b]-s.bloques[a]});
  var maxB=blist.length?s.bloques[blist[0]]:1;
  var bb='';
  blist.forEach(function(b){
    var n=s.bloques[b],pct=Math.round(n/maxB*100),color=getBloqueColor(b);
    var safe=b.replace(/\\/g,'\\\\').replace(/'/g,"\\'");
    var on=dashFiltroBloque===b?' on':'';
    bb+='<div class="bloque-row'+on+'" onclick="clickDashBloque(\''+safe+'\')"><span class="bloque-name">'+esc(b)+'</span><div class="bloque-bar-track"><div class="bloque-bar-fill" style="width:'+pct+'%;background:'+color+'"></div></div><span class="bloque-count">'+n+'</span></div>';
  });
  document.getElementById('bloque-bars').innerHTML=bb||'<div style="font-size:11px;color:#aaa">Sin datos.</div>';

  var clist=Object.keys(s.coms).sort(function(a,b){return s.coms[b]-s.coms[a]}).slice(0,10);
  var maxC=clist.length?s.coms[clist[0]]:1;
  var cb='';
  clist.forEach(function(c){
    var n=s.coms[c],pct=Math.round(n/maxC*100);
    var safe=c.replace(/\\/g,'\\\\').replace(/'/g,"\\'");
    var on=dashFiltroCom===c?' on':'';
    cb+='<div class="com-row'+on+'" onclick="clickDashCom(\''+safe+'\')"><span class="com-name">'+esc(c)+'</span><div class="com-bar-track"><div class="com-bar-fill" style="width:'+pct+'%"></div></div><span class="com-count">'+n+'</span></div>';
  });
  document.getElementById('com-bars').innerHTML=cb||'<div style="font-size:11px;color:#aaa">Sin datos.</div>';
}
function clickDashTipo(t){dashFiltroTipo=dashFiltroTipo===t?'':t;renderDash(getDashFiltered())}
function clickDashBloque(b){dashFiltroBloque=dashFiltroBloque===b?'':b;renderDash(getDashFiltered())}
function clickDashCom(c){dashFiltroCom=dashFiltroCom===c?'':c;renderDash(getDashFiltered())}
function setDashAnio(anio){
  dashActiveAnio=anio;
  ['all','2025','2026'].forEach(function(a){
    var el=document.getElementById('dash-anio-'+a);
    if(el)el.className='chip'+(anio===(a==='all'?'':a)?' on':'');
  });
  renderDash(getDashFiltered());
}
function toggleDashSanc(){
  dashSancionado=!dashSancionado;
  document.getElementById('dash-sanc').className='chip'+(dashSancionado?' on':'');
  renderDash(getDashFiltered());
}
function clearDash(){dashFiltroTipo='';dashFiltroBloque='';dashFiltroCom='';renderDash(getDashFiltered())}

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
   los del buscador, mapea fila+columna de la celda y baja hasta el buscador */
function drillPivot(ri,ci){
  resetBuscadorOnly();
  applyDimToFilter(pvRow,PV_ROWKEYS[ri]);
  if(pvCol!=='none')applyDimToFilter(pvCol,PV_COLKEYS[ci]);
  applyAll();
  var b=document.getElementById('buscador-block');
  if(b)b.scrollIntoView({behavior:'smooth',block:'start'});
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
function toggleAnalisis(){
  var b=document.getElementById('analisis-body'),btn=document.getElementById('analisis-toggle');
  var collapsed=(b.style.display==='none');
  b.style.display=collapsed?'':'none';
  btn.innerHTML=collapsed?'Colapsar &#9650;':'Expandir &#9660;';
}

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
    <button class="sub-btn active" data-sub="dashboard" onclick="switchSub('dashboard')">Dashboard</button>
    <button class="sub-btn" data-sub="expedientes" onclick="switchSub('expedientes')">Expedientes</button>
  </div>

  <!-- SUB: DASHBOARD -->
  <div id="sub-dashboard" class="sub-content active">
    <div class="section-block">
      <div class="section-header">
        <h2>Resumen general</h2>
        <span class="section-hint">Toc&aacute; las barras para filtrar</span>
      </div>
      <div class="section-body">
        <div id="dash-context" class="dash-context"></div>
        <div class="filter-row" style="margin-bottom:12px;align-items:center">
          <button class="chip on" id="dash-anio-all" onclick="setDashAnio('')">Todos</button>
          <button class="chip" id="dash-anio-2025" onclick="setDashAnio('2025')">2025</button>
          <button class="chip" id="dash-anio-2026" onclick="setDashAnio('2026')">2026</button>
          <span style="width:1px;height:18px;background:#D6E4F0;margin:0 4px"></span>
          <button class="chip" id="dash-sanc" onclick="toggleDashSanc()">Sancionados</button>
        </div>
        <div class="dash-stats-row">
          <div class="stat-card">
            <div class="stat-num" id="stat-total">{total}</div>
            <div class="stat-label">Total proyectos</div>
          </div>
          <div class="stat-card" style="border-left-color:#2E75B6">
            <div class="stat-num" style="color:#2E75B6" id="stat-pl">{pl}</div>
            <div class="stat-label">Proyectos de ley</div>
          </div>
          <div class="stat-card" style="border-left-color:#5B4DA0">
            <div class="stat-num" style="color:#5B4DA0" id="stat-pd">{pd}</div>
            <div class="stat-label">Declaraciones</div>
          </div>
          <div class="stat-card" style="border-left-color:#1a7a4a">
            <div class="stat-num" style="color:#1a7a4a" id="stat-otros">{otros}</div>
            <div class="stat-label">Otros tipos</div>
          </div>
        </div>
        <div class="dash-panels-row">
          <div>
            <div class="dash-subtitle">Por tipo de proyecto</div>
            <div id="tipo-bars"></div>
          </div>
          <div>
            <div class="dash-subtitle">Por bloque pol&iacute;tico</div>
            <div id="bloque-bars"></div>
          </div>
          <div>
            <div class="dash-subtitle">Por comisiones (Top 10)</div>
            <div id="com-bars"></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- SUB: EXPEDIENTES (panel de análisis + buscador unificados) -->
  <div id="sub-expedientes" class="sub-content">

    <!-- BLOQUE SUPERIOR: panel de análisis (pivot table, colapsable) -->
    <div class="section-block">
      <div class="section-header">
        <h2>Panel de an&aacute;lisis</h2>
        <button class="analisis-toggle-btn" id="analisis-toggle" onclick="toggleAnalisis()">Colapsar &#9650;</button>
      </div>
      <div class="section-body" id="analisis-body">
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

    <!-- BLOQUE INFERIOR: buscador de expedientes -->
    <div id="buscador-block">
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
    </div><!-- /buscador-block -->
  </div><!-- /sub-expedientes -->
</div><!-- /main-proyectos -->

<!-- ====================== MAIN: COMISIONES ====================== -->
<div id="main-comisiones" class="mtab-content">
  <div class="placeholder">
    <div class="placeholder-icon">&#127963;</div>
    <h3>Comisiones</h3>
    <p>Secci&oacute;n en construcci&oacute;n &mdash; pr&oacute;ximamente en Fase 2.</p>
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

<div class="footer">Prosecretar&iacute;a Parlamentaria &middot; Senado de la Naci&oacute;n Argentina<br>Datos al {fecha}</div>

<script>
var DATA = {datos};
{js}
init();
</script>
</body>
</html>"""


def _cargar(nombre, default):
    path = os.path.join(DATA_DIR, nombre)
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except Exception:
            return default
    return default


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
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    html = HTML_TEMPLATE.format(
        css=CSS,
        js=JS,
        datos=datos_js,
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
