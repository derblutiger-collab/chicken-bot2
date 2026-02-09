"""
Общие утилиты для обработчиков
"""
import logging
from aiogram.types import Message
from aiogram import Bot

from database import Database
from config import Config


log = logging.getLogger(__name__)


async def send_or_edit(
    message: Message,
    text: str,
    is_callback: bool = False,
    reply_markup=None
) -> Message:
    """
    Универсальная функция для отправки или редактирования сообщения
    
    Args:
        message: объект сообщения
        text: текст сообщения
        is_callback: True если это callback (нужно редактировать), False если обычное сообщение
        reply_markup: клавиатура
        
    Returns:
        Message: отправленное или отредактированное сообщение
    """
    if is_callback:
        return await message.edit_text(text, reply_markup=reply_markup)
    else:
        return await message.answer(text, reply_markup=reply_markup)


async def log_message(message: Message, db: Database, config: Config):
    """
    Логирование сообщения для последующего удаления
    
    Args:
        message: сообщение для логирования
        db: экземпляр базы данных
        config: конфигурация
    """
    try:
        # Добавить сообщение в БД
        await db.add_message(message.message_id, message.chat.id)
        
        # Получить старые сообщения
        old_messages = await db.get_old_messages(config.max_messages_store)
        
        # Удалить старые сообщения
        bot = message.bot
        for record_id, msg_id, chat_id in old_messages:
            try:
                await bot.delete_message(chat_id, msg_id)
            except Exception as e:
                log.debug(f"Не удалось удалить сообщение {msg_id}: {e}")
            finally:
                await db.delete_message_record(record_id)
                
    except Exception as e:
        log.error(f"Ошибка при логировании сообщения: {e}")
