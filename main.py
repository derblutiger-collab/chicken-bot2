"""
Главный файл бота для отслеживания курицы
"""
import asyncio
import logging
import sys
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import Config
from database import Database
from middlewares import LoggingMiddleware, ErrorHandlerMiddleware, TopicFilterMiddleware
from handlers import register_handlers
from backup import BackupManager


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

log = logging.getLogger(__name__)


async def on_startup(bot: Bot, config: Config):
    """Действия при запуске бота"""
    log.info("Бот запускается...")
    
    # Получение информации о боте
    bot_info = await bot.get_me()
    log.info(f"Бот запущен: @{bot_info.username} (ID: {bot_info.id})")
    
    if config.admin_ids:
        log.info(f"Администраторы: {config.admin_ids}")
    else:
        log.warning("Администраторы не настроены")


async def on_shutdown(bot: Bot):
    """Действия при остановке бота"""
    log.info("Бот останавливается...")
    await bot.session.close()


async def main():
    """Главная функция"""
    try:
        # Загрузка конфигурации
        config = Config.from_env()
        log.info("Конфигурация загружена")
        
        # Создание директории для БД если её нет (для BotHost.ru)
        import os
        db_dir = os.path.dirname(config.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            log.info(f"Создана директория для БД: {db_dir}")
        
        # Инициализация базы данных
        db = Database(config.db_path, timezone_offset=config.timezone_offset)
        await db.init()
        log.info(f"База данных инициализирована: {config.db_path} (часовой пояс: UTC{config.timezone_offset:+d})")
        
        # Создание бота и диспетчера
        bot = Bot(
            token=config.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        dp = Dispatcher()
        
        # Регистрация middleware
        # TopicFilter должен быть ПЕРВЫМ (фильтрует до всего остального)
        if config.topic_id:
            dp.message.middleware(TopicFilterMiddleware(config.topic_id))
            log.info(f"Бот будет работать только в топике ID: {config.topic_id}")
        
        dp.message.middleware(LoggingMiddleware())
        dp.callback_query.middleware(LoggingMiddleware())
        dp.message.middleware(ErrorHandlerMiddleware())
        dp.callback_query.middleware(ErrorHandlerMiddleware())
        
        # Регистрация обработчиков
        register_handlers(dp)
        
        # Передача зависимостей в обработчики
        dp["db"] = db
        dp["config"] = config
        
        # Настройка автоматических бэкапов
        if config.admin_ids:
            backup_manager = BackupManager(db.db_path)
            scheduler = AsyncIOScheduler(timezone="UTC")
            
            # Автобэкап каждый день в 03:00 UTC (06:00 MSK)
            scheduler.add_job(
                backup_manager.auto_backup,
                trigger=CronTrigger(hour=3, minute=0),
                args=[bot, config.admin_ids],
                id="daily_backup",
                name="Ежедневный автобэкап БД",
                replace_existing=True
            )
            
            scheduler.start()
            log.info("✅ Планировщик автобэкапов запущен (каждый день в 03:00 UTC)")
        else:
            log.warning("⚠️ Автобэкапы отключены: администраторы не настроены")
        
        # Запуск бота
        await on_startup(bot, config)
        
        try:
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        finally:
            await on_shutdown(bot)
            
    except Exception as e:
        log.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Бот остановлен пользователем")
    except Exception as e:
        log.error(f"Неожиданная ошибка: {e}", exc_info=True)
        sys.exit(1)
