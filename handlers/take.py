"""
Обработчик взятия порции
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import Database
from config import Config
from states import TakeFSM
from utils import WeightParser, WeightValidator, PortionValidator
from keyboards import main_kb, take_kb
from .common import send_or_edit, log_message


router = Router(name="take")


@router.callback_query(F.data == "take")
async def take_start(callback: CallbackQuery, state: FSMContext, db: Database):
    """Начало взятия порции"""
    # Проверка наличия партии
    batch = await db.get_batch()
    
    if not batch:
        await callback.message.edit_text(
            "❌ Партия не задана\n\n"
            "Сначала создай партию: «➕ Новая партия»",
            reply_markup=main_kb()
        )
        await callback.answer()
        return
    
    # Проверка остатка
    raw_left = batch["raw_left"]
    
    if raw_left <= 0:
        await callback.message.edit_text(
            "❌ Курица закончилась!\n\n"
            "Создай новую партию: «➕ Новая партия»",
            reply_markup=main_kb()
        )
        await callback.answer()
        return
    
    await state.set_state(TakeFSM.raw_take)
    
    formatted_left = WeightParser.format_weight(raw_left)
    await callback.message.edit_text(
        f"🍗 <b>Взять порцию</b>\n\n"
        f"Осталось сырой: <b>{formatted_left}</b>\n\n"
        f"Сколько <b>СЫРОЙ</b> берёшь?",
        reply_markup=take_kb()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("take_"), TakeFSM.raw_take)
async def take_quick(
    callback: CallbackQuery,
    state: FSMContext,
    db: Database,
    config: Config
):
    """Быстрый выбор порции"""
    # Проверка на "другое"
    if callback.data == "take_other":
        # Клавиатура с кнопкой отмены
        from keyboards import InlineKeyboardMarkup, InlineKeyboardButton
        cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
        ])
        
        await callback.message.edit_text(
            "✍️ Введи вес сырой курицы:\n\n"
            "💡 Примеры: 150, 200, 0.25кг",
            reply_markup=cancel_kb
        )
        await callback.answer()
        return
    
    # Извлечение веса из callback_data
    try:
        grams = float(callback.data.split("_")[1])
    except (IndexError, ValueError):
        await callback.answer("Ошибка при обработке")
        return
    
    await process_take(callback.message, grams, state, db, config, is_callback=True)
    await callback.answer()


@router.message(TakeFSM.raw_take)
async def take_manual(
    message: Message,
    state: FSMContext,
    db: Database,
    config: Config
):
    """Ручной ввод веса порции"""
    # Парсинг веса
    grams = WeightParser.parse(message.text)
    
    # Валидация
    validator = WeightValidator(config.min_weight, config.max_weight)
    is_valid, error_msg = validator.validate(grams)
    
    if not is_valid:
        await message.answer(
            f"❌ {error_msg}\n\n"
            f"Попробуй ещё раз:"
        )
        return
    
    await process_take(message, grams, state, db, config, is_callback=False)


async def process_take(
    message: Message,
    grams: float,
    state: FSMContext,
    db: Database,
    config: Config,
    is_callback: bool = False
):
    """
    Обработка взятия порции
    
    Args:
        message: сообщение
        grams: количество грамм
        state: FSM контекст
        db: база данных
        config: конфигурация
        is_callback: True если вызвано из callback
    """
    # Попытка взять порцию
    result = await db.take_portion(grams)
    
    if result is None:
        # Получаем информацию о партии для ошибки
        batch = await db.get_batch()
        
        if not batch:
            text = (
                "❌ Партия не найдена\n\n"
                "Создай новую партию: «➕ Новая партия»"
            )
        else:
            raw_left = batch["raw_left"]
            formatted_left = WeightParser.format_weight(raw_left)
            text = (
                f"❌ Столько нет!\n\n"
                f"Осталось только <b>{formatted_left}</b> сырой"
            )
        
        await send_or_edit(message, text, is_callback, reply_markup=main_kb())
        await state.clear()
        return
    
    cooked_portion, new_raw_left = result
    
    # Очистка состояния
    await state.clear()
    
    # Форматирование весов
    raw_formatted = WeightParser.format_weight(grams)
    cooked_formatted = WeightParser.format_weight(cooked_portion)
    left_formatted = WeightParser.format_weight(new_raw_left)
    
    # Формирование ответа
    response_text = (
        f"✅ <b>Порция взята!</b>\n\n"
        f"📥 Взял:\n"
        f"🥩 Сырой: <b>{raw_formatted}</b>\n"
        f"🍗 Готовой: <b>{cooked_formatted}</b>\n\n"
        f"📊 Осталось сырой: <b>{left_formatted}</b>\n\n"
        f"Приятного аппетита! ❤️"
    )
    
    msg = await send_or_edit(
        message,
        response_text,
        is_callback,
        reply_markup=main_kb()
    )
    
    # Логирование только для не-callback сообщений
    if not is_callback:
        await log_message(msg, db, config)
    
    # Предупреждение о низком остатке
    if new_raw_left < config.low_threshold:
        await message.answer(
            "⚠️ <b>Остаток низкий!</b>\n"
            "Подумай о новой партии ❤️"
        )
