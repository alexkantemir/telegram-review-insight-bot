from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.context import AppContext


class AppContextMiddleware(BaseMiddleware):
    def __init__(self, app_context: AppContext) -> None:
        self.app_context = app_context

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["app_context"] = self.app_context
        return await handler(event, data)
