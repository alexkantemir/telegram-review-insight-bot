from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "<b>Review Insight Bot</b>\n\n"
        "Отправьте отзыв клиента обычным текстовым сообщением — "
        "я проанализирую его с помощью ИИ:\n"
        "тональность, тип, тема, краткое резюме, "
        "флаг эскалации и предложенный ответ.\n\n"
        "Используйте /help, чтобы увидеть список команд."
    )
