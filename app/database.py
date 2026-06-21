"""SQLite database setup and connection management."""

import sqlite3
from pathlib import Path

from loguru import logger

from app.config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    video_title TEXT DEFAULT '',
    channel TEXT DEFAULT '',
    duration TEXT DEFAULT '',
    language TEXT DEFAULT 'en',
    summary TEXT DEFAULT '',
    study_notes TEXT DEFAULT '',
    chapters TEXT DEFAULT '[]',
    key_points TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_history_video_id ON history(video_id);
CREATE INDEX IF NOT EXISTS idx_history_created ON history(created_at);
"""


def get_db() -> sqlite3.Connection:
    """Get a SQLite database connection."""
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Initialize the database schema."""
    conn = get_db()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
        logger.info("Database initialized at {}", settings.database_path)
    finally:
        conn.close()
