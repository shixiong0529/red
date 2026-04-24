# 红蜻蜓聊天室运维手册

这份文档是生产环境站点的日常运维清单。

- 站点地址：`https://chat.slow.best`
- 应用服务：`red`
- 反向代理：`nginx`
- 项目目录：`/opt/red/current`
- 数据目录：`/opt/red/data`

## 1. 快速检查服务状态

```bash
systemctl status red --no-pager
```

作用：检查 FastAPI 聊天室服务是否正常运行。

```bash
systemctl status nginx --no-pager
```

作用：检查 nginx 是否正常运行。

```bash
ss -lntp | grep -E ':80|:443|:8000'
```

作用：确认 `80`、`443`、`8000` 这些端口是否正在监听。

## 2. 查看日志

```bash
journalctl -u red -f
```

作用：实时查看聊天室应用日志。

```bash
journalctl -u nginx -f
```

作用：实时查看 nginx 日志。

## 3. 重启服务

```bash
systemctl restart red
```

作用：在代码或配置变更后重启聊天室应用。

```bash
systemctl reload nginx
```

作用：修改 nginx 配置后平滑重载，不中断现有连接。

```bash
systemctl restart nginx
```

作用：如果 `reload` 不够，就完整重启 nginx。

## 4. 更新项目代码

推荐优先使用项目自带脚本：

```bash
bash update.sh
```

作用：一键拉取最新代码、安装依赖、重启 `red` 服务，并检查服务状态。

如果你希望手动执行，也可以使用下面这组命令：

```bash
cd /opt/red/current
git pull
. .venv/bin/activate
pip install -r requirements.txt
systemctl restart red
```

作用：拉取最新代码、刷新依赖并重启应用。

## 5. 检查生产环境配置

```bash
cat /opt/red/current/.env
```

作用：查看当前线上正在使用的环境变量配置。

生产环境推荐值如下：

```env
DATABASE_URL=sqlite:////opt/red/data/red_dragonfly.db
SESSION_COOKIE_NAME=session
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=lax
SESSION_COOKIE_DOMAIN=
```

如果同一套服务同时挂多个互不隶属的域名，例如 `chat.slow.best` 和 `shi.show`，`SESSION_COOKIE_DOMAIN` 必须留空。写死为 `chat.slow.best` 时，浏览器访问 `shi.show` 会拒收登录接口返回的 session Cookie，表现为登录接口成功但仍停留在登录页。

## 6. 验证站点可用性

```bash
curl -I http://chat.slow.best
```

作用：确认 HTTP 是否会跳转到 HTTPS。

```bash
curl -I https://chat.slow.best/login
```

作用：确认 HTTPS 登录页是否可达。

```bash
curl -iL http://chat.slow.best
```

作用：跟随完整跳转链路，确认最终页面是否能正常返回。

## 7. 备份数据库

```bash
cp /opt/red/data/red_dragonfly.db /opt/red/data/red_dragonfly.db.bak.$(date +%F-%H%M%S)
```

作用：在升级或风险操作前，创建带时间戳的 SQLite 备份文件。

如果当前线上已经切到 PostgreSQL，再额外执行：

```bash
sudo -u postgres pg_dump -d red_db > /opt/red/data/red_db.$(date +%F-%H%M%S).sql
```

作用：导出当前 PostgreSQL 数据库为 SQL 备份文件，方便后续恢复。

如果需要从 PostgreSQL 备份恢复：

```bash
sudo -u postgres psql -d red_db < /opt/red/data/你的备份文件.sql
```

作用：把指定 SQL 备份重新导入到 `red_db`。

## 8. HTTPS 证书续期

当前证书信息：

- 域名：`chat.slow.best`
- 续期方式：手动 DNS 验证
- 到期时间：`2026-07-09`

重要说明：

- 当前证书不会自动续期。
- 必须在到期前手动续签。
- 建议在 `2026-06-25` 左右设置提醒。

续签命令：

```bash
certbot certonly --manual --preferred-challenges dns --key-type rsa --cert-name chat.slow.best -d chat.slow.best --force-renewal
```

作用：通过 DNS TXT 验证方式，重新签发线上使用的 RSA 证书。

执行到提示时，需要在阿里云 DNS 中新增一条 TXT 记录：

- 记录类型：`TXT`
- 主机记录：`_acme-challenge.chat`
- 记录值：`certbot` 输出的那串验证值

TXT 记录生效后，先执行：

```bash
dig TXT _acme-challenge.chat.slow.best +short
```

作用：确认 DNS 验证记录已经生效，再回到 certbot 继续。

证书签发成功后，执行：

```bash
systemctl reload nginx
```

作用：让 nginx 重新加载新证书。

检查新证书是否生效：

```bash
curl -Iv https://chat.slow.best
```

作用：确认 HTTPS 证书校验正常。

### 手动续证极简版

如果你不打算现在改造成自动续期，以后每次手动续证只需要按下面做：

1. 登录服务器，执行下面这条命令：

```bash
certbot certonly --manual --preferred-challenges dns --key-type rsa --cert-name chat.slow.best -d chat.slow.best --force-renewal
```

作用：向 Let's Encrypt 申请重新签发 `chat.slow.best` 的证书。

2. 看到提示后，去阿里云 DNS 控制台添加一条 TXT 记录：

- 主机记录：`_acme-challenge.chat`
- 记录类型：`TXT`
- 记录值：使用 certbot 当次输出的那一串随机字符串

作用：告诉证书机构“这个域名确实由我控制”。

3. 在服务器上执行：

```bash
dig TXT _acme-challenge.chat.slow.best +short
```

作用：确认 TXT 记录已经生效。

4. 回到刚才运行 certbot 的窗口，按回车继续。

作用：让 certbot 完成验证并签发新证书。

5. 证书签发成功后，执行：

```bash
systemctl reload nginx
```

作用：让 nginx 重新加载新证书。

6. 最后执行：

```bash
curl -Iv https://chat.slow.best
```

作用：确认新证书已经生效，HTTPS 校验正常。

7. 可选操作：回到阿里云 DNS，删除 `_acme-challenge.chat` 这条临时 TXT 记录。

作用：清理续证时临时添加的验证记录。

一句话总结：

- 运行 certbot
- 按提示去阿里云加 TXT
- 等 TXT 生效
- 回车完成签证
- reload nginx

## 9. 常见故障排查

如果应用无法启动：

```bash
journalctl -u red -n 100 --no-pager
```

作用：查看最近 100 行应用启动日志，定位错误原因。

如果修改过 nginx 配置：

```bash
nginx -t
```

作用：在 reload 或 restart 前检查 nginx 配置语法是否正确。

如果 HTTPS 看起来异常：

```bash
echo | openssl s_client -connect chat.slow.best:443 -servername chat.slow.best 2>/dev/null | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

作用：查看 nginx 当前实际对外提供的证书信息。

如果浏览器打不开 HTTPS，但服务器本机看起来正常：

- 重新检查轻量应用服务器的防火墙模板
- 确认 `80` 和 `443` 端口已经放行
- 用浏览器无痕窗口测试
- 如有需要，清理本地 DNS 缓存

## 10. 常用文件位置

- 应用服务文件：`/etc/systemd/system/red.service`
- nginx 站点配置：`/etc/nginx/sites-available/red`
- TLS 证书目录：`/etc/letsencrypt/live/chat.slow.best/`
- 应用环境变量文件：`/opt/red/current/.env`
- SQLite 数据库文件：`/opt/red/data/red_dragonfly.db`
