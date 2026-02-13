"""
Форматирование статуса партии
"""
from datetime import datetime
from typing import Optional
import aiosqlite


def format_progress_bar(current: float, total: float, length: int = 10) -> str:
    """
    Создать прогресс-бар
    
    Args:
        current: текущее значение
        total: максимальное значение
        length: длина бара в символах
        
    Returns:
        str: прогресс-бар (например "■■■■■□□□□□")
    """
    if total == 0:
        return "□" * length
    
    percentage = current / total
    filled = int(percentage * length)
    empty = length - filled
    
    return "■" * filled + "□" * empty


def get_status_emoji(percentage: float) -> str:
    """
    Получить эмодзи статуса в зависимости от остатка
    
    Args:
        percentage: процент остатка (0.0 - 1.0)
        
    Returns:
        str: эмодзи индикатора
    """
    if percentage >= 0.7:
        return "🟢"  # Много
    elif percentage >= 0.3:
        return "🟡"  # Средне
    else:
        return "🔴"  # Мало


def calculate_avg_consumption(history_records, days: int = 7) -> Optional[float]:
    """
    Рассчитать средний расход за период
    
    Args:
        history_records: записи истории
        days: количество дней для анализа
        
    Returns:
        float: средний расход в граммах/день или None
    """
    if not history_records:
        return None
    
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.now() - timedelta(days=days)
    total_taken = 0
    count = 0
    
    for record in history_records:
        if record["action_type"] == "take":
            try:
                # Парсим дату
                created = datetime.fromisoformat(record["created"])
                if created >= cutoff_date:
                    # Извлекаем вес из текста "Взято: 200г сырой → 160г готовой"
                    text = record["text"]
                    if "Взято:" in text and "г сырой" in text:
                        weight_str = text.split("Взято:")[1].split("г сырой")[0].strip()
                        weight = float(weight_str)
                        total_taken += weight
                        count += 1
            except (ValueError, IndexError):
                continue
    
    if count == 0:
        return None
    
    # Средний расход в день
    return total_taken / days


def estimate_days_left(current: float, avg_per_day: float) -> Optional[int]:
    """
    Оценить сколько дней осталось
    
    Args:
        current: текущий остаток
        avg_per_day: средний расход в день
        
    Returns:
        int: количество дней или None
    """
    if not avg_per_day or avg_per_day <= 0:
        return None
    
    return int(current / avg_per_day)


def format_status_message(batch_data: aiosqlite.Row, history_records=None) -> str:
    """
    Форматировать сообщение о статусе партии
    
    Args:
        batch_data: данные партии из БД
        history_records: записи истории для прогноза
        
    Returns:
        str: отформатированное сообщение
    """
    raw_total = batch_data["raw_total"]
    raw_left = batch_data["raw_left"]
    cooked_total = batch_data["cooked_total"]
    coef = batch_data["coef"]
    created = batch_data["created"]
    note = batch_data.get("note")
    
    # Вычисления
    cooked_left = raw_left * coef
    percentage = raw_left / raw_total if raw_total > 0 else 0
    
    # Прогресс-бар
    progress_bar = format_progress_bar(raw_left, raw_total, length=10)
    status_emoji = get_status_emoji(percentage)
    
    # Форматирование даты
    try:
        created_dt = datetime.fromisoformat(created)
        created_str = created_dt.strftime("%d-%m-%y %H:%M")
    except:
        created_str = created
    
    # Базовое сообщение
    lines = [
        "📊 <b>СТАТУС ПАРТИИ</b>",
        "",
        f"{status_emoji} <b>Остаток:</b> {int(percentage * 100)}%",
        f"{progress_bar}",
        "",
        f"🥩 <b>Сырой:</b> {int(raw_left)} г / {int(raw_total)} г",
        f"🍗 <b>Готовой:</b> {int(cooked_left)} г / {int(cooked_total)} г",
        f"⚖️ <b>Коэффициент:</b> {coef:.3f}",
        "",
        f"📅 <b>Создано:</b> {created_str}",
    ]
    
    # Заметка
    if note:
        lines.append(f"📝 <b>Заметка:</b> {note}")
    
    # Прогноз расхода
    if history_records:
        avg_consumption = calculate_avg_consumption(history_records, days=7)
        if avg_consumption and avg_consumption > 0:
            days_left = estimate_days_left(raw_left, avg_consumption)
            
            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━━")
            lines.append("📈 <b>ПРОГНОЗ</b>")
            lines.append(f"📊 Средний расход: {int(avg_consumption)} г/день")
            
            if days_left is not None:
                if days_left == 0:
                    lines.append("⏰ Осталось: <b>менее 1 дня</b>")
                elif days_left == 1:
                    lines.append("⏰ Осталось: <b>~1 день</b>")
                else:
                    lines.append(f"⏰ Осталось: <b>~{days_left} дней</b>")
                
                # Предупреждения
                if days_left <= 1:
                    lines.append("🔴 <b>СРОЧНО!</b> Готовь новую партию!")
                elif days_left <= 3:
                    lines.append("🟡 <b>Внимание!</b> Скоро закончится")
    
    # Предупреждение о низком остатке
    if percentage < 0.2:
        lines.append("")
        lines.append("⚠️ <b>Остаток критически низкий!</b>")
    elif percentage < 0.4:
        lines.append("")
        lines.append("⚠️ <b>Остаток становится низким</b>")
    
    # Последнее обновление
    lines.append("")
    now = datetime.now().strftime("%d-%m %H:%M")
    lines.append(f"🔄 Обновлено: {now}")
    
    return "\n".join(lines)
