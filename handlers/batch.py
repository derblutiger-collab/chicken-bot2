"""
Обработчик создания новой партии
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import Database
from config import Config
from states import CookFSM
from utils import WeightParser, WeightValidator
from keyboards import main_kb
from .common import send_or_edit, log_message


router = Router(name="batch")


@router.callback_query(F.data == "new")
async def new_batch_start(callback: CallbackQuery, state: FSMContext):
    """Начало создания новой партии"""
    await state.set_state(CookFSM.raw_total)
    
    # Клавиатура с кнопкой отмены
    from keyboards import InlineKeyboardMarkup, InlineKeyboardButton
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])
    
    await callback.message.edit_text(
        "🥩 <b>Новая партия</b>\n\n"
        "Сколько весила <b>СЫРАЯ</b> курица?\n\n"
        "💡 Примеры: 1500, 1.5кг, полкило",
        reply_markup=cancel_kb
    )
    await callback.answer()


@router.message(CookFSM.raw_total)
async def set_raw_weight(message: Message, state: FSMContext, config: Config):
    """Установка веса сырой курицы"""
    # Удалить сообщение пользователя для чистоты
    try:
        await message.delete()
    except:
        pass
    
    # Парсинг веса
    raw = WeightParser.parse(message.text)
    
    # Валидация
    validator = WeightValidator(config.min_weight, config.max_weight)
    is_valid, error_msg = validator.validate(raw)
    
    if not is_valid:
        await message.answer(
            f"❌ {error_msg}\n\n"
            f"💡 Примеры правильного ввода:\n"
            f"• 1500 или 1500г\n"
            f"• 1.5 или 1.5кг\n"
            f"• полкило, четверть"
        )
        return
    
    # Сохранение и переход к следующему шагу
    await state.update_data(raw=raw)
    await state.set_state(CookFSM.cooked_total)
    
    # Клавиатура с кнопкой отмены
    from keyboards import InlineKeyboardMarkup, InlineKeyboardButton
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])
    
    formatted_weight = WeightParser.format_weight(raw)
    await message.answer(
        f"✅ Сырая курица: <b>{formatted_weight}</b>\n\n"
        f"🍗 Теперь сколько весит <b>ГОТОВАЯ</b> курица?\n\n"
        f"💡 Примеры: 1200, 1.2кг",
        reply_markup=cancel_kb
    )


@router.message(CookFSM.cooked_total)
async def set_cooked_weight(
    message: Message, 
    state: FSMContext, 
    db: Database,
    config: Config
):
    """Установка веса готовой курицы"""
    # Удалить сообщение пользователя для чистоты
    try:
        await message.delete()
    except:
        pass
    
    # Парсинг веса
    cooked = WeightParser.parse(message.text)
    
    # Валидация веса
    validator = WeightValidator(config.min_weight, config.max_weight)
    is_valid, error_msg = validator.validate(cooked)
    
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        return
    
    # Получение данных о сырой курице
    data = await state.get_data()
    raw = data["raw"]
    
    # Валидация коэффициента
    is_valid, error_msg = validator.validate_coef(raw, cooked)
    
    if not is_valid:
        await message.answer(
            f"❌ {error_msg}\n\n"
            f"Попробуй ввести вес готовой курицы ещё раз:"
        )
        return
    
    # Сохранить готовый вес и перейти к заметке
    await state.update_data(cooked=cooked)
    await state.set_state(CookFSM.note)
    
    # Клавиатура с кнопками
    from keyboards import InlineKeyboardMarkup, InlineKeyboardButton
    note_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Пропустить", callback_data="skip_note")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])
    
    coef = cooked / raw
    raw_formatted = WeightParser.format_weight(raw)
    cooked_formatted = WeightParser.format_weight(cooked)
    
    await message.answer(
        f"✅ Вес принят!\n\n"
        f"🥩 Сырая: <b>{raw_formatted}</b>\n"
        f"🍗 Готовая: <b>{cooked_formatted}</b>\n"
        f"⚖️ Коэффициент: <b>{coef:.3f}</b>\n\n"
        f"📝 Хочешь добавить заметку к партии?\n"
        f"💡 Например: \"острая\", \"с овощами\", \"маринованная\"\n\n"
        f"Напиши заметку или нажми \"Пропустить\":",
        reply_markup=note_kb
    )


@router.callback_query(F.data == "skip_note", CookFSM.note)
async def skip_note(callback: CallbackQuery, state: FSMContext, db: Database, config: Config):
    """Пропустить добавление заметки"""
    await create_batch_final(callback.message, state, db, config, note=None)
    await callback.answer()


@router.message(CookFSM.note)
async def set_note(message: Message, state: FSMContext, db: Database, config: Config):
    """Установка заметки к партии"""
    # Удалить сообщение пользователя для чистоты
    try:
        await message.delete()
    except:
        pass
    
    note = message.text.strip()
    
    # Ограничение длины заметки
    if len(note) > 100:
        await message.answer("❌ Заметка слишком длинная! Максимум 100 символов.")
        return
    
    await create_batch_final(message, state, db, config, note=note)


async def create_batch_final(
    message: Message,
    state: FSMContext,
    db: Database,
    config: Config,
    note: str = None
):
    """Финальное создание партии с заметкой"""
    # Получение данных
    data = await state.get_data()
    raw = data["raw"]
    cooked = data["cooked"]
    
    # Создание партии с заметкой
    success = await db.create_batch(raw, cooked, note)
    
    if not success:
        await message.answer(
            "😔 Произошла ошибка при сохранении партии.\n"
            "Попробуй ещё раз позже.",
            reply_markup=main_kb()
        )
        await state.clear()
        return
    
    # Обновить закреплённое сообщение
    from pinned_status import update_pinned_status
    await update_pinned_status(
        bot=message.bot,
        chat_id=message.chat.id,
        db=db,
        message_thread_id=message.message_thread_id
    )
    
    # Проверить есть ли уже закреплённое сообщение
    batch = await db.get_batch()
    has_pinned = batch and batch.get("pinned_msg_id")
    
    # Очистка состояния
    await state.clear()
    
    # Отправка подтверждения
    coef = cooked / raw
    raw_formatted = WeightParser.format_weight(raw)
    cooked_formatted = WeightParser.format_weight(cooked)
    
    note_text = f"\n📝 Заметка: <b>{note}</b>" if note else ""
    
    # Если это первая партия - добавить подсказку
    pin_hint = ""
    if not has_pinned:
        pin_hint = (
            "\n\n"
            "📌 <b>ВАЖНО!</b>\n"
            "Найди сообщение выше со статусом (📊 СТАТУС ПАРТИИ)\n"
            "и закрепи его вручную! Дальше он будет обновляться автоматически."
        )
    
    msg = await message.answer(
        f"✅ <b>Партия успешно создана!</b>\n\n"
        f"🥩 Сырая: <b>{raw_formatted}</b>\n"
        f"🍗 Готовая: <b>{cooked_formatted}</b>\n"
        f"⚖️ Коэффициент: <b>{coef:.3f}</b>{note_text}{pin_hint}\n\n"
        f"Теперь можешь брать порции! 😋",
        reply_markup=main_kb()
    )
    
    await log_message(msg, db, config)
