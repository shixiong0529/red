let currentUser = null;

function initColorPicker(selected) {
  const opts = document.getElementById("setColorOpts");
  if (!opts) return;
  opts.querySelectorAll(".color-dot").forEach((d) => {
    d.classList.toggle("selected", d.dataset.color === selected);
  });
  opts.onclick = function (e) {
    if (e.target.classList.contains("color-dot")) {
      opts.querySelectorAll(".color-dot").forEach((d) => d.classList.remove("selected"));
      e.target.classList.add("selected");
    }
  };
}

function initAvatarGrid(current) {
  const ag = document.getElementById("avatarGrid");
  if (!ag) return;
  const avatars = [
    "🐬",
    "🌊",
    "🦋",
    "🌸",
    "🌟",
    "🎵",
    "🍀",
    "💎",
    "🌈",
    "☕",
    "🍻",
    "🎮",
    "🌙",
    "🌞",
  ];
  ag.innerHTML = "";
  avatars.forEach((av) => {
    const sp = document.createElement("span");
    sp.textContent = av;
    sp.style.cssText =
      "font-size:24px;padding:4px 6px;cursor:pointer;border:2px solid " +
      (av === current ? "#f60" : "transparent") +
      ";background:" +
      (av === current ? "#fff0e0" : "transparent");
    sp.dataset.av = av;
    sp.onclick = function () {
      document.querySelectorAll("#avatarGrid span").forEach((s) => {
        s.style.borderColor = "transparent";
        s.style.background = "transparent";
      });
      sp.style.borderColor = "#f60";
      sp.style.background = "#fff0e0";
    };
    ag.appendChild(sp);
  });
}

function getSelectedAvatar() {
  const sel = document.querySelector("#avatarGrid span[style*='border-color: rgb(255, 102, 0)']");
  if (sel) return sel.dataset.av;
  const cur = document.querySelector("#avatarGrid span[style*='#f60']");
  return cur ? cur.dataset.av : "🐬";
}

function getSelectedColor() {
  const sel = document.querySelector("#setColorOpts .color-dot.selected");
  return sel ? sel.dataset.color : "#00ff00";
}

async function initSettings() {
  try {
    const me = await apiFetch("/api/me");
    if (!me.user) {
      location.href = "/login";
      return;
    }
    currentUser = me.user;
    const profile = await apiFetch("/api/profile/me");
    document.getElementById("setNick").value = profile.user.username;
    document.getElementById("setGender").value = profile.user.gender;
    document.getElementById("setAge").value = profile.age || "";
    document.getElementById("setCity").value = profile.city || "";
    document.getElementById("setEmail").value = profile.email || "";
    document.getElementById("setOICQ").value = profile.oicq || "";
    document.getElementById("setSig").value = profile.sig || "";

    const saved = JSON.parse(localStorage.getItem("chatPrefs") || "{}");
    initColorPicker(saved.color || "#00ff00");
    document.getElementById("setFontDef").value = saved.style || "normal";
    document.getElementById("setShowJoin").checked = saved.showJoin !== false;
    document.getElementById("setAutoScroll").checked = saved.autoScroll !== false;
    document.getElementById("setSound").checked = !!saved.sound;
    document.getElementById("setRefresh").value = saved.refresh || "5";

    initAvatarGrid(profile.avatar || "🐬");
  } catch (e) {
    showToast(e.message || "加载失败", "error");
  }
}

async function saveSettings() {
  try {
    const payload = {
      username: document.getElementById("setNick").value.trim(),
      gender: document.getElementById("setGender").value,
      age: document.getElementById("setAge").value,
      city: document.getElementById("setCity").value.trim(),
      email: document.getElementById("setEmail").value.trim(),
      oicq: document.getElementById("setOICQ").value.trim(),
      sig: document.getElementById("setSig").value.trim(),
      avatar: getSelectedAvatar(),
    };
    if (!payload.username) {
      showToast("昵称不能为空", "error");
      return;
    }
    await apiFetch("/api/profile/me", { method: "PUT", body: payload });
    const prefs = {
      color: getSelectedColor(),
      style: document.getElementById("setFontDef").value,
      showJoin: document.getElementById("setShowJoin").checked,
      autoScroll: document.getElementById("setAutoScroll").checked,
      sound: document.getElementById("setSound").checked,
      refresh: document.getElementById("setRefresh").value,
    };
    localStorage.setItem("chatPrefs", JSON.stringify(prefs));
    showToast("设置已保存", "success");
  } catch (e) {
    showToast(e.message || "保存失败", "error");
  }
}

function resetSettings() {
  localStorage.removeItem("chatPrefs");
  showToast("已重置为默认", "success");
  initSettings();
}

initSettings();
