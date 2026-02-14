"""
Автоматические бэкапы базы данных
"""
import logging
import os
import gzip
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from aiogram import Bot
from aiogram.types import FSInputFile


log = logging.getLogger(__name__)


class BackupManager:
    """Менеджер бэкапов базы данных"""
    
    def __init__(
        self,
        db_path: str,
        backup_dir: str = "/tmp/backups",
        keep_days: int = 7
    ):
        """
        Args:
            db_path: путь к файлу БД
            backup_dir: директория для хранения бэкапов
            keep_days: сколько дней хранить бэкапы
        """
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.keep_days = keep_days
        
        # Создать директорию если нет
        os.makedirs(backup_dir, exist_ok=True)
    
    async def create_backup(self) -> Optional[str]:
        """
        Создать бэкап БД
        
        Returns:
            str: путь к созданному бэкапу или None если ошибка
        """
        try:
            # Проверить что БД существует
            if not os.path.exists(self.db_path):
                log.error(f"БД не найдена: {self.db_path}")
                return None
            
            # Имя бэкапа с датой и временем
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"chicken_backup_{timestamp}.db.gz"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Сжать и скопировать БД
            with open(self.db_path, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Размер бэкапа
            size_bytes = os.path.getsize(backup_path)
            size_kb = size_bytes / 1024
            
            log.info(f"✅ Бэкап создан: {backup_name} ({size_kb:.1f} KB)")
            return backup_path
            
        except Exception as e:
            log.error(f"❌ Ошибка создания бэкапа: {e}", exc_info=True)
            return None
    
    async def send_backup_to_admin(
        self,
        bot: Bot,
        admin_id: int,
        backup_path: str
    ) -> bool:
        """
        Отправить бэкап администратору
        
        Args:
            bot: экземпляр бота
            admin_id: ID администратора
            backup_path: путь к бэкапу
            
        Returns:
            bool: успешно ли отправлено
        """
        try:
            # Информация о бэкапе
            size_bytes = os.path.getsize(backup_path)
            size_kb = size_bytes / 1024
            filename = os.path.basename(backup_path)
            
            # Отправить файл
            document = FSInputFile(backup_path, filename=filename)
            
            caption = (
                f"💾 <b>Автоматический бэкап БД</b>\n\n"
                f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                f"📦 Размер: {size_kb:.1f} KB\n"
                f"🔐 Сжат: gzip\n\n"
                f"<i>Храни в безопасном месте!</i>"
            )
            
            await bot.send_document(
                chat_id=admin_id,
                document=document,
                caption=caption
            )
            
            log.info(f"✅ Бэкап отправлен админу {admin_id}")
            return True
            
        except Exception as e:
            log.error(f"❌ Ошибка отправки бэкапа: {e}", exc_info=True)
            return False
    
    async def cleanup_old_backups(self):
        """Удалить старые бэкапы"""
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=self.keep_days)
            deleted_count = 0
            
            # Перебрать файлы в директории
            for filename in os.listdir(self.backup_dir):
                if not filename.startswith("chicken_backup_"):
                    continue
                
                filepath = os.path.join(self.backup_dir, filename)
                
                # Получить дату файла
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                # Удалить если старый
                if file_time < cutoff_date:
                    os.remove(filepath)
                    deleted_count += 1
                    log.info(f"🗑️ Удалён старый бэкап: {filename}")
            
            if deleted_count > 0:
                log.info(f"🧹 Удалено старых бэкапов: {deleted_count}")
            
        except Exception as e:
            log.error(f"❌ Ошибка очистки бэкапов: {e}", exc_info=True)
    
    async def auto_backup(self, bot: Bot, admin_ids: list[int]) -> bool:
        """
        Автоматический бэкап (вызывать по расписанию)
        
        Args:
            bot: экземпляр бота
            admin_ids: список ID администраторов
            
        Returns:
            bool: успешно ли выполнено
        """
        try:
            log.info("🔄 Запуск автоматического бэкапа...")
            
            # Создать бэкап
            backup_path = await self.create_backup()
            if not backup_path:
                return False
            
            # Отправить всем админам
            success_count = 0
            for admin_id in admin_ids:
                if await self.send_backup_to_admin(bot, admin_id, backup_path):
                    success_count += 1
            
            # Очистить старые бэкапы
            await self.cleanup_old_backups()
            
            log.info(f"✅ Автобэкап завершён: отправлено {success_count}/{len(admin_ids)} админам")
            return success_count > 0
            
        except Exception as e:
            log.error(f"❌ Ошибка автобэкапа: {e}", exc_info=True)
            return False
