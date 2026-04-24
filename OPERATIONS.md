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

当前线上证书：

- `chat.slow.best`：到期时间 `2026-07-09`
- `shi.show` / `www.shi.show`：到期时间 `2026-07-23`

重要说明：

- `certbot.timer` 虽然存在，但当前 `certbot renew --dry-run` 会因为 HTTP webroot 验证返回 `403` 而失败。
- 在没有重新修好 ACME HTTP 验证路径前，不要依赖自动续期。
- 建议在证书到期前 2 周手动续期。

### 推荐手动续期方式

临时停止 nginx，用 certbot standalone 模式续期。这个方式不依赖 nginx 的 `/.well-known/acme-challenge/` 配置，只需要 80 端口能被 certbot 临时占用。

1. 先确认当前证书和 nginx 状态：

```bash
sudo certbot certificates
sudo systemctl status nginx --no-pager
```

作用：确认两张证书当前存在，并确认 nginx 正在运行。

2. 停止 nginx，释放 80 端口：

```bash
sudo systemctl stop nginx
```

作用：standalone 模式会临时启动一个验证服务，占用 80 端口。nginx 不停掉时，certbot 通常会因为端口被占用而失败。

3. 续签 `chat.slow.best`：

```bash
sudo certbot certonly --standalone --force-renewal \
  --cert-name chat.slow.best \
  -d chat.slow.best
```

作用：重新签发 `/etc/letsencrypt/live/chat.slow.best/` 这套证书。

4. 续签 `shi.show` 和 `www.shi.show`：

```bash
sudo certbot certonly --standalone --force-renewal \
  --cert-name shi.show \
  -d shi.show \
  -d www.shi.show
```

作用：重新签发 `/etc/letsencrypt/live/shi.show/` 这套证书。这里必须同时带上 `shi.show` 和 `www.shi.show`，否则可能会把原证书覆盖成只包含一个域名。

5. 无论续签成功还是失败，都要重新启动 nginx：

```bash
sudo systemctl start nginx
```

作用：恢复网站访问。

6. 检查 nginx 和证书列表：

```bash
sudo nginx -t
sudo systemctl status nginx --no-pager
sudo certbot certificates
```

作用：确认 nginx 配置语法正常、服务已经启动，并确认 `Expiry Date` 已经更新。

7. 检查两个网站是否正常返回：

```bash
curl -L https://chat.slow.best/ -o /dev/null -w "%{http_code}\n"
curl -L https://shi.show/ -o /dev/null -w "%{http_code}\n"
```

两个域名都返回 `200`，并且 `sudo certbot certificates` 里的到期时间已经更新，就说明续期成功。

注意：停止 nginx 期间网站会短暂不可访问，建议在低访问时段操作。

### 如果中途失败

如果 certbot 失败，先恢复 nginx：

```bash
sudo systemctl start nginx
sudo systemctl status nginx --no-pager
```

然后查看失败原因：

```bash
sudo journalctl -u nginx -n 80 --no-pager
sudo tail -n 120 /var/log/letsencrypt/letsencrypt.log
```

常见原因：

- 80 端口没有放行。
- nginx 没有真正停掉，80 端口仍被占用。
- 域名 DNS 没有指向当前服务器公网 IP。
- `www.shi.show` 没有解析到当前服务器，但续签命令里包含了它。

### 如果要恢复自动续期

当前自动续期失败的直接原因是 ACME HTTP 验证地址返回 `403`。如果后续要恢复 `certbot renew` 自动续期，需要先修好 nginx 对 `/.well-known/acme-challenge/` 的访问，再运行：

```bash
sudo certbot renew --dry-run
```

只有 dry-run 全部成功后，才能认为自动续期可靠。

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
