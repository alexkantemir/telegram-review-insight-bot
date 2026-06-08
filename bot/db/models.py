from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class TelegramUserRecord:
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    created_at: datetime


@dataclass(slots=True)
class ReviewRecord:
    id: int
    user_id: int
    raw_text: str
    sentiment: str
    review_type: str
    topic: str
    short_summary: str
    escalation_required: bool
    suggested_reply: str
    analysis_json: str
    created_at: datetime
