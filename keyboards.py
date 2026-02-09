"""
Клавиатуры бота
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_kb() -> InlineKeyboardMarkup:
    """Главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🥩 Остаток", callback_data="status")],
        [InlineKeyboardButton(text="🍗 Взять порцию", callback_data="take")],
        [InlineKeyboardButton(text="➕ Новая партия", callback_data="new")],
        [InlineKeyboardButton(text="📜 История", callback_data="history")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
    ])


def take_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора порции"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="100 г", callback_data="take_100"),
            InlineKeyboardButton(text="150 г", callback_data="take_150"),
        ],
        [
            InlineKeyboardButton(text="200 г", callback_data="take_200"),
            InlineKeyboardButton(text="300 г", callback_data="take_300"),
        ],
        [InlineKeyboardButton(text="✍️ Другое", callback_data="take_other")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])


def confirm_kb(action: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="cancel")
        ]
    ])


def admin_kb() -> InlineKeyboardMarkup:
    """Клавиатура администратора"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Очистить партию", callback_data="admin_clear_batch")],
        [InlineKeyboardButton(text="📜 Очистить историю", callback_data="admin_clear_history")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="cancel")]
    ])


def back_kb() -> InlineKeyboardMarkup:
    """Простая кнопка назад"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="cancel")]
    ])
