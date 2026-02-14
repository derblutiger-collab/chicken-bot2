"""
Обработчики быстрых действий
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from database import Database
from config import Config
from keyboards import main_kb
from utils.parser import WeightParser
from handlers.common import log_message


log = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("quick_"))
async def quick_take(
    callback: CallbackQuery,
    db: Database,
    config: Config,
    state: FSMContext
):
    """
    Быстрое взятие порции одним нажатием
    
    Поддерживает: quick_200, quick_300
    """
    # Очистить состояние если было
    await state.clear()
    
    # Получить вес из callback
    weight_str = callback.data.split("_")[1]  # "quick_200" -> "200"
    grams = float(weight_str)
    
    # Проверить что партия существует
    batch = await db.get_batch()
    if not batch:
        await callback.message.edit_text(
            "❌ <b>Партия не найдена</b>\n\n"
            "Сначала создай партию:\n"
            "➕ Новая партия",
            reply_markup=main_kb()
        )
        await callback.answer()
        return
    
    # Попытка взять порцию
    result = await db.take_portion(grams)
    
    if result is None:
        raw_left = batch["raw_left"]
        left_formatted = WeightParser.format_weight(raw_left)
        
        await callback.message.edit_text(
            f"❌ <b>Столько нет!</b>\n\n"
            f"Осталось только <b>{left_formatted}</b> сырой\n\n"
            "Выбери меньше или создай новую партию",
            reply_markup=main_kb()
        )
        await callback.answer()
        return
    
    cooked_portion, new_raw_left = result
    
    # Форматирование
    raw_formatted = WeightParser.format_weight(grams)
    cooked_formatted = WeightParser.format_weight(cooked_portion)
    left_formatted = WeightParser.format_weight(new_raw_left)
    
    # Определить эмодзи в зависимости от остатка
    percentage = (new_raw_left / batch["raw_total"]) * 100 if batch["raw_total"] > 0 else 0
    if percentage >= 50:
        status_emoji = "🟢"
    elif percentage >= 20:
        status_emoji = "🟡"
    else:
        status_emoji = "🔴"
    
    # Ответ
    response_text = (
        f"⚡ <b>Быстрое действие!</b>\n\n"
        f"✅ Взято:\n"
        f"🥩 Сырой: <b>{raw_formatted}</b>\n"
        f"🍗 Готовой: <b>{cooked_formatted}</b>\n\n"
        f"{status_emoji} Осталось: <b>{left_formatted}</b>\n\n"
        f"Приятного аппетита! ❤️"
    )
    
    await callback.message.edit_text(
        response_text,
        reply_markup=main_kb()
    )
    
    # Обновить закреплённое сообщение
    try:
        from pinned_status import update_pinned_status
        await update_pinned_status(
            bot=callback.message.bot,
            chat_id=callback.message.chat.id,
            db=db,
            message_thread_id=callback.message.message_thread_id
        )
    except Exception as e:
        log.error(f"Ошибка обновления закрепа: {e}")
    
    # Проверить нужно ли уведомление
    try:
        from notifications import NotificationManager
        notif_manager = NotificationManager(db, config)
        await notif_manager.check_and_notify(
            callback.message.bot,
            callback.message.chat.id,
            callback.message.message_thread_id
        )
    except Exception as e:
        log.error(f"Ошибка уведомлений: {e}")
    
    await callback.answer("⚡ Готово!")
