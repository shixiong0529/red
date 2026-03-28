/* Shared helpers */
async function apiFetch(url, opts) {
  const options = opts || {};
  options.credentials = "include";
  if (options.body && typeof options.body === "object" && !(options.body instanceof FormData)) {
    options.headers = options.headers || {};
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(options.body);
  }
  const res = await fetch(url, options);
  if (!res.ok) {
    let msg = "请求失败";
    try {
      const data = await res.json();
      msg = data.detail || msg;
    } catch (e) {}
    throw new Error(msg);
  }
  if (res.headers.get("content-type") && res.headers.get("content-type").includes("application/json")) {
    return res.json();
  }
  return res.text();
}

async function showAdminLink() {
  const link = document.getElementById("adminLink");
  if (!link) return;
  try {
    const me = await apiFetch("/api/me");
    if (me.user && me.user.is_admin) {
      link.style.display = "inline-block";
    }
  } catch (e) {}
}

function showToast(message, type) {
  const t = document.getElementById("toast");
  if (!t) return;
  t.textContent = message;
  t.className = "toast show" + (type ? " " + type : "");
  clearTimeout(t._t);
  t._t = setTimeout(function () {
    t.className = "toast";
  }, 2500);
}

function confirmDialog(message, onYes) {
  const overlay = document.getElementById("confirmOverlay");
  const text = document.getElementById("confirmText");
  const yes = document.getElementById("confirmYes");
  if (!overlay || !text || !yes) return;
  text.textContent = message;
  overlay.classList.remove("hidden");
  const handler = function () {
    overlay.classList.add("hidden");
    yes.removeEventListener("click", handler);
    if (typeof onYes === "function") onYes();
  };
  yes.addEventListener("click", handler);
}

function hideConfirm() {
  const overlay = document.getElementById("confirmOverlay");
  if (overlay) overlay.classList.add("hidden");
}

// Keep scroll position stable across page navigation
(function () {
  function key() {
    return "scroll:" + location.pathname;
  }
  window.addEventListener("beforeunload", function () {
    try {
      sessionStorage.setItem(key(), String(window.scrollY || 0));
    } catch (e) {}
  });
  window.addEventListener("DOMContentLoaded", function () {
    try {
      const y = sessionStorage.getItem(key());
      if (y !== null) window.scrollTo(0, parseInt(y, 10) || 0);
    } catch (e) {}
  });
})();

document.addEventListener("DOMContentLoaded", function () {
  showAdminLink();
});
