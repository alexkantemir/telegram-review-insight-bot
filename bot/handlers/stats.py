from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.context import AppContext
from bot.utils.formatters import format_stats

router = Router(name="stats")


@router.message(Command("stats"))
async def cmd_stats(message: Message, app_context: AppContext) -> None:
    stats = await app_context.stats_service.get_stats()
    await message.answer(format_stats(stats))
