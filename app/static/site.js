// Menu sur petit écran : le bouton ☰ ouvre / ferme la navigation (indépendant des animations)
(function () {
  var header = document.querySelector(".site-header.public");
  var btn = header && header.querySelector(".menu-btn");
  if (!btn) return;
  function set(open) { header.classList.toggle("open", open); btn.setAttribute("aria-expanded", open ? "true" : "false"); }
  btn.addEventListener("click", function () { set(!header.classList.contains("open")); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && header.classList.contains("open")) { set(false); btn.focus(); } });
  header.querySelectorAll(".nav a").forEach(function (a) { a.addEventListener("click", function () { set(false); }); });
})();

// Sous-menus de la barre (课程体系 → 法语与证书) : clic sur ▾, Échap ou clic ailleurs pour fermer
(function () {
  var groups = document.querySelectorAll(".nav-group");
  function close(gr) { gr.classList.remove("open"); gr.querySelector(".sub-toggle").setAttribute("aria-expanded", "false"); }
  groups.forEach(function (gr) {
    var b = gr.querySelector(".sub-toggle");
    b.addEventListener("click", function (e) { e.stopPropagation(); var o = !gr.classList.contains("open"); groups.forEach(close); if (o) { gr.classList.add("open"); b.setAttribute("aria-expanded", "true"); } });
    gr.addEventListener("keydown", function (e) { if (e.key === "Escape") { close(gr); b.focus(); } });
  });
  document.addEventListener("click", function (e) { groups.forEach(function (gr) { if (!gr.contains(e.target)) close(gr); }); });
})();

// Animations avec Motion (vanilla, static/vendor/motion.js, MIT). Rien ne bouge si l'utilisateur a demandé moins de mouvement.
(function () {
  window.__mdfAnim = true;
  var M = window.Motion;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!M || reduce) {
    document.documentElement.classList.remove("js");
    return;
  }
  var ease = [0.22, 1, 0.36, 1];

  // Hero : la classe apparaît, puis les élèves un par un, puis l'élève qui lève la main
  var visual = document.querySelector(".hero-visual");
  if (visual) {
    M.animate(visual, { opacity: [0, 1], y: [32, 0] }, { duration: 0.8, delay: 0.15, ease: ease });
    M.animate(".pupils div", { opacity: [0, 1], scale: [0.85, 1] }, { delay: M.stagger(0.08, { startDelay: 0.6 }), duration: 0.4 });
    M.animate(".pupils .talk", { scale: [1, 1.08, 1] }, { delay: 1.4, duration: 0.6 });
  }

  // Sections : montée douce à l'entrée dans l'écran ; les grilles de cartes en cascade
  M.inView("[data-reveal]", function (info) {
    var el = info.target || info;
    var kids = el.matches(".grid") ? el.children : null;
    M.animate(el, { opacity: [0, 1], y: [24, 0] }, { duration: 0.7, ease: ease });
    if (kids && kids.length) {
      M.animate(kids, { opacity: [0, 1], y: [16, 0] }, { delay: M.stagger(0.08), duration: 0.5, ease: ease });
    }
  }, { amount: 0.2 });
})();

// Filtres : repliés par défaut sur petit écran, toujours ouverts sur grand écran
(function () {
  var boxes = document.querySelectorAll(".filters-box");
  if (!boxes.length) return;
  var mq = window.matchMedia("(max-width: 900px)");
  function sync() { boxes.forEach(function (b) { if (mq.matches) { if (!b.dataset.touched) b.open = !!b.querySelector(".filters-dot"); } else { b.open = true; } }); }
  boxes.forEach(function (b) {
    b.querySelector("summary").addEventListener("click", function (e) { if (!mq.matches) e.preventDefault(); else b.dataset.touched = "1"; });
  });
  sync();
  (mq.addEventListener ? mq.addEventListener("change", sync) : mq.addListener(sync));
})();
