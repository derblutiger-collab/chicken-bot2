"""
Парсер веса из текста
"""
import re
from typing import Optional


class WeightParser:
    """Парсер веса из текстового ввода"""
    
    # Словарь распространенных выражений
    WEIGHT_WORDS = {
        "полкило": 500,
        "пол кило": 500,
        "половина": 500,
        "половинка": 500,
        "четверть": 250,
        "1/4": 250,
        "1/2": 500,
        "кило": 1000,
        "килограмм": 1000,
        "килограма": 1000,
    }
    
    @classmethod
    def parse(cls, text: str) -> Optional[float]:
        """
        Парсинг веса из текста
        
        Поддерживает форматы:
        - 1500 или 1500г - граммы
        - 1.5 или 1.5кг - килограммы
        - полкило, четверть и т.д.
        
        Returns:
            float: вес в граммах или None если не удалось распарсить
        """
        if not text:
            return None
        
        # Нормализация текста
        t = text.lower().strip()
        t = t.replace(",", ".")  # Заменить запятую на точку
        
        # Проверка на ключевые слова
        for word, value in cls.WEIGHT_WORDS.items():
            if word in t:
                return float(value)
        
        # Убираем всё кроме цифр, точек, пробелов и букв "кг"
        t = re.sub(r"[^\d\.кгkg ]", "", t)
        
        # Парсинг килограммов
        kg_patterns = [
            r"([\d\.]+)\s*кг",
            r"([\d\.]+)\s*kg",
        ]
        
        for pattern in kg_patterns:
            kg_match = re.search(pattern, t)
            if kg_match:
                try:
                    kg_value = float(kg_match.group(1))
                    return kg_value * 1000
                except ValueError:
                    continue
        
        # Парсинг граммов (просто число)
        g_match = re.search(r"([\d\.]+)", t)
        if g_match:
            try:
                value = float(g_match.group(1))
                
                # Автоопределение: если меньше 50, вероятно килограммы
                if 0 < value < 50:
                    return value * 1000
                
                return value
            except ValueError:
                return None
        
        return None
    
    @classmethod
    def format_weight(cls, grams: float) -> str:
        """
        Форматирование веса для отображения
        
        Args:
            grams: вес в граммах
            
        Returns:
            str: отформатированная строка в граммах (например "1500 г")
        """
        return f"{int(grams)} г"
