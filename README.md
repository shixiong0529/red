# Red Dragonfly Chat (FastAPI)

## 环境要求
- Python 3.12 或 3.13（当前 Python 3.14 无法编译 pydantic-core）

## 运行
1. 安装依赖
   - `python -m pip install -r requirements.txt`
2. 启动服务
   - `uvicorn app.main:app --reload`
3. 打开浏览器
   - `http://127.0.0.1:8000`

SQLite 数据库文件会在首次启动时生成：`red_dragonfly.db`

## 页面
- `/` 聊天大厅
- `/guestbook` 留言板
- `/settings` 个人设置
- `/profile` 资料页
- `/help` 帮助
- `/login` 注册/登录
