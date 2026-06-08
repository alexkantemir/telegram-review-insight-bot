from bot.db.repository import ReviewRepository


class StatsService:
    def __init__(self, repository: ReviewRepository) -> None:
        self._repository = repository

    async def get_stats(self) -> dict:
        total = await self._repository.count_reviews()
        sentiment = await self._repository.sentiment_distribution()
        topics = await self._repository.topic_distribution()
        escalations = await self._repository.count_escalations()
        recurring = await self._repository.top_recurring_issues(limit=3)

        return {
            "total_reviews": total,
            "sentiment_distribution": sentiment or {"none": 0},
            "topic_distribution": topics or {"none": 0},
            "escalation_count": escalations,
            "top_recurring_issues": recurring,
        }

    async def get_last_reviews(self, limit: int = 10) -> list[dict]:
        return await self._repository.get_last_reviews(limit=limit)
