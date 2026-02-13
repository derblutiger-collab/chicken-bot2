"""
Управление закреплённым сообщением со статусом
"""
import logging
from aiogram import Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

from database import Database
from utils.status_formatter import format_status_message


log = logging.getLogger(__name__)


async def update_pinned_status(
    bot: Bot,
    chat_id: int,
    db: Database,
    message_thread_id: int = None
) -> bool:
    """
    Обновить или создать закреплённое сообщение со статусом
    
    Args:
        bot: экземпляр бота
        chat_id: ID чата
        db: экземпляр базы данных
        message_thread_id: ID топика (для групп с темами)
        
    Returns:
        bool: успешно ли обновлено
    """
    try:
        # Получить данные партии
        batch = await db.get_batch()
        if not batch:
            log.debug("Партия не найдена, закреп не обновляется")
            return False
        
        # Получить историю для прогноза
        history = await db.get_history(limit=50)
        
        # Форматировать сообщение
        status_text = format_status_message(batch, history)
        
        # Получить ID старого закреплённого сообщения
        old_pinned_id = batch.get("pinned_msg_id")
        
        # Попытка обновить существующее сообщение
        if old_pinned_id:
            try:
                await bot.edit_message_text(
                    text=status_text,
                    chat_id=chat_id,
                    message_id=old_pinned_id
                )
                log.info(f"✅ ОБНОВЛЕНО сообщение со статусом (ID: {old_pinned_id})")
                return True
            except TelegramBadRequest as e:
                log.warning(f"⚠️ Не удалось обновить сообщение {old_pinned_id}: {e}")
                log.info("Создаём новое сообщение со статусом...")
        
        # Создать новое сообщение со статусом
        new_msg = await bot.send_message(
            chat_id=chat_id,
            text=status_text,
            message_thread_id=message_thread_id
        )
        
        # Сохранить ID сообщения в БД
        await db.update_pinned_msg_id(new_msg.message_id)
        
        # ВАЖНО: НЕ ЗАКРЕПЛЯЕМ АВТОМАТИЧЕСКИ!
        # В топиках Telegram это работает некорректно
        log.info("=" * 60)
        log.info(f"📌 СОЗДАНО сообщение со статусом!")
        log.info(f"📝 ID сообщения: {new_msg.message_id}")
        log.info("")
        log.info("⚠️  ЗАКРЕПИ ЕГО ВРУЧНУЮ:")
        log.info("   1. Найди сообщение со статусом (📊 СТАТУС ПАРТИИ)")
        log.info("   2. Нажми на него → Закрепить")
        log.info("   3. Готово! Дальше бот будет обновлять его автоматически")
        log.info("=" * 60)
        
        return True
        
    except Exception as e:
        log.error(f"Ошибка при обновлении закрепа: {e}", exc_info=True)
        return False


async def unpin_status(bot: Bot, chat_id: int, db: Database) -> bool:
    """
    Открепить сообщение со статусом
    
    Args:
        bot: экземпляр бота
        chat_id: ID чата
        db: экземпляр базы данных
        
    Returns:
        bool: успешно ли откреплено
    """
    try:
        batch = await db.get_batch()
        if not batch:
            return False
        
        pinned_id = batch.get("pinned_msg_id")
        if not pinned_id:
            return False
        
        try:
            await bot.unpin_chat_message(chat_id=chat_id, message_id=pinned_id)
            log.info(f"Откреплено сообщение {pinned_id}")
        except TelegramBadRequest as e:
            log.warning(f"Не удалось открепить сообщение: {e}")
        
        # Очистить ID в БД
        await db.update_pinned_msg_id(None)
        
        return True
        
    except Exception as e:
        log.error(f"Ошибка при откреплении: {e}")
        return False
