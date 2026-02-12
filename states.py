"""
FSM состояния
"""
from aiogram.fsm.state import State, StatesGroup


class CookFSM(StatesGroup):
    """Состояния для создания новой партии"""
    raw_total = State()
    cooked_total = State()
    note = State()  # Заметка к партии


class TakeFSM(StatesGroup):
    """Состояния для взятия порции"""
    raw_take = State()
