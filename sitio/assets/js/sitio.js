/* Sitio del 48.º FIMNME: menú, filtros de la agenda, «hoy», próximos eventos,
   archivo de calendario (.ics) y botón para volver arriba. Todo es una
   mejora: sin JavaScript el sitio muestra la programación completa. */
(function () {
  "use strict";

  // Fecha y hora actuales en la Ciudad de México («2026-11-06», «2026-11-06T20:00»)
  function ahoraCDMX() {
    try {
      var partes = new Intl.DateTimeFormat("en-CA", {
        timeZone: "America/Mexico_City", year: "numeric", month: "2-digit", day: "2-digit",
        hour: "2-digit", minute: "2-digit", hourCycle: "h23"
      }).formatToParts(new Date());
      var v = {};
      partes.forEach(function (p) { v[p.type] = p.value; });
      return { dia: v.year + "-" + v.month + "-" + v.day, momento: v.year + "-" + v.month + "-" + v.day + "T" + v.hour + ":" + v.minute };
    } catch (e) {
      var d = new Date(), z = function (n) { return (n < 10 ? "0" : "") + n; };
      var dia = d.getFullYear() + "-" + z(d.getMonth() + 1) + "-" + z(d.getDate());
      return { dia: dia, momento: dia + "T" + z(d.getHours()) + ":" + z(d.getMinutes()) };
    }
  }
  var ahora = ahoraCDMX();

  // Sin acentos ni mayúsculas, como el campo «buscar» que genera sitio.lua
  function clave(s) {
    return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").trim();
  }

  /* --- Menú en pantallas angostas ----------------------------------------- */
  var boton = document.querySelector(".menu-boton");
  var menu = document.getElementById("menu");
  if (boton && menu) {
    boton.addEventListener("click", function () {
      var abierto = menu.classList.toggle("abierto");
      boton.setAttribute("aria-expanded", abierto ? "true" : "false");
    });
  }

  /* --- Volver arriba ------------------------------------------------------ */
  var arriba = document.querySelector(".arriba");
  if (arriba) {
    window.addEventListener("scroll", function () {
      arriba.classList.toggle("visible", window.scrollY > 700);
    }, { passive: true });
  }

  /* --- «Hoy» en la agenda y en el calendario ------------------------------- */
  document.querySelectorAll('[data-fecha="' + ahora.dia + '"]').forEach(function (el) {
    el.classList.add("hoy");
  });

  /* --- Agenda: filtro por sección y búsqueda ------------------------------- */
  var agenda = document.querySelector(".agenda");
  if (agenda) {
    var chips = document.querySelectorAll(".chip[data-seccion]");
    var campo = document.getElementById("buscar");
    var resultado = document.querySelector(".filtro-resultado");
    var sinResultados = agenda.querySelector(".sin-resultados");
    var dias = agenda.querySelectorAll(".dia");
    var enlacesDia = document.querySelectorAll(".tira-dias a");
    var params = new URLSearchParams(location.search);
    var seccion = params.get("seccion") || "";
    if (params.get("q")) campo.value = params.get("q");

    function aplicar() {
      var palabras = clave(campo.value).split(/\s+/).filter(Boolean);
      var visibles = 0;
      dias.forEach(function (dia) {
        var hay = 0;
        dia.querySelectorAll(".tarjeta").forEach(function (t) {
          var ok = (!seccion || t.dataset.seccion === seccion) &&
            palabras.every(function (p) { return t.dataset.buscar.indexOf(p) !== -1; });
          t.hidden = !ok;
          if (ok) hay++;
        });
        dia.hidden = hay === 0;
        visibles += hay;
        enlacesDia.forEach(function (a) {
          if (a.dataset.fecha === dia.dataset.fecha) a.classList.toggle("vacio", hay === 0);
        });
      });
      chips.forEach(function (c) { c.setAttribute("aria-pressed", c.dataset.seccion === seccion ? "true" : "false"); });
      sinResultados.hidden = visibles > 0;
      var filtrado = seccion || palabras.length;
      resultado.textContent = filtrado ? visibles + (visibles === 1 ? " evento" : " eventos") : "";
      // la dirección conserva el filtro (para compartirla)
      var q = new URLSearchParams();
      if (seccion) q.set("seccion", seccion);
      if (campo.value.trim()) q.set("q", campo.value.trim());
      var nueva = location.pathname + (q.toString() ? "?" + q : "") + location.hash;
      history.replaceState(null, "", nueva);
    }

    chips.forEach(function (c) {
      c.addEventListener("click", function () { seccion = c.dataset.seccion; aplicar(); });
    });
    campo.addEventListener("input", aplicar);
    aplicar();

    // el día que se está viendo, resaltado en la tira de días
    if ("IntersectionObserver" in window) {
      var obs = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (e) {
          if (!e.isIntersecting) return;
          enlacesDia.forEach(function (a) {
            var activo = a.dataset.fecha === e.target.dataset.fecha;
            a.classList.toggle("activo", activo);
            if (activo && a.scrollIntoView && a.parentNode.scrollWidth > a.parentNode.clientWidth) {
              a.parentNode.scrollTo({ left: a.offsetLeft - 40, behavior: "smooth" });
            }
          });
        });
      }, { rootMargin: "-45% 0px -50% 0px" });
      dias.forEach(function (d) { obs.observe(d); });
    }
  }

  /* --- Inicio: próximos eventos -------------------------------------------- */
  var proximos = document.querySelector("[data-proximos]");
  if (proximos) {
    var tarjetas = Array.prototype.slice.call(proximos.querySelectorAll(".tarjeta[data-inicio]"));
    var futuras = tarjetas.filter(function (t) { return t.dataset.inicio >= ahora.momento; });
    futuras.sort(function (a, b) { return a.dataset.inicio < b.dataset.inicio ? -1 : 1; });
    if (futuras.length) {
      var primerDia = futuras[0].dataset.inicio.slice(0, 10);
      var titulo = proximos.querySelector("[data-proximos-titulo]");
      if (primerDia === ahora.dia) titulo.textContent = "Hoy y próximos eventos";
      futuras.slice(0, 6).forEach(function (t) { t.classList.add("mostrar"); });
      proximos.hidden = false;
    }
  }

  /* --- Archivo de calendario (.ics) junto al enlace de Google Calendar ------ */
  document.querySelectorAll("a.calendario[data-inicio]").forEach(function (a) {
    var ics = document.createElement("a");
    ics.className = "boton boton-claro";
    ics.textContent = "Archivo .ics";
    ics.title = "Para Apple Calendar, Outlook y otros";
    ics.href = "#";
    ics.addEventListener("click", function (ev) {
      ev.preventDefault();
      var esc = function (s) { return s.replace(/\\/g, "\\\\").replace(/([,;])/g, "\\$1"); };
      var texto = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//INBAL//48 FIMNME//ES", "BEGIN:VEVENT",
        "UID:" + a.dataset.inicio + "-" + a.dataset.url.replace(/[^a-z0-9]/gi, "") + "@fimnme",
        "DTSTAMP:" + new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d+/, ""),
        "DTSTART;TZID=America/Mexico_City:" + a.dataset.inicio,
        "DTEND;TZID=America/Mexico_City:" + a.dataset.fin,
        "SUMMARY:" + esc(a.dataset.titulo + " · 48.º FIMNME"),
        "LOCATION:" + esc(a.dataset.lugar),
        "URL:" + a.dataset.url,
        "DESCRIPTION:" + esc(a.dataset.url),
        "END:VEVENT", "END:VCALENDAR"
      ].join("\r\n");
      var blob = new Blob([texto], { type: "text/calendar;charset=utf-8" });
      var url = URL.createObjectURL(blob);
      var d = document.createElement("a");
      d.href = url;
      d.download = "fimnme-" + a.dataset.inicio.slice(0, 8) + ".ics";
      document.body.appendChild(d);
      d.click();
      setTimeout(function () { URL.revokeObjectURL(url); d.remove(); }, 500);
    });
    a.parentNode.insertBefore(ics, a.nextSibling);
    a.textContent = "Google Calendar";
  });

  /* --- Índice de la página del evento: sección visible ---------------------- */
  var indice = document.querySelectorAll(".indice a");
  if (indice.length && "IntersectionObserver" in window) {
    var obsIndice = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (e) {
        if (!e.isIntersecting) return;
        indice.forEach(function (a) { a.classList.toggle("activo", a.getAttribute("href") === "#" + e.target.id); });
      });
    }, { rootMargin: "-30% 0px -60% 0px" });
    indice.forEach(function (a) {
      var s = document.getElementById(a.getAttribute("href").slice(1));
      if (s) obsIndice.observe(s);
    });
  }

  /* --- Abrir la nota al programa si se llega con su ancla ------------------- */
  function abrirNota() {
    if (location.hash.indexOf("#nota-") === 0) {
      var n = document.getElementById(location.hash.slice(1));
      if (n && n.tagName === "DETAILS") n.open = true;
    }
  }
  window.addEventListener("hashchange", abrirNota);
  abrirNota();
})();
