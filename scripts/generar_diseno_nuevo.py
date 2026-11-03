"""
generar_diseno_nuevo.py — Toma el index.html ya generado y crea index_nuevo.html
con el diseño "D" (barra lateral azul, números en mono, colores por tipo).
No modifica index.html ni generar_web.py. Correr DESPUÉS de generar_web.py.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "index.html")
DST = os.path.join(ROOT, "index_nuevo.html")

# Colores por tipo: (texto, fondo)
TIPOS = {
    "PL": ("#0A3F7E", "#E1ECF9"), "PD": ("#0B5F57", "#DDF3F0"),
    "PC": ("#8A4B08", "#FCEBD3"), "PR": ("#5B21B6", "#EBE3FB"),
    "DC": ("#9D174D", "#FBE3EE"), "AC": ("#3F6212", "#E6F2D5"),
}
def mapa(nombre, idx):
    # conserva los tipos no redefinidos con su color original
    def rep(m):
        cuerpo = m.group(2)
        for k, v in TIPOS.items():
            nuevo = "%s:'%s'" % (k, v[idx])
            if re.search(r"\b%s:'#[0-9A-Fa-f]{6}'" % k, cuerpo):
                cuerpo = re.sub(r"\b%s:'#[0-9A-Fa-f]{6}'" % k, nuevo, cuerpo)
            else:
                cuerpo += "," + nuevo
        return m.group(1) + cuerpo + m.group(3)
    return nombre, rep

CSS = r"""
/* ===== DISEÑO NUEVO (D) ===== */
:root{--azul:#0A3F7E;--azul2:#0F4C93;--fondo:#F4F7FB;--linea:#D5DEEA;--txt:#0D1B2E;--muted:#55657A;--acento:#F2B134}
body{font-family:'Schibsted Grotesk','Poppins',sans-serif;background:var(--fondo);color:var(--txt);padding-left:236px}
.topbar{position:fixed;top:0;left:0;bottom:0;width:236px;background:var(--azul);display:flex;flex-direction:column;overflow-y:auto;z-index:100}
.header{background:transparent;border:none;padding:22px 20px 14px}
.header-row{flex-direction:column;align-items:flex-start;gap:2px}
.header-inst,.header-dep{font-size:10px;letter-spacing:1.6px;color:rgba(255,255,255,.7)}
.header-title{font-size:21px;line-height:1.15;margin-top:14px;font-weight:700;letter-spacing:-.3px}
.header-sub{font-family:'IBM Plex Mono',monospace;font-size:10.5px;margin-top:8px;color:rgba(255,255,255,.6)}
.main-nav{flex-direction:column;background:transparent;padding:6px 10px 20px;gap:2px;overflow:visible}
.mtab-btn{text-align:left;text-transform:none;letter-spacing:0;font-size:14px;font-weight:500;padding:10px 12px;border:none;border-left:3px solid transparent;border-radius:6px;color:rgba(255,255,255,.72)}
.mtab-btn:hover{background:rgba(255,255,255,.08);color:#fff}
.mtab-btn.active{background:rgba(255,255,255,.14);color:#fff;border-left-color:var(--acento);border-bottom-color:transparent;font-weight:600}
.sub-nav,.am-sub-nav{background:transparent;box-shadow:none;border-bottom:1px solid var(--linea);padding:0 20px}
.sub-btn,.am-sub-btn{font-size:13px;color:var(--muted)}
.section-block{background:#fff;border:1px solid var(--linea);box-shadow:none;border-radius:8px;margin:16px 20px}
.section-header{background:#fff;border-bottom:1px solid var(--linea);padding:14px 18px}
.section-header h2{color:var(--txt);font-size:15px;text-transform:none;letter-spacing:-.2px}
.card{border:1px solid var(--linea);border-radius:8px;box-shadow:none}
.card:hover{border-color:var(--azul);box-shadow:0 2px 10px rgba(10,63,126,.12)}
.card-exp{background:#fff;border-bottom:1px solid #E6ECF3}
.exp-badge{border-radius:3px;font-family:'IBM Plex Mono',monospace;font-size:11px;padding:3px 8px}
.exp-nro,.exp-fecha{font-family:'IBM Plex Mono',monospace}
.exp-nro{color:var(--txt);font-size:12.5px}
.btag{border-radius:999px;font-weight:600;padding:3px 10px 3px 8px}
.btag::before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;background:currentColor;margin-right:6px}
.ctag{background:#fff;color:var(--muted);border:1px solid var(--linea);border-radius:4px}
.chip.on{background:var(--azul);border-color:var(--azul)}
.proy-controls{border-radius:8px;border-color:var(--linea)}
.proy-control-group label{color:var(--muted)}
.nd-volver{display:block;margin:4px 20px 16px;padding:7px 10px;border:1px dashed rgba(255,255,255,.35);border-radius:6px;color:rgba(255,255,255,.8);font-size:12px;text-decoration:none;text-align:center}
.nd-volver:hover{background:rgba(255,255,255,.1);color:#fff}
@media (max-width:820px){
  body{padding-left:0}
  .topbar{position:sticky;width:auto;bottom:auto;flex-direction:column;overflow:visible}
  .header{padding:10px 14px}
  .header-row{flex-direction:row;justify-content:space-between}
  .header-title{margin-top:4px;font-size:18px}
  .main-nav{flex-direction:row;overflow-x:auto;padding:0 8px}
  .mtab-btn{white-space:nowrap;border-left:none;border-bottom:3px solid transparent;border-radius:0;padding:10px 12px}
  .mtab-btn.active{background:transparent;border-bottom-color:var(--acento)}
  .nd-volver{display:none}
  .section-block{margin:10px 8px}
}

/* menú plegable */
.nd-toggle{margin:0 10px 6px auto;display:block;width:30px;height:30px;border:1px solid rgba(255,255,255,.3);background:transparent;color:#fff;border-radius:6px;cursor:pointer;font-size:16px;line-height:1}
.nd-toggle:hover{background:rgba(255,255,255,.12)}
body.nd-colapsado{padding-left:64px}
body.nd-colapsado .topbar{width:64px}
body.nd-colapsado .header{padding:10px 8px;text-align:center}
body.nd-colapsado .header-row,body.nd-colapsado .header-sub,body.nd-colapsado .nd-volver{display:none}
body.nd-colapsado .header-title{font-size:0;margin:0}
body.nd-colapsado .header-title::first-letter{font-size:20px}
body.nd-colapsado .nd-toggle{margin:8px auto}
body.nd-colapsado .mtab-btn{font-size:0;text-align:center;padding:10px 0}
body.nd-colapsado .mtab-btn::before{content:attr(data-ini);font-size:13px;font-weight:700;font-family:'IBM Plex Mono',monospace}
@media (max-width:820px){.nd-toggle{display:none}body.nd-colapsado{padding-left:0}body.nd-colapsado .topbar{width:auto}
 body.nd-colapsado .header-row,body.nd-colapsado .header-sub{display:flex}body.nd-colapsado .header-title{font-size:18px}
 body.nd-colapsado .mtab-btn{font-size:14px;padding:10px 12px}body.nd-colapsado .mtab-btn::before{content:none}}
"""
INICIO_HTML = """<div id="main-inicio" class="mtab-content">
  <div class="ini-hero">
    <div class="ini-kicker">PROSECRETAR&Iacute;A PARLAMENTARIA</div>
    <h1>&iquest;Qu&eacute; est&aacute;s buscando hoy?</h1>
    <form class="ini-search" onsubmit="return iniBuscar(event)">
      <input id="ini-q" type="search" placeholder="Expediente, senador, comisi&oacute;n o palabra del extracto&hellip;" aria-label="Buscar">
      <button type="submit">Buscar</button>
    </form>
    <div id="ini-res" class="ini-res"></div>
  </div>
  <div class="ini-wrap">
    <div id="ini-cards" class="ini-cards"></div>
  </div>
</div>
"""

INICIO_JS = r"""<script>
(function(){
  function pf(s){var m=/^(\d{2})\/(\d{2})\/(\d{4})$/.exec(s||'');return m?new Date(+m[3],+m[2]-1,+m[1]).getTime():0;}
  function tipoCol(t){return {PL:['#E1ECF9','#0A3F7E'],PD:['#DDF3F0','#0B5F57'],PC:['#FCEBD3','#8A4B08'],PR:['#EBE3FB','#5B21B6'],DC:['#FBE3EE','#9D174D'],AC:['#E6F2D5','#3F6212']}[t]||['#EEF2F8','#55657A'];}
  function tg(t,txt,bg,fg){var c=tipoCol(t);return '<span class="ini-tag" style="background:'+(bg||c[0])+';color:'+(fg||c[1])+'">'+esc(txt||t)+'</span>';}
  function cut(t,n){t=(t||'').replace(/\s+/g,' ').trim();t=t.charAt(0)+t.slice(1).toLowerCase();return t.length>n?t.slice(0,n-1)+'\u2026':t;}
  function fila(tag,label,txt,onclick){return '<div class="ini-row"'+(onclick?' onclick="'+onclick+'" style="cursor:pointer"':'')+'>'+tag+'<span><b>'+esc(label)+'</b> <span class="ini-mut">'+esc(txt)+'</span></span></div>';}
  function ultimoTipo(t){
    var best=null,bt=-1;
    (typeof DATA!=='undefined'?DATA:[]).forEach(function(p){
      if(p.tipo!==t||p.origen!=='S')return; var d=pf(p.fecha);
      if(d>bt||(d===bt&&best&&p.nro>best.nro)){best=p;bt=d;}
    });
    return best;
  }
  function card(titulo,n,sub,rows,go){
    return '<a class="ini-card" href="#'+go+'" onclick="switchMain(\''+go+'\');return false;"><div class="ini-ch"><div class="ini-ct">'+titulo+'</div><div class="ini-n">'+n+'</div></div><div class="ini-sub">'+sub+'</div><div class="ini-rows">'+rows+'</div></a>';
  }
  function armar(){
    var cont=document.getElementById('ini-cards'); if(!cont)return;
    var out='';
    try{
      var lim=Date.now()-7*864e5,sem=DATA.filter(function(p){return pf(p.fecha)>=lim;});
      var cnt={PL:0,PD:0,PC:0};sem.forEach(function(p){if(cnt[p.tipo]!==undefined)cnt[p.tipo]++;});
      var conOD=DATA.filter(function(p){return p.od;}).length;
      function cl(t,sem7,od){return "event.stopPropagation();event.preventDefault();iniProy('"+t+"',"+sem7+","+od+");return false;";}
      function np(n){return n+(n===1?' proyecto':' proyectos');}
      var r=fila(tg('7D','7D','#E1ECF9','#0A3F7E'),'Últimos 7 días',np(sem.length),cl('',1,0));
      ['PL','PD','PC'].forEach(function(t){r+=fila(tg(t),t+' en 7 días',np(cnt[t]),cl(t,1,0));});
      r+=fila(tg('OD','OD','#FCEBD3','#8A4B08'),'Con Orden del Día',np(conOD),cl('',0,1));
      out+=card('Proyectos',DATA.length.toLocaleString('es-AR'),'Proyectos cargados',r,'proyectos');
    }catch(e){}
    try{
      var am=AYUDA_MEMORIA.slice(); var maxN=0,minP=null;
      am.forEach(function(o){var n=parseInt(o.numero,10)||0;if(n>maxN)maxN=n;});
      var ult=am.filter(function(o){return (parseInt(o.numero,10)||0)===maxN})[0];
      var fmax=0;am.forEach(function(o){var d=pf(o.fechaDictamen);if(d>fmax)fmax=d;});
      var nuevas=am.filter(function(o){return pf(o.fechaDictamen)===fmax}).length;
      var r2='';
      if(ult)r2+=fila(tg('OD','OD','#E1ECF9','#0A3F7E'),'Última OD','N.\u00ba '+ult.numero+' \u00b7 '+cut(ult.descripcion,44));
      r2+=fila(tg('NUEVAS','NUEVAS','#E6F2D5','#3F6212'),'Dictamen más reciente',nuevas+(nuevas===1?' orden':' \u00f3rdenes')+' \u00b7 '+(ult&&ult.fechaDictamen||''));
      out+=card('Ayuda Memoria',am.length,'Órdenes del día pendientes',r2,'ayuda');
    }catch(e){}
    try{
      var hoy=new Date();hoy.setHours(0,0,0,0);
      var rs=(Array.isArray(AGENDA)?AGENDA:[]).filter(function(x){return x&&x.fecha_iso&&!x.suspendida;}).map(function(x){
        var t=(typeof reunionTime==='function')?reunionTime(x):new Date(x.fecha_iso).getTime();
        return {x:x,d:new Date(t)};
      });
      var prox=rs.filter(function(o){return o.d>=hoy}).sort(function(a,b){return a.d-b.d});
      var sem=prox.filter(function(o){return o.d-hoy<7*864e5}).length;
      var r3='';
      prox.slice(0,3).forEach(function(o,i){
        r3+=fila(tg('',(o.x.dia||'').slice(0,3)+' '+String(o.d.getDate()),'#E1ECF9','#0A3F7E'),i===0?'Próxima':'Siguiente',(o.x.hora||'')+' \u00b7 '+cut((o.x.comisiones||[]).join(', '),40));
      });
      if(!prox.length)r3=fila('','Sin reuniones próximas','');
      out+=card('Agenda',sem,'Reuniones en los próximos 7 días',r3,'agenda');
    }catch(e){}
    try{
      var rs2=(typeof senResumen==='function')?senResumen():null;
      if(rs2){
        var r5='';
        rs2.bloques.slice(0,3).forEach(function(b){
          r5+=fila(tg('',String(b[1]),'#E1ECF9','#0A3F7E'),b[0],b[1]+(b[1]===1?' senador/a':' senadores/as'),"event.stopPropagation();event.preventDefault();senFiltrar('"+jsStr(b[0])+"');return false;");
        });
        if(rs2.top)r5+=fila(tg('TOP','TOP','#E6F2D5','#3F6212'),'Más proyectos',rs2.top.nombre+' · '+rs2.top.n,"event.stopPropagation();event.preventDefault();senAbrirDesdeInicio('"+jsStr(rs2.top.raw)+"');return false;");
        out+=card('Senadores',rs2.vigentes,'Senadores/as en ejercicio',r5,'senadores');
      }
    }catch(e){}
    try{
      var hoy2=new Date();hoy2.setHours(0,0,0,0);
      var ag=(Array.isArray(AGENDA)?AGENDA:[]).filter(function(x){return x&&x.fecha_iso&&!x.suspendida;}).map(function(x){return {x:x,d:new Date((typeof reunionTime==='function')?reunionTime(x):new Date(x.fecha_iso).getTime())};}).filter(function(o){return o.d>=hoy2&&o.d-hoy2<7*864e5;}).sort(function(a,b){return a.d-b.d;});
      var cs={};ag.forEach(function(o){(o.x.comisiones||[]).forEach(function(c){cs[c]=1;});});
      var ncs=Object.keys(cs).length;
      var r6=fila(tg('7D','7D','#E1ECF9','#0A3F7E'),'Con reunión esta semana',ncs+(ncs===1?' comisión':' comisiones'),"event.stopPropagation();event.preventDefault();switchMain('agenda');return false;");
      if(ag[0])r6+=fila(tg('',(ag[0].x.dia||'').slice(0,3)+' '+ag[0].d.getDate(),'#FCEBD3','#8A4B08'),'Próxima',(ag[0].x.hora||'')+' · '+cut((ag[0].x.comisiones||[]).join(', '),36),"event.stopPropagation();event.preventDefault();switchMain('agenda');return false;");
      out+=card('Comisiones',(typeof COMISIONES!=='undefined'?COMISIONES.length:0),'Comisiones permanentes',r6,'comisiones');
    }catch(e){}
    cont.innerHTML=out;
  }
  function nrm(t){return (t||'').toString().toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'');}
  function aplicar(inputId,q,main){
    switchMain(main);
    if(inputId==='agenda-search'&&typeof toggleAgendaVista==='function')toggleAgendaVista('calendario');
    var el=document.getElementById(inputId);
    if(el){el.value=q;el.dispatchEvent(new Event('input',{bubbles:true}));if(inputId==='search'&&typeof onFilterChange==='function')onFilterChange();
    if(inputId==='agenda-search'){try{var fl=agendaPrincipalesFiltradas().filter(function(r){return r.fecha_iso}),n=Date.now();
      if(fl.length){fl.sort(function(x,y){return Math.abs(reunionTime(x)-n)-Math.abs(reunionTime(y)-n)});var d=new Date(fl[0].fecha_iso);AGENDA_CAL_MES=new Date(d.getFullYear(),d.getMonth(),1);renderAgendaCalendario();}}catch(e){}}
  }
  }
  /* lista de TODAS las reuniones encontradas (el calendario muestra un solo mes) */
  (function(){
    var orig=window.renderAgendaCalendario; if(typeof orig!=='function')return;
    window.renderAgendaCalendario=function(){
      orig.apply(this,arguments);
      try{
        var g=document.getElementById('cal-grid'); if(!g)return;
        var box=document.getElementById('agenda-hits');
        if(!box){box=document.createElement('div');box.id='agenda-hits';g.parentNode.insertBefore(box,g.nextSibling);}
        var hay=(typeof agendaSearch!=='undefined'&&agendaSearch)||(typeof agendaComision!=='undefined'&&agendaComision);
        var fl=hay?agendaPrincipalesFiltradas().filter(function(r){return r.fecha_iso}):[];
        if(!fl.length){box.innerHTML='';return;}
        var n=Date.now();
        fl.sort(function(x,y){var a=reunionTime(x)>=n,b=reunionTime(y)>=n;if(a!==b)return a?-1:1;var d=reunionTime(x)-reunionTime(y);return a?d:-d;});
        var h='<div class="ini-sec" style="margin-top:18px"><div class="ini-sec-h"><span>'+fl.length+' reunion'+(fl.length===1?'':'es')+' encontrada'+(fl.length===1?'':'s')+' (todos los meses)</span></div>';
        fl.forEach(function(r){var d=new Date(r.fecha_iso);
          var tem=(r.temario||[]).filter(function(x){return typeof agendaSearch!=='undefined'&&agendaSearch&&matchPalabraExacta(agendaSearch,(x.numero||'')+' '+(x.extracto||''))})[0];
          h+='<a class="ini-sug" href="#" onclick="agendaAbrirDia('+d.getFullYear()+','+d.getMonth()+','+d.getDate()+');return false;"><b>'+esc(r.fecha+(r.hora?' '+r.hora+' hs':''))+'</b> <span class="ini-mut">'+(r.suspendida?'Suspendida':reunionTime(r)>=n?'Pr&oacute;xima':'Realizada')+' &middot; '+esc(cut((r.comisiones||[]).join(', '),60))+(tem?' &middot; '+esc(cut(tem.extracto||tem.numero,80)):'')+'</span></a>';});
        box.innerHTML=h+'</div>';
      }catch(e){}
    };
  })();
  /* buscador de la Agenda: ignorar tildes (mineria = minería) */
  (function(){var o=window.matchPalabraExacta; if(typeof o!=='function')return;
    window.matchPalabraExacta=function(q,t){return o(nrm(q),nrm(t));};})();
  window.iniIr=function(inputId,main){aplicar(inputId,window.__iniQ||'',main);return false;};
  function iniReuniones(nq){
    var now=Date.now(),out=[],q=window.__iniQ||'';
    try{agendaPrincipales().forEach(function(r){
      if(!matchPalabraExacta(q,agendaTextoBusqueda(r)))return;
      var t=(r.temario||[]).filter(function(x){return matchPalabraExacta(q,(x.numero||'')+' '+(x.extracto||''))});
      out.push({r:r,t:t,prox:reunionTime(r)>=now-3600000&&!r.suspendida});
    });}catch(e){}
    out.sort(function(a,b){if(a.prox!==b.prox)return a.prox?-1:1;var d=reunionTime(a.r)-reunionTime(b.r);return a.prox?d:-d;});
    return out;
  }
  function iniReunTxt(o){
    var r=o.r,l=o.t.length?o.t[0]:null;
    return '<b>'+esc((r.fecha||'')+(r.hora?' '+r.hora+' hs':''))+'</b> <span class="ini-mut">'+(r.suspendida?'Suspendida':o.prox?'Pr&oacute;xima':'Realizada')+' &middot; '+esc(cut((r.comisiones||[]).join(', '),50))+(l?' &middot; '+esc(cut(l.extracto||l.numero,70)):'')+'</span>';
  }
  window.iniBuscar=function(ev){
    ev.preventDefault();
    var q=document.getElementById('ini-q').value.trim(); window.__iniQ=q;
    var box=document.getElementById('ini-res'); if(!q){box.innerHTML='';return false;}
    var nq=nrm(q),res=[];
    try{
      var np=(DATA||[]).filter(function(p){return nrm(expNroOf(p)+' '+p.extracto+' '+(p.autores||[]).join(' ')+' '+(p.comisiones||[]).join(' ')).indexOf(nq)>=0}).length;
      res.push(['Proyectos',np,np?np.toLocaleString('es-AR')+' resultado'+(np===1?'':'s'):'',"iniIr('search','proyectos')"]);
    }catch(e){}
    try{
      var am=(AYUDA_MEMORIA||[]).filter(function(o){return nrm('OD '+o.numero+' '+o.descripcion+' '+(o.autor||'')+' '+(o.expedientes||[]).map(function(x){return x.codigo}).join(' ')).indexOf(nq)>=0});
      var det=am.length?(am.length===1?'OD '+am[0].numero:'OD '+am[0].numero+' y '+(am.length-1)+' más'):'';
      res.push(['Ayuda Memoria',am.length,det,"iniIr('am-search','ayuda')"]);
    }catch(e){}
    try{
      var sc=(SANCIONES_DATA||[]).filter(function(x){return nrm((x.expediente||'')+' OD '+(x.od_nro||'')+' '+(x.observaciones||'')+' '+(x.solicitante||'')).indexOf(nq)>=0});
      res.push(['Sanciones HSN',sc.length,sc.length?sc.length+' ítem'+(sc.length===1?'':'s'):'',"iniIr('sanc-search','sanciones')"]);
    }catch(e){}
    try{
      var cm=(COMISIONES||[]).filter(function(c){return nrm(c.nombre).indexOf(nq)>=0});
      res.push(['Comisiones',cm.length,cm.length?(cm.length===1?cm[0].nombre:cm.length+' comisiones'):'',"iniIr('com-search','comisiones')"]);
    }catch(e){}
    try{
      var rn=iniReuniones(nq),pn=rn.filter(function(x){return x.prox}).length;
      res.push(['Reuniones de comisión',rn.length,rn.length?rn.length+' reunion'+(rn.length===1?'':'es')+(pn?' ('+pn+' próxima'+(pn===1?'':'s')+')':''):'',"iniIr('agenda-search','agenda')"]);
    }catch(e){}
    var h='<div class="ini-res-t">Resultados para &laquo;'+esc(q)+'&raquo;</div>';
    res.forEach(function(r){
      var ok=r[1]>0;
      h+='<a class="ini-res-r'+(ok?'':' vacio')+'" href="#" '+(ok?'onclick="return '+r[3]+'"':'onclick="return false"')+'><span class="ini-res-s">'+r[0]+'</span><span class="ini-res-d">'+(ok?esc(String(r[2])):'Sin resultados')+'</span>'+(ok?'<span class="ini-res-go">Ver &rarr;</span>':'')+'</a>';
    });
    box.innerHTML=h; return false;
  };
  /* --- sugerencias mientras se escribe --- */
  function iniLive(){
    var q=document.getElementById('ini-q').value.trim(); window.__iniQ=q;
    var box=document.getElementById('ini-res'); if(!q){box.innerHTML='';return;}
    var nq=nrm(q),h='',MAX=3;
    function sec(titulo,total,items,irFn){
      if(!total)return '';
      var o='<div class="ini-sec"><div class="ini-sec-h"><span>'+titulo+'</span><a href="#" onclick="return '+irFn+'">Ver los '+total.toLocaleString('es-AR')+' &rarr;</a></div>';
      items.forEach(function(it){o+='<a class="ini-sug" href="#" onclick="'+it[1]+'">'+it[0]+'</a>';});
      return o+'</div>';
    }
    try{
      var pr=[];(DATA||[]).forEach(function(p){if(nrm(expNroOf(p)+' '+p.extracto+' '+(p.autores||[]).join(' ')+' '+(p.comisiones||[]).join(' ')).indexOf(nq)>=0)pr.push(p);});
      pr.sort(function(a,b){return pf(b.fecha)-pf(a.fecha)});
      h+=sec('Proyectos',pr.length,pr.slice(0,MAX).map(function(p){
        return [tg(p.tipo)+' <b>'+esc(expNroOf(p))+'</b> <span class="ini-mut">'+esc(cut(p.extracto,70))+'</span>',"abrirFicha('"+jsStr(claveP(p))+"');return false;"];
      }),"iniIr('search','proyectos')");
    }catch(e){}
    try{
      var am=(AYUDA_MEMORIA||[]).filter(function(o){return nrm('OD '+o.numero+' '+o.descripcion+' '+(o.autor||'')+' '+(o.expedientes||[]).map(function(x){return x.codigo}).join(' ')).indexOf(nq)>=0});
      h+=sec('Ayuda Memoria',am.length,am.slice(0,MAX).map(function(o){
        return [tg('OD','OD','#E1ECF9','#0A3F7E')+' <b>OD '+esc(o.numero)+'</b> <span class="ini-mut">'+esc(cut(o.descripcion,70))+'</span>',"return iniIr('am-search','ayuda')"];
      }),"iniIr('am-search','ayuda')");
    }catch(e){}
    try{
      var sc=(SANCIONES_DATA||[]).filter(function(x){return nrm((x.expediente||'')+' OD '+(x.od_nro||'')+' '+(x.observaciones||'')+' '+(x.solicitante||'')).indexOf(nq)>=0});
      h+=sec('Sanciones HSN',sc.length,sc.slice(0,MAX).map(function(x){
        return [tg('LEY','SANC','#E6F2D5','#3F6212')+' <b>'+esc(x.expediente||'')+'</b> <span class="ini-mut">'+esc((x.od_nro?'OD '+x.od_nro+' · ':'')+(x.observaciones||x.resultado||''))+'</span>',"return iniIr('sanc-search','sanciones')"];
      }),"iniIr('sanc-search','sanciones')");
    }catch(e){}
    try{
      var cm=(COMISIONES||[]).filter(function(c){return nrm(c.nombre).indexOf(nq)>=0});
      h+=sec('Comisiones',cm.length,cm.slice(0,MAX).map(function(c){
        return [tg('COM','COM','#EBE3FB','#5B21B6')+' <b>'+esc(c.nombre)+'</b>',"return iniIr('com-search','comisiones')"];
      }),"iniIr('com-search','comisiones')");
    }catch(e){}
    try{
      var rn=iniReuniones(nq);
      h+=sec('Reuniones de comisi&oacute;n',rn.length,rn.slice(0,MAX).map(function(o){return [iniReunTxt(o),"return iniIr('agenda-search','agenda')"];}),"iniIr('agenda-search','agenda')");
    }catch(e){}
    box.innerHTML=h||'<div class="ini-res-t">Sin coincidencias para &laquo;'+esc(q)+'&raquo;</div>';
  }
  (function(){var t=null,q=document.getElementById('ini-q');if(!q)return;
    q.addEventListener('input',function(){clearTimeout(t);t=setTimeout(iniLive,120);});})();
  window.iniProy=function(tipo,sem7,od){
    switchMain('proyectos');
    try{switchSub('buscador');resetBuscadorOnly();activeAnio='';activeTipos={};activeOrigen='';activeAcuerdoEstado='';
      setSelVal('origen-select','');setSelVal('tipo-select','');
      if(tipo){activeTipos[tipo]=1;setSelVal('tipo-select',tipo);}
      if(od){activeConOD=true;var c=document.getElementById('con-od-check');if(c)c.checked=true;}
      if(sem7){var d=new Date(Date.now()-7*864e5),z=function(n){return (n<10?'0':'')+n;};
        document.getElementById('fecha-desde').value=d.getFullYear()+'-'+z(d.getMonth()+1)+'-'+z(d.getDate());}
      applyAll();}catch(e){}
    return false;
  };
  function iniciar(){
    armar();
    if(!location.hash||location.hash==='#')activateMain('inicio');
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',iniciar);else iniciar();
})();
</script>"""

INICIO_CSS = r"""
/* ===== Fondo cálido ===== */
/* ===== Textura del fondo: degradé suave + grano de papel ===== */
body{background-color:#F4EFE6;background-image:
 url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .35  0 0 0 0 .28  0 0 0 0 .15  0 0 0 .07 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>"),
 radial-gradient(900px 500px at 85% -5%,rgba(242,177,52,.14),transparent 60%),
 radial-gradient(800px 600px at 10% 105%,rgba(10,63,126,.07),transparent 60%),
 linear-gradient(180deg,#F7F2E9 0%,#F1EADD 100%);
 background-attachment:scroll,fixed,fixed,fixed}

:root{--fondo:#F4EFE6;--linea:#E3DACB;--papel:#FFFDF9}
.section-block,.section-header,.card,.cards-grid .card,.proy-controls,.od-card,.ini-card,.ini-res,.sub-nav,.am-sub-nav,.viz-card,.com-card,.senator-card{background:var(--papel)}
.section-block,.section-header,.card,.proy-controls,.od-card,.ini-card,.sub-nav,.am-sub-nav,.viz-card{border-color:var(--linea)}
.card-exp{background:var(--papel);border-bottom-color:#EFE7D8}
.ini-rows,.ini-sec,.ini-res-r{border-top-color:#EFE7D8}
.ini-card{box-shadow:0 4px 14px rgba(90,70,30,.08)}
.ctag{background:var(--papel);border-color:var(--linea)}
.ini-wrap+*,.footer{color:#8A7F6B}

/* ===== Inicio ===== */
.ini-hero{background:linear-gradient(#0A3F7E,#0F4C93);color:#fff;padding:52px 32px 70px;text-align:center}
.ini-kicker{font-size:12px;letter-spacing:1.6px;color:#B9D6F2}
.ini-hero h1{font-size:34px;font-weight:800;letter-spacing:-.7px;margin:10px 0 24px}
.ini-search{max-width:720px;margin:0 auto;background:#fff;border-radius:14px;padding:6px 6px 6px 18px;display:flex;gap:10px;box-shadow:0 12px 30px rgba(0,0,0,.25)}
.ini-search input{flex:1;border:none;outline:none;font-family:inherit;font-size:16px;color:#0D1B2E;background:transparent;min-width:0}
.ini-search button{background:#0A3F7E;color:#fff;border:none;border-radius:10px;font-family:inherit;font-weight:700;font-size:15px;padding:12px 22px;cursor:pointer}
.ini-res{max-width:720px;margin:14px auto 0;background:#fff;color:#0D1B2E;border-radius:12px;text-align:left;box-shadow:0 12px 30px rgba(0,0,0,.2)}
.ini-res:empty{display:none}
.ini-res-t{padding:12px 18px 8px;font-size:12px;color:#55657A;letter-spacing:.3px}
.ini-res-r{display:flex;gap:14px;align-items:center;padding:11px 18px;border-top:1px solid #E6ECF3;text-decoration:none;color:#0D1B2E}
.ini-res-r:hover{background:#F4F9FF}
.ini-res-r.vacio{color:#8896A8;cursor:default}.ini-res-r.vacio:hover{background:transparent}
.ini-res-s{font-weight:700;width:130px;flex-shrink:0}
.ini-res-d{flex:1;font-size:14px}
.ini-res-go{font-weight:700;font-size:13px;color:#0A3F7E}
.ini-sec{border-top:1px solid #E6ECF3;padding:8px 0}
.ini-sec-h{display:flex;justify-content:space-between;padding:4px 18px;font-weight:700;font-size:13px}
.ini-sec-h a{font-size:12px;color:#0A3F7E;text-decoration:none}
.ini-sug{display:block;padding:7px 18px;font-size:13.5px;text-decoration:none;color:#0D1B2E;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ini-sug:hover{background:#F4F9FF}
.ini-wrap{max-width:1120px;margin:-34px auto 40px;padding:0 20px}
.ini-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}
.ini-card{background:#fff;border:1px solid #D5DEEA;border-radius:12px;padding:18px;text-decoration:none;color:#0D1B2E;box-shadow:0 4px 14px rgba(10,63,126,.08);display:flex;flex-direction:column;gap:8px}
.ini-card:hover{border-color:#0A3F7E}
.ini-ch{display:flex;justify-content:space-between;align-items:baseline}
.ini-ct{font-weight:700;font-size:15px}
.ini-n{font-family:'IBM Plex Mono',monospace;font-size:28px;font-weight:600;color:#0A3F7E}
.ini-sub{font-size:12.5px;color:#55657A;margin-top:-4px}
.ini-rows{border-top:1px solid #E6ECF3;padding-top:10px;display:flex;flex-direction:column;gap:7px;font-size:13px}
.ini-row{display:flex;gap:8px;align-items:baseline}
.ini-row b{font-weight:600}
.ini-mut{color:#55657A}
.ini-tag{font-family:'IBM Plex Mono',monospace;font-size:10.5px;font-weight:600;padding:2px 6px;border-radius:3px;flex-shrink:0}
body.nd-colapsado .mtab-btn[data-main="inicio"]::before{content:"In"}
"""

SANC_JS = r"""<script>
/* Sanciones (solo diseño nuevo): muestra las "aprobado con modificaciones"
   como "Vuelve a Diputados" y permite buscar por número de OD / observaciones. */
(function(){
  function esModif(it){return /^APROBAD\w*\s+con\s+modif/i.test(it.resultado||'');}
  window.sancAprobado=function(it){return it.resultado==='APROBADO'||it.resultado==='APROBADA'||esModif(it);};
  function nrm(t){return (t||'').toString().toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'');}
  window.renderSanciones=function(){
    var searchEl=document.getElementById('sanc-search');
    var q=nrm(searchEl&&searchEl.value||'').trim();
    var lista=(SANCIONES_DATA||[]).filter(function(it){
      var cat=sancCategoriaLanding(it);
      if(!cat)return false;
      if(sancCat!=='TODOS'&&cat!==sancCat)return false;
      if(!q)return true;
      var exp=parseExpNumero(it.expediente);
      var p=exp?proyectoDeExp(exp):null;
      var hay=nrm(it.expediente+' od '+(it.od_nro||'')+' od n '+(it.od_nro||'')+' '+(it.observaciones||'')+' '+(esModif(it)?'vuelve a diputados con modificaciones':'')+' '+(p&&p.extracto||''));
      return hay.indexOf(q)>=0;
    });
    lista=lista.slice().sort(function(a,b){return (b.fecha_sesion||'').localeCompare(a.fecha_sesion||'')});
    var el=document.getElementById('sanc-list'); if(!el)return;
    if(!lista.length){el.innerHTML='<div class="no-results">Sin resultados para este filtro.</div>';return}
    var html='';lista.forEach(function(it){html+=buildSancCard(it)});el.innerHTML=html;
  };
  var _bsc=window.buildSancCard;
  window.buildSancCard=function(it){
    var h=_bsc(it);
    if(esModif(it))h=h.replace('<div class="od-card-top">','<div class="od-card-top"><span class="od-tipo-tag" style="background:#FCEBD3;color:#8A4B08;border-color:#F0CFA0">Vuelve a Diputados</span>');
    return h;
  };
  if(typeof renderSanciones==='function')try{renderSanciones();}catch(e){}
})();
</script>"""

SEN_HTML = """<div id="main-senadores" class="mtab-content">
  <div class="section-block">
    <div class="section-header"><h2>Senadores y senadoras</h2></div>
    <div id="sen-lista">
      <div class="proy-controls" style="margin:14px 18px;display:flex;gap:10px;flex-wrap:wrap;align-items:center">
        <input class="search-box" type="text" id="sen-q" placeholder="Buscar por nombre&hellip;" style="max-width:260px">
        <div class="select-wrapper"><select class="filter-select" id="sen-bloque"><option value="">Todos los bloques</option></select><span class="select-arrow">&#9660;</span></div>
        <div class="select-wrapper"><select class="filter-select" id="sen-prov"><option value="">Todas las provincias</option></select><span class="select-arrow">&#9660;</span></div>
        <label class="sen-chk"><input type="checkbox" id="sen-ex"> Incluir mandatos cumplidos</label>
        <span id="sen-cnt" class="ini-mut"></span>
      </div>
      <div id="sen-grid" class="sen-grid"></div>
    </div>
    <div id="sen-ficha" hidden></div>
  </div>
</div>"""

SEN_CSS = r"""
.sen-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px;padding:0 18px 18px}
.sen-card{display:flex;gap:12px;align-items:center;border:1px solid var(--linea);border-radius:8px;padding:12px;background:#fff;cursor:pointer;text-align:left;font:inherit}
.sen-card:hover{border-color:var(--azul);box-shadow:0 2px 10px rgba(10,63,126,.12)}
.sen-card.ex{opacity:.6}
.sen-ph{width:52px;height:52px;border-radius:50%;background:#EEF2F8;object-fit:cover;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-weight:700;color:var(--muted)}
.sen-nom{font-weight:600;font-size:14px;line-height:1.2}
.sen-mut{font-size:12px;color:var(--muted);margin-top:3px}
.sen-chk{font-size:13px;color:var(--muted);display:flex;gap:6px;align-items:center}
.sen-head{display:flex;gap:16px;align-items:center;padding:16px 18px;border-bottom:1px solid var(--linea);flex-wrap:wrap}
.sen-head .sen-ph{width:84px;height:84px;font-size:26px}
.sen-head h3{margin:0;font-size:20px;letter-spacing:-.3px}
.sen-sec{padding:14px 18px;border-bottom:1px solid #E6ECF3}
.sen-sec h4{margin:0 0 10px;font-size:13px;text-transform:uppercase;letter-spacing:.8px;color:var(--muted)}
.sen-kpis{display:flex;gap:10px;flex-wrap:wrap;padding:14px 18px}
.sen-kpi{border:1px solid var(--linea);border-radius:8px;padding:8px 14px;min-width:110px}
.sen-kpi b{display:block;font-family:'IBM Plex Mono',monospace;font-size:20px}
.sen-kpi span{font-size:12px;color:var(--muted)}
.sen-proy{display:flex;gap:8px;align-items:baseline;padding:6px 0;border-bottom:1px solid #F0F3F8;cursor:pointer;font-size:13px}
.sen-proy:hover{background:#F4F7FB}
.sen-tag{font-family:'IBM Plex Mono',monospace;font-size:11px;padding:2px 6px;border-radius:3px;flex-shrink:0}
"""

SEN_JS = r"""<script>
(function(){
  var SEN=__SENADORES__;
  function nrm(t){return (t||'').toString().toUpperCase().normalize('NFD').replace(/[̀-ͯ]/g,'').trim();}
  function bonito(n){var p=(n||'').split(',');var ap=p[0].trim(),no=(p[1]||'').trim();
    function tc(s){return s.toLowerCase().replace(/(^|[\s\-'])([a-záéíóúñü])/g,function(m,a,b){return a+b.toUpperCase();});}
    return (no?tc(no)+' ':'')+tc(ap);}
  function pf(f){var m=/(\d+)\/(\d+)\/(\d+)/.exec(f||'');return m?Date.UTC(+m[3],+m[2]-1,+m[1]):0;}
  function iniciales(n){var p=bonito(n).split(' ');return ((p[0]||'')[0]||'')+((p[p.length-1]||'')[0]||'');}
  function foto(n,cls){var u=(typeof fotoSenadorUrl==='function')?fotoSenadorUrl(n):null;
    return u?'<img class="sen-ph" src="'+esc(u)+'" alt="" loading="lazy" onerror="this.outerHTML=\'<div class=&quot;sen-ph&quot;>'+esc(iniciales(n))+'</div>\'">':'<div class="sen-ph">'+esc(iniciales(n))+'</div>';}
  var porKey={},porApe={};
  SEN.forEach(function(s){s.k=nrm(s.nombre);porKey[s.k]=s;var a=s.k.split(',')[0].trim();(porApe[a]=porApe[a]||[]).push(s);});
  function buscar(nombre){var k=nrm(nombre);if(porKey[k])return porKey[k];
    var a=k.split(',')[0].trim(),c=porApe[a]||[];if(c.length===1)return c[0];
    var pn=(k.split(',')[1]||'').trim().split(/\s+/)[0];
    for(var i=0;i<c.length;i++){var q=(c[i].k.split(',')[1]||'').trim().split(/\s+/)[0];if(pn&&q&&(q.indexOf(pn)===0||pn.indexOf(q)===0))return c[i];}
    return null;}
  /* índices (se arman una vez) */
  var proy={},coau={},coms={},dict={};
  function indices(){
    if(indices.hecho)return;indices.hecho=1;
    (DATA||[]).forEach(function(p){
      (p.autores||[]).forEach(function(a){var s=buscar(a);if(s)(proy[s.k]=proy[s.k]||[]).push(p);});
      (p.coautores||[]).forEach(function(a){var s=buscar(a);if(s)(coau[s.k]=coau[s.k]||[]).push(p);});
    });
    (COMISIONES||[]).forEach(function(c){(c.integrantes||[]).forEach(function(m){var s=buscar(m.nombre);if(s)(coms[s.k]=coms[s.k]||[]).push({c:c.nombre,rol:m.rol});});});
    (AYUDA_MEMORIA||[]).forEach(function(o){(o.firmantesMayoria||[]).forEach(function(f){
      var nf=nrm(f);SEN.forEach(function(s){var ap=s.k.split(',')[0].trim(),no=(s.k.split(',')[1]||'').trim();
        if(nf.length>ap.length&&nf.slice(-ap.length)===ap&&nf[0]===no[0]&&(nf.length===ap.length||nf[nf.length-ap.length-1]===' '))(dict[s.k]=dict[s.k]||[]).push(o);});});});
  }
  function tagTipo(t){var fg=(typeof TIPO_FG!=='undefined'&&TIPO_FG[t])||'#0A3F7E',bg=(typeof TIPO_BG!=='undefined'&&TIPO_BG[t])||'#E1ECF9';
    return '<span class="sen-tag" style="color:'+fg+';background:'+bg+'">'+esc(t)+'</span>';}
  function btag(b){var c=(typeof blqColor==='function')?blqColor(b):{bg:'#EEF2F8',badge:'#333'};
    return '<span class="senator-bloque-tag" style="background:'+c.bg+';color:'+c.badge+'">'+esc(b||'Sin bloque')+'</span>';}
  var $=function(i){return document.getElementById(i)};
  function lista(){
    indices();
    var q=nrm($('sen-q').value),bl=$('sen-bloque').value,pv=$('sen-prov').value,ex=$('sen-ex').checked;
    var r=SEN.filter(function(s){return (ex||s.vigente)&&(!q||s.k.indexOf(q)>=0||nrm(bonito(s.nombre)).indexOf(q)>=0)&&(!bl||s.bloque===bl)&&(!pv||s.provincia===pv);});
    r.sort(function(a,b){return a.k.localeCompare(b.k,'es')});
    $('sen-cnt').textContent=r.length+' senador'+(r.length===1?'':'es/as');
    $('sen-grid').innerHTML=r.map(function(s){
      return '<button class="sen-card'+(s.vigente?'':' ex')+'" onclick="senAbrir(\''+jsStr(s.nombre)+'\')">'+foto(s.nombre)
        +'<div><div class="sen-nom">'+esc(bonito(s.nombre))+'</div>'+btag(s.bloque)
        +'<div class="sen-mut">'+esc(s.provincia||'')+(s.vigente?'':' &middot; mandato cumplido')+'</div>'
        +'<div class="sen-mut">'+(proy[s.k]||[]).length+' proyectos &middot; '+(coms[s.k]||[]).length+' comisiones</div></div></button>';
    }).join('')||'<div class="com-empty" style="grid-column:1/-1">Sin resultados.</div>';
  }
  window.senResumen=function(){
    indices();
    var v=SEN.filter(function(s){return s.vigente;}),bl={};
    v.forEach(function(s){var b=s.bloque||'Sin bloque';bl[b]=(bl[b]||0)+1;});
    var arr=Object.keys(bl).map(function(k){return [k,bl[k]];}).sort(function(a,b){return b[1]-a[1];});
    var top=null;v.forEach(function(s){var n=(proy[s.k]||[]).length;if(!top||n>top.n)top={nombre:bonito(s.nombre),raw:s.nombre,n:n};});
    return {vigentes:v.length,bloques:arr,top:top};
  };
  window.senFiltrar=function(b){
    switchMain('senadores');
    if(typeof window.senVolver==='function')try{window.senVolver();}catch(e){}
    ['sen-q','sen-prov'].forEach(function(i){var e=$(i);if(e){e.value='';}});
    var x=$('sen-ex');if(x)x.checked=false;
    var e=$('sen-bloque');if(e){e.value=(b==='Sin bloque'?'':b);e.dispatchEvent(new Event('change',{bubbles:true}));}
  };
  window.senAbrirDesdeInicio=function(raw){switchMain('senadores');window.senAbrir(raw);};
  var tipoSel='',rolSel='autor';
  window.senAbrir=function(nombre){
    indices();var s=buscar(nombre);if(!s)return;window.__senActual=s.nombre;
    var P0=(proy[s.k]||[]).slice().sort(function(a,b){return pf(b.fecha)-pf(a.fecha)});
    var C0=(coau[s.k]||[]).slice().sort(function(a,b){return pf(b.fecha)-pf(a.fecha)});
    var C=C0,P=(rolSel==='coautor')?C0:P0;
    var M=coms[s.k]||[],D=(dict[s.k]||[]).slice();
    var leyes=P0.filter(function(p){return p.sancionado}).length;
    var tipos={};P.forEach(function(p){tipos[p.tipo]=(tipos[p.tipo]||0)+1});
    var lst=tipoSel?P.filter(function(p){return p.tipo===tipoSel}):P;
    var h='<div class="sen-head"><button class="btn-export" onclick="senVolver()">&larr; Volver</button>'+foto(s.nombre)
      +'<div><h3>'+esc(bonito(s.nombre))+(s.vigente?'':' <span class="ini-mut">(mandato cumplido)</span>')+'</h3>'+btag(s.bloque)
      +'<div class="sen-mut">'+esc(s.provincia||'')+'</div></div></div>'
      +'<div class="sen-kpis"><div class="sen-kpi"><b>'+P0.length+'</b><span>proyectos como autor/a</span></div>'
      +'<div class="sen-kpi"><b>'+C0.length+'</b><span>como coautor/a</span></div>'
      +'<div class="sen-kpi"><b>'+leyes+'</b><span>convertidos en ley</span></div>'
      +'<div class="sen-kpi"><b>'+M.length+'</b><span>comisiones</span></div>'
      +'<div class="sen-kpi"><b>'+D.length+'</b><span>dict&aacute;menes firmados</span></div></div>';
    h+='<div class="sen-sec"><h4>Comisiones</h4>'+(M.length?M.map(function(m){
      return '<span class="chip" style="cursor:default">'+esc(typeof nombreComCorto==='function'?nombreComCorto(m.c):m.c)+((m.rol&&m.rol!=='Vocal')?' &middot; '+esc(m.rol):'')+'</span> ';
    }).join(''):'<span class="ini-mut">Sin comisiones cargadas.</span>')+'</div>';
    h+='<div class="sen-sec"><h4>Proyectos</h4><div style="margin-bottom:10px">'
      +'<span class="chip'+(rolSel==='autor'?' on':'')+'" onclick="senRol(\'autor\')">Como autor/a ('+P0.length+')</span> '
      +'<span class="chip'+(rolSel==='coautor'?' on':'')+'" onclick="senRol(\'coautor\')">Como coautor/a ('+C0.length+')</span></div><div style="margin-bottom:10px">'
      +'<span class="chip'+(tipoSel?'':' on')+'" onclick="senTipo(\'\')">Todos ('+P.length+')</span> '
      +Object.keys(tipos).sort().map(function(t){return '<span class="chip'+(tipoSel===t?' on':'')+'" onclick="senTipo(\''+t+'\')">'+esc(t)+' ('+tipos[t]+')</span> ';}).join('')+'</div>'
      +(lst.slice(0,60).map(function(p){
        return '<div class="sen-proy" onclick="abrirFicha(\''+jsStr(claveP(p))+'\')">'+tagTipo(p.tipo)+'<b class="mono">'+esc(expNroOf(p))+'</b><span>'+esc((p.extracto||'').slice(0,150))+'</span><span class="ini-mut" style="margin-left:auto;white-space:nowrap">'+esc(p.fecha||'')+'</span></div>';
      }).join('')||'<span class="ini-mut">Sin proyectos.</span>')
      +(lst.length>60?'<div class="ini-mut" style="margin-top:8px">Mostrando 60 de '+lst.length+'. <a href="#" onclick="return senVerProyectos()">Ver todos en Proyectos &rarr;</a></div>':'')+'</div>';
    if(D.length)h+='<div class="sen-sec"><h4>Dict&aacute;menes que firm&oacute; (mayor&iacute;a)</h4>'+D.slice(0,30).map(function(o){
      return '<div class="sen-proy" onclick="return senAbrirOD('+AYUDA_MEMORIA.indexOf(o)+')"><span class="sen-tag" style="background:#E1ECF9;color:#0A3F7E">OD '+esc(o.numero)+'</span><span>'+esc((o.descripcion||'').slice(0,150))+'</span><span class="ini-mut" style="margin-left:auto">'+esc(o.fechaDictamen||'')+'</span></div>';}).join('')+'</div>';
    $('sen-lista').hidden=true;$('sen-ficha').hidden=false;$('sen-ficha').innerHTML=h;window.scrollTo(0,0);
  };
  window.senTipo=function(t){tipoSel=t;senAbrir(window.__senActual)};
  window.senRol=function(r){rolSel=r;tipoSel='';senAbrir(window.__senActual)};
  window.senVolver=function(){tipoSel='';rolSel='autor';$('sen-ficha').hidden=true;$('sen-lista').hidden=false;};
  window.senVerProyectos=function(){var s=buscar(window.__senActual);if(!s)return false;switchMain('proyectos');var el=$('search');if(el){el.value=bonito(s.nombre).split(' ').slice(-1)[0];el.dispatchEvent(new Event('input',{bubbles:true}));if(typeof onFilterChange==='function')onFilterChange();}return false;};
  window.senAbrirOD=function(i){switchMain('ayuda');if(typeof amOpenStory==='function'&&i>=0)amOpenStory(i);return false;};
  window.iniIr2=function(id,q,main){switchMain(main);var el=$(id);if(el){el.value=q;el.dispatchEvent(new Event('input',{bubbles:true}));}return false;};
  function init(){
    var bs={},ps={};SEN.forEach(function(s){if(s.bloque)bs[s.bloque]=1;if(s.provincia)ps[s.provincia]=1;});
    $('sen-bloque').innerHTML+=Object.keys(bs).sort().map(function(b){return '<option>'+esc(b)+'</option>'}).join('');
    $('sen-prov').innerHTML+=Object.keys(ps).sort().map(function(b){return '<option>'+esc(b)+'</option>'}).join('');
    ['sen-q','sen-bloque','sen-prov','sen-ex'].forEach(function(i){$(i).addEventListener(i==='sen-q'?'input':'change',lista)});
    lista();
  }
  var mb=document.querySelector('[data-main="senadores"]');
  if(mb)mb.addEventListener('click',function(){indices();lista();});
  try{init();}catch(e){}
})();
</script>"""

HEAD = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Schibsted+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">')


JS_NUEVO = """<script>
(function(){
  var b=document.body;
  try{if(localStorage.getItem('nd_colapsado')==='1')b.classList.add('nd-colapsado');}catch(e){}
  document.querySelectorAll('.mtab-btn').forEach(function(x){x.setAttribute('data-ini',(x.textContent.trim().slice(0,2)));x.title=x.textContent.trim();});
  var t=document.getElementById('nd-toggle');
  if(t)t.addEventListener('click',function(){
    var c=b.classList.toggle('nd-colapsado');
    try{localStorage.setItem('nd_colapsado',c?'1':'0');}catch(e){}
    t.textContent=c?'\u203A':'\u2039';
  });
  if(t&&b.classList.contains('nd-colapsado'))t.textContent='\u203A';
})();
</script>"""

def _cargar_senadores():
    import json
    try:
        d = json.load(open(os.path.join(ROOT, "data", "senadores.json"), encoding="utf-8"))
    except Exception:
        d = {}
    lst = [{"nombre": k, "bloque": v.get("bloque", ""), "provincia": v.get("provincia", ""),
            "vigente": bool(v.get("vigente", True))} for k, v in d.items()]
    return json.dumps(lst, ensure_ascii=False).replace("</", "<\\/")


def _cargar_noticias():
    import json
    try:
        d = json.load(open(os.path.join(ROOT, "data", "noticias.json"), encoding="utf-8"))
    except Exception:
        d = []
    return json.dumps(d, ensure_ascii=False).replace("</", "<\\/")


NOTICIAS_JS = r"""<script>
(function(){
  var NOT=__NOTICIAS__;
  if(!NOT.length||typeof abrirReunion!=='function')return;
  function nrm(t){return (t||'').toString().toUpperCase().normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/[^A-Z0-9 ]/g,' ').replace(/\s+/g,' ').trim();}
  function core(t){return nrm(t).replace(/^(DE LA |DE LOS |DE LAS |DE |DEL )/,'');}
  function iso(r){var d=r.fecha_iso?new Date(r.fecha_iso):null;if(!d||isNaN(d))return '';
    var z=function(n){return (n<10?'0':'')+n;};return d.getFullYear()+'-'+z(d.getMonth()+1)+'-'+z(d.getDate());}
  function mas(f,n){var d=new Date(f+'T12:00:00');d.setDate(d.getDate()+n);var z=function(x){return (x<10?'0':'')+x;};return d.getFullYear()+'-'+z(d.getMonth()+1)+'-'+z(d.getDate());}
  window.noticiasDeReunion=function(r){
    var f=iso(r);if(!f)return [];
    var cs=(r.comisiones||[]).map(core).filter(function(c){return c&&c.length>3;});
    var ok=[f,mas(f,1)];
    return NOT.filter(function(n){
      if(ok.indexOf(n.fecha)<0)return false;
      return (n.comisiones||[]).some(function(c){return cs.some(function(x){return x===c||x.indexOf(c)>=0||c.indexOf(x)>=0;});});
    }).sort(function(a,b){return (a.fecha===f?0:1)-(b.fecha===f?0:1);});
  };
  var orig=window.abrirReunion;
  window.abrirReunion=function(idx,sinHash){
    orig.apply(this,arguments);
    try{
      var r=AGENDA[idx],box=document.getElementById('agenda-noticia');
      var meta=document.getElementById('agenda-detalle-meta');if(!meta)return;
      if(!box){box=document.createElement('div');box.id='agenda-noticia';box.style.margin='10px 0';meta.parentNode.insertBefore(box,meta.nextSibling);}
      var ns=noticiasDeReunion(r);
      box.innerHTML=ns.map(function(n){return '<a class="bf-btn" style="margin:0 8px 6px 0;text-decoration:none" target="_blank" rel="noopener" href="'+esc(n.url)+'">&#128240; Ver noticia en senado.gob.ar'+(n.fecha!==iso(r)?' <span style="font-weight:500">(del '+esc(n.fecha.split('-').reverse().slice(0,2).join('/'))+')</span>':'')+(ns.length>1?' ('+esc(n.titulo.slice(0,40))+'&hellip;)':'')+'</a>';}).join('');
    }catch(e){}
  };
})();
</script>"""


def _fotos_embebidas():
    """Fotos de senadores como data-URI dentro del HTML, para que index_nuevo.html se vea completo
    aunque se abra sola (sin la carpeta data/fotos)."""
    import base64, json
    try:
        mapa = json.load(open(os.path.join(ROOT, "data", "fotos_senadores.json"), encoding="utf-8"))
    except Exception:
        return "{}"
    out = {}
    for arch in set(mapa.values()):
        f = os.path.join(ROOT, "data", "fotos", arch)
        if os.path.exists(f):
            ext = arch.rsplit(".", 1)[-1].lower().replace("jpg", "jpeg")
            out[arch] = "data:image/%s;base64,%s" % (ext, base64.b64encode(open(f, "rb").read()).decode())
    return json.dumps(out)



BORRAR_CSS = """
.bf-btn{display:inline-flex;align-items:center;gap:6px;border:1.5px solid #D6E4F0;background:#fff;color:#1B5EA2;border-radius:8px;padding:8px 12px;font:inherit;font-size:13px;font-weight:600;cursor:pointer;margin:0 0 10px 8px;white-space:nowrap}
.bf-btn:hover{background:#EEF4FB;border-color:#1B5EA2}
"""

BORRAR_JS = r"""<script>
(function(){
  function ev(el,t){if(el)el.dispatchEvent(new Event(t,{bubbles:true}));}
  function vac(id){var el=document.getElementById(id);if(!el)return;
    if(el.type==='checkbox'){if(el.checked){el.checked=false;ev(el,'change');}}
    else if(el.value!==''){el.value='';ev(el,el.tagName==='SELECT'?'change':'input');ev(el,'change');}}
  var ACC={
    proyectos:function(){
      try{resetBuscadorOnly();activeAnio='';activeTipos={};activeOrigen='';activeAcuerdoEstado='';
        setSelVal('origen-select','');setSelVal('tipo-select','');applyAll();}catch(e){}
    },
    comisiones:function(){['com-search','senador-search'].forEach(vac);},
    agenda:function(){['agenda-search','agenda-comision-select'].forEach(vac);
      try{agendaSearch='';agendaComision='';agendaOnFiltro();}catch(e){}},
    ayuda:function(){['am-search','am-comision-select','am-autor-select','am-bloque-select'].forEach(vac);},
    sanciones:function(){vac('sanc-search');try{setSancCat('TODOS');}catch(e){}},
    senadores:function(){['sen-q','sen-bloque','sen-prov','sen-ex'].forEach(vac);}
  };
  function boton(fn){var b=document.createElement('button');b.type='button';b.className='bf-btn';
    b.innerHTML='&#10005; Borrar filtros';b.onclick=fn;return b;}
  function poner(selector,fn,antes){
    var ref=document.querySelector(selector); if(!ref||ref.parentNode.querySelector(':scope > .bf-btn[data-bf="'+selector+'"]'))return;
    var b=boton(fn);b.setAttribute('data-bf',selector);
    if(antes)ref.parentNode.insertBefore(b,ref);else ref.parentNode.insertBefore(b,ref.nextSibling);
  }
  function init(){
    poner('#main-proyectos .filters-primary .checkbox-filter',ACC.proyectos);
    poner('#com-search',ACC.comisiones);
    poner('#agenda-comision-select',ACC.agenda,false);
    poner('#am-bloque-select',ACC.ayuda,false);
    poner('#sanc-search',ACC.sanciones);
    poner('#sen-cnt',ACC.senadores,true);
    var pj=document.getElementById('pj-btn-clear');
    if(pj){pj.className='bf-btn';pj.style.margin='0';pj.innerHTML='&#10005; Borrar filtros';}
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
  setTimeout(init,600);
})();
</script>"""

VOLVER_CSS = """
.vb-fab{position:fixed;right:22px;bottom:26px;z-index:900;width:54px;height:54px;border-radius:50%;border:none;background:#0A3F7E;color:#fff;box-shadow:0 6px 18px rgba(10,63,126,.4);cursor:pointer;display:none;align-items:center;justify-content:center;padding:0}
.vb-fab.on{display:flex}
.vb-fab:hover{background:#1B5EA2;transform:scale(1.06)}
.vb-fab svg{width:26px;height:26px}
@media (max-width:700px){.vb-fab{right:14px;bottom:18px;width:50px;height:50px}}
@media print{.vb-fab,.bf-btn{display:none!important}}
"""

VOLVER_JS = r"""<script>
(function(){
  var pila=[],actual=null,propio=false;
  function actualId(){var a=document.querySelector('.mtab-content.active');return a?a.id.replace(/^main-/,''):null;}
  var orig=window.activateMain;
  if(typeof orig!=='function')return;
  window.activateMain=function(id){
    var prev=actualId();
    var ok=orig.apply(this,arguments);
    if(ok&&!propio&&prev&&prev!==id){pila.push(prev);if(pila.length>40)pila.shift();}
    return ok;
  };
  function visible(id){var e=document.getElementById(id);return e&&!e.hidden&&e.offsetParent!==null;}
  window.volverAtras=function(){
    /* 1) cerrar lo que esté abierto encima de la pantalla */
    try{
      if(document.body.classList.contains('ficha-activa')&&typeof cerrarFichaReunion==='function'){cerrarFichaReunion();return;}
      var ag=document.getElementById('agenda-nivel2');
      if(ag&&ag.classList.contains('active')&&typeof volverAgenda==='function'){volverAgenda();return;}
      var sf=document.getElementById('sen-ficha');
      if(sf&&!sf.hidden&&typeof senVolver==='function'){senVolver();return;}
      var sc=document.getElementById('am-scrim');
      if(sc&&sc.classList.contains('open')&&typeof amCloseStory==='function'){amCloseStory();return;}
      var cal=document.getElementById('agenda-calendario-wrap');
      if(cal&&!cal.hidden&&actualId()==='agenda'&&typeof toggleAgendaVista==='function'){toggleAgendaVista('hoy');return;}
    }catch(e){}
    /* 2) volver a la sección anterior */
    var base=document.getElementById('main-inicio')?'inicio':'proyectos';
    var prev=pila.pop()||base;
    if(prev===actualId())prev=base;
    propio=true;try{window.activateMain(prev);}finally{propio=false;}
    try{history.replaceState({main:prev},'','#'+prev);}catch(e){}
    window.scrollTo({top:0});
  };
  var fab=null;
  function actualizar(){if(fab)fab.classList.toggle('on',actualId()!==(document.getElementById('main-inicio')?'inicio':'proyectos')&&actualId()!==null);}
  function init(){
    if(fab)return;
    fab=document.createElement('button');fab.type='button';fab.className='vb-fab no-print';
    fab.setAttribute('aria-label','Volver');fab.title='Volver';
    fab.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5"/><path d="m12 19-7-7 7-7"/></svg>';
    fab.onclick=function(){volverAtras();setTimeout(actualizar,50);};
    document.body.appendChild(fab);actualizar();
    setInterval(actualizar,400);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
</script>"""

FOTOS_JS = """<script>
(function(){
  var EMB=__FOTOS__;
  var orig=window.fotoSenadorUrl;
  if(typeof orig!=='function')return;
  window.fotoSenadorUrl=function(nombre){
    var u=orig(nombre);if(!u)return u;
    var arch=u.split('/').pop();
    return EMB[arch]||u;
  };
})();
</script>"""


MARCA_COMUNES = "<!--HSN-COMUNES-->"
FALLBACK_CSS = """
:root{--azul:#0A3F7E;--linea:#D5DEEA;--muted:#55657A}
.ini-mut{color:#55657A}
"""
_PARES = {
    "css": ("/*HSN-C-CSS*/", "/*HSN-C-CSS-FIN*/"),
    "js": ("<!--HSN-C-JS-->", "<!--HSN-C-JS-FIN-->"),
    "nav": ("<!--HSN-C-NAV-->", "<!--HSN-C-NAV-FIN-->"),
    "html": ("<!--HSN-C-HTML-->", "<!--HSN-C-HTML-FIN-->"),
}


def _env(k, texto):
    return _PARES[k][0] + texto + _PARES[k][1]


def quitar_comunes(s):
    """Saca lo agregado en una corrida anterior (para que 'Probar diseño' no duplique y
    refresque los datos embebidos: senadores, fotos, noticias)."""
    for a, b in _PARES.values():
        s = re.sub(re.escape(a) + r".*?" + re.escape(b), "", s, flags=re.S)
    return s


def aplicar_comunes(s):
    """Funciones que van en AMBOS diseños (anterior y nuevo): pestaña Senadores con fotos,
    botón Borrar filtros, botón Volver flotante y botón de noticia en la Agenda."""
    s = quitar_comunes(s)
    s = s.replace("</style>", _env("css", FALLBACK_CSS + SEN_CSS + BORRAR_CSS + VOLVER_CSS) + "\n</style>", 1)
    sen = _cargar_senadores()
    js = (FOTOS_JS.replace("__FOTOS__", _fotos_embebidas()) + SEN_JS.replace("__SENADORES__", sen)
          + BORRAR_JS + VOLVER_JS + NOTICIAS_JS.replace("__NOTICIAS__", _cargar_noticias()))
    s = s.replace("</body>", _env("js", js) + "</body>", 1)
    s = s.replace('<button class="mtab-btn" data-main="comisiones"',
                  _env("nav", '<button class="mtab-btn" data-main="senadores" onclick="switchMain(\'senadores\')">Senadores</button>\n    ')
                  + '<button class="mtab-btn" data-main="comisiones"', 1)
    marca = "<!-- ====================== MAIN: PROYECTOS"
    if marca in s:
        s = s.replace(marca, _env("html", SEN_HTML) + marca, 1)
    return s


def main():
    if not os.path.exists(SRC):
        sys.exit("No existe index.html: correr primero generar_web.py")
    s = open(SRC, encoding="utf-8").read()
    if "</style>" not in s or "</head>" not in s:
        sys.exit("Estructura inesperada del HTML")
    avisos = []
    # 1) diseño anterior (index.html): recibe las funciones comunes
    s = aplicar_comunes(s)
    open(SRC, "w", encoding="utf-8").write(s)
    # 2) diseño nuevo (index_nuevo.html): lo comun + Inicio y el estilo nuevo
    for var, idx in (("TIPO_FG", 0), ("TIPO_BG", 1), ("AM_TIPO_FG", 0), ("AM_TIPO_BG", 1)):
        pat = r"(var %s=\{)([^}]*)(\};)" % var
        if not re.search(pat, s):
            avisos.append(var); continue
        _, rep = mapa(var, idx)
        s = re.sub(pat, rep, s, count=1)
    s = s.replace("</style>", CSS + INICIO_CSS + "\n</style>", 1)
    s = s.replace("</head>", HEAD + "</head>", 1)
    s = s.replace('<div class="main-nav">',
                  '<button id="nd-toggle" class="nd-toggle" title="Plegar menú">‹</button><div class="main-nav">', 1)
    s = s.replace("</body>", INICIO_JS + SANC_JS + JS_NUEVO + "</body>", 1)
    s = s.replace('<button class="mtab-btn active" data-main="proyectos"',
                  '<button class="mtab-btn" data-main="inicio" onclick="switchMain(\'inicio\')">Inicio</button>\n    <button class="mtab-btn active" data-main="proyectos"', 1)
    marca = "<!-- ====================== MAIN: PROYECTOS"
    if marca in s:
        s = s.replace(marca, INICIO_HTML + marca, 1)
    else:
        avisos.append("seccion Inicio (no se encontro el marcador)")
    # link para volver al diseño anterior, al final de la barra lateral
    s = re.sub(r'(<div class="main-nav">.*?</div>)',
               r'\1<a class="nd-volver" href="index.html">← Ver diseño anterior</a>', s, count=1, flags=re.S)
    s = s.replace("<title>", "<title>[Nuevo] ", 1)
    open(DST, "w", encoding="utf-8").write(s)
    print("index.html (anterior) con funciones comunes; index_nuevo.html generado: %.2f MB" % (len(s.encode()) / 1048576))
    if avisos:
        print("AVISO: no se encontraron los mapas de color:", ", ".join(avisos))

if __name__ == "__main__":
    main()
