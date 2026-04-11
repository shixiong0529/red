let currentUser = null;
let selectedColor = "#00ff00";
let ws = null;

let reconnectDelayMs = 500;
let reconnectTimer = null;

const ACTIONS = [
  "向 {t} 送了一朵玫瑰 🌹",
  "对 {t} 抛了一个媚眼 😘",
  "给 {t} 倒了一杯茶 ☕",
  "和 {t} 碰杯 🍻",
  "向 {t} 挥挥手 👋",
  "对 {t} 微微一笑 😊",
  "送给 {t} 一束花 💐",
  "拍了拍 {t} 的肩膀",
];

function esc(t) {
  const d = document.createElement("div");
  d.textContent = String(t ?? "");
  return d.innerHTML;
}

function el(id) {
  return document.getElementById(id);
}

function isWsOpen() {
  return ws && ws.readyState === WebSocket.OPEN;
}

function appendSys(html) {
  const c = el("chatMessages");
  if (!c) return;
  const d = document.createElement("div");
  d.className = "msg msg-sys";
  d.innerHTML = "[系统] " + html;
  c.appendChild(d);
  c.scrollTop = c.scrollHeight;
}

function fmtTs(dateLike) {
  const now = new Date(dateLike || Date.now());
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  const ss = String(now.getSeconds()).padStart(2, "0");
  return `${hh}:${mm}:${ss}`;
}

function appendMessage(msg) {
  const c = el("chatMessages");
  if (!c) return;
  const d = document.createElement("div");
  d.className = msg.is_action ? "msg msg-action" : "msg";

  const ts = fmtTs(msg.created_at);
  if (msg.is_action) {
    d.innerHTML = `<span class="msg-time">[${ts}]</span> ${esc(msg.user?.username || "")} ${esc(msg.content || "")}`;
  } else {
    const cls = msg.style === "rainbow" ? "rainbow-text" : "";
    let sty = "color:" + (msg.color || "#00ff00") + ";";
    if (msg.style === "bold") sty += "font-weight:bold;";
    if (msg.style === "italic") sty += "font-style:italic;";

    const wl = msg.target_user_id ? '<span class="whisper">[悄悄话]</span> ' : "";
    const nameColor = msg.user?.gender === "female" ? "#cc3399" : "#3366cc";
    const uname = String(msg.user?.username || "");
    d.innerHTML =
      `<span class="msg-time">[${ts}]</span> ` +
      wl +
      `<span class="msg-name" style="color:${nameColor}" onclick="cReplyById(${Number(msg.user?.id || 0)})">` +
      esc(uname) +
      `</span> 说：<span class="${cls}" style="${sty}">` +
      esc(msg.content || "") +
      `</span>`;
  }

  c.appendChild(d);
  c.scrollTop = c.scrollHeight;
}

function updateOnline(users) {
  const list = el("userList");
  const sel = el("targetUser");

  let html = "";
  if (currentUser) {
    html +=
      `<div class="user-list-item ${currentUser.gender === "female" ? "female" : "male"}" ` +
      `style="color:#cc6600;font-weight:bold">${esc(currentUser.username)}(我)</div>`;
  }
  (users || []).forEach((u) => {
    html +=
      `<div class="user-list-item ${u.is_admin ? "admin" : u.gender}" ` +
      `onclick="cReplyById(${Number(u.id || 0)})">` +
      esc(u.username) +
      `</div>`;
  });
  if (list) list.innerHTML = html;

  if (sel) {
    sel.innerHTML = '<option value="all">所有人</option>';
    (users || []).forEach((u) => {
      const o = document.createElement("option");
      o.value = String(u.id);
      o.textContent = u.username;
      sel.appendChild(o);
    });
  }

  const count = el("onlineCount");
  if (count) count.textContent = String((users || []).length + (currentUser ? 1 : 0));
}

function cReplyById(userId) {
  if (!currentUser || !userId || Number(userId) === Number(currentUser.id)) return;
  const sel = el("targetUser");
  if (!sel) return;
  for (let i = 0; i < sel.options.length; i++) {
    if (sel.options[i].value === String(userId)) {
      sel.selectedIndex = i;
      break;
    }
  }
  const inp = el("chatInput");
  if (inp) inp.focus();
}

function wsSend(payload) {
  if (!isWsOpen()) {
    showToast("聊天连接未建立（WebSocket 未连接）。请刷新页面，或退出后重新登录。", "error");
    return false;
  }
  try {
    ws.send(JSON.stringify(payload));
    return true;
  } catch (e) {
    showToast("发送失败：聊天连接已断开。请刷新页面。", "error");
    return false;
  }
}

function chatSend() {
  const inp = el("chatInput");
  if (!inp) return;
  const tx = inp.value.trim();
  if (!tx) return;

  if (tx === "/help") {
    appendSys("可用指令：/help /clear");
    inp.value = "";
    return;
  }
  if (tx === "/clear") {
    el("chatMessages").innerHTML = "";
    appendSys("聊天记录已清空");
    inp.value = "";
    return;
  }

  const st = el("fontStyle")?.value || "normal";
  const tg = el("targetUser")?.value || "all";
  const ok = wsSend({
    type: "message",
    content: tx,
    color: selectedColor,
    style: st,
    target_user_id: tg === "all" ? null : parseInt(tg, 10),
  });
  if (ok) inp.value = "";
}

function chatSendAction() {
  const tg = el("targetUser")?.value || "all";
  const tn =
    tg === "all"
      ? "大家"
      : el("targetUser")?.selectedOptions?.[0]?.textContent || "对方";
  const act = ACTIONS[Math.floor(Math.random() * ACTIONS.length)].replace("{t}", tn);
  wsSend({
    type: "action",
    content: act,
    color: selectedColor,
    style: "normal",
    target_user_id: tg === "all" ? null : parseInt(tg, 10),
  });
}

// Expose for inline onclick handlers in the template.
window.chatSend = chatSend;
window.chatSendAction = chatSendAction;
window.cReplyById = cReplyById;

function scheduleReconnect(reason) {
  if (reconnectTimer) return;
  const ms = reconnectDelayMs;
  reconnectDelayMs = Math.min(8000, Math.floor(reconnectDelayMs * 1.8));
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connectWs();
  }, ms);
  if (reason) appendSys(esc(reason) + `（${ms}ms 后重试）`);
}

function connectWs() {
  try {
    if (ws) {
      try {
        ws.close();
      } catch (e) {}
    }
    const url = (location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/ws/chat";
    ws = new WebSocket(url);

    ws.onopen = async () => {
      reconnectDelayMs = 500;
      showToast("聊天已连接", "success");
      try {
        const online = await apiFetch("/api/chat/online");
        updateOnline(online);
      } catch (e) {}
    };

    ws.onmessage = (ev) => {
      let msg;
      try {
        msg = JSON.parse(ev.data);
      } catch (e) {
        return;
      }
      if (msg.type === "online") {
        updateOnline(msg.users || []);
        return;
      }
      appendMessage(msg);
    };

    ws.onerror = () => {
      // If uvicorn is missing websocket deps, the browser will fail the handshake.
      showToast("聊天连接错误（WebSocket 连接失败）。", "error");
    };

    ws.onclose = (ev) => {
      const code = ev && typeof ev.code === "number" ? ev.code : 0;
      if (code === 4401) {
        showToast("登录状态已失效，请重新登录。", "error");
        location.href = "/login";
        return;
      }
      // 1006 often means handshake failed (e.g. server returned 404/500 instead of 101).
      if (code === 1006) {
        appendSys("WebSocket 握手失败。若你刚安装依赖，请重启后端。");
      } else {
        appendSys(`聊天连接已断开（code=${code}）。`);
      }
      scheduleReconnect("连接断开，正在重连");
    };
  } catch (e) {
    scheduleReconnect("连接失败，正在重试");
  }
}

function ie(e) {
  const inp = el("chatInput");
  if (!inp) return;
  inp.value += e;
  inp.focus();
}
window.ie = ie;

async function initChat() {
  const me = await apiFetch("/api/me");
  if (!me.user) {
    location.href = "/login";
    return;
  }
  currentUser = me.user;

  const prefs = JSON.parse(localStorage.getItem("chatPrefs") || "{}");
  if (prefs.color) selectedColor = prefs.color;
  if (prefs.style) el("fontStyle").value = prefs.style;

  // Apply selected color UI.
  document.querySelectorAll("#colorOptions .color-dot").forEach((d) => {
    d.classList.toggle("selected", d.dataset.color === selectedColor);
  });

  const history = await apiFetch("/api/chat/history?limit=50");
  (history || []).forEach((m) => appendMessage(m));

  connectWs();
}

el("colorOptions")?.addEventListener("click", function (e) {
  if (!e.target.classList.contains("color-dot")) return;
  this.querySelectorAll(".color-dot").forEach((d) => d.classList.remove("selected"));
  e.target.classList.add("selected");
  selectedColor = e.target.dataset.color;
  try {
    const prefs = JSON.parse(localStorage.getItem("chatPrefs") || "{}");
    prefs.color = selectedColor;
    localStorage.setItem("chatPrefs", JSON.stringify(prefs));
  } catch (err) {}
});

el("fontStyle")?.addEventListener("change", function () {
  try {
    const prefs = JSON.parse(localStorage.getItem("chatPrefs") || "{}");
    prefs.style = this.value;
    localStorage.setItem("chatPrefs", JSON.stringify(prefs));
  } catch (err) {}
});

el("roomList")?.addEventListener("click", function (e) {
  const li = e.target.closest("li");
  if (!li) return;
  document.querySelectorAll(".room-list li").forEach((l) => l.classList.remove("current"));
  li.classList.add("current");
  const roomName = li.textContent.replace(/\\s*\\(\\d+\\)/, "");
  el("currentRoom").textContent = roomName;
  apiFetch("/api/chat/room?room=" + encodeURIComponent(roomName), { method: "PUT" }).catch(() => {});
});

initChat().catch((e) => {
  showToast(e.message || "初始化失败", "error");
});
