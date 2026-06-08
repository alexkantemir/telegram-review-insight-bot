from datetime import datetime, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.context import AppContext

router = Router(name="health")


@router.message(Command("health"))
async def cmd_health(message: Message, app_context: AppContext) -> None:
    try:
        review_count = await app_context.repository.count_reviews()
        db_path = app_context.settings.database_path
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        await message.answer(
            "<b>Проверка состояния</b>\n\n"
            f"<b>Статус:</b> ok\n"
            f"<b>База данных:</b> {db_path}\n"
            f"<b>Сохранённых отзывов:</b> {review_count}\n"
            f"<b>Модель OpenAI:</b> {app_context.settings.openai_model}\n"
            f"<b>Проверено:</b> {timestamp}"
        )
    except Exception as exc:
        await message.answer(
            "<b>Проверка состояния</b>\n\n"
            f"<b>Статус:</b> degraded\n"
            f"<b>Ошибка:</b> {exc}"
        )
