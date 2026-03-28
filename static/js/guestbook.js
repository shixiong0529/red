let currentUser = null;

function esc(t) {
  const d = document.createElement("div");
  d.textContent = t;
  return d.innerHTML;
}

function formatTime(ts) {
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
    p(d.getMinutes()) +
    ":" +
    p(d.getSeconds())
  );
}

function renderPosts(posts) {
  const list = document.getElementById("messageList");
  const totalCount = document.getElementById("totalCount");
  const todayCount = document.getElementById("todayCount");
  totalCount.textContent = posts.length;
  todayCount.textContent = Math.min(posts.length, 3);
  if (!posts.length) {
    list.innerHTML =
      '<div class="empty-state"><span class="big-icon">🧡</span>暂时还没有留言<br>快来写下你的心声吧</div>';
    return;
  }
  let html = "";
  posts.forEach((m, idx) => {
    const floor = posts.length - idx;
    const canDel = currentUser && currentUser.id === m.user.id;
    let replies = "";
    if (m.replies && m.replies.length) {
      replies += '<div class="replies-section">';
      m.replies.forEach((r, i) => {
        const canDelR = currentUser && currentUser.id === r.user.id;
        replies +=
          '<div class="reply-card" id="gbr-' +
          r.id +
          '"><div class="reply-header"><div class="reply-header-left"><span class="reply-tag">回复#' +
          (i + 1) +
          '</span><span class="reply-author ' +
          r.user.gender +
          '">' +
          esc(r.user.username) +
          '</span></div><div style="display:flex;align-items:center;gap:6px"><span class="reply-time">' +
          formatTime(r.created_at) +
          '</span>' +
          (canDelR ? '<button class="gb-action-btn delete" onclick="gbDelR(' + r.id + ')">删</button>' : "") +
          '</div></div><div class="reply-body">' +
          esc(r.content) +
          "</div></div>";
      });
      replies += "</div>";
    }
    html +=
      '<div class="gb-card" id="gbm-' +
      m.id +
      '"><div class="gb-header"><div class="gb-header-left"><span class="gb-floor">#' +
      floor +
      "楼</span><span class=\"gb-author " +
      m.user.gender +
      '">' +
      esc(m.user.username) +
      '</span><span class="gb-mood">' +
      esc(m.mood || "") +
      '</span></div><span class="gb-time">' +
      formatTime(m.created_at) +
      "</span></div>" +
      (m.subject ? '<div class="gb-subject">' + esc(m.subject) + "</div>" : "") +
      '<div class="gb-body">' +
      esc(m.content) +
      '</div><div class="gb-footer"><div class="gb-footer-left">回复: ' +
      (m.replies ? m.replies.length : 0) +
      '</div><div class="gb-actions"><button class="gb-action-btn" onclick="gbTR(' +
      m.id +
      ')">回复</button>' +
      (canDel ? '<button class="gb-action-btn delete" onclick="gbDelP(' + m.id + ')">删除</button>' : "") +
      "</div></div></div>" +
      replies +
      '<div class="reply-form" id="gbrf-' +
      m.id +
      '"><div class="reply-form-title">回复 <span style="color:#fc0">' +
      esc(m.user.username) +
      '</span></div><div class="rfr"><label>内容：</label><textarea id="gbrc-' +
      m.id +
      '" placeholder="写下你的回复..." maxlength="300"></textarea></div><div style="display:flex;gap:5px;justify-content:flex-end;margin-top:4px"><button class="reply-submit-btn" onclick="gbSR(' +
      m.id +
      ')">提交</button><button class="reply-cancel-btn" onclick="gbTR(' +
      m.id +
      ')">取消</button></div></div>';
  });
  list.innerHTML = html;
}

function gbTR(id) {
  document.querySelectorAll(".reply-form.show").forEach((f) => {
    if (f.id !== "gbrf-" + id) f.classList.remove("show");
  });
  const form = document.getElementById("gbrf-" + id);
  form.classList.toggle("show");
  if (form.classList.contains("show")) {
    document.getElementById("gbrc-" + id).focus();
  }
}

async function gbSR(id) {
  const co = document.getElementById("gbrc-" + id).value.trim();
  if (!co) {
    showToast("请输入回复内容", "error");
    return;
  }
  try {
    await apiFetch("/api/guestbook/" + id + "/reply", { method: "POST", body: { content: co } });
    await loadPosts();
    showToast("回复成功", "success");
  } catch (e) {
    showToast(e.message || "回复失败", "error");
  }
}

function gbDelP(id) {
  confirmDialog("确认删除该留言？", async function () {
    try {
      await apiFetch("/api/guestbook/" + id, { method: "DELETE" });
      await loadPosts();
      showToast("已删除", "success");
    } catch (e) {
      showToast(e.message || "删除失败", "error");
    }
  });
}

function gbDelR(id) {
  confirmDialog("确认删除该回复？", async function () {
    try {
      await apiFetch("/api/guestbook/reply/" + id, { method: "DELETE" });
      await loadPosts();
      showToast("已删除", "success");
    } catch (e) {
      showToast(e.message || "删除失败", "error");
    }
  });
}

async function loadPosts() {
  const posts = await apiFetch("/api/guestbook");
  renderPosts(posts);
}

async function gbSubmit() {
  const subject = document.getElementById("postSubject").value.trim();
  const content = document.getElementById("postContent").value.trim();
  const me = document.querySelector(".mood-option.selected");
  const mood = me ? me.dataset.mood : "😊";
  if (!content) {
    showToast("请输入留言内容", "error");
    return;
  }
  try {
    await apiFetch("/api/guestbook", { method: "POST", body: { mood, subject, content } });
    document.getElementById("postSubject").value = "";
    document.getElementById("postContent").value = "";
    showToast("留言成功", "success");
    await loadPosts();
  } catch (e) {
    showToast(e.message || "留言失败", "error");
  }
}

function gbReset() {
  document.getElementById("postSubject").value = "";
  document.getElementById("postContent").value = "";
  document.querySelectorAll(".mood-option").forEach((m) => m.classList.remove("selected"));
  document.querySelector(".mood-option").classList.add("selected");
}

document.getElementById("moodSelect").addEventListener("click", function (e) {
  const o = e.target.closest(".mood-option");
  if (!o) return;
  document.querySelectorAll(".mood-option").forEach((m) => m.classList.remove("selected"));
  o.classList.add("selected");
});

document.getElementById("postContent").addEventListener("keydown", function (e) {
  if (e.ctrlKey && e.key === "Enter") gbSubmit();
});

(async function init() {
  try {
    const me = await apiFetch("/api/me");
    if (!me.user) {
      location.href = "/login";
      return;
    }
    currentUser = me.user;
    const nick = document.getElementById("postNick");
    if (nick) {
      nick.value = currentUser.username;
      nick.disabled = true;
    }
    const gender = document.getElementById("postGender");
    if (gender) {
      gender.value = currentUser.gender;
      gender.disabled = true;
    }
    await loadPosts();
  } catch (e) {
    showToast(e.message || "加载失败", "error");
  }
})();
