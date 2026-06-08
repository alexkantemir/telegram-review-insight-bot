from dataclasses import dataclass

from bot.config import Settings
from bot.db.repository import ReviewRepository
from bot.db.sqlite import Database
from bot.services.knowledge_provider import KnowledgeProvider, LocalKnowledgeProvider
from bot.services.review_analyzer import ReviewAnalyzer
from bot.services.openai_service import OpenAIService
from bot.services.stats_service import StatsService


@dataclass(slots=True)
class AppContext:
    settings: Settings
    db: Database
    repository: ReviewRepository
    openai_service: OpenAIService
    knowledge_provider: KnowledgeProvider
    review_analyzer: ReviewAnalyzer
    stats_service: StatsService


def build_context(settings: Settings) -> AppContext:
    db = Database(settings.database_path)
    repository = ReviewRepository(db)
    openai_service = OpenAIService(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
    )
    knowledge_provider = LocalKnowledgeProvider()
    review_analyzer = ReviewAnalyzer(
        openai_service=openai_service,
        knowledge_provider=knowledge_provider,
        system_prompt_path=settings.system_prompt_path,
    )
    stats_service = StatsService(repository)
    return AppContext(
        settings=settings,
        db=db,
        repository=repository,
        openai_service=openai_service,
        knowledge_provider=knowledge_provider,
        review_analyzer=review_analyzer,
        stats_service=stats_service,
    )
