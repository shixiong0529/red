function esc(t) {
  const d = document.createElement("div");
  d.textContent = t;
  return d.innerHTML;
}

function fmt(ts) {
  const d = new Date(ts);
  const p = (n) => String(n).padStart(2, "0");
  return (
    d.getFullYear() +
    "-" +
    p(d.getMonth() + 1) +
    "-" +
    p(d.getDate()) +
    " " +
    p(d.getHours()) +
    ":" +
    p(d.getMinutes())
  );
}

async function loadUsers() {
  const users = await apiFetch("/api/admin/users");
  const el = document.getElementById("adminUsers");
  let html = '<table style="width:100%;border-collapse:collapse;font-size:14px">';
  html +=
    '<tr style="border-bottom:1px dotted #ddd"><th style="text-align:left;padding:6px">ID</th><th style="text-align:left;padding:6px">昵称</th><th style="text-align:left;padding:6px">性别</th><th style="text-align:left;padding:6px">管理员</th><th style="text-align:left;padding:6px">注册</th><th style="text-align:left;padding:6px">操作</th></tr>';
  users.forEach((u) => {
    html +=
      '<tr style="border-bottom:1px dotted #eee"><td style="padding:6px">' +
      u.id +
      "</td><td style=\"padding:6px\">" +
      esc(u.username) +
      "</td><td style=\"padding:6px\">" +
      esc(u.gender) +
      "</td><td style=\"padding:6px\">" +
      (u.is_admin ? "是" : "否") +
      "</td><td style=\"padding:6px\">" +
      fmt(u.created_at) +
      "</td><td style=\"padding:6px\"><button class=\"gb-action-btn delete\" onclick=\"deleteUser(" +
      u.id +
      ')\">删除</button></td></tr>';
  });
  html += "</table>";
  el.innerHTML = html;
}

async function loadPosts() {
  const posts = await apiFetch("/api/admin/posts");
  const el = document.getElementById("adminPosts");
  let html = "";
  posts.forEach((p) => {
    html +=
      '<div class="gb-card"><div class="gb-header"><div class="gb-header-left"><span class="gb-floor">#' +
      p.id +
      "</span><span class=\"gb-author male\">" +
      esc(p.user.username) +
      '</span></div><span class="gb-time">' +
      fmt(p.created_at) +
      "</span></div>" +
      (p.subject ? '<div class="gb-subject">' + esc(p.subject) + "</div>" : "") +
      '<div class="gb-body">' +
      esc(p.content) +
      '</div><div class="gb-footer"><div class="gb-actions"><button class="gb-action-btn delete" onclick="deletePost(' +
      p.id +
      ')">删除</button></div></div></div>';
  });
  el.innerHTML = html;
}

function deleteUser(id) {
  confirmDialog("确认删除该用户？", async function () {
    try {
      await apiFetch("/api/admin/user/" + id, { method: "DELETE" });
      showToast("已删除", "success");
      loadUsers();
    } catch (e) {
      showToast(e.message || "删除失败", "error");
    }
  });
}

function deletePost(id) {
  confirmDialog("确认删除该留言？", async function () {
    try {
      await apiFetch("/api/guestbook/" + id, { method: "DELETE" });
      showToast("已删除", "success");
      loadPosts();
    } catch (e) {
      showToast(e.message || "删除失败", "error");
    }
  });
}

(async function init() {
  try {
    await loadUsers();
    await loadPosts();
  } catch (e) {
    showToast(e.message || "加载失败", "error");
  }
})();
