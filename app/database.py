"""
数据库模块
SQLAlchemy 2.0 声明式模型、会话管理、辅助函数。
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import (
    Column, String, Integer, DateTime, Index,
    create_engine, event, text
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

logger = logging.getLogger(__name__)

from app.config import DATABASE_URL

# ============================================================
# Engine 配置
# ============================================================
_engine_kwargs: dict = {}

if DATABASE_URL.startswith("sqlite"):
    # SQLite 专用：允许多线程访问
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_kwargs)

# SQLite 专用：启用 WAL 日志模式提升并发性能
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================
# 模型定义
# ============================================================
class Word(Base):
    """单词表"""
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, autoincrement=True)
    spanish = Column(String, nullable=False, unique=True)
    english = Column(String, nullable=True)
    chinese = Column(String, nullable=True)
    status = Column(String, default="active")  # active / favorite / killed
    created_at = Column(DateTime, default=datetime.utcnow)
    last_reviewed_at = Column(DateTime, nullable=True)

    # 复合索引：加速按状态+复习时间的查询
    __table_args__ = (
        Index("idx_status_reviewed", "status", "last_reviewed_at"),
    )


class Setting(Base):
    """设置表（key-value 存储）"""
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=True)


# ============================================================
# 建表 & 初始化默认设置
# ============================================================
def init_db():
    """创建所有表，并写入默认设置（如果不存在）"""
    Base.metadata.create_all(bind=engine)

    # 默认设置项
    defaults = {
        "ai_provider": "qwen",
        "quiz_days": "3",
        "quiz_limit": "20",
    }
    db = SessionLocal()
    try:
        for k, v in defaults.items():
            existing = db.query(Setting).filter(Setting.key == k).first()
            if not existing:
                db.add(Setting(key=k, value=v))
        db.commit()
    finally:
        db.close()


# ============================================================
# 播种初始数据
# ============================================================
def seed_words():
    """首次启动时，如果 words 表为空且种子文件存在，则批量导入初始单词。"""
    seed_file = Path(__file__).parent.parent / "seed" / "initial_words.json"
    if not seed_file.exists():
        return

    db = SessionLocal()
    try:
        count = db.query(Word).count()
        if count > 0:
            return

        with open(seed_file, "r", encoding="utf-8") as f:
            words_data = json.load(f)

        seen: set = set()
        for item in words_data:
            spanish = (item.get("spanish") or "").strip()
            if not spanish or spanish in seen:
                continue
            seen.add(spanish)
            db.add(Word(
                spanish=spanish,
                english=(item.get("english") or "").strip() or None,
                chinese=(item.get("chinese") or "").strip() or None,
            ))

        db.commit()
        logger.info(f"Seeded {len(seen)} words from seed/initial_words.json")
        print(f"Seeded {len(seen)} words from seed/initial_words.json")
    finally:
        db.close()


# 应用启动时自动初始化
init_db()
seed_words()


# ============================================================
# 依赖注入：获取数据库会话
# ============================================================
def get_db() -> Generator[Session, None, None]:
    """FastAPI Depends 用的数据库会话生成器"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# 辅助函数：读写设置
# ============================================================
def get_setting(db: Session, key: str) -> Optional[str]:
    """获取单个设置值"""
    row = db.query(Setting).filter(Setting.key == key).first()
    return row.value if row else None


def set_setting(db: Session, key: str, value: str):
    """设置单个值（存在则更新，不存在则插入）"""
    row = db.query(Setting).filter(Setting.key == key).first()
    if row:
        row.value = value
    else:
        db.add(Setting(key=key, value=value))
    db.commit()
