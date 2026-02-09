"""
Обработчик истории операций
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import Database
from keyboards import main_kb


router = Router(name="history")


@router.callback_query(F.data == "history")
async def show_history(callback: CallbackQuery, db: Database):
    """Показать историю операций"""
    history = await db.get_history(limit=15)
    
    if not history:
        await callback.message.edit_text(
            "📜 <b>История операций</b>\n\n"
            "История пуста.\n"
            "Создай партию или возьми порцию!",
            reply_markup=main_kb()
        )
        await callback.answer()
        return
    
    # Формирование текста истории
    text = "📜 <b>История операций:</b>\n\n"
    
    for record in history:
        # Эмодзи для разных типов операций
        emoji_map = {
            "new_batch": "➕",
            "take": "🍗",
            "reset": "🗑",
        }
        
        action_type = record["action_type"]
        emoji = emoji_map.get(action_type, "•")
        
        text += f"{emoji} <code>{record['created']}</code>\n"
        text += f"   {record['text']}\n\n"
    
    text += "─────────────────\n"
    text += f"Показано последних {len(history)} записей"
    
    await callback.message.edit_text(text, reply_markup=main_kb())
    await callback.answer()
