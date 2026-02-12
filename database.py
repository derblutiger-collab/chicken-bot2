"""
Работа с базой данных
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List, Tuple

import aiosqlite


log = logging.getLogger(__name__)


class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    @asynccontextmanager
    async def connection(self):
        """Контекстный менеджер для подключения к БД"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db
    
    async def init(self):
        """Инициализация таблиц БД"""
        async with self.connection() as db:
            # Таблица партий
            await db.execute("""
                CREATE TABLE IF NOT EXISTS batch (
                    id INTEGER PRIMARY KEY,
                    raw_total REAL NOT NULL,
                    raw_left REAL NOT NULL,
                    cooked_total REAL NOT NULL,
                    coef REAL NOT NULL,
                    created TEXT NOT NULL,
                    note TEXT,
                    pinned_msg_id INTEGER,
                    CHECK(raw_total > 0 AND cooked_total > 0 AND coef > 0 AND raw_left >= 0)
                )
            """)
            
            # Таблица истории операций
            await db.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type TEXT NOT NULL,
                    text TEXT NOT NULL,
                    created TEXT NOT NULL
                )
            """)
            
            # Таблица сообщений для автоудаления
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    msg_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    created TEXT NOT NULL
                )
            """)
            
            # Создание индексов для оптимизации
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_created 
                ON history(created DESC)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_created 
                ON messages(created DESC)
            """)
            
            await db.commit()
            log.info("База данных инициализирована")
    
    # ─────────────────── ПАРТИИ ───────────────────
    
    async def get_batch(self) -> Optional[aiosqlite.Row]:
        """Получить текущую партию"""
        try:
            async with self.connection() as db:
                cur = await db.execute("SELECT * FROM batch WHERE id = 1")
                return await cur.fetchone()
        except aiosqlite.Error as e:
            log.error(f"Ошибка при получении партии: {e}")
            return None
    
    async def create_batch(self, raw_total: float, cooked_total: float, note: str = None) -> bool:
        """Создать новую партию"""
        try:
            coef = cooked_total / raw_total
            created = self._now()
            
            async with self.connection() as db:
                await db.execute("DELETE FROM batch")
                await db.execute(
                    """INSERT INTO batch (id, raw_total, raw_left, cooked_total, coef, created, note, pinned_msg_id) 
                       VALUES (1, ?, ?, ?, ?, ?, ?, NULL)""",
                    (raw_total, raw_total, cooked_total, coef, created, note)
                )
                
                # Записать в историю в той же транзакции
                note_text = f" ({note})" if note else ""
                await db.execute(
                    "INSERT INTO history (action_type, text, created) VALUES (?, ?, ?)",
                    ("new_batch", f"Новая партия: {int(raw_total)}г сырой → {int(cooked_total)}г готовой (к={coef:.3f}){note_text}", self._now())
                )
                
                await db.commit()
                
            log.info(f"Создана партия: сырая={raw_total}г, готовая={cooked_total}г, к={coef:.3f}, заметка={note}")
            return True
        except aiosqlite.Error as e:
            log.error(f"Ошибка при создании партии: {e}")
            return False
    
    async def update_raw_left(self, new_value: float) -> bool:
        """Обновить остаток сырой курицы"""
        try:
            async with self.connection() as db:
                await db.execute(
                    "UPDATE batch SET raw_left = ? WHERE id = 1",
                    (new_value,)
                )
                await db.commit()
            return True
        except aiosqlite.Error as e:
            log.error(f"Ошибка при обновлении остатка: {e}")
            return False
    
    async def take_portion(self, raw_amount: float) -> Optional[Tuple[float, float]]:
        """
        Взять порцию
        Возвращает (готовая_порция, новый_остаток) или None при ошибке
        """
        try:
            async with self.connection() as db:
                cur = await db.execute("SELECT raw_left, coef FROM batch WHERE id = 1")
                row = await cur.fetchone()
                
                if not row:
                    log.warning("Партия не найдена")
                    return None
                
                raw_left = row["raw_left"]
                coef = row["coef"]
                
                if raw_amount > raw_left:
                    log.warning(f"Недостаточно сырой: запрошено {raw_amount}г, доступно {raw_left}г")
                    return None
                
                cooked_portion = raw_amount * coef
                new_raw_left = raw_left - raw_amount
                
                await db.execute(
                    "UPDATE batch SET raw_left = ? WHERE id = 1",
                    (new_raw_left,)
                )
                
                # Записать в историю в той же транзакции
                await db.execute(
                    "INSERT INTO history (action_type, text, created) VALUES (?, ?, ?)",
                    ("take", f"Взято: {int(raw_amount)}г сырой → {int(cooked_portion)}г готовой", self._now())
                )
                
                await db.commit()
                
                log.info(f"Взято {raw_amount}г, осталось {new_raw_left}г")
                return cooked_portion, new_raw_left
                
        except aiosqlite.Error as e:
            log.error(f"Ошибка при взятии порции: {e}")
            return None
    
    async def reset_batch(self) -> bool:
        """Очистить текущую партию"""
        try:
            async with self.connection() as db:
                await db.execute("DELETE FROM batch")
                
                # Записать в историю в той же транзакции
                await db.execute(
                    "INSERT INTO history (action_type, text, created) VALUES (?, ?, ?)",
                    ("reset", "Партия удалена", self._now())
                )
                
                await db.commit()
                
            log.info("Партия удалена")
            return True
        except aiosqlite.Error as e:
            log.error(f"Ошибка при удалении партии: {e}")
            return False
    
    async def update_pinned_msg_id(self, msg_id: int) -> bool:
        """Обновить ID закреплённого сообщения"""
        try:
            async with self.connection() as db:
                await db.execute(
                    "UPDATE batch SET pinned_msg_id = ? WHERE id = 1",
                    (msg_id,)
                )
                await db.commit()
            log.info(f"Обновлён ID закреплённого сообщения: {msg_id}")
            return True
        except aiosqlite.Error as e:
            log.error(f"Ошибка при обновлении pinned_msg_id: {e}")
            return False
    
    # ─────────────────── ИСТОРИЯ ───────────────────
    
    async def add_history(self, action_type: str, text: str):
        """Добавить запись в историю"""
        try:
            async with self.connection() as db:
                await db.execute(
                    "INSERT INTO history (action_type, text, created) VALUES (?, ?, ?)",
                    (action_type, text, self._now())
                )
                await db.commit()
        except aiosqlite.Error as e:
            log.error(f"Ошибка при добавлении в историю: {e}")
    
    async def get_history(self, limit: int = 10) -> List[aiosqlite.Row]:
        """Получить последние записи истории"""
        try:
            async with self.connection() as db:
                cur = await db.execute(
                    "SELECT * FROM history ORDER BY id DESC LIMIT ?",
                    (limit,)
                )
                return await cur.fetchall()
        except aiosqlite.Error as e:
            log.error(f"Ошибка при получении истории: {e}")
            return []
    
    async def clear_history(self) -> bool:
        """Очистить историю"""
        try:
            async with self.connection() as db:
                await db.execute("DELETE FROM history")
                await db.commit()
            log.info("История очищена")
            return True
        except aiosqlite.Error as e:
            log.error(f"Ошибка при очистке истории: {e}")
            return False
    
    # ─────────────────── СООБЩЕНИЯ ───────────────────
    
    async def add_message(self, msg_id: int, chat_id: int):
        """Добавить сообщение для отслеживания"""
        try:
            async with self.connection() as db:
                await db.execute(
                    "INSERT INTO messages (msg_id, chat_id, created) VALUES (?, ?, ?)",
                    (msg_id, chat_id, self._now())
                )
                await db.commit()
        except aiosqlite.Error as e:
            log.error(f"Ошибка при добавлении сообщения: {e}")
    
    async def get_old_messages(self, keep_count: int = 5) -> List[Tuple[int, int, int]]:
        """Получить старые сообщения для удаления (id, msg_id, chat_id)"""
        try:
            async with self.connection() as db:
                cur = await db.execute(
                    "SELECT id, msg_id, chat_id FROM messages ORDER BY id DESC"
                )
                rows = await cur.fetchall()
                
                if len(rows) <= keep_count:
                    return []
                
                return [(r["id"], r["msg_id"], r["chat_id"]) for r in rows[keep_count:]]
        except aiosqlite.Error as e:
            log.error(f"Ошибка при получении старых сообщений: {e}")
            return []
    
    async def delete_message_record(self, record_id: int):
        """Удалить запись о сообщении"""
        try:
            async with self.connection() as db:
                await db.execute("DELETE FROM messages WHERE id = ?", (record_id,))
                await db.commit()
        except aiosqlite.Error as e:
            log.error(f"Ошибка при удалении записи сообщения: {e}")
    
    async def clear_messages(self) -> bool:
        """Очистить все записи сообщений"""
        try:
            async with self.connection() as db:
                await db.execute("DELETE FROM messages")
                await db.commit()
            return True
        except aiosqlite.Error as e:
            log.error(f"Ошибка при очистке сообщений: {e}")
            return False
    
    # ─────────────────── УТИЛИТЫ ───────────────────
    
    @staticmethod
    def _now() -> str:
        """Текущая дата и время"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
