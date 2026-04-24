# 红蜻蜓聊天室部署说明

本项目是一个单进程 FastAPI 应用，使用 SQLite、Jinja2 模板、静态资源和 WebSocket 聊天接口。

## 当前已验证的部署方式

这份文档优先描述已经在生产环境跑通的部署方式：

- 服务器类型：阿里云轻量应用服务器
- 地域：武汉
- 运行方式：`systemd + uvicorn + nginx`
- 数据库：SQLite
- 正式域名：`chat.slow.best`
- HTTPS：Let's Encrypt 手动 DNS 验证

## 服务器建议配置

- 2 vCPU
- 2 GB RAM
- 40 GB 磁盘
- 有公网 IP

## 防火墙 / 安全放行

如果你使用的是阿里云轻量应用服务器，请在防火墙模板中放行：

- `22/tcp`
- `80/tcp`
- `443/tcp`

如果你使用的是标准 ECS，请在安全组中放行：

- `22/tcp`
- `80/tcp`
- `443/tcp`

## 1. 准备服务器

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx git
sudo useradd -r -s /usr/sbin/nologin www || true
sudo mkdir -p /opt/red
sudo mkdir -p /opt/red/data
```

## 2. 拉取项目代码

```bash
cd /opt/red
git clone <your-repo-url> current
cd current
```

如果你不是通过 Git 拉代码，也可以通过 `scp` 或其他方式把完整项目上传到 `/opt/red/current`。

## 3. 创建 Python 虚拟环境并安装依赖

```bash
cd /opt/red/current
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 4. 准备环境变量

```bash
cd /opt/red/current
cp .env.example .env
```

推荐的初始 `.env` 内容：

```env
DATABASE_URL=sqlite:////opt/red/data/red_dragonfly.db
SESSION_COOKIE_NAME=session
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_SAMESITE=lax
SESSION_COOKIE_DOMAIN=
```

## 5. 首次手动启动测试

```bash
cd /opt/red/current
. .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

临时测试地址：

```text
http://127.0.0.1:8000
```

确认服务可以启动后，按 `Ctrl + C` 停止，进入正式托管步骤。

## 6. 安装 systemd 服务

```bash
sudo cp /opt/red/current/deploy/red.service /etc/systemd/system/red.service
sudo chown -R www:www /opt/red/current
sudo chown -R www:www /opt/red/data
sudo systemctl daemon-reload
sudo systemctl enable --now red
sudo systemctl status red --no-pager
```

常用命令：

```bash
sudo journalctl -u red -f
sudo systemctl restart red
sudo systemctl stop red
```

## 7. 配置 nginx

```bash
sudo cp /opt/red/current/deploy/nginx-red.conf /etc/nginx/sites-available/red
sudo ln -sf /etc/nginx/sites-available/red /etc/nginx/sites-enabled/red
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

此时可以先通过公网 IP 测试：

```text
http://server-ip/
```

## 8. 绑定域名

在阿里云云解析 DNS 中添加：

- `chat` -> `A` -> 服务器公网 IP

如果你的主站 `slow.best` 和 `www.slow.best` 仍然指向 GitHub Pages，请保持它们原有记录不变，只新增 `chat` 这条记录即可。

## 9. 启用 HTTPS

首次启用 HTTPS 时，需要先为实际绑定的域名准备 Let's Encrypt 证书。证书签发、续期和故障处理步骤统一维护在 [OPERATIONS.md](./OPERATIONS.md)。

证书签发成功后，按服务器实际域名和证书路径更新 nginx 站点配置：

- nginx 站点配置：`/etc/nginx/sites-available/red`
- 证书目录：`/etc/letsencrypt/live/<域名>/`
- 项目内的基础反代配置模板：`deploy/nginx-red.conf`

然后执行：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

再把 `.env` 改成生产 HTTPS 模式：

```env
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_DOMAIN=
```

注意：如果同一应用同时通过多个根域名访问，例如 `chat.slow.best` 和 `shi.show`，不要把 `SESSION_COOKIE_DOMAIN` 写死为其中一个域名。留空会下发 host-only Cookie，两个域名都能各自保存登录态。

应用新配置：

```bash
sudo systemctl restart red
```

## 10. 更新项目

```bash
cd /opt/red/current
git pull
. .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart red
```

## 补充说明

- SQLite 适合当前这种轻量部署和中低并发场景。
- 如果后续并发增长，可以迁移到 MySQL 或 PostgreSQL，并通过 `DATABASE_URL` 切换。
- WebSocket 接口是 `/ws/chat`，当前 nginx 配置已经包含升级头支持。
- 应用首次启动时会从 `bak/` 目录中读取旧版页面素材和初始数据，因此生产环境请保留 `bak/`。
- 证书续期操作统一维护在 [OPERATIONS.md](./OPERATIONS.md)。
