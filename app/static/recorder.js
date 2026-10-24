// Enregistreur du test de niveau (oral) : 3 réponses d'1 minute au plus, envoyées une par une.
(function () {
  var box = document.getElementById("recorder");
  if (!box) return;
  var L = box.dataset, MAX = 60;
  var types = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];
  var mime = window.MediaRecorder ? types.filter(function (t) { return MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(t); })[0] : null;
  if (!navigator.mediaDevices || !window.MediaRecorder) { box.querySelector(".pt-nomic").hidden = false; box.querySelectorAll(".pt-rec-btn").forEach(function (b) { b.disabled = true; }); return; }
  var current = null;
  box.querySelectorAll(".pt-task").forEach(function (task) {
    var btn = task.querySelector(".pt-rec-btn"), timer = task.querySelector(".pt-timer"), play = task.querySelector(".pt-play");
    btn.addEventListener("click", function () {
      if (current && current.task === task) { current.rec.stop(); return; }
      if (current) return; // un enregistrement à la fois
      navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
        var chunks = [], rec = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined), left = MAX;
        current = { task: task, rec: rec };
        btn.textContent = L.lStop; btn.classList.replace("btn-red", "btn-navy");
        timer.textContent = "● " + left + " s";
        var tick = setInterval(function () { left -= 1; timer.textContent = "● " + left + " s"; if (left <= 0) rec.stop(); }, 1000);
        rec.ondataavailable = function (e) { if (e.data.size) chunks.push(e.data); };
        rec.onstop = function () {
          clearInterval(tick); stream.getTracks().forEach(function (t) { t.stop(); });
          current = null; btn.classList.replace("btn-navy", "btn-red"); btn.textContent = L.lRedo;
          var blob = new Blob(chunks, { type: rec.mimeType || mime || "audio/webm" });
          play.src = URL.createObjectURL(blob); play.hidden = false;
          timer.textContent = L.lUp;
          var fd = new FormData(); fd.append("csrf", L.csrf); fd.append("audio", blob, "rec");
          fetch(task.dataset.url, { method: "POST", body: fd, credentials: "same-origin" })
            .then(function (r) { timer.textContent = r.ok ? "✓ " + L.lSaved : L.lErr; })
            .catch(function () { timer.textContent = L.lErr; });
        };
        rec.start();
      }).catch(function () { box.querySelector(".pt-nomic").hidden = false; });
    });
  });
})();
