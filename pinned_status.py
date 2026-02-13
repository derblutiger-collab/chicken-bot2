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
                log.info(f"✅ Обновлено закреплённое сообщение {old_pinned_id} (без повторного закрепа)")
                return True
            except TelegramBadRequest as e:
                log.warning(f"Не удалось обновить старое сообщение: {e}")
                # Сообщение удалено или недоступно - создадим новое
        
        # Создать новое сообщение (ТОЛЬКО если старое не найдено)
        log.info("📌 Создаём НОВОЕ закреплённое сообщение со статусом")
        new_msg = await bot.send_message(
            chat_id=chat_id,
            text=status_text,
            message_thread_id=message_thread_id
        )
        
        # Закрепить новое сообщение (ТОЛЬКО при первом создании!)
        # ВАЖНО: В топиках Telegram закреп через API может работать некорректно
        if message_thread_id is None or message_thread_id == 1:
            # Это основная ветка или личка - можно закреплять
            try:
                await bot.pin_chat_message(
                    chat_id=chat_id,
                    message_id=new_msg.message_id,
                    disable_notification=True  # Без уведомления
                )
                log.info(f"✅ Создано и ЗАКРЕПЛЕНО новое сообщение {new_msg.message_id}")
            except TelegramBadRequest as e:
                log.warning(f"⚠️ Не удалось закрепить сообщение (возможно бот не админ): {e}")
                log.info(f"💡 Закрепи сообщение {new_msg.message_id} вручную")
        else:
            # Это топик - в топиках закреп через API не работает
            log.info(f"ℹ️ Сообщение {new_msg.message_id} создано в топике")
            log.info(f"💡 ЗАКРЕПИ ЕГО ВРУЧНУЮ (в топиках автозакреп не работает)")
        
        # Сохранить ID нового сообщения в БД
        await db.update_pinned_msg_id(new_msg.message_id)
        
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
