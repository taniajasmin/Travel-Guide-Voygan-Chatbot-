(function () {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  function init() {
    const chat = document.getElementById("chat");
    const msg  = document.getElementById("msg");
    const send = document.getElementById("send");
    if (!chat || !msg || !send) return;

    const timeNow = () =>
      new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const esc = (s) =>
      String(s).replace(/[&<>"']/g, (m) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      })[m]);
    const nl2br = (s) => esc(s).split("\n").join("<br>");

    function addMe(text) {
      const row = document.createElement("div");
      row.className = "flex justify-end";
      row.innerHTML = `<div class="bubble me">
          <div>${esc(text)}</div>
          <div class="text-[10px] text-slate-400 mt-1">${timeNow()}</div>
        </div>`;
      chat.appendChild(row);
      chat.scrollTop = chat.scrollHeight;
    }

    function addBot(text, b64, mime) {
      const audio = (b64 && mime)
        ? `<audio controls preload="none" class="w-64 mt-1">
             <source src="data:${mime};base64,${b64}">
           </audio>`
        : "";
      const row = document.createElement("div");
      row.className = "flex";
      row.innerHTML = `<div class="bubble bot">
          <div>${nl2br(text)}</div>
          ${audio}
          <div class="text-[10px] text-slate-400 mt-1">${timeNow()}</div>
        </div>`;
      chat.appendChild(row);
      chat.scrollTop = chat.scrollHeight;
    }

    // Text-only welcome (no TTS)
    (async function greet() {
      try {
        const r = await fetch("/api/greet");
        const d = await r.json();
        addBot(d.text || "Hello!", null, null);
      } catch {
        addBot("Hello!", null, null);
      }
    })();

    async function sendMsg() {
      const message = (msg.value || "").trim();
      if (!message) return;
      addMe(message);
      msg.value = "";
      send.disabled = true;
      send.classList.add("opacity-60");

      try {
        const r = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message, tts: true })
        });
        const d = await r.json();
        if (!r.ok) throw new Error(d.detail || "API error");
        addBot(d.text || "(no text)", d.audio_b64, d.audio_mime);
      } catch (e) {
        addBot("Sorry, something went wrong. " + (e.message || e), null, null);
      } finally {
        send.disabled = false;
        send.classList.remove("opacity-60");
        msg.focus();
      }
    }

    send.addEventListener("click", sendMsg);
    msg.addEventListener("keydown", (e) => { if (e.key === "Enter") sendMsg(); });
  }
})();
