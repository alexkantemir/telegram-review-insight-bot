from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.context import AppContext
from bot.utils.formatters import format_last_reviews

router = Router(name="last_reviews")


@router.message(Command("last_reviews"))
async def cmd_last_reviews(message: Message, app_context: AppContext) -> None:
    reviews = await app_context.stats_service.get_last_reviews(limit=10)
    await message.answer(format_last_reviews(reviews))
