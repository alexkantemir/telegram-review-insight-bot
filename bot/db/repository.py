import json
from datetime import datetime

from aiogram.types import User

from bot.db.models import ReviewRecord, TelegramUserRecord
from bot.db.sqlite import Database
from bot.schemas.review_analysis import ReviewAnalysis


class ReviewRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def upsert_user(self, user: User) -> TelegramUserRecord:
        await self._db.execute(
            """
            INSERT INTO users (telegram_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name
            """,
            (
                user.id,
                user.username,
                user.first_name,
                user.last_name,
            ),
        )
        await self._db.commit()
        cursor = await self._db.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (user.id,),
        )
        row = await cursor.fetchone()
        if row is None:
            raise RuntimeError("Failed to upsert user")
        return self._row_to_user(row)

    async def save_review(
        self,
        user_id: int,
        raw_text: str,
        analysis: ReviewAnalysis,
    ) -> ReviewRecord:
        analysis_json = analysis.model_dump_json()
        cursor = await self._db.execute(
            """
            INSERT INTO reviews (
                user_id, raw_text, sentiment, review_type, topic,
                short_summary, escalation_required, suggested_reply, analysis_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                raw_text,
                analysis.sentiment.value,
                analysis.review_type.value,
                analysis.topic.value,
                analysis.short_summary,
                int(analysis.escalation_required),
                analysis.suggested_reply,
                analysis_json,
            ),
        )
        await self._db.commit()
        review_id = cursor.lastrowid
        if review_id is None:
            raise RuntimeError("Failed to insert review")
        return await self.get_review_by_id(review_id)

    async def get_review_by_id(self, review_id: int) -> ReviewRecord:
        cursor = await self._db.execute(
            "SELECT * FROM reviews WHERE id = ?",
            (review_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            raise ValueError(f"Review {review_id} not found")
        return self._row_to_review(row)

    async def get_last_reviews(self, limit: int = 10) -> list[dict]:
        cursor = await self._db.execute(
            """
            SELECT id, raw_text, sentiment, review_type, topic,
                   short_summary, escalation_required, created_at
            FROM reviews
            ORDER BY datetime(created_at) DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": row["id"],
                "raw_text": row["raw_text"],
                "sentiment": row["sentiment"],
                "review_type": row["review_type"],
                "topic": row["topic"],
                "short_summary": row["short_summary"],
                "escalation_required": bool(row["escalation_required"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    async def count_reviews(self) -> int:
        cursor = await self._db.execute("SELECT COUNT(*) AS cnt FROM reviews")
        row = await cursor.fetchone()
        return int(row["cnt"]) if row else 0

    async def count_escalations(self) -> int:
        cursor = await self._db.execute(
            "SELECT COUNT(*) AS cnt FROM reviews WHERE escalation_required = 1"
        )
        row = await cursor.fetchone()
        return int(row["cnt"]) if row else 0

    async def sentiment_distribution(self) -> dict[str, int]:
        cursor = await self._db.execute(
            """
            SELECT sentiment, COUNT(*) AS cnt
            FROM reviews
            GROUP BY sentiment
            ORDER BY cnt DESC
            """
        )
        rows = await cursor.fetchall()
        return {row["sentiment"]: row["cnt"] for row in rows}

    async def topic_distribution(self) -> dict[str, int]:
        cursor = await self._db.execute(
            """
            SELECT topic, COUNT(*) AS cnt
            FROM reviews
            GROUP BY topic
            ORDER BY cnt DESC
            """
        )
        rows = await cursor.fetchall()
        return {row["topic"]: row["cnt"] for row in rows}

    async def top_recurring_issues(self, limit: int = 3) -> list[dict]:
        cursor = await self._db.execute(
            """
            SELECT topic, COUNT(*) AS cnt
            FROM reviews
            WHERE sentiment IN ('negative', 'mixed')
               OR escalation_required = 1
               OR review_type IN ('complaint', 'repeated_claim')
            GROUP BY topic
            HAVING cnt > 1
            ORDER BY cnt DESC, topic ASC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [{"topic": row["topic"], "count": row["cnt"]} for row in rows]

    async def seed_review_without_user(self, raw_text: str, analysis: ReviewAnalysis) -> ReviewRecord:
        """Insert a demo review linked to a synthetic seed user."""
        cursor = await self._db.execute(
            "SELECT id FROM users WHERE telegram_id = ?",
            (0,),
        )
        row = await cursor.fetchone()
        if row is None:
            await self._db.execute(
                """
                INSERT INTO users (telegram_id, username, first_name, last_name)
                VALUES (0, 'seed_user', 'Demo', 'Seed')
                """,
            )
            await self._db.commit()
            cursor = await self._db.execute(
                "SELECT id FROM users WHERE telegram_id = ?",
                (0,),
            )
            row = await cursor.fetchone()
        user_id = int(row["id"])
        return await self.save_review(user_id, raw_text, analysis)

    @staticmethod
    def _row_to_user(row) -> TelegramUserRecord:
        return TelegramUserRecord(
            id=row["id"],
            telegram_id=row["telegram_id"],
            username=row["username"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    @staticmethod
    def _row_to_review(row) -> ReviewRecord:
        return ReviewRecord(
            id=row["id"],
            user_id=row["user_id"],
            raw_text=row["raw_text"],
            sentiment=row["sentiment"],
            review_type=row["review_type"],
            topic=row["topic"],
            short_summary=row["short_summary"],
            escalation_required=bool(row["escalation_required"]),
            suggested_reply=row["suggested_reply"],
            analysis_json=row["analysis_json"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
