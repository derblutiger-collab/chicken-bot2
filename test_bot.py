"""
Тесты для бота
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Добавление корневой директории в путь
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from database import Database
from utils import WeightParser, WeightValidator


async def test_database():
    """Тест базы данных"""
    print("🧪 Тестирование базы данных...")
    
    # Создание временной БД
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = Database(db_path)
        await db.init()
        print("✅ БД инициализирована")
        
        # Тест создания партии
        success = await db.create_batch(1500, 1200)
        assert success, "Не удалось создать партию"
        print("✅ Партия создана")
        
        # Тест получения партии
        batch = await db.get_batch()
        assert batch is not None, "Партия не найдена"
        assert batch["raw_total"] == 1500
        assert batch["cooked_total"] == 1200
        assert abs(batch["coef"] - 0.8) < 0.001
        print("✅ Партия получена корректно")
        
        # Тест взятия порции
        result = await db.take_portion(300)
        assert result is not None, "Не удалось взять порцию"
        cooked, raw_left = result
        assert abs(cooked - 240) < 0.1  # 300 * 0.8
        assert abs(raw_left - 1200) < 0.1  # 1500 - 300
        print("✅ Порция взята корректно")
        
        # Тест истории
        history = await db.get_history()
        assert len(history) == 2, f"Ожидалось 2 записи, получено {len(history)}"
        print("✅ История работает")
        
        print("✅ Все тесты БД пройдены!")
        
    finally:
        # Удаление временной БД
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_weight_parser():
    """Тест парсера веса"""
    print("\n🧪 Тестирование парсера веса...")
    
    test_cases = [
        ("1500", 1500),
        ("1500г", 1500),
        ("1.5кг", 1500),
        ("1.5 кг", 1500),
        ("полкило", 500),
        ("четверть", 250),
        ("1/2", 500),
        ("200", 200),
        ("2", 2000),  # Авто-определение кг
        ("invalid", None),
    ]
    
    for text, expected in test_cases:
        result = WeightParser.parse(text)
        if expected is None:
            assert result is None, f"'{text}' должно вернуть None, получено {result}"
        else:
            assert result is not None, f"'{text}' вернуло None"
            assert abs(result - expected) < 0.1, f"'{text}': ожидалось {expected}, получено {result}"
        print(f"✅ '{text}' → {result}г")
    
    print("✅ Все тесты парсера пройдены!")


def test_weight_validator():
    """Тест валидатора веса"""
    print("\n🧪 Тестирование валидатора...")
    
    validator = WeightValidator(min_weight=10, max_weight=10000)
    
    test_cases = [
        (100, True),
        (5000, True),
        (5, False),  # Слишком мало
        (15000, False),  # Слишком много
        (None, False),  # None
        (0, False),  # Ноль
        (-100, False),  # Отрицательное
    ]
    
    for weight, should_be_valid in test_cases:
        is_valid, error = validator.validate(weight)
        assert is_valid == should_be_valid, \
            f"Вес {weight}: ожидалось {should_be_valid}, получено {is_valid}"
        if not is_valid:
            print(f"✅ {weight}г → невалидно ({error})")
        else:
            print(f"✅ {weight}г → валидно")
    
    # Тест валидации коэффициента
    print("\n   Тест валидации коэффициента:")
    coef_tests = [
        (1500, 1200, True),  # 0.8 - норма
        (1500, 1000, True),  # 0.67 - норма
        (1500, 500, False),  # 0.33 - слишком мало
        (1500, 1600, False),  # >1 - больше чем сырая
    ]
    
    for raw, cooked, should_be_valid in coef_tests:
        is_valid, error = validator.validate_coef(raw, cooked)
        assert is_valid == should_be_valid, \
            f"Коэфф {raw}→{cooked}: ожидалось {should_be_valid}, получено {is_valid}"
        coef = cooked / raw
        if not is_valid:
            print(f"✅ {raw}г→{cooked}г (к={coef:.2f}) → невалидно")
        else:
            print(f"✅ {raw}г→{cooked}г (к={coef:.2f}) → валидно")
    
    print("✅ Все тесты валидатора пройдены!")


def test_weight_formatter():
    """Тест форматирования веса"""
    print("\n🧪 Тестирование форматирования веса...")
    
    test_cases = [
        (1500, "1.5 кг"),
        (1000, "1 кг"),
        (500, "500 г"),
        (2500, "2.5 кг"),
        (3000, "3 кг"),
    ]
    
    for grams, expected in test_cases:
        result = WeightParser.format_weight(grams)
        assert result == expected, f"{grams}г: ожидалось '{expected}', получено '{result}'"
        print(f"✅ {grams}г → '{result}'")
    
    print("✅ Все тесты форматирования пройдены!")


def test_config():
    """Тест конфигурации"""
    print("\n🧪 Тестирование конфигурации...")
    
    # Сохранение текущих переменных
    old_token = os.getenv("BOT_TOKEN")
    old_admin_ids = os.getenv("ADMIN_IDS")
    
    try:
        # Установка тестовых значений
        os.environ["BOT_TOKEN"] = "test_token_123"
        os.environ["ADMIN_IDS"] = "123,456,789"
        
        config = Config.from_env()
        
        assert config.bot_token == "test_token_123"
        assert config.admin_ids == [123, 456, 789]
        assert config.is_admin(123) == True
        assert config.is_admin(999) == False
        
        print("✅ Конфигурация загружается корректно")
        print("✅ is_admin работает корректно")
        
    finally:
        # Восстановление переменных
        if old_token:
            os.environ["BOT_TOKEN"] = old_token
        if old_admin_ids:
            os.environ["ADMIN_IDS"] = old_admin_ids
    
    print("✅ Все тесты конфигурации пройдены!")


async def main():
    """Запуск всех тестов"""
    print("=" * 60)
    print("🚀 ЗАПУСК ТЕСТОВ CHICKEN BOT")
    print("=" * 60)
    
    try:
        # Синхронные тесты
        test_config()
        test_weight_parser()
        test_weight_validator()
        test_weight_formatter()
        
        # Асинхронные тесты
        await test_database()
        
        print("\n" + "=" * 60)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ ТЕСТ НЕ ПРОЙДЕН: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Установка тестового токена если не установлен
    if not os.getenv("BOT_TOKEN"):
        os.environ["BOT_TOKEN"] = "test_token_for_tests"
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
