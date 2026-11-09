// Salle de classe en direct de Maison du français (moteur LiveKit, client livekit-client 2.23 servi depuis /static/vendor).
// Rôles : teacher, student (caméra + micro), trial (essai : parle si le professeur l'invite), parent et observer (écoute seule).
(function () {
  "use strict";
  var LK = window.LivekitClient;
  var cfg = JSON.parse(document.getElementById("cr-config").textContent);
  var x = cfg.x, $ = function (id) { return document.getElementById(id); };
  var Track = LK.Track, RoomEvent = LK.RoomEvent;
  var room = null, hands = {}, unread = 0, joining = false;
  var canTalk = cfg.role === "teacher" || cfg.role === "student";

  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function roleOf(p) { try { return JSON.parse(p.metadata || "{}").role || "student"; } catch (e) { return "student"; } }
  function status(msg, kind) { var s = $("cr-status"); s.textContent = msg || ""; s.className = "cr-status" + (kind ? " " + kind : ""); }
  function banner(msg, ms) {
    var b = $("cr-banner"); b.textContent = msg; b.hidden = false;
    clearTimeout(banner.t); banner.t = setTimeout(function () { b.hidden = true; }, ms || 6000);
  }

  // ---------- avant d'entrer : aperçu caméra, niveau du micro, choix des appareils ----------
  var preview = null, meterStop = null;
  async function startPreview() {
    if (!canTalk || !$("cr-preview")) return;
    try {
      var cam = $("cr-cam").value || undefined, mic = $("cr-mic").value || undefined;
      if (preview) preview.getTracks().forEach(function (t) { t.stop(); });
      preview = await navigator.mediaDevices.getUserMedia({ video: cam ? { deviceId: { exact: cam } } : true, audio: mic ? { deviceId: { exact: mic } } : true });
      $("cr-preview").srcObject = preview;
      meter(preview);
      await listDevices();
      $("cr-nodev").hidden = true;
    } catch (e) { $("cr-nodev").hidden = false; }
  }
  async function listDevices() {
    var devs = await navigator.mediaDevices.enumerateDevices();
    [["cr-cam", "videoinput"], ["cr-mic", "audioinput"]].forEach(function (pair) {
      var sel = $(pair[0]), cur = sel.value; sel.textContent = "";
      devs.filter(function (d) { return d.kind === pair[1]; }).forEach(function (d, i) {
        var o = el("option", null, d.label || (pair[1] === "videoinput" ? x.cam : x.mic) + " " + (i + 1)); o.value = d.deviceId; sel.appendChild(o);
      });
      if (cur) sel.value = cur;
    });
  }
  function meter(stream) {
    if (meterStop) meterStop();
    try {
      var ctx = new (window.AudioContext || window.webkitAudioContext)(), an = ctx.createAnalyser(), buf = new Uint8Array(256), run = true;
      ctx.createMediaStreamSource(stream).connect(an); an.fftSize = 512;
      (function tick() {
        if (!run) return; an.getByteTimeDomainData(buf);
        var peak = 0; for (var i = 0; i < buf.length; i++) peak = Math.max(peak, Math.abs(buf[i] - 128));
        $("cr-meter").style.width = Math.min(100, peak * 1.6) + "%"; requestAnimationFrame(tick);
      })();
      meterStop = function () { run = false; ctx.close(); };
    } catch (e) { /* pas d'indicateur, sans gravité */ }
  }
  function stopPreview() { if (meterStop) meterStop(); if (preview) preview.getTracks().forEach(function (t) { t.stop(); }); preview = null; }
  if ($("cr-cam")) { $("cr-cam").onchange = startPreview; $("cr-mic").onchange = startPreview; }

  // ---------- connexion ----------
  async function join() {
    if (joining) return; joining = true; $("cr-join").disabled = true; status(x.connecting);
    try {
      var body = new URLSearchParams({ csrf: cfg.csrf, as: cfg.as });
      var r = await fetch(cfg.token_url, { method: "POST", body: body, credentials: "same-origin" });
      if (!r.ok) throw new Error("token " + r.status);
      var info = await r.json();
      var camId = $("cr-cam") && $("cr-cam").value, micId = $("cr-mic") && $("cr-mic").value;
      stopPreview();
      room = new LK.Room({
        adaptiveStream: true, dynacast: true,
        videoCaptureDefaults: { resolution: LK.VideoPresets.h360.resolution, deviceId: camId || undefined },
        audioCaptureDefaults: { echoCancellation: true, noiseSuppression: true, autoGainControl: true, deviceId: micId || undefined },
        publishDefaults: { simulcast: true, videoSimulcastLayers: [LK.VideoPresets.h180], dtx: true, red: true }
      });
      bind(room);
      await room.connect(info.url, info.token);
      $("cr-prejoin").hidden = true; $("cr-after").hidden = true; $("cr-room").hidden = false;
      status(x.connected, "ok");
      if (canTalk) {
        try { await room.localParticipant.setMicrophoneEnabled(true); } catch (e) { banner(x.no_device); }
        try { await room.localParticipant.setCameraEnabled(true); } catch (e) { /* pas de caméra */ }
      }
      if (!room.canPlaybackAudio) $("cr-audio").hidden = false;
      render(); controls();
    } catch (e) {
      status(x.error, "bad"); $("cr-join").disabled = false; console.error(e);
    } finally { joining = false; }
  }

  function bind(r) {
    [RoomEvent.ParticipantConnected, RoomEvent.ParticipantDisconnected, RoomEvent.TrackSubscribed, RoomEvent.TrackUnsubscribed,
     RoomEvent.TrackMuted, RoomEvent.TrackUnmuted, RoomEvent.LocalTrackPublished, RoomEvent.LocalTrackUnpublished,
     RoomEvent.ParticipantMetadataChanged, RoomEvent.ParticipantNameChanged].forEach(function (ev) { r.on(ev, function () { render(); controls(); }); });
    r.on(RoomEvent.ParticipantDisconnected, function (p) { delete hands[p.identity]; });
    r.on(RoomEvent.ActiveSpeakersChanged, function (speakers) {
      document.querySelectorAll(".cr-tile.speaking").forEach(function (t) { t.classList.remove("speaking"); });
      speakers.forEach(function (p) { var t = document.querySelector('.cr-tile[data-id="' + CSS.escape(p.identity) + '"]'); if (t) t.classList.add("speaking"); });
    });
    r.on(RoomEvent.ConnectionQualityChanged, function () { render(); });
    r.on(RoomEvent.Reconnecting, function () { status(x.reconnecting, "warn"); });
    r.on(RoomEvent.Reconnected, function () { status(x.connected, "ok"); });
    r.on(RoomEvent.AudioPlaybackStatusChanged, function () { $("cr-audio").hidden = r.canPlaybackAudio; });
    r.on(RoomEvent.ParticipantPermissionsChanged, function (prev, p) {
      if (p !== r.localParticipant) return;
      var now = p.permissions && p.permissions.canPublish;
      if (cfg.role === "trial") {
        canTalk = !!now;
        if (now) { banner(x.allowed); r.localParticipant.setMicrophoneEnabled(true).catch(function () {}); }
        else banner(x.revoked);
      }
      controls(); render();
    });
    r.on(RoomEvent.DataReceived, function (payload, p) {
      var m; try { m = JSON.parse(new TextDecoder().decode(payload)); } catch (e) { return; }
      if (!p) return;
      if (m.t === "hand") {
        var who = (m.for && roleOf(p) === "teacher") ? m.for : p.identity;        // le professeur peut baisser la main d'un élève
        if (m.up) hands[who] = Date.now(); else delete hands[who];
        render(); controls(); if (m.up && cfg.role === "teacher") banner(p.name + " " + x.raised, 4000);
      }
      else if (m.t === "hands-clear" && roleOf(p) === "teacher") { hands = {}; render(); controls(); }
      else if (m.t === "chat" && typeof m.text === "string") addMsg(p.name, m.text.slice(0, 300), roleOf(p));
    });
    r.on(RoomEvent.Disconnected, function (reason) {
      var R = LK.DisconnectReason, msg = x.left;
      if (reason === R.PARTICIPANT_REMOVED) msg = x.removed;
      else if (reason === R.ROOM_DELETED) msg = x.ended;
      $("cr-room").hidden = true; $("cr-after").hidden = false; $("cr-after-msg").textContent = msg;
      $("cr-rejoin").hidden = reason === R.ROOM_DELETED || reason === R.PARTICIPANT_REMOVED;
      status(""); hands = {}; $("cr-main").textContent = ""; $("cr-grid").textContent = "";
    });
  }

  // ---------- affichage des participants ----------
  var ORDER = { teacher: 0, student: 1, trial: 2, parent: 3, observer: 4 };
  function everyone() {
    if (!room) return [];
    var list = [room.localParticipant].concat(Array.from(room.remoteParticipants.values()));
    return list.sort(function (a, b) { return (ORDER[roleOf(a)] - ORDER[roleOf(b)]) || (a.name || "").localeCompare(b.name || ""); });
  }
  function pub(p, src) { return p.getTrackPublication(src); }
  function videoOf(p, src) { var pb = pub(p, src); return pb && pb.track && !pb.isMuted ? pb.track : null; }

  function tile(p, big) {
    var id = p.identity + (big ? "#big" : ""), t = document.querySelector('.cr-tile[data-id="' + CSS.escape(id) + '"]');
    if (!t) {
      t = el("div", "cr-tile"); t.dataset.id = id;
      t.appendChild(el("video")).setAttribute("playsinline", ""); t.querySelector("video").autoplay = true;
      if (p.isLocal) t.querySelector("video").muted = true;
      t.appendChild(el("div", "cr-avatar"));
      t.appendChild(el("div", "cr-name"));
    }
    var r = roleOf(p), share = big && videoOf(p, Track.Source.ScreenShare), track = share || videoOf(p, Track.Source.Camera);
    var v = t.querySelector("video");
    if (track) { if (v._track !== track) { if (v._track) v._track.detach(v); track.attach(v); v._track = track; } v.hidden = false; }
    else { if (v._track) { v._track.detach(v); v._track = null; } v.hidden = true; }
    t.classList.toggle("is-share", !!share); t.classList.toggle("mirror", p.isLocal && !share);
    t.querySelector(".cr-avatar").textContent = (p.name || "?").replace(/^家长 · |^Parent · /, "").slice(0, 1).toUpperCase();
    t.querySelector(".cr-avatar").hidden = !!track;
    var mic = pub(p, Track.Source.Microphone), muted = !mic || mic.isMuted;
    var q = { excellent: "▮▮▮", good: "▮▮▯", poor: "▮▯▯", lost: "▯▯▯" }[p.connectionQuality] || "";
    t.querySelector(".cr-name").textContent = (hands[p.identity] ? "✋ " : "") + (muted ? "🔇 " : "") + p.name + (p.isLocal ? " (" + x.you + ")" : "") +
      (r === "teacher" ? " · " + x.teacher : "") + (q ? "  " + q : "");
    t.title = x.quality[p.connectionQuality] || "";
    return t;
  }

  function attachAudio() {
    room.remoteParticipants.forEach(function (p) {
      p.audioTrackPublications.forEach(function (pb) {
        if (pb.track && !pb.track._crEl) { var a = pb.track.attach(); a._crAudio = true; pb.track._crEl = a; document.body.appendChild(a); }
      });
    });
    document.querySelectorAll("audio").forEach(function (a) { if (a._crAudio && !a.srcObject) a.remove(); });
  }

  function render() {
    if (!room) return;
    attachAudio();
    var all = everyone(), teacher = all.find(function (p) { return roleOf(p) === "teacher"; });
    var sharer = all.find(function (p) { return videoOf(p, Track.Source.ScreenShare); });
    var main = $("cr-main"), grid = $("cr-grid"), mainP = sharer || teacher;
    var keep = new Set();
    if (mainP) { var mt = tile(mainP, true); keep.add(mt); if (mt.parentNode !== main) main.appendChild(mt); }
    else if (cfg.role !== "teacher") { main.textContent = ""; main.appendChild(el("p", "cr-wait", x.waiting_teacher)); }
    main.querySelectorAll(".cr-wait").forEach(function (w) { if (mainP) w.remove(); });
    all.forEach(function (p) {
      var r = roleOf(p);
      if (r === "parent" || r === "observer") return;                      // en écoute : listés à droite, pas de vignette
      if (p === mainP && !sharer) return;                                  // le professeur est déjà au centre
      if (r === "trial" && !videoOf(p, Track.Source.Camera) && !(p.permissions && p.permissions.canPublish) && !hands[p.identity]) return;
      var t = tile(p, false); keep.add(t); grid.appendChild(t);
    });
    document.querySelectorAll(".cr-tile").forEach(function (t) { if (!keep.has(t)) { var v = t.querySelector("video"); if (v._track) v._track.detach(v); t.remove(); } });
    grid.dataset.n = grid.children.length;
    people(all);
  }

  function people(all) {
    var ul = $("cr-people"); ul.textContent = "";
    $("cr-count").textContent = "(" + all.length + ")";
    all.forEach(function (p) {
      var r = roleOf(p), li = el("li"), name = el("span", "cr-pname", (hands[p.identity] ? "✋ " : "") + p.name + (p.isLocal ? " (" + x.you + ")" : ""));
      li.appendChild(name); li.appendChild(el("span", "cr-prole", x[r] || r));
      if (cfg.role === "teacher" && !p.isLocal && r !== "teacher") {
        var acts = el("span", "cr-acts"), mic = pub(p, Track.Source.Microphone);
        if (mic && !mic.isMuted) acts.appendChild(actBtn(x.mute, function () { act("mute", p, mic.trackSid); }));
        if (r === "trial") {
          var on = p.permissions && p.permissions.canPublish;
          acts.appendChild(actBtn(on ? x.revoke : x.allow, function () { act(on ? "revoke" : "allow", p); }));
        }
        acts.appendChild(actBtn(x.remove, function () { if (confirm(x.remove_confirm.replace("{n}", p.name))) act("remove", p); }, "danger"));
        li.appendChild(acts);
      }
      ul.appendChild(li);
    });
  }
  function actBtn(label, fn, cls) { var b = el("button", cls || "", label); b.type = "button"; b.onclick = fn; return b; }
  async function act(action, p, track) {
    var body = new URLSearchParams({ csrf: cfg.csrf, action: action, identity: p ? p.identity : "", track: track || "", as: cfg.as });
    var r = await fetch(cfg.action_url, { method: "POST", body: body, credentials: "same-origin" });
    if (!r.ok) banner(x.error);
    if (action === "allow" || action === "revoke") { delete hands[p.identity]; send({ t: "hand", up: false, for: p.identity }); }
  }

  // ---------- boutons ----------
  function controls() {
    if (!room) return;
    var lp = room.localParticipant, micOn = lp.isMicrophoneEnabled, camOn = lp.isCameraEnabled;
    $("b-mic").hidden = $("b-cam").hidden = !canTalk;
    $("b-mic").textContent = (micOn ? "🎙 " : "🔇 ") + (micOn ? x.mic_on : x.mic_off); $("b-mic").classList.toggle("off", !micOn);
    $("b-cam").textContent = (camOn ? "📷 " : "🚫 ") + (camOn ? x.cam_on : x.cam_off); $("b-cam").classList.toggle("off", !camOn);
    $("b-hand").hidden = !(cfg.role === "student" || cfg.role === "trial");
    $("b-hand").textContent = "✋ " + (hands[lp.identity] ? x.hand_down : x.hand_up); $("b-hand").classList.toggle("on", !!hands[lp.identity]);
    $("b-share").hidden = cfg.role !== "teacher" || !navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia;
    $("b-share").textContent = "🖥 " + (lp.isScreenShareEnabled ? x.share_stop : x.share);
  }
  $("cr-join") && ($("cr-join").onclick = join);
  $("cr-rejoin") && ($("cr-rejoin").onclick = function () { $("cr-after").hidden = true; join(); });
  $("b-mic") && ($("b-mic").onclick = async function () { await room.localParticipant.setMicrophoneEnabled(!room.localParticipant.isMicrophoneEnabled).catch(function () { banner(x.no_device); }); controls(); render(); });
  $("b-cam") && ($("b-cam").onclick = async function () { await room.localParticipant.setCameraEnabled(!room.localParticipant.isCameraEnabled).catch(function () { banner(x.no_device); }); controls(); render(); });
  $("b-share") && ($("b-share").onclick = async function () { await room.localParticipant.setScreenShareEnabled(!room.localParticipant.isScreenShareEnabled, { audio: true }).catch(function () {}); controls(); render(); });
  $("b-hand") && ($("b-hand").onclick = function () {
    var up = !hands[room.localParticipant.identity];
    if (up) hands[room.localParticipant.identity] = Date.now(); else delete hands[room.localParticipant.identity];
    send({ t: "hand", up: up }); controls(); render();
  });
  $("b-leave") && ($("b-leave").onclick = function () { room && room.disconnect(); });
  $("b-end") && ($("b-end").onclick = function () { if (confirm(x.end_confirm)) act("end"); });
  $("b-side") && ($("b-side").onclick = function () { $("cr-side").classList.toggle("open"); });
  $("cr-audio") && ($("cr-audio").onclick = function () { room.startAudio().then(function () { $("cr-audio").hidden = true; }); });

  // ---------- discussion (publique, non conservée) ----------
  function send(obj) { if (room) room.localParticipant.publishData(new TextEncoder().encode(JSON.stringify(obj)), { reliable: true }).catch(function () {}); }
  function addMsg(name, text, role) {
    var li = el("li", role === "teacher" ? "t" : ""); li.appendChild(el("b", null, name)); li.appendChild(el("span", null, text));
    $("cr-msgs").appendChild(li); $("cr-msgs").scrollTop = 1e9;
    var chatHidden = document.querySelector('[data-panel="chat"]').hidden;
    if (chatHidden) { unread++; $("cr-unread").hidden = false; }
  }
  $("cr-chatform") && ($("cr-chatform").onsubmit = function (e) {
    e.preventDefault(); var v = $("cr-chatin").value.trim(); if (!v || !room) return;
    if (cfg.role === "parent" || cfg.role === "observer") return;          // écoute seule : pas de message
    send({ t: "chat", text: v }); addMsg(room.localParticipant.name + " (" + x.you + ")", v, cfg.role); $("cr-chatin").value = "";
  });
  if (cfg.role === "parent" || cfg.role === "observer") { var ci = $("cr-chatin"); if (ci) { ci.disabled = true; ci.placeholder = x.listen_only; } }
  document.querySelectorAll(".cr-tabs button").forEach(function (b) {
    b.onclick = function () {
      document.querySelectorAll(".cr-tabs button").forEach(function (o) { o.setAttribute("aria-selected", o === b); });
      document.querySelectorAll("[data-panel]").forEach(function (pn) { pn.hidden = pn.dataset.panel !== b.dataset.tab; });
      if (b.dataset.tab === "chat") { unread = 0; $("cr-unread").hidden = true; }
    };
  });

  // ---------- horloge du cours ----------
  var starts = new Date(cfg.starts).getTime();
  setInterval(function () {
    var now = Date.now(), c = $("cr-clock");
    if (now < starts) c.textContent = x.starts_in.replace("{m}", Math.ceil((starts - now) / 60000));
    else if (now < starts + cfg.teaching_min * 60000) c.textContent = x.time_left.replace("{m}", Math.ceil((starts + cfg.teaching_min * 60000 - now) / 60000));
    else c.textContent = x.homework;
  }, 1000);

  if ($("cr-preview")) startPreview();
  window.addEventListener("beforeunload", function () { if (room) room.disconnect(); });
})();
