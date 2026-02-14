"""
Обработчики статистики
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import Database
from keyboards import stats_kb, main_kb
from statistics import Statistics


log = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "stats")
async def stats_menu(callback: CallbackQuery, db: Database):
    """Меню статистики"""
    await callback.message.edit_text(
        "📊 <b>СТАТИСТИКА</b>\n\n"
        "Выбери период:",
        reply_markup=stats_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "stats_today")
async def stats_today(callback: CallbackQuery, db: Database):
    """Статистика за сегодня"""
    stats = Statistics(db, timezone_offset=3)
    message = await stats.format_stats_message(days=1)
    
    await callback.message.edit_text(
        message,
        reply_markup=stats_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "stats_week")
async def stats_week(callback: CallbackQuery, db: Database):
    """Статистика за неделю"""
    stats = Statistics(db, timezone_offset=3)
    message = await stats.format_stats_message(days=7)
    
    await callback.message.edit_text(
        message,
        reply_markup=stats_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "stats_month")
async def stats_month(callback: CallbackQuery, db: Database):
    """Статистика за месяц"""
    stats = Statistics(db, timezone_offset=3)
    message = await stats.format_stats_message(days=30)
    
    await callback.message.edit_text(
        message,
        reply_markup=stats_kb()
    )
    await callback.answer()
