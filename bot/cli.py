import asyncio
import json
import sys

from bot.config import get_settings
from bot.context import build_context
from bot.db.migrations import run_migrations
from bot.schemas.review_analysis import ReviewAnalysis
from bot.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)


async def seed_demo_reviews(analyze_with_openai: bool = False, reset: bool = False) -> int:
    settings = get_settings()
    setup_logging(settings.log_level)

    if reset and settings.database_path.exists():
        settings.database_path.unlink()
        logger.info("База данных сброшена: %s", settings.database_path)

    context = build_context(settings)

    await context.db.connect()
    await run_migrations(context.db)

    demo_path = settings.demo_reviews_path
    if not demo_path.exists():
        raise FileNotFoundError(f"Demo reviews file not found: {demo_path}")

    with demo_path.open(encoding="utf-8") as file:
        payload = json.load(file)

    reviews = payload.get("reviews", [])
    inserted = 0

    for item in reviews:
        raw_text = item["text"]
        if analyze_with_openai:
            analysis = await context.review_analyzer.analyze(raw_text)
        else:
            analysis = ReviewAnalysis.model_validate(item["analysis"])

        await context.repository.seed_review_without_user(raw_text, analysis)
        inserted += 1
        logger.info("Seeded review: %s", raw_text[:60])

    await context.db.close()
    logger.info("Seeded %s demo reviews", inserted)
    return inserted


def main() -> None:
    if len(sys.argv) < 2:
        print("Использование: python -m bot.cli seed [--reset] [--analyze]")
        sys.exit(1)

    command = sys.argv[1]
    if command != "seed":
        print(f"Неизвестная команда: {command}")
        print("Использование: python -m bot.cli seed [--reset] [--analyze]")
        sys.exit(1)

    analyze = "--analyze" in sys.argv
    reset = "--reset" in sys.argv
    count = asyncio.run(seed_demo_reviews(analyze_with_openai=analyze, reset=reset))
    print(f"Успешно загружено {count} демо-отзывов в базу данных.")


if __name__ == "__main__":
    main()
