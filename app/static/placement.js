// Test de niveau : le bouton « Suivant » n'est actif que quand tout est répondu (le serveur vérifie aussi).
(function () {
  // QCM : une réponse par question
  var form = document.querySelector(".pt-qcm");
  if (form) {
    var total = +form.dataset.total, next = form.querySelector("[data-next]"), done = form.querySelector("[data-done]");
    var update = function () {
      var names = {};
      form.querySelectorAll('input[type=radio]:checked').forEach(function (i) { names[i.name] = 1; });
      var n = Object.keys(names).length;
      done.textContent = n;
      next.disabled = n < total;
      form.querySelectorAll(".pt-q").forEach(function (q) { if (q.querySelector("input:checked")) { q.classList.remove("pt-missing"); var m = q.querySelector(".pt-miss-msg"); if (m) m.remove(); } });
    };
    form.addEventListener("change", update);
    update();
    var first = form.querySelector(".pt-missing");
    if (first) first.scrollIntoView({ block: "center" });
  }
  // Rédaction : nombre de mots en français
  var ta = document.querySelector(".pt-form textarea[name=writing]"), wc = document.getElementById("wc");
  if (ta && wc) {
    var need = +document.querySelector(".pt-wc").dataset.need, btn = ta.form.querySelector("[data-next]");
    var count = function () {
      var words = (ta.value.match(/[A-Za-zÀ-ÖØ-öø-ÿŒœ'’-]+/g) || []).filter(function (w) { return /[A-Za-zÀ-ÿ]/.test(w) && (w.length === 1 || new Set(w.toLowerCase()).size > 1); });
      wc.textContent = words.length;
      wc.style.color = words.length >= need ? "#1F5A33" : "";
      btn.disabled = words.length < need;
    };
    ta.addEventListener("input", count);
    count();
  }
})();
