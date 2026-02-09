"""
Обработчики команд администратора
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database import Database
from config import Config
from keyboards import main_kb, admin_kb, confirm_kb


router = Router(name="admin")


def check_admin(config: Config):
    """Фильтр проверки прав администратора"""
    async def _check(message: Message) -> bool:
        return config.is_admin(message.from_user.id)
    return _check


@router.message(Command("admin"))
async def admin_panel(message: Message, config: Config):
    """Панель администратора"""
    if not config.is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав")
        return
    
    await message.answer(
        "⚙️ <b>Панель администратора</b>\n\n"
        "Выбери действие:",
        reply_markup=admin_kb()
    )


@router.callback_query(F.data == "admin_clear_batch")
async def admin_clear_batch_confirm(callback: CallbackQuery, config: Config):
    """Подтверждение очистки партии"""
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    await callback.message.edit_text(
        "⚠️ <b>Подтверждение</b>\n\n"
        "Удалить текущую партию?\n"
        "Это действие нельзя отменить!",
        reply_markup=confirm_kb("clear_batch")
    )
    await callback.answer()


@router.callback_query(F.data == "confirm_clear_batch")
async def admin_clear_batch_execute(callback: CallbackQuery, config: Config, db: Database):
    """Выполнение очистки партии"""
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    success = await db.reset_batch()
    
    if success:
        await callback.message.edit_text(
            "✅ Партия успешно удалена",
            reply_markup=main_kb()
        )
        await callback.answer("Партия удалена")
    else:
        await callback.message.edit_text(
            "❌ Ошибка при удалении партии",
            reply_markup=admin_kb()
        )
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data == "admin_clear_history")
async def admin_clear_history_confirm(callback: CallbackQuery, config: Config):
    """Подтверждение очистки истории"""
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    await callback.message.edit_text(
        "⚠️ <b>Подтверждение</b>\n\n"
        "Очистить всю историю операций?\n"
        "Это действие нельзя отменить!",
        reply_markup=confirm_kb("clear_history")
    )
    await callback.answer()


@router.callback_query(F.data == "confirm_clear_history")
async def admin_clear_history_execute(callback: CallbackQuery, config: Config, db: Database):
    """Выполнение очистки истории"""
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    success = await db.clear_history()
    
    if success:
        await callback.message.edit_text(
            "✅ История успешно очищена",
            reply_markup=main_kb()
        )
        await callback.answer("История очищена")
    else:
        await callback.message.edit_text(
            "❌ Ошибка при очистке истории",
            reply_markup=admin_kb()
        )
        await callback.answer("Ошибка", show_alert=True)


@router.message(Command("reset"))
async def reset_all(message: Message, config: Config, db: Database):
    """Полный сброс (только для админов)"""
    if not config.is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав")
        return
    
    # Удаление партии, истории и сообщений
    batch_cleared = await db.reset_batch()
    history_cleared = await db.clear_history()
    messages_cleared = await db.clear_messages()
    
    if batch_cleared and history_cleared and messages_cleared:
        await message.answer(
            "✅ <b>Полный сброс выполнен</b>\n\n"
            "• Партия удалена\n"
            "• История очищена\n"
            "• Записи сообщений удалены",
            reply_markup=main_kb()
        )
    else:
        await message.answer(
            "⚠️ Сброс выполнен с ошибками",
            reply_markup=main_kb()
        )


@router.message(Command("stats"))
async def show_stats(message: Message, config: Config, db: Database):
    """Показать статистику (только для админов)"""
    if not config.is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав")
        return
    
    batch = await db.get_batch()
    history = await db.get_history(limit=100)
    
    if not batch:
        batch_text = "Нет активной партии"
    else:
        batch_text = (
            f"Сырой: {int(batch['raw_total'])}г → {int(batch['raw_left'])}г\n"
            f"Готовой: {int(batch['cooked_total'])}г\n"
            f"Коэфф: {batch['coef']:.3f}\n"
            f"Создана: {batch['created']}"
        )
    
    # Подсчёт операций по типам
    take_count = sum(1 for h in history if h['action_type'] == 'take')
    batch_count = sum(1 for h in history if h['action_type'] == 'new_batch')
    
    await message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"<b>Текущая партия:</b>\n{batch_text}\n\n"
        f"<b>История:</b>\n"
        f"• Всего записей: {len(history)}\n"
        f"• Создано партий: {batch_count}\n"
        f"• Взято порций: {take_count}",
        reply_markup=main_kb()
    )
