"""
Статистика и аналитика
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from database import Database


log = logging.getLogger(__name__)


class Statistics:
    """Класс для работы со статистикой"""
    
    def __init__(self, db: Database, timezone_offset: int = 0):
        self.db = db
        self.timezone_offset = timezone_offset
    
    async def get_period_stats(self, days: int = 7) -> Optional[Dict]:
        """
        Получить статистику за период
        
        Args:
            days: количество дней
            
        Returns:
            dict: статистика или None
        """
        try:
            # Получить историю
            history = await self.db.get_history(limit=1000)
            if not history:
                return None
            
            # Граница периода
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Фильтровать по периоду
            period_history = []
            for record in history:
                try:
                    created = datetime.fromisoformat(record["created"])
                    if created >= cutoff_date:
                        period_history.append(record)
                except:
                    continue
            
            if not period_history:
                return None
            
            # Подсчёт статистики
            total_taken = 0
            total_portions = 0
            batches_created = 0
            
            for record in period_history:
                if record["action_type"] == "take":
                    # Извлечь вес из текста "Взято: 200г сырой → ..."
                    try:
                        text = record["text"]
                        if "Взято:" in text and "г сырой" in text:
                            weight_str = text.split("Взято:")[1].split("г сырой")[0].strip()
                            weight = float(weight_str)
                            total_taken += weight
                            total_portions += 1
                    except:
                        continue
                
                elif record["action_type"] == "new_batch":
                    batches_created += 1
            
            # Средние значения
            avg_per_day = total_taken / days if days > 0 else 0
            avg_portion = total_taken / total_portions if total_portions > 0 else 0
            
            return {
                "days": days,
                "total_taken": total_taken,
                "total_portions": total_portions,
                "batches_created": batches_created,
                "avg_per_day": avg_per_day,
                "avg_portion": avg_portion,
                "period_start": cutoff_date,
                "period_end": datetime.now()
            }
            
        except Exception as e:
            log.error(f"Ошибка расчёта статистики: {e}")
            return None
    
    async def get_today_stats(self) -> Optional[Dict]:
        """Получить статистику за сегодня"""
        return await self.get_period_stats(days=1)
    
    async def get_week_stats(self) -> Optional[Dict]:
        """Получить статистику за неделю"""
        return await self.get_period_stats(days=7)
    
    async def get_month_stats(self) -> Optional[Dict]:
        """Получить статистику за месяц"""
        return await self.get_period_stats(days=30)
    
    async def get_batch_history(self, limit: int = 10) -> List[Dict]:
        """
        Получить историю партий
        
        Args:
            limit: количество партий
            
        Returns:
            list: список партий с коэффициентами
        """
        try:
            history = await self.db.get_history(limit=1000)
            if not history:
                return []
            
            batches = []
            for record in history:
                if record["action_type"] == "new_batch":
                    # Извлечь данные из текста
                    try:
                        text = record["text"]
                        # "Новая партия: 1500г сырой → 1200г готовой (к=0.800)"
                        if "→" in text and "к=" in text:
                            raw_str = text.split(":")[1].split("г сырой")[0].strip()
                            cooked_str = text.split("→")[1].split("г готовой")[0].strip()
                            coef_str = text.split("к=")[1].split(")")[0]
                            
                            batches.append({
                                "created": record["created"],
                                "raw": float(raw_str),
                                "cooked": float(cooked_str),
                                "coef": float(coef_str),
                                "text": record["text"]
                            })
                    except:
                        continue
            
            return batches[:limit]
            
        except Exception as e:
            log.error(f"Ошибка получения истории партий: {e}")
            return []
    
    async def format_stats_message(self, days: int = 7) -> str:
        """
        Форматировать сообщение со статистикой
        
        Args:
            days: период в днях
            
        Returns:
            str: отформатированное сообщение
        """
        stats = await self.get_period_stats(days)
        
        if not stats:
            return (
                "📊 <b>СТАТИСТИКА</b>\n\n"
                f"За последние {days} дней нет данных\n\n"
                "Начни брать порции чтобы увидеть статистику! 📈"
            )
        
        # Период
        period_name = {
            1: "СЕГОДНЯ",
            7: "ЗА НЕДЕЛЮ",
            30: "ЗА МЕСЯЦ"
        }.get(days, f"ЗА {days} ДНЕЙ")
        
        # Эмодзи индикатор активности
        activity_emoji = "🔥" if stats["total_portions"] > 10 else "✅" if stats["total_portions"] > 5 else "📊"
        
        lines = [
            f"{activity_emoji} <b>СТАТИСТИКА {period_name}</b>",
            "",
            f"🍗 <b>Съедено:</b> {int(stats['total_taken'])} г",
            f"📊 <b>В среднем:</b> {int(stats['avg_per_day'])} г/день",
            f"🍽️ <b>Порций взято:</b> {stats['total_portions']} шт",
            f"📦 <b>Средняя порция:</b> {int(stats['avg_portion'])} г",
        ]
        
        if stats["batches_created"] > 0:
            lines.append(f"👨‍🍳 <b>Партий создано:</b> {stats['batches_created']}")
        
        # Тренд (если есть данные за предыдущий период)
        prev_stats = await self.get_period_stats(days * 2)
        if prev_stats and prev_stats["total_taken"] > 0:
            prev_taken = prev_stats["total_taken"] - stats["total_taken"]
            if prev_taken > 0:
                change_pct = ((stats["total_taken"] - prev_taken) / prev_taken) * 100
                if abs(change_pct) > 5:
                    trend_emoji = "📈" if change_pct > 0 else "📉"
                    trend_text = "больше" if change_pct > 0 else "меньше"
                    lines.append("")
                    lines.append(f"{trend_emoji} <b>Тренд:</b> {abs(int(change_pct))}% {trend_text}")
        
        # Текущий статус
        batch = await self.db.get_batch()
        if batch:
            raw_left = batch["raw_left"]
            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━━")
            lines.append(f"💾 <b>Текущий остаток:</b> {int(raw_left)} г")
        
        return "\n".join(lines)
