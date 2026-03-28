let currentUser = null;

function esc(t) {
  const d = document.createElement("div");
  d.textContent = t;
  return d.innerHTML;
}

function formatDate(ts) {
  const d = new Date(ts);
  const p = (n) => String(n).padStart(2, "0");
  return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate());
}

async function initProfile() {
  try {
    const me = await apiFetch("/api/me");
    if (!me.user) {
      location.href = "/login";
      return;
    }
    currentUser = me.user;
    const online = await apiFetch("/api/chat/online");
    const list = document.getElementById("profUserList");
    let h = "";
    h +=
      '<div class="user-list-item ' +
      (currentUser.gender === "female" ? "female" : "male") +
      '" style="color:#ff0;font-weight:bold;cursor:pointer" onclick="showProfile(' +
      currentUser.id +
      ')">' +
      esc(currentUser.username) +
      "(我)</div>";
    online.forEach((u) => {
      h +=
        '<div class="user-list-item ' +
        (u.is_admin ? "admin" : u.gender) +
        '" style="cursor:pointer" onclick="showProfile(' +
        u.id +
        ')">' +
        esc(u.username) +
        "</div>";
    });
    list.innerHTML = h;
    showProfile(currentUser.id);
  } catch (e) {
    showToast(e.message || "加载失败", "error");
  }
}

async function showProfile(userId) {
  try {
    let data;
    if (userId === currentUser.id) {
      data = await apiFetch("/api/profile/me");
      data.reg = new Date().toISOString();
    } else {
      data = await apiFetch("/api/users/" + userId);
    }
    const p = data;
    const gLabel = p.user.gender === "male" ? "♂ 男" : p.user.gender === "female" ? "♀ 女" : "？ 保密";
    const gColor = p.user.gender === "male" ? "#6cf" : p.user.gender === "female" ? "#f9c" : "#ccc";
    document.getElementById("profCardTitle").innerHTML = "个人名片 —— " + esc(p.user.username);
    document.getElementById("profCard").innerHTML =
      '<div style="display:flex;gap:15px;align-items:flex-start;flex-wrap:wrap">' +
      '<div style="text-align:center;min-width:80px">' +
      '<div style="font-size:56px;background:#fff8f0;border:2px groove #ccc;padding:8px 12px;display:inline-block">' +
      esc(p.avatar || "🐬") +
      "</div>" +
      '<div style="color:' +
      gColor +
      ';font-weight:bold;font-size:16px;margin-top:6px">' +
      esc(p.user.username) +
      "</div>" +
      '<div style="color:#666;font-size:13px">' +
      gLabel +
      "</div>" +
      "</div>" +
      '<div style="flex:1;min-width:200px">' +
      '<table style="width:100%;border-collapse:collapse;font-size:12px">' +
      '<tr style="border-bottom:1px dotted #ddd"><td style="color:#996633;padding:4px 8px;white-space:nowrap;width:70px">年龄</td><td style="color:#555;padding:4px 8px">' +
      esc(p.age || "保密") +
      "</td></tr>" +
      '<tr style="border-bottom:1px dotted #ddd"><td style="color:#996633;padding:4px 8px">所在地</td><td style="color:#555;padding:4px 8px">' +
      esc(p.city || "未填写") +
      "</td></tr>" +
      '<tr style="border-bottom:1px dotted #ddd"><td style="color:#996633;padding:4px 8px">OICQ</td><td style="color:#009900;padding:4px 8px;font-family:Courier New">' +
      esc(p.oicq || "未填写") +
      "</td></tr>" +
      '<tr style="border-bottom:1px dotted #ddd"><td style="color:#996633;padding:4px 8px">邮箱</td><td style="color:#3366cc;padding:4px 8px">' +
      esc(p.email || "未填写") +
      "</td></tr>" +
      '<tr style="border-bottom:1px dotted #ddd"><td style="color:#996633;padding:4px 8px">注册日期</td><td style="color:#888;padding:4px 8px">' +
      formatDate(p.reg) +
      "</td></tr>" +
      '<tr><td style="color:#996633;padding:4px 8px">个性签名</td><td style="color:#996633;padding:4px 8px;font-style:italic">"' +
      esc(p.sig || "这个人很懒，什么都没写～") +
      '"</td></tr>' +
      "</table>" +
      (userId === currentUser.id
        ? '<div style="margin-top:10px;text-align:right"><button class="gb-action-btn" onclick="location.href=\'/settings\'" style="padding:3px 12px">✎ 编辑资料</button></div>'
        : '<div style="margin-top:10px;text-align:right"><button class="gb-action-btn" onclick="location.href=\'/\'" style="padding:3px 12px">💬 去聊天</button></div>') +
      "</div></div>";
  } catch (e) {
    showToast(e.message || "加载失败", "error");
  }
}

initProfile();
