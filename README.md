# Red

一个复古风格的轻量聊天室网站，基于 `FastAPI + Jinja2 + 原生 JavaScript + WebSocket` 构建。

项目保留了早期网页聊天室的视觉风格，同时补齐了现代 Web 服务常见的部署、运维和数据迁移能力，适合做个人站点、怀旧作品展示和轻量在线互动项目。

## 当前线上状态

- 正式地址：`https://chat.slow.best`
- 部署环境：阿里云轻量应用服务器（武汉）
- 运行方式：`systemd + uvicorn + nginx`
- HTTPS：已启用
- 当前线上数据库：`PostgreSQL`
- 保留回滚库：`SQLite`

## 项目特点

- 复古聊天室视觉风格
- 支持注册、登录、在线聊天
- 支持公聊和私聊
- 支持留言板
- 支持个人资料与个人设置
- 支持管理员后台
- 支持 WebSocket 实时在线状态与消息推送
- 支持从 SQLite 升级到 PostgreSQL

## 技术栈

### 后端

- FastAPI
- SQLAlchemy
- Pydantic
- Passlib
- Uvicorn

### 前端

- Jinja2 Templates
- HTML / CSS / JavaScript
- WebSocket

### 数据库

- SQLite：本地开发、历史兼容、回滚备用
- PostgreSQL：当前线上正式数据库

## 项目结构

```text
red/
├─ app/
│  ├─ main.py
│  ├─ models.py
│  ├─ crud.py
│  ├─ schemas.py
│  ├─ deps.py
│  ├─ db.py
│  ├─ config.py
│  ├─ security.py
│  ├─ ws.py
│  ├─ seed.py
│  └─ bots.py
├─ templates/
├─ static/
├─ scripts/
├─ deploy/
├─ bak/
├─ requirements.txt
├─ update.sh
├─ DEPLOY.md
├─ OPERATIONS.md
├─ POSTGRESQL_MIGRATION.md
├─ POSTGRESQL_USAGE.md
└─ red-技术架构与功能模块.md
```

## 运行环境

- Python 3.12 或 3.13
- 本地开发可使用 SQLite
- 生产环境推荐 PostgreSQL

## 本地启动

### 1. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 2. 启动项目

```bash
uvicorn app.main:app --reload
```

### 3. 访问地址

```text
http://127.0.0.1:8000
```

## 数据库说明

项目通过 `DATABASE_URL` 切换数据库类型。

### SQLite 示例

```env
DATABASE_URL=sqlite:///./red_dragonfly.db
```

### PostgreSQL 示例

```env
DATABASE_URL=postgresql://red_user:your_password@127.0.0.1:5432/red_db
```

### 当前线上使用方式

线上项目已经切换到 PostgreSQL，正式业务数据写入 PostgreSQL。

同时仍然保留原 SQLite 数据文件，作为回滚保险，不建议立即删除。

## 页面入口

- `/`：聊天大厅
- `/guestbook`：留言板
- `/settings`：个人设置
- `/profile`：个人资料
- `/help`：帮助页面
- `/login`：登录 / 注册
- `/admin`：后台管理

## 登录与实时通信

### 登录方式

项目使用 Cookie + Session 方案管理登录状态。

- 登录成功后生成 `session token`
- token 写入 cookie
- 服务端从 cookie 中读取 token 恢复登录状态

### 实时聊天

聊天室使用 WebSocket：

- 普通页面数据通过 HTTP API 获取
- 聊天消息和在线状态通过 `/ws/chat` 实时推送

## 初始化与历史兼容

项目保留了一些复古站点素材和历史结构，便于还原聊天室体验。

同时，数据库层已经升级为“可切换”模式：

- 可以继续使用 SQLite
- 也可以切换到 PostgreSQL
- 已提供 SQLite -> PostgreSQL 迁移脚本

## 常用运维

### 更新项目

```bash
bash update.sh
```

作用：

- 拉取最新代码
- 安装依赖
- 重启 `red`
- 输出服务状态

补充说明：

- 这个脚本适合日常代码更新
- 执行它会重启聊天室服务
- 它不会修改 `.env`
- 它不会主动变更 PostgreSQL 数据
- 它不会修改 nginx 或证书配置

### 手动续签 HTTPS 证书

当前线上证书续期步骤统一维护在：

- [OPERATIONS.md](./OPERATIONS.md)

## 相关文档

- [DEPLOY.md](./DEPLOY.md)
- [OPERATIONS.md](./OPERATIONS.md)
- [POSTGRESQL_MIGRATION.md](./POSTGRESQL_MIGRATION.md)
- [POSTGRESQL_USAGE.md](./POSTGRESQL_USAGE.md)
- [red-技术架构与功能模块.md](./red-技术架构与功能模块.md)

## 后续可继续增强的方向

- PostgreSQL 备份与恢复脚本
- Alembic 数据库迁移管理
- 更完整的后台审计功能
- 聊天记录分页与搜索
- 自动续签 HTTPS 证书

## License

当前仓库未单独提供正式 License 文件。如需公开分发或商用，请先补充许可证说明。
