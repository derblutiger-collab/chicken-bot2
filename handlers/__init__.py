"""
Инициализация обработчиков
"""
from aiogram import Dispatcher

from . import start, status, batch, take, history, admin, quick, stats_handler


def register_handlers(dp: Dispatcher):
    """Регистрация всех обработчиков"""
    # Порядок важен! Более специфичные роутеры должны быть первыми
    dp.include_router(start.router)
    dp.include_router(quick.router)  # Быстрые действия
    dp.include_router(stats_handler.router)  # Статистика
    dp.include_router(status.router)
    dp.include_router(batch.router)
    dp.include_router(take.router)
    dp.include_router(history.router)
    dp.include_router(admin.router)
