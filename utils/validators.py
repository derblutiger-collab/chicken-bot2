"""
Валидаторы данных
"""
from typing import Optional, Tuple


class WeightValidator:
    """Валидатор веса"""
    
    def __init__(self, min_weight: float = 10.0, max_weight: float = 10000.0):
        self.min_weight = min_weight
        self.max_weight = max_weight
    
    def validate(self, weight: Optional[float]) -> Tuple[bool, Optional[str]]:
        """
        Валидация веса
        
        Args:
            weight: вес в граммах
            
        Returns:
            Tuple[bool, Optional[str]]: (валидно, сообщение об ошибке)
        """
        if weight is None:
            return False, "Не удалось распознать вес. Попробуй: 1500 или 1.5 кг"
        
        if weight <= 0:
            return False, "Вес должен быть больше нуля"
        
        if weight < self.min_weight:
            return False, f"Слишком мало (минимум {int(self.min_weight)} г)"
        
        if weight > self.max_weight:
            kg = self.max_weight / 1000
            return False, f"Слишком много (максимум {kg:.0f} кг)"
        
        return True, None
    
    def validate_coef(self, raw: float, cooked: float) -> Tuple[bool, Optional[str]]:
        """
        Валидация коэффициента (готовая должна быть меньше сырой)
        
        Args:
            raw: вес сырой
            cooked: вес готовой
            
        Returns:
            Tuple[bool, Optional[str]]: (валидно, сообщение об ошибке)
        """
        if cooked > raw:
            return False, "Готовой курицы не может быть больше, чем сырой! Проверь данные 🤔"
        
        coef = cooked / raw
        
        # Проверка на адекватность коэффициента (обычно 0.6-0.9)
        if coef < 0.4:
            return False, f"Коэффициент слишком маленький ({coef:.2f}). Курица уменьшилась более чем в 2 раза? 🤨"
        
        if coef > 0.99:
            return False, f"Коэффициент слишком большой ({coef:.2f}). Курица почти не потеряла в весе? 🤨"
        
        return True, None


class PortionValidator:
    """Валидатор порций"""
    
    @staticmethod
    def validate_available(requested: float, available: float) -> Tuple[bool, Optional[str]]:
        """
        Проверка доступности количества
        
        Args:
            requested: запрошенное количество
            available: доступное количество
            
        Returns:
            Tuple[bool, Optional[str]]: (валидно, сообщение об ошибке)
        """
        if requested > available:
            return False, f"Столько нет! Осталось только {int(available)} г"
        
        return True, None
