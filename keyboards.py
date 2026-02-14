"""
Клавиатуры бота
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_kb() -> InlineKeyboardMarkup:
    """Главное меню - Modern Design 2026"""
    return InlineKeyboardMarkup(inline_keyboard=[
        # БЫСТРЫЕ ДЕЙСТВИЯ (топ приоритет)
        [
            InlineKeyboardButton(text="⚡ 200г", callback_data="quick_200"),
            InlineKeyboardButton(text="⚡ 300г", callback_data="quick_300"),
        ],
        # ОСНОВНОЕ
        [InlineKeyboardButton(text="🍗 Взять порцию", callback_data="take")],
        [InlineKeyboardButton(text="➕ Новая партия", callback_data="new")],
        # ИНФОРМАЦИЯ
        [
            InlineKeyboardButton(text="📊 Остаток", callback_data="status"),
            InlineKeyboardButton(text="📈 Статистика", callback_data="stats"),
        ],
        # ДОПОЛНИТЕЛЬНО
        [
            InlineKeyboardButton(text="📜 История", callback_data="history"),
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"),
        ],
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
        [InlineKeyboardButton(text="💾 Создать бэкап", callback_data="admin_backup")],
        [InlineKeyboardButton(text="🗑 Очистить партию", callback_data="admin_clear_batch")],
        [InlineKeyboardButton(text="📜 Очистить историю", callback_data="admin_clear_history")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="cancel")]
    ])


def back_kb() -> InlineKeyboardMarkup:
    """Простая кнопка назад"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="cancel")]
    ])


def stats_kb() -> InlineKeyboardMarkup:
    """Клавиатура статистики"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Сегодня", callback_data="stats_today"),
            InlineKeyboardButton(text="📈 Неделя", callback_data="stats_week"),
        ],
        [
            InlineKeyboardButton(text="📅 Месяц", callback_data="stats_month"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="cancel")]
    ])
