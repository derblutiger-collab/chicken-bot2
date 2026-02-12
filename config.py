"""
Конфигурация бота
"""
import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    """Конфигурация приложения"""
    
    bot_token: str
    db_path: str = "chicken.db"
    low_threshold: int = 300  # г
    max_messages_store: int = 5
    admin_ids: List[int] = field(default_factory=list)
    
    # ID топика (ветки) в группе где работает бот
    # Если None - работает везде
    topic_id: int = None
    
    # Лимиты веса
    min_weight: float = 10.0  # г
    max_weight: float = 10000.0  # г (10 кг)
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Создание конфигурации из переменных окружения"""
        token = os.getenv("BOT_TOKEN")
        if not token:
            raise RuntimeError("BOT_TOKEN не найден в переменных окружения")
        
        # Парсинг списка админов
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        admin_ids = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip()]
        
        # Парсинг ID топика
        topic_id_str = os.getenv("TOPIC_ID", "")
        topic_id = int(topic_id_str) if topic_id_str.strip() else None
        
        return cls(
            bot_token=token,
            db_path=os.getenv("DB_PATH", "chicken.db"),
            low_threshold=int(os.getenv("LOW_THRESHOLD", "300")),
            max_messages_store=int(os.getenv("MAX_MESSAGES", "5")),
            admin_ids=admin_ids if admin_ids else [],
            topic_id=topic_id,
            min_weight=float(os.getenv("MIN_WEIGHT", "10.0")),
            max_weight=float(os.getenv("MAX_WEIGHT", "10000.0"))
        )
    
    def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        return user_id in self.admin_ids if self.admin_ids else False
