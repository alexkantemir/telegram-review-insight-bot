import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import get_settings
from bot.context import build_context
from bot.db.migrations import run_migrations
from bot.handlers import health, help, last_reviews, reviews, start, stats
from bot.middlewares.context import AppContextMiddleware
from bot.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    app_context = build_context(settings)

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()
    dispatcher.update.middleware(AppContextMiddleware(app_context))

    @dispatcher.startup.register
    async def on_startup() -> None:
        await app_context.db.connect()
        await run_migrations(app_context.db)
        logger.info("Bot startup complete")

    @dispatcher.shutdown.register
    async def on_shutdown() -> None:
        await app_context.db.close()
        logger.info("Bot shutdown complete")

    dispatcher.include_router(start.router)
    dispatcher.include_router(help.router)
    dispatcher.include_router(stats.router)
    dispatcher.include_router(last_reviews.router)
    dispatcher.include_router(health.router)
    dispatcher.include_router(reviews.router)

    logger.info("Starting Review Insight Bot")
    logger.info("Database path: %s", settings.database_path)
    logger.info("OpenAI model: %s", settings.openai_model)

    try:
        await dispatcher.start_polling(bot)
    except asyncio.CancelledError:
        logger.info("Получен сигнал остановки, завершаем polling…")
    finally:
        await app_context.db.close()
        await bot.session.close()
        logger.info("Бот корректно остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Остановка по Ctrl+C.")
