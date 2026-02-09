#!/usr/bin/env python3
"""
Скрипт проверки кода перед деплоем
Запускает все проверки без запуска бота
"""
import sys
import os

# Добавить путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("🔍 ПРОВЕРКА КОДА CHICKEN BOT")
print("=" * 70)
print()

# Цвета для вывода
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

errors = []
warnings = []

# ═══════════════════════════════════════════════════════════════════════
# ПРОВЕРКА 1: Синтаксис Python
# ═══════════════════════════════════════════════════════════════════════
print("📝 Проверка 1: Синтаксис Python файлов")
print("-" * 70)

import py_compile

files_to_check = [
    'main.py', 'config.py', 'database.py', 'keyboards.py', 
    'middlewares.py', 'states.py',
    'handlers/__init__.py', 'handlers/start.py', 'handlers/batch.py',
    'handlers/take.py', 'handlers/status.py', 'handlers/history.py',
    'handlers/admin.py', 'handlers/common.py',
    'utils/__init__.py', 'utils/parser.py', 'utils/validators.py'
]

syntax_ok = True
for filepath in files_to_check:
    try:
        py_compile.compile(filepath, doraise=True)
        print(f"  {GREEN}✓{RESET} {filepath}")
    except py_compile.PyCompileError as e:
        print(f"  {RED}✗{RESET} {filepath}: {e}")
        errors.append(f"Ошибка синтаксиса в {filepath}")
        syntax_ok = False

if syntax_ok:
    print(f"\n{GREEN}✅ Синтаксис всех файлов корректен{RESET}\n")
else:
    print(f"\n{RED}❌ Найдены ошибки синтаксиса{RESET}\n")

# ═══════════════════════════════════════════════════════════════════════
# ПРОВЕРКА 2: Импорты
# ═══════════════════════════════════════════════════════════════════════
print("📦 Проверка 2: Импорты модулей")
print("-" * 70)

import_ok = True
try:
    # Установить фиктивный токен для импорта
    os.environ['BOT_TOKEN'] = 'test_token_12345:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh'
    
    print("  Импорт config...")
    from config import Config
    print(f"  {GREEN}✓{RESET} config.Config")
    
    print("  Импорт database...")
    from database import Database
    print(f"  {GREEN}✓{RESET} database.Database")
    
    print("  Импорт keyboards...")
    from keyboards import main_kb, take_kb
    print(f"  {GREEN}✓{RESET} keyboards")
    
    print("  Импорт middlewares...")
    from middlewares import LoggingMiddleware, ErrorHandlerMiddleware
    print(f"  {GREEN}✓{RESET} middlewares")
    
    print("  Импорт states...")
    from states import CookFSM, TakeFSM
    print(f"  {GREEN}✓{RESET} states")
    
    print("  Импорт utils...")
    from utils import WeightParser, WeightValidator
    print(f"  {GREEN}✓{RESET} utils")
    
    print("  Импорт handlers...")
    from handlers import register_handlers
    print(f"  {GREEN}✓{RESET} handlers")
    
    print(f"\n{GREEN}✅ Все импорты работают{RESET}\n")
    
except ImportError as e:
    print(f"  {RED}✗{RESET} Ошибка импорта: {e}")
    errors.append(f"Ошибка импорта: {e}")
    import_ok = False
    print(f"\n{RED}❌ Проблемы с импортами{RESET}\n")

# ═══════════════════════════════════════════════════════════════════════
# ПРОВЕРКА 3: Конфигурация
# ═══════════════════════════════════════════════════════════════════════
print("⚙️  Проверка 3: Конфигурация")
print("-" * 70)

if import_ok:
    try:
        config = Config.from_env()
        print(f"  {GREEN}✓{RESET} BOT_TOKEN загружен")
        print(f"  {GREEN}✓{RESET} DB_PATH: {config.db_path}")
        print(f"  {GREEN}✓{RESET} LOW_THRESHOLD: {config.low_threshold}")
        print(f"  {GREEN}✓{RESET} ADMIN_IDS: {config.admin_ids}")
        print(f"\n{GREEN}✅ Конфигурация корректна{RESET}\n")
    except Exception as e:
        print(f"  {RED}✗{RESET} Ошибка конфигурации: {e}")
        errors.append(f"Ошибка конфигурации: {e}")
        print(f"\n{RED}❌ Проблемы с конфигурацией{RESET}\n")

# ═══════════════════════════════════════════════════════════════════════
# ПРОВЕРКА 4: WeightParser
# ═══════════════════════════════════════════════════════════════════════
print("🔢 Проверка 4: WeightParser")
print("-" * 70)

if import_ok:
    test_cases = [
        ("1500", 1500),
        ("1.5кг", 1500),
        ("полкило", 500),
        ("200", 200),
        ("invalid", None),
    ]
    
    parser_ok = True
    for text, expected in test_cases:
        result = WeightParser.parse(text)
        if expected is None:
            if result is None:
                print(f"  {GREEN}✓{RESET} '{text}' → None")
            else:
                print(f"  {RED}✗{RESET} '{text}' → {result} (ожидалось None)")
                parser_ok = False
        else:
            if result and abs(result - expected) < 0.1:
                print(f"  {GREEN}✓{RESET} '{text}' → {result}г")
            else:
                print(f"  {RED}✗{RESET} '{text}' → {result} (ожидалось {expected})")
                parser_ok = False
    
    if parser_ok:
        print(f"\n{GREEN}✅ WeightParser работает корректно{RESET}\n")
    else:
        errors.append("Ошибки в WeightParser")
        print(f"\n{RED}❌ Проблемы с WeightParser{RESET}\n")

# ═══════════════════════════════════════════════════════════════════════
# ПРОВЕРКА 5: Валидаторы
# ═══════════════════════════════════════════════════════════════════════
print("✓  Проверка 5: Валидаторы")
print("-" * 70)

if import_ok:
    validator = WeightValidator(min_weight=10, max_weight=10000)
    
    test_cases = [
        (100, True, "100г валиден"),
        (5, False, "5г невалиден (слишком мало)"),
        (15000, False, "15000г невалиден (слишком много)"),
        (None, False, "None невалиден"),
    ]
    
    validator_ok = True
    for weight, should_be_valid, desc in test_cases:
        is_valid, error = validator.validate(weight)
        if is_valid == should_be_valid:
            print(f"  {GREEN}✓{RESET} {desc}")
        else:
            print(f"  {RED}✗{RESET} {desc} - получено {is_valid}")
            validator_ok = False
    
    # Проверка коэффициента
    is_valid, error = validator.validate_coef(1500, 1200)
    if is_valid:
        print(f"  {GREEN}✓{RESET} Коэффициент 1500→1200 валиден")
    else:
        print(f"  {RED}✗{RESET} Коэффициент должен быть валиден")
        validator_ok = False
    
    is_valid, error = validator.validate_coef(1500, 1600)
    if not is_valid:
        print(f"  {GREEN}✓{RESET} Коэффициент 1500→1600 невалиден (правильно)")
    else:
        print(f"  {RED}✗{RESET} Коэффициент должен быть невалиден")
        validator_ok = False
    
    if validator_ok:
        print(f"\n{GREEN}✅ Валидаторы работают корректно{RESET}\n")
    else:
        errors.append("Ошибки в валидаторах")
        print(f"\n{RED}❌ Проблемы с валидаторами{RESET}\n")

# ═══════════════════════════════════════════════════════════════════════
# ПРОВЕРКА 6: Наличие файлов для BotHost
# ═══════════════════════════════════════════════════════════════════════
print("📁 Проверка 6: Файлы для BotHost.ru")
print("-" * 70)

required_files = ['Procfile', 'runtime.txt', 'requirements.txt']
bothost_ok = True

for filename in required_files:
    if os.path.exists(filename):
        print(f"  {GREEN}✓{RESET} {filename} существует")
        with open(filename) as f:
            content = f.read().strip()
            print(f"     Содержимое: {content[:50]}...")
    else:
        print(f"  {RED}✗{RESET} {filename} не найден")
        errors.append(f"Отсутствует файл {filename}")
        bothost_ok = False

if bothost_ok:
    print(f"\n{GREEN}✅ Все файлы для BotHost.ru на месте{RESET}\n")
else:
    print(f"\n{RED}❌ Не хватает файлов для BotHost.ru{RESET}\n")

# ═══════════════════════════════════════════════════════════════════════
# ИТОГИ
# ═══════════════════════════════════════════════════════════════════════
print("=" * 70)
print("📊 ИТОГОВЫЙ ОТЧЁТ")
print("=" * 70)

if not errors and not warnings:
    print(f"{GREEN}")
    print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
    print("Код готов к деплою на BotHost.ru")
    print(f"{RESET}")
    sys.exit(0)
else:
    if errors:
        print(f"{RED}")
        print("❌ НАЙДЕНЫ ОШИБКИ:")
        for error in errors:
            print(f"  • {error}")
        print(f"{RESET}")
    
    if warnings:
        print(f"{YELLOW}")
        print("⚠️  ПРЕДУПРЕЖДЕНИЯ:")
        for warning in warnings:
            print(f"  • {warning}")
        print(f"{RESET}")
    
    print()
    print("Исправь ошибки перед деплоем!")
    sys.exit(1)
