from bot.db.sqlite import Database
from bot.utils.logger import get_logger

logger = get_logger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL UNIQUE,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    raw_text TEXT NOT NULL,
    sentiment TEXT NOT NULL,
    review_type TEXT NOT NULL,
    topic TEXT NOT NULL,
    short_summary TEXT NOT NULL,
    escalation_required INTEGER NOT NULL DEFAULT 0,
    suggested_reply TEXT NOT NULL,
    analysis_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reviews_sentiment ON reviews(sentiment);
CREATE INDEX IF NOT EXISTS idx_reviews_topic ON reviews(topic);
CREATE INDEX IF NOT EXISTS idx_reviews_escalation ON reviews(escalation_required);
CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews(created_at DESC);
"""


async def run_migrations(db: Database) -> None:
    conn = await db.connect()
    await conn.executescript(SCHEMA_SQL)
    await db.commit()
    logger.info("Database schema initialized")
