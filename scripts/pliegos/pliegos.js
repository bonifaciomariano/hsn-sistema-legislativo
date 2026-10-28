/* ── Pliegos judiciales ───────────────────────────────────────────────────
   Port nativo del navegador de https://github.com/bonifaciomariano/Pliegos-Poder-Judicial
   (template.html). La lógica de filtros/pestañas/estadísticas/línea de tiempo
   es la original; cambian los ids (prefijo pj-), los nombres de clase (.pj-*),
   la fuente de datos (PLIEGOS_DATA, embebida al construir desde el
   pliegos_data.json del repo de origen) y se suman los deep links:
     #pliegos                 -> la pestaña
     #pliegos/PE-293-26       -> abre el modal de ese expediente (PE-293/26)
   Cuando cambie la UI en el repo de origen hay que re-portar a mano; los
   DATOS, en cambio, se actualizan solos (ver cargar_pliegos() en generar_web.py). */
(function () {
  "use strict";
  var DATA = (typeof PLIEGOS_DATA !== "undefined" && PLIEGOS_DATA) || { pliegos: [], provincias: [], total: 0 };
  var pliegos = DATA.pliegos || [];

  var CATEGORIES = [
    { key: "todos", label: "Todos" },
    { key: "dar_cuenta", label: "Para dar cuenta" },
    { key: "sin_audiencia", label: "En comisión" },
    { key: "con_od", label: "Con Orden del Día" },
    { key: "sancionado", label: "Sancionado" },
    { key: "rechazado", label: "Rechazado" },
    { key: "stats", label: "📊 Estadísticas", noCount: true }
  ];
  var PILL_META = {
    dar_cuenta: { cls: "pendiente", label: "Para dar cuenta" },
    sin_audiencia: { cls: "comision", label: "En comisión" },
    con_od: { cls: "od", label: "Con Orden del Día" },
    sancionado: { cls: "sancion", label: "Sancionado" },
    rechazado: { cls: "rechazo", label: "Rechazado" }
  };
  var RANGO_ORDEN = [
    "Corte Suprema", "Procurador/a General", "Conjueces", "Defensor/a",
    "Fiscal", "Camarista / Vocal de Cámara", "Juez/a (primera instancia)",
    "Sin rango (mensaje administrativo)"
  ];
  var FUERO_ORDEN = [
    "Penal", "Penal Económico", "Casación Penal", "Menores", "Familia",
    "Seguridad Social", "Laboral", "Contencioso Administrativo", "Comercial",
    "Civil", "Ejecuciones Fiscales / Tributario", "Otros"
  ];

  var state = { categoria: "todos", provincia: "", rango: "", fuero: "", q: "", soloProgramada: false };

  var $ = function (id) { return document.getElementById(id); };
  var elTabs = $("pj-tabs"), elGrid = $("pj-grid"), elEmpty = $("pj-empty"), elEmptyMsg = $("pj-empty-msg");
  var elResultCount = $("pj-result-count"), elSearch = $("pj-search");
  var elProvincia = $("pj-provincia"), elRango = $("pj-rango"), elFuero = $("pj-fuero");
  var elToggle = $("pj-toggle-programada"), elToggleWrap = $("pj-toggle-wrap");
  var elHint = $("pj-hint"), elStats = $("pj-stats-panel"), elFilterRow = $("pj-filter-row");
  var elBtnClear = $("pj-btn-clear");
  var elOverlay = $("pj-modal-overlay"), elMExp = $("pj-modal-expediente"), elMTitle = $("pj-modal-title");
  var elMCargo = $("pj-modal-cargo"), elMBadge = $("pj-modal-badge"), elMTimeline = $("pj-modal-timeline");
  var elMLink = $("pj-modal-link"), elMClose = $("pj-modal-close");
  if (!elTabs || !elGrid) return;

  function escapeHTML(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function formatFecha(iso) {
    var parts = String(iso || "").split("-");
    if (parts.length !== 3) return iso;
    var d = new Date(Date.UTC(+parts[0], +parts[1] - 1, +parts[2]));
    var meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
    return d.getUTCDate() + " de " + meses[d.getUTCMonth()] + " de " + d.getUTCFullYear();
  }

  if (elHint) {
    elHint.textContent = pliegos.length
      ? "Gestión Milei · " + (DATA.total || pliegos.length) + " pliegos" + (DATA.generado_al ? " · datos al " + formatFecha(DATA.generado_al) : "")
      : "Pliegos del Poder Judicial en trámite";
  }

  (DATA.provincias || []).forEach(function (p) {
    var opt = document.createElement("option");
    opt.value = p; opt.textContent = p;
    elProvincia.appendChild(opt);
  });
  function poblarSelect(el, campo, valoresOrdenados) {
    var presentes = {};
    pliegos.forEach(function (p) { presentes[p[campo]] = true; });
    valoresOrdenados.filter(function (v) { return presentes[v]; }).forEach(function (v) {
      var opt = document.createElement("option");
      opt.value = v; opt.textContent = v;
      el.appendChild(opt);
    });
  }
  poblarSelect(elRango, "rango", RANGO_ORDEN);
  poblarSelect(elFuero, "fuero", FUERO_ORDEN);

  function counts() {
    var c = { todos: pliegos.length, dar_cuenta: 0, sin_audiencia: 0, con_od: 0, sancionado: 0, rechazado: 0 };
    pliegos.forEach(function (p) { if (c[p.categoria] != null) c[p.categoria]++; });
    return c;
  }

  function renderTabs() {
    var c = counts();
    elTabs.innerHTML = "";
    CATEGORIES.forEach(function (cat) {
      var btn = document.createElement("button");
      btn.className = "pj-tab";
      btn.type = "button";
      btn.setAttribute("role", "tab");
      btn.setAttribute("aria-selected", state.categoria === cat.key ? "true" : "false");
      btn.innerHTML = cat.label + (cat.noCount ? "" : ' <span class="pj-count">' + c[cat.key] + "</span>");
      btn.addEventListener("click", function () {
        state.categoria = cat.key;
        if (cat.key !== "sin_audiencia") { state.soloProgramada = false; elToggle.checked = false; }
        renderTabs();
        renderView();
      });
      elTabs.appendChild(btn);
    });
  }

  function renderView() {
    var isStats = state.categoria === "stats";
    elFilterRow.style.display = isStats ? "none" : "flex";
    elToggleWrap.style.display = (!isStats && state.categoria === "sin_audiencia") ? "flex" : "none";
    elResultCount.style.display = isStats ? "none" : "block";
    elGrid.style.display = isStats ? "none" : "grid";
    elStats.style.display = isStats ? "block" : "none";
    if (isStats) { elEmpty.style.display = "none"; renderStats(); }
    else renderGrid();
  }

  function odHaystack(p) {
    var od = p.timeline && p.timeline.orden_del_dia;
    if (!od) return "";
    return "od " + od.numero + " " + od.numero + "/" + od.anio;
  }

  function matches(p) {
    if (state.categoria !== "todos" && p.categoria !== state.categoria) return false;
    if (state.provincia && p.provincia !== state.provincia) return false;
    if (state.rango && p.rango !== state.rango) return false;
    if (state.fuero && p.fuero !== state.fuero) return false;
    if (state.soloProgramada && !p.audiencia_programada) return false;
    if (state.q) {
      var haystack = (p.candidato + " " + p.cargo + " " + p.expediente + " " + p.provincia + " " + odHaystack(p)).toLowerCase();
      if (haystack.indexOf(state.q) === -1) return false;
    }
    return true;
  }

  function cardHTML(p) {
    var meta = PILL_META[p.categoria] || PILL_META.sin_audiencia;
    var pillLabel = meta.label;
    if (p.categoria === "con_od" && p.timeline && p.timeline.orden_del_dia && p.timeline.orden_del_dia.numero) {
      var od = p.timeline.orden_del_dia;
      pillLabel = "OD " + od.numero + (od.anio ? "/" + String(od.anio).slice(-2) : "");
    }
    var badge = "";
    if (p.audiencia_programada) {
      var ap = p.audiencia_programada;
      badge = '<span class="pj-badge-audiencia"><span class="pj-dot"></span>Audiencia ' + escapeHTML(ap.fecha) + " · " + escapeHTML(ap.hora) + "h · Salón " + escapeHTML(ap.salon) + "</span>";
    } else if (p.audiencia_sin_dictamen) {
      badge = '<span class="pj-badge-audiencia sin-dictamen"><span class="pj-dot"></span>Audiencia realizada, dictamen pendiente</span>';
    }
    return (
      '<button type="button" class="pj-card" data-expediente="' + escapeHTML(p.expediente) + '">' +
        '<div class="pj-card-top">' +
          '<span class="pj-expediente">' + escapeHTML(p.expediente) + "</span>" +
          '<span class="pj-pill ' + meta.cls + '">' + escapeHTML(pillLabel) + "</span>" +
        "</div>" +
        "<div>" +
          '<div class="pj-candidato">' + escapeHTML(p.candidato) + "</div>" +
          '<div class="pj-cargo">' + escapeHTML(p.cargo) + "</div>" +
        "</div>" +
        '<div class="pj-card-bottom"><span class="pj-provincia-tag">' + escapeHTML(p.provincia) + "</span></div>" +
        (badge ? "<div>" + badge + "</div>" : "") +
      "</button>"
    );
  }

  function renderGrid() {
    if (!pliegos.length) {
      elGrid.innerHTML = "";
      elResultCount.textContent = "";
      elEmptyMsg.textContent = "No hay datos de pliegos disponibles por el momento.";
      elEmpty.style.display = "block";
      return;
    }
    var list = pliegos.filter(matches);
    elResultCount.textContent = list.length + (list.length === 1 ? " pliego encontrado" : " pliegos encontrados");
    if (!list.length) {
      elGrid.innerHTML = "";
      elEmptyMsg.textContent = "No hay pliegos que coincidan con estos filtros.";
      elEmpty.style.display = "block";
      return;
    }
    elEmpty.style.display = "none";
    elGrid.innerHTML = list.map(cardHTML).join("");
    Array.prototype.forEach.call(elGrid.querySelectorAll(".pj-card"), function (card) {
      card.addEventListener("click", function () { openModal(card.getAttribute("data-expediente")); });
    });
  }

  // --- Estadísticas ---
  function diffDias(desde, hasta) {
    var pd = desde.split("/"), ph = hasta.split("/");
    return Math.round((Date.UTC(+ph[2], +ph[1] - 1, +ph[0]) - Date.UTC(+pd[2], +pd[1] - 1, +pd[0])) / 86400000);
  }

  function renderStats() {
    var c = counts();
    var total = c.todos || 1;
    var pctSancion = Math.round((c.sancionado / total) * 100);
    var conProgramada = pliegos.filter(function (p) { return p.audiencia_programada; }).length;

    var porProvincia = {};
    pliegos.forEach(function (p) { porProvincia[p.provincia] = (porProvincia[p.provincia] || 0) + 1; });
    var provinciasOrdenadas = Object.keys(porProvincia)
      .map(function (nombre) { return { nombre: nombre, n: porProvincia[nombre] }; })
      .sort(function (a, b) { return b.n - a.n; });

    var duraciones = [];
    pliegos.forEach(function (p) {
      var t = p.timeline;
      if (t && t.ingreso && t.sancion) duraciones.push(diffDias(t.ingreso, t.sancion));
    });
    var duracionPromedio = duraciones.length
      ? Math.round(duraciones.reduce(function (a, b) { return a + b; }, 0) / duraciones.length) : null;

    var cards = [
      { value: total, label: "Total de pliegos judiciales", cls: "" },
      { value: c.sancionado, small: pctSancion + "%", label: "Sancionados (aprobados)", cls: "accent-sancion" },
      { value: c.dar_cuenta, label: "Para dar cuenta en el recinto", cls: "accent-pendiente" },
      { value: c.con_od, label: "Con Orden del Día emitido", cls: "accent-od" },
      { value: c.sin_audiencia, label: "En comisión, sin audiencia", cls: "accent-comision" },
      { value: c.rechazado, label: "Rechazados", cls: "accent-rechazo" },
      { value: conProgramada, label: "Con audiencia pública programada", cls: "accent-live" },
      { value: provinciasOrdenadas.length, label: "Jurisdicciones representadas", cls: "" }
    ];
    if (duracionPromedio !== null) {
      cards.push({ value: duracionPromedio, small: "días", label: "Trámite promedio: ingreso → sanción", cls: "" });
    }
    var cardsHTML = cards.map(function (s) {
      return '<div class="pj-stat-card ' + s.cls + '"><div class="pj-stat-value">' + s.value +
        (s.small ? " <small>" + s.small + "</small>" : "") + '</div><div class="pj-stat-label">' + s.label + "</div></div>";
    }).join("");

    function barRowsHTML(items) {
      var max = items.length ? Math.max.apply(null, items.map(function (i) { return i.n; })) : 1;
      return items.map(function (it) {
        var pct = Math.round((it.n / max) * 100);
        return '<div class="pj-bar-row"><div class="pj-bar-name">' + escapeHTML(it.nombre) + '</div>' +
          '<div class="pj-bar-track"><div class="pj-bar-fill" style="width:' + pct + '%"></div></div>' +
          '<div class="pj-bar-count">' + it.n + "</div></div>";
      }).join("");
    }
    function countsByOrder(campo, orden) {
      var cnt = {};
      pliegos.forEach(function (p) { cnt[p[campo]] = (cnt[p[campo]] || 0) + 1; });
      return orden.filter(function (v) { return cnt[v]; }).map(function (v) { return { nombre: v, n: cnt[v] }; });
    }

    elStats.innerHTML =
      '<div class="pj-stats-grid">' + cardsHTML + "</div>" +
      '<p class="pj-stats-title">Pliegos por jurisdicción</p><div class="pj-bars">' + barRowsHTML(provinciasOrdenadas) + "</div>" +
      '<p class="pj-stats-title">Pliegos por rango</p><div class="pj-bars">' + barRowsHTML(countsByOrder("rango", RANGO_ORDEN)) + "</div>" +
      '<p class="pj-stats-title">Pliegos por fuero</p><div class="pj-bars">' + barRowsHTML(countsByOrder("fuero", FUERO_ORDEN)) + "</div>";
  }

  // --- Modal (línea de tiempo) ---
  function timelineHTML(p) {
    var t = p.timeline || {};
    var steps = [];
    steps.push({ label: "Ingreso a la comisión", value: t.ingreso || "Sin registrar", done: !!t.ingreso });
    var dc = t.dado_cuenta;
    steps.push({ label: "Dado cuenta en el recinto", value: dc && dc.fecha ? dc.fecha : "Pendiente", done: !!(dc && dc.fecha) });
    steps.push({ label: "Audiencia pública", value: t.audiencia || "Sin realizar", done: !!t.audiencia });

    var odValue = "Sin emitir";
    if (t.orden_del_dia) {
      odValue = "N° " + t.orden_del_dia.numero + "/" + String(t.orden_del_dia.anio).slice(-2);
      if (t.orden_del_dia.fecha_dictamen) {
        odValue += " · (" + t.orden_del_dia.fecha_dictamen.replace(/\/(\d{4})$/, function (m, y) { return "/" + y.slice(-2); }) + ")";
      }
    }
    var odExtra = "";
    if (t.orden_del_dia && t.orden_del_dia.firmantes && t.orden_del_dia.firmantes.length) {
      odExtra = '<div class="pj-step-firmantes">Firmantes del dictamen: ' + escapeHTML(t.orden_del_dia.firmantes.join(", ")) + "</div>";
    }
    steps.push({ label: "Orden del Día", value: odValue, done: !!t.orden_del_dia, extra: odExtra });
    steps.push({
      label: t.rechazo ? "Rechazado por el Senado" : "Sanción del Senado",
      value: t.rechazo ? t.rechazo : (t.sancion ? t.sancion : "Pendiente"),
      done: !!t.sancion, rejected: !!t.rechazo
    });

    var activeMarked = false;
    return steps.map(function (s) {
      var cls = s.rejected ? "rejected" : (s.done ? "done" : "");
      if (!s.done && !s.rejected && !activeMarked) { cls = "active"; activeMarked = true; }
      return '<li class="' + cls + '"><div class="pj-step-label">' + s.label + "</div>" +
        '<div class="pj-step-value' + (s.done || s.rejected ? "" : " muted") + '">' + escapeHTML(s.value) + "</div>" +
        (s.extra || "") + "</li>";
    }).join("");
  }

  function slugDe(expediente) { return String(expediente).replace(/\//g, "-"); }
  function pliegoPorSlug(slug) {
    return pliegos.filter(function (x) { return slugDe(x.expediente) === slug; })[0] || null;
  }

  var lastFocused = null;
  function onKeydown(e) { if (e.key === "Escape") closeModal(); }

  function openModal(expediente, sinHash) {
    var p = pliegos.filter(function (x) { return x.expediente === expediente; })[0];
    if (!p) return;
    lastFocused = document.activeElement;
    elMExp.textContent = p.expediente;
    elMTitle.textContent = p.candidato;
    elMCargo.textContent = p.cargo + " — " + p.provincia;
    elMTimeline.innerHTML = timelineHTML(p);
    elMLink.href = p.url;
    if (p.audiencia_programada) {
      var ap = p.audiencia_programada;
      elMBadge.style.display = "flex";
      elMBadge.innerHTML = "📅 Audiencia pública programada: " + escapeHTML(ap.fecha) + " · " + escapeHTML(ap.hora) + " h · Salón " + escapeHTML(ap.salon);
    } else {
      elMBadge.style.display = "none";
    }
    elOverlay.classList.add("open");
    elMClose.focus();
    document.addEventListener("keydown", onKeydown);
    if (!sinHash) {
      var h = "#pliegos/" + slugDe(p.expediente);
      if (location.hash !== h) history.pushState({}, "", h);
    }
  }

  function closeModal(sinHash) {
    if (!elOverlay.classList.contains("open")) return;
    elOverlay.classList.remove("open");
    document.removeEventListener("keydown", onKeydown);
    if (lastFocused && lastFocused.focus) lastFocused.focus();
    if (sinHash !== true && location.hash.indexOf("#pliegos/") === 0) history.pushState({}, "", "#pliegos");
  }

  elMClose.addEventListener("click", function () { closeModal(); });
  elOverlay.addEventListener("click", function (e) { if (e.target === elOverlay) closeModal(); });

  // --- Filtros ---
  var searchTimer = null;
  elSearch.addEventListener("input", function () {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(function () { state.q = elSearch.value.trim().toLowerCase(); renderGrid(); }, 120);
  });
  elProvincia.addEventListener("change", function () { state.provincia = elProvincia.value; renderGrid(); });
  elRango.addEventListener("change", function () { state.rango = elRango.value; renderGrid(); });
  elFuero.addEventListener("change", function () { state.fuero = elFuero.value; renderGrid(); });
  elToggle.addEventListener("change", function () { state.soloProgramada = elToggle.checked; renderGrid(); });
  elBtnClear.addEventListener("click", function () {
    state.provincia = state.rango = state.fuero = state.q = "";
    state.soloProgramada = false;
    elSearch.value = ""; elProvincia.value = ""; elRango.value = ""; elFuero.value = "";
    elToggle.checked = false;
    renderGrid();
  });

  // Deep links: llamado al cargar y en cada popstate (ver generar_web.py).
  // Devuelve true si el hash es de esta sección (así el ruteo general no lo pisa).
  window.pjSyncHash = function () {
    var h = location.hash || "";
    if (h !== "#pliegos" && h.indexOf("#pliegos/") !== 0) { closeModal(true); return false; }
    activateMain("pliegos");
    var m = h.match(/^#pliegos\/(.+)$/);
    if (m) {
      var p = pliegoPorSlug(decodeURIComponent(m[1]));
      if (p) openModal(p.expediente, true); else closeModal(true);
    } else {
      closeModal(true);
    }
    return true;
  };

  renderTabs();
  renderView();
})();
