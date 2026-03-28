async function loginSubmit() {
  const username = document.getElementById("loginNick").value.trim();
  const password = document.getElementById("loginPass").value.trim();
  if (!username || !password) {
    showToast("请输入昵称和密码", "error");
    return;
  }
  try {
    await apiFetch("/api/auth/login", { method: "POST", body: { username, password } });
    showToast("登录成功", "success");
    setTimeout(() => (location.href = "/"), 500);
  } catch (e) {
    const msg = String(e.message || "");
    if (msg === "Invalid credentials") showToast("账号或密码错误（如未注册请先点“注册”）", "error");
    else showToast(msg || "登录失败", "error");
  }
}

async function registerSubmit() {
  const username = document.getElementById("loginNick").value.trim();
  const password = document.getElementById("loginPass").value.trim();
  const gender = document.getElementById("loginGender").value;
  if (!username || !password) {
    showToast("请输入昵称和密码", "error");
    return;
  }
  try {
    await apiFetch("/api/auth/register", { method: "POST", body: { username, password, gender } });
    showToast("注册成功", "success");
    setTimeout(() => (location.href = "/"), 500);
  } catch (e) {
    const msg = String(e.message || "");
    if (msg === "Username exists") showToast("用户名已存在，请换一个或直接登录", "error");
    else if (msg === "Username must be alphanumeric") showToast("用户名只能包含字母和数字", "error");
    else if (msg === "Password too short") showToast("密码太短（至少 4 位）", "error");
    else showToast(msg || "注册失败", "error");
  }
}

document.getElementById("loginPass").addEventListener("keydown", function (e) {
  if (e.key === "Enter") loginSubmit();
});
