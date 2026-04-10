# Red

一个复古风格的轻量聊天室网站，基于 `FastAPI + SQLite + Jinja2 + 原生 JavaScript + WebSocket` 构建。

项目已经从早期静态原型演进为可运行的 Web 应用，支持用户注册登录、实时聊天、留言板、个人资料、后台管理和机器人陪聊。

## 当前线上状态

- 正式地址：`https://chat.slow.best`
- 当前部署环境：阿里云轻量应用服务器
- 运行方式：`systemd + uvicorn + nginx`
- HTTPS：已启用

## 功能概览

- 用户注册、登录、退出
- 聊天大厅实时收发消息
- 在线用户列表
- 私聊消息与动作消息
- 留言板发帖、回复、删除
- 个人资料查看与编辑
- 管理员后台基础管理
- 机器人账号与自动发言

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

### 数据存储

- SQLite

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
├─ deploy/
├─ bak/
├─ red_dragonfly.db
├─ requirements.txt
├─ DEPLOY.md
├─ OPERATIONS.md
└─ red-技术架构与功能模块.md
```

## 运行环境

- Python 3.12 或 3.13

说明：

- 当前依赖版本对 Python 3.14 没有验证，不建议直接使用 3.14 运行。

## 安装与启动

### 1. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 2. 启动服务

```bash
uvicorn app.main:app --reload
```

### 3. 打开浏览器

```text
http://127.0.0.1:8000
```

## 页面入口

- `/`：聊天大厅
- `/guestbook`：留言板
- `/settings`：个人设置
- `/profile`：个人资料
- `/help`：帮助页
- `/login`：注册 / 登录
- `/admin`：后台管理

## 数据说明

项目默认使用本地 SQLite：

- 数据文件：`red_dragonfly.db`

数据库中主要包含以下几类数据：

- 用户账号
- 用户资料
- 登录会话
- 聊天记录
- 留言板帖子与回复
- 用户当前房间状态

## 初始化机制

应用首次启动时会自动执行以下动作：

- 创建数据库表
- 从 `bak/red-dragonfly-chatroom.html` 读取旧版素材
- 初始化机器人账号
- 初始化部分留言板和聊天历史
- 启动后台机器人发言任务

这意味着 `bak/` 目录目前仍然是运行相关目录，不建议删除。

## 开发说明

### 登录态

项目使用 Cookie + Session 机制维持登录状态：

- 登录成功后后端生成 `session token`
- token 写入浏览器 cookie
- 后续请求通过 cookie 识别当前用户

### 聊天通信

聊天室消息分两部分：

- 历史消息通过 HTTP API 拉取
- 实时消息通过 WebSocket `/ws/chat` 收发

### 房间机制

当前项目支持用户切换房间并记录房间状态，但消息广播逻辑目前仍以全局广播为主，房间隔离还不是严格频道模型。

## 相关文档

- [red-技术架构与功能模块.md](./red-技术架构与功能模块.md)
- [DEPLOY.md](./DEPLOY.md)
- [OPERATIONS.md](./OPERATIONS.md)
- [deploy/ACME_AUTORENEW.md](./deploy/ACME_AUTORENEW.md)

## 更新项目

服务器更新推荐直接执行：

```bash
bash update.sh
```

这个脚本会自动完成：

- 拉取最新代码
- 安装依赖
- 重启 `red` 服务
- 检查服务状态

## 适用场景

- 小型聊天室网站
- 复古社区风格页面
- 静态原型改造成可运行 Web 应用
- 本地部署或轻量服务器部署

## 后续可演进方向

- 将房间逻辑改为真正隔离的频道广播
- 将 SQLite 升级到 MySQL 或 PostgreSQL
- 增加消息审核和敏感词过滤
- 增加头像上传和文件消息
- 将前端交互进一步组件化

## License

当前仓库未单独声明 License，如需开源或对外分发，建议补充许可证文件。
