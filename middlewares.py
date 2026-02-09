"""
Middleware для бота
"""
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject


log = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования сообщений и callback'ов"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Обработка события"""
        
        if isinstance(event, Message):
            user = event.from_user
            username = f"@{user.username}" if user.username else "no_username"
            text = event.text[:50] if event.text else "[no_text]"
            log.info(f"Message from {user.id} ({username}): {text}")
            
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            username = f"@{user.username}" if user.username else "no_username"
            log.info(f"Callback from {user.id} ({username}): {event.data}")
        
        return await handler(event, data)


class ErrorHandlerMiddleware(BaseMiddleware):
    """Middleware для обработки ошибок"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Обработка события с перехватом ошибок"""
        try:
            return await handler(event, data)
        except Exception as e:
            log.error(f"Ошибка в обработчике: {e}", exc_info=True)
            
            # Попытка уведомить пользователя
            try:
                if isinstance(event, Message):
                    await event.answer(
                        "😔 Произошла ошибка. Попробуй ещё раз или напиши /start"
                    )
                elif isinstance(event, CallbackQuery):
                    await event.message.answer(
                        "😔 Произошла ошибка. Попробуй ещё раз или напиши /start"
                    )
                    await event.answer()
            except Exception as notify_error:
                log.error(f"Не удалось уведомить пользователя об ошибке: {notify_error}")
            
            return None
