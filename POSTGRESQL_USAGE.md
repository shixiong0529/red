# PostgreSQL 使用与改密说明

这份文档用于说明当前 `red` 项目在线上如何使用 PostgreSQL，以及后续如何安全修改数据库密码。

## 1. 当前线上数据库状态

当前线上项目已经从 SQLite 切换到 PostgreSQL。

项目代码目录：

```bash
/opt/red/current
```

线上 PostgreSQL 连接配置写在：

```bash
/opt/red/current/.env
```

当前数据库连接项示例：

```env
DATABASE_URL=postgresql://red_user:你的密码@127.0.0.1:5432/red_db
```

说明：

- `red_db` 是当前业务数据库名
- `red_user` 是当前业务数据库用户
- `127.0.0.1:5432` 表示 PostgreSQL 运行在服务器本机

## 2. 常用查看命令

### 查看当前项目使用的数据库连接

```bash
cat /opt/red/current/.env
```

作用：确认项目当前使用的是 PostgreSQL，而不是 SQLite。

### 查看 PostgreSQL 服务状态

```bash
systemctl status postgresql --no-pager
```

作用：确认 PostgreSQL 数据库服务是否正常运行。

### 查看聊天室服务状态

```bash
systemctl status red --no-pager
```

作用：确认 `red` 项目本身是否正常连接数据库并运行。

### 查看 PostgreSQL 中的用户数据量

```bash
sudo -u postgres psql -d red_db -c "SELECT count(*) FROM users;"
```

作用：快速确认新数据库中已经存在业务数据。

### 查看 PostgreSQL 中最新聊天记录

```bash
sudo -u postgres psql -d red_db -c "SELECT id, content, created_at FROM chat_messages ORDER BY id DESC LIMIT 5;"
```

作用：确认新消息确实写入了 PostgreSQL。

## 3. 如何修改数据库密码

推荐做法：只改密码，不改数据库用户名。

原因：

- 最稳
- 对线上影响最小
- 配置改动少

### 第一步：进入 PostgreSQL

```bash
sudo -u postgres psql
```

作用：以 PostgreSQL 管理员身份进入数据库控制台。

### 第二步：修改业务用户密码

```sql
ALTER USER red_user WITH PASSWORD '这里换成你的新强密码';
```

作用：把 `red_user` 的密码改成新密码。

### 第三步：退出 PostgreSQL

```sql
\q
```

作用：退出数据库控制台。

### 第四步：修改项目配置

```bash
sed -i 's#^DATABASE_URL=.*#DATABASE_URL=postgresql://red_user:你的新强密码@127.0.0.1:5432/red_db#' /opt/red/current/.env
```

作用：让项目连接串里的密码与数据库中的新密码保持一致。

### 第五步：检查配置

```bash
cat /opt/red/current/.env
```

作用：确认 `.env` 已经更新。

### 第六步：重启项目服务

```bash
systemctl restart red
```

作用：让新数据库密码生效。

### 第七步：确认项目恢复正常

```bash
systemctl status red --no-pager
```

作用：确认 `red` 服务能正常连接 PostgreSQL。

如果需要顺手确认日志没有报错：

```bash
journalctl -u red -n 50 --no-pager
```

作用：查看最近 50 行日志，确认没有数据库连接失败。

## 4. 服务器上执行 git pull 是否安全

结论：当前是安全的，但要知道边界。

### 不会被 git pull 覆盖的内容

这些内容不是 Git 仓库里的受控文件，`git pull` 不会直接覆盖：

- `/opt/red/current/.env`
- `/opt/red/data/red_dragonfly.db`
- PostgreSQL 数据库里的真实业务数据
- `/etc/systemd/system/red.service`
- `/etc/nginx/sites-available/red`

原因：

- `.env` 当前没有被 Git 跟踪
- SQLite 正式数据在 `/opt/red/data`，不在仓库里
- PostgreSQL 数据存在数据库服务里，不在 Git 仓库里
- systemd 和 nginx 真正生效的是系统目录里的副本，不是仓库里的模板文件

### 会被 git pull 更新的内容

这些属于仓库里的项目文件，`git pull` 会更新：

- Python 代码
- 前端 JS / CSS
- 模板文件
- 文档
- 脚本
- `deploy/` 目录中的模板文件

### 什么时候 git pull 可能出问题

如果服务器上你手工改过某些“已被 Git 跟踪”的文件，比如：

- `app/main.py`
- `static/js/chat.js`
- `README.md`

那执行 `git pull` 时，可能会出现冲突或被拒绝快进更新。

### 当前建议

服务器上日常可以放心执行：

```bash
cd /opt/red/current
git pull
```

然后再执行：

```bash
bash update.sh
```

作用：更新代码、安装依赖、重启服务。

## 5. 回滚说明

如果未来 PostgreSQL 出现问题，仍然可以回退到 SQLite。

### 把 `.env` 改回 SQLite

```env
DATABASE_URL=sqlite:////opt/red/data/red_dragonfly.db
```

### 重启服务

```bash
systemctl restart red
```

作用：把项目重新切回原来的 SQLite 数据库。

因此，当前建议继续保留：

```bash
/opt/red/data/red_dragonfly.db
```

作为回滚保险，不要急着删除。
