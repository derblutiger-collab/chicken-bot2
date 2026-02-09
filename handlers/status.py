"""
Обработчик просмотра остатка
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import Database
from config import Config
from keyboards import main_kb


router = Router(name="status")


@router.callback_query(F.data == "status")
async def show_status(callback: CallbackQuery, db: Database, config: Config):
    """Показать текущий остаток"""
    batch = await db.get_batch()
    
    if not batch:
        await callback.message.edit_text(
            "❌ Партия не задана\n\n"
            "Нажми «➕ Новая партия» чтобы начать",
            reply_markup=main_kb()
        )
        await callback.answer()
        return
    
    raw_left = batch["raw_left"]
    coef = batch["coef"]
    cooked_left = raw_left * coef
    
    # Формирование сообщения
    text = (
        f"📊 <b>Текущий остаток:</b>\n\n"
        f"🥩 Сырой: <b>{int(raw_left)} г</b>\n"
        f"🍗 Готовой: <b>{int(cooked_left)} г</b>\n\n"
        f"⚖️ Коэффициент: {coef:.3f}\n"
        f"📅 Партия от: {batch['created']}"
    )
    
    await callback.message.edit_text(text, reply_markup=main_kb())
    
    # Предупреждение о низком остатке
    if raw_left < config.low_threshold:
        await callback.message.answer(
            "⚠️ <b>Остаток низкий!</b>\n"
            "Подумай о новой партии ❤️"
        )
    
    await callback.answer()
