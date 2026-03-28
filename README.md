# Red

一个复古风格的轻量聊天室网站，基于 `FastAPI + SQLite + Jinja2 + 原生 JavaScript + WebSocket` 构建。

项目目前已经从早期静态页面原型演进为可运行的动态 Web 应用，支持用户注册登录、实时聊天、留言板、个人资料、后台管理和机器人陪聊。

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
│  ├─ main.py          # 应用入口，页面/API/WebSocket 路由
│  ├─ models.py        # 数据模型
│  ├─ crud.py          # 数据访问逻辑
│  ├─ schemas.py       # 请求/响应模型
│  ├─ deps.py          # 依赖注入与登录态解析
│  ├─ db.py            # 数据库连接配置
│  ├─ security.py      # 密码哈希、token、session
│  ├─ ws.py            # WebSocket 连接管理
│  ├─ seed.py          # 启动时种子数据初始化
│  └─ bots.py          # 机器人逻辑
├─ templates/          # 页面模板
├─ static/
│  ├─ css/             # 样式文件
│  └─ js/              # 页面脚本
├─ bak/                # 旧版页面素材，初始化数据仍会读取
├─ red_dragonfly.db    # SQLite 数据库文件
├─ requirements.txt    # Python 依赖清单
└─ red-技术架构与功能模块.md
```

## 运行环境

- Python 3.12 或 3.13

说明：

- 当前项目依赖版本对 Python 3.14 兼容性不稳定，不建议直接使用 3.14 运行

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

- 登录成功后后端生成 session token
- token 写入浏览器 cookie
- 后续请求通过 cookie 识别当前用户

### 聊天通信

聊天室消息分两部分：

- 历史消息通过 HTTP API 拉取
- 实时消息通过 WebSocket `/ws/chat` 收发

### 房间机制

当前项目支持用户切换房间并记录房间状态，但消息广播逻辑仍以全局广播为主，房间隔离能力还不是严格频道模型。

## 相关文档

- [red-技术架构与功能模块.md](./red-技术架构与功能模块.md)

该文档中包含：

- 技术架构说明
- 功能模块清单
- Mermaid 架构图
- Mermaid 请求流转图

## 适用场景

这个项目适合：

- 小型聊天室网站
- 复古社区风格页面
- 原型改造为可运行 Web 应用
- 本地部署或轻量服务器部署

## 后续可演进方向

- 将房间逻辑改为真正隔离的频道广播
- 将 SQLite 升级到 MySQL 或 PostgreSQL
- 增加消息审核和敏感词过滤
- 增加头像上传和文件消息
- 将前端交互进一步组件化

## License

当前仓库未单独声明 License，如需开源或对外分发，建议补充许可证文件。
