# 西班牙语背单词 App

## 本地启动（macOS）

1. 双击 `start.command` 即可自动完成：创建虚拟环境 → 安装依赖 → 打开浏览器 → 启动服务。
2. 首次启动需联网下载依赖，之后离线可用。
3. 关闭终端窗口即停止服务。

## 拷贝到新电脑

将整个项目文件夹复制到新电脑，确保安装了 Python 3.9+，然后双击 `start.command`。
虚拟环境和数据库会自动重建（data/words.db 如需保留历史数据请一并拷贝）。

## 云部署（Render / PostgreSQL）

1. 设置环境变量 `DATABASE_URL` 为 PostgreSQL 连接串（如 `postgresql://user:pass@host:5432/dbname`）。
2. 安装 `requirements-cloud.txt`（含 psycopg2-binary）。
3. 启动命令：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`。
4. 参考 `render.yaml` 一键部署到 Render。
