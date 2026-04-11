# PostgreSQL 升级与迁移说明

这份文档用于把当前项目从 SQLite 升级为 PostgreSQL，并在本地验证成功后迁移到阿里云服务器。

## 本次升级范围

- 项目代码同时支持 SQLite 和 PostgreSQL
- 新增 PostgreSQL 驱动依赖
- 新增 SQLite -> PostgreSQL 数据迁移脚本
- 保持原有 `DATABASE_URL` 环境变量切换方式

## 已完成的代码改造

- [requirements.txt](./requirements.txt) 新增 `psycopg[binary]`
- [app/config.py](./app/config.py) 支持把 `postgres://` 和 `postgresql://` 自动规范为 `postgresql+psycopg://`
- [app/db.py](./app/db.py) 已兼容 PostgreSQL 连接
- [scripts/migrate_sqlite_to_postgres.py](./scripts/migrate_sqlite_to_postgres.py) 可用于迁移现有 SQLite 数据

## 一、先在本地验证 PostgreSQL

### 1. 安装 PostgreSQL

你可以用本机安装方式，或直接使用 Docker。

示例 Docker 命令：

```bash
docker run --name red-postgres ^
  -e POSTGRES_USER=red_user ^
  -e POSTGRES_PASSWORD=red_pass ^
  -e POSTGRES_DB=red_db ^
  -p 5432:5432 ^
  -d postgres:16
```

作用：本地快速启动一个 PostgreSQL 16 容器。

### 2. 安装新依赖

```bash
python -m pip install -r requirements.txt
```

作用：安装 PostgreSQL 驱动。

### 3. 准备本地 PostgreSQL 连接串

示例：

```env
DATABASE_URL=postgresql://red_user:red_pass@127.0.0.1:5432/red_db
```

### 4. 迁移本地 SQLite 数据到 PostgreSQL

PowerShell 示例：

```powershell
$env:POSTGRES_URL="postgresql://red_user:red_pass@127.0.0.1:5432/red_db"
$env:SQLITE_PATH="c:\Users\Administrator\Desktop\red\red_dragonfly.db"
python scripts\migrate_sqlite_to_postgres.py
```

作用：把当前 SQLite 数据导入 PostgreSQL。

### 5. 用 PostgreSQL 启动项目

PowerShell 示例：

```powershell
$env:DATABASE_URL="postgresql://red_user:red_pass@127.0.0.1:5432/red_db"
uvicorn app.main:app --reload
```

作用：用 PostgreSQL 作为主数据库启动本地项目。

### 6. 本地验收清单

至少验证这些功能：

- 注册
- 登录
- 聊天大厅历史消息
- WebSocket 实时消息
- 留言板发帖与回复
- 个人资料修改
- 后台管理页

## 二、迁移到阿里云服务器

建议先在服务器上安装 PostgreSQL，再迁移数据，确认无误后再把 `.env` 切到 PostgreSQL。

### 1. 在服务器安装 PostgreSQL

Ubuntu 示例：

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
```

### 2. 创建数据库和用户

```bash
sudo -u postgres psql
```

进入 PostgreSQL 后执行：

```sql
CREATE USER red_user WITH PASSWORD 'replace_me';
CREATE DATABASE red_db OWNER red_user;
\q
```

### 3. 在服务器安装项目新依赖

```bash
cd /opt/red/current
. .venv/bin/activate
pip install -r requirements.txt
```

### 4. 迁移服务器现有 SQLite 数据

```bash
cd /opt/red/current
. .venv/bin/activate
export POSTGRES_URL="postgresql://red_user:replace_me@127.0.0.1:5432/red_db"
export SQLITE_PATH="/opt/red/data/red_dragonfly.db"
python scripts/migrate_sqlite_to_postgres.py
```

作用：把当前线上 SQLite 数据导入服务器本机 PostgreSQL。

### 5. 修改服务器 `.env`

把：

```env
DATABASE_URL=sqlite:////opt/red/data/red_dragonfly.db
```

改成：

```env
DATABASE_URL=postgresql://red_user:replace_me@127.0.0.1:5432/red_db
```

### 6. 重启服务

```bash
systemctl restart red
systemctl status red --no-pager
```

## 三、切换前建议

正式切库前，建议先做这两件事：

### 1. 备份当前 SQLite

```bash
cp /opt/red/data/red_dragonfly.db /opt/red/data/red_dragonfly.db.bak.$(date +%F-%H%M%S)
```

### 2. 保留回滚路径

如果 PostgreSQL 切换后发现问题，只需要把 `.env` 中的 `DATABASE_URL` 改回 SQLite 路径，再重启：

```env
DATABASE_URL=sqlite:////opt/red/data/red_dragonfly.db
```

```bash
systemctl restart red
```

## 四、今天的推荐节奏

最稳的推进方式是：

1. 本地启动 PostgreSQL
2. 本地跑迁移脚本
3. 本地用 PostgreSQL 启动并测试
4. 本地验证通过后，再去阿里云安装 PostgreSQL
5. 迁移服务器 SQLite 数据
6. 修改 `.env` 切换到 PostgreSQL

这样风险最小，也最容易回滚。
