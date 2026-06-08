from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="help")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "<b>Доступные команды</b>\n\n"
        "/start — краткое описание бота\n"
        "/help — это сообщение со справкой\n"
        "/stats — статистика по отзывам\n"
        "/last_reviews — последние 10 сохранённых отзывов\n"
        "/health — проверка состояния сервиса\n\n"
        "Отправьте любое текстовое сообщение без команды, "
        "чтобы проанализировать отзыв клиента."
    )
