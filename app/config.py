"""
应用配置模块
读取环境变量，提供全局配置项。
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件（如果存在）
load_dotenv()

# ============================================================
# 数据库连接串，默认使用本地 SQLite
# 云部署时设置环境变量 DATABASE_URL 为 PostgreSQL 连接串即可
# ============================================================
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/words.db")

# Render 等平台提供的连接串常以 postgres:// 开头，
# 而 SQLAlchemy 2.0 只识别 postgresql://，此处做一次归一化。
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ============================================================
# 确保 data/ 目录存在（仅 SQLite 模式需要）
# ============================================================
if DATABASE_URL.startswith("sqlite"):
    db_path = DATABASE_URL.replace("sqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
