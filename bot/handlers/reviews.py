from aiogram import F, Router
from aiogram.types import Message

from bot.context import AppContext
from bot.utils.formatters import format_analysis_response
from bot.utils.logger import get_logger

logger = get_logger(__name__)

router = Router(name="reviews")


@router.message(F.text & ~F.text.startswith("/"))
async def handle_review_message(message: Message, app_context: AppContext) -> None:
    if message.from_user is None or message.text is None:
        await message.answer("Не удалось обработать это сообщение.")
        return

    review_text = message.text.strip()
    if not review_text:
        await message.answer("Пожалуйста, отправьте непустой текст отзыва.")
        return

    status_message = await message.answer("Анализирую отзыв…")

    try:
        user = await app_context.repository.upsert_user(message.from_user)
        analysis = await app_context.review_analyzer.analyze(review_text)
        await app_context.repository.save_review(
            user_id=user.id,
            raw_text=review_text,
            analysis=analysis,
        )
        await status_message.edit_text(format_analysis_response(analysis))
        logger.info(
            "Review analyzed for user %s: sentiment=%s topic=%s",
            message.from_user.id,
            analysis.sentiment.value,
            analysis.topic.value,
        )
    except Exception as exc:
        logger.exception("Failed to analyze review for user %s", message.from_user.id)
        await status_message.edit_text(
            "К сожалению, сейчас не удалось проанализировать отзыв. "
            "Попробуйте позже.\n"
            f"<i>Подробности: {exc}</i>"
        )
