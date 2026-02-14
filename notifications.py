"""
Умные уведомления для пользователя
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Bot
from database import Database


log = logging.getLogger(__name__)


class NotificationManager:
    """Менеджер уведомлений"""
    
    def __init__(self, db: Database, config):
        self.db = db
        self.config = config
        self.last_low_alert = None
        self.last_critical_alert = None
    
    async def check_and_notify(
        self,
        bot: Bot,
        chat_id: int,
        message_thread_id: int = None
    ):
        """
        Проверить статус и отправить уведомления если нужно
        
        Args:
            bot: экземпляр бота
            chat_id: ID чата
            message_thread_id: ID топика
        """
        try:
            batch = await self.db.get_batch()
            if not batch:
                return
            
            raw_left = batch["raw_left"]
            raw_total = batch["raw_total"]
            percentage = (raw_left / raw_total) * 100 if raw_total > 0 else 0
            
            # Критически низкий остаток (< 10%)
            if percentage < 10:
                await self._send_critical_alert(
                    bot, chat_id, raw_left, message_thread_id
                )
            # Низкий остаток (< 20%)
            elif percentage < 20:
                await self._send_low_alert(
                    bot, chat_id, raw_left, percentage, message_thread_id
                )
            # Средний остаток (< 40%)
            elif percentage < 40:
                await self._send_medium_alert(
                    bot, chat_id, percentage, message_thread_id
                )
            
        except Exception as e:
            log.error(f"Ошибка проверки уведомлений: {e}")
    
    async def _send_critical_alert(
        self,
        bot: Bot,
        chat_id: int,
        raw_left: float,
        message_thread_id: int = None
    ):
        """Критическое предупреждение"""
        # Отправлять не чаще раза в 6 часов
        if self.last_critical_alert:
            if datetime.now() - self.last_critical_alert < timedelta(hours=6):
                return
        
        message = (
            "🚨 <b>КРИТИЧНО!</b> 🚨\n\n"
            f"Осталось только <b>{int(raw_left)} г</b> сырой курицы!\n\n"
            "⚠️ <b>СРОЧНО готовь новую партию!</b>\n\n"
            "Иначе скоро закончится! 😱"
        )
        
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                message_thread_id=message_thread_id
            )
            self.last_critical_alert = datetime.now()
            log.info("🚨 Отправлено критическое уведомление")
        except Exception as e:
            log.error(f"Ошибка отправки критического уведомления: {e}")
    
    async def _send_low_alert(
        self,
        bot: Bot,
        chat_id: int,
        raw_left: float,
        percentage: float,
        message_thread_id: int = None
    ):
        """Предупреждение о низком остатке"""
        # Отправлять не чаще раза в 12 часов
        if self.last_low_alert:
            if datetime.now() - self.last_low_alert < timedelta(hours=12):
                return
        
        message = (
            "🔴 <b>Остаток низкий!</b>\n\n"
            f"Осталось <b>{int(raw_left)} г</b> ({int(percentage)}%)\n\n"
            "💡 <b>Подумай о новой партии</b>\n"
            "Через 1-2 дня может закончиться"
        )
        
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                message_thread_id=message_thread_id
            )
            self.last_low_alert = datetime.now()
            log.info("🔴 Отправлено предупреждение о низком остатке")
        except Exception as e:
            log.error(f"Ошибка отправки предупреждения: {e}")
    
    async def _send_medium_alert(
        self,
        bot: Bot,
        chat_id: int,
        percentage: float,
        message_thread_id: int = None
    ):
        """Напоминание о среднем остатке (один раз)"""
        # Отправлять не чаще раза в 24 часа
        if self.last_low_alert:
            if datetime.now() - self.last_low_alert < timedelta(hours=24):
                return
        
        message = (
            "🟡 <b>FYI:</b> Остаток курицы\n\n"
            f"Осталось примерно {int(percentage)}%\n\n"
            "Скоро понадобится новая партия 👌"
        )
        
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                message_thread_id=message_thread_id
            )
            log.info("🟡 Отправлено напоминание о среднем остатке")
        except Exception as e:
            log.error(f"Ошибка отправки напоминания: {e}")
