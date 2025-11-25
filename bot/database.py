"""
SQLite база данных для хранения Business Connections владельцев

Решает критическую проблему потери данных business_owners после рестарта бота.
При каждом деплое Railway данные сохраняются в SQLite и восстанавливаются при старте.
"""

import aiosqlite
import logging
from datetime import datetime
from typing import Optional, Dict, List
import os

logger = logging.getLogger(__name__)


class BusinessOwnersDB:
    """Управление базой данных владельцев Business Connections"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_directory()

    def _ensure_directory(self):
        """Создает директорию для БД если не существует"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"✅ Создана директория для БД: {db_dir}")

    async def init_db(self):
        """Инициализация базы данных и создание таблиц"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS business_connections (
                        connection_id TEXT PRIMARY KEY,
                        owner_user_id INTEGER NOT NULL,
                        owner_name TEXT,
                        owner_username TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Индекс для быстрого поиска по owner_user_id
                await db.execute('''
                    CREATE INDEX IF NOT EXISTS idx_owner_user_id
                    ON business_connections(owner_user_id)
                ''')

                await db.commit()
                logger.info(f"✅ БД инициализирована: {self.db_path}")

                # Показываем статистику
                cursor = await db.execute('SELECT COUNT(*) FROM business_connections WHERE is_active = 1')
                count = await cursor.fetchone()
                logger.info(f"📊 Активных Business Connections в БД: {count[0]}")

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise

    async def save_business_owner(
        self,
        connection_id: str,
        owner_user_id: int,
        owner_name: Optional[str] = None,
        owner_username: Optional[str] = None,
        is_active: bool = True
    ) -> bool:
        """
        Сохраняет или обновляет информацию о владельце Business Connection

        Args:
            connection_id: ID Business Connection
            owner_user_id: Telegram User ID владельца
            owner_name: Имя владельца
            owner_username: Username владельца
            is_active: Активно ли соединение

        Returns:
            True если успешно, False при ошибке
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO business_connections
                    (connection_id, owner_user_id, owner_name, owner_username, is_active, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(connection_id) DO UPDATE SET
                        owner_user_id = excluded.owner_user_id,
                        owner_name = excluded.owner_name,
                        owner_username = excluded.owner_username,
                        is_active = excluded.is_active,
                        updated_at = CURRENT_TIMESTAMP
                ''', (connection_id, owner_user_id, owner_name, owner_username, is_active))

                await db.commit()

                status = "активен" if is_active else "отключен"
                logger.info(f"✅ Сохранен владелец Business Connection: {owner_name or owner_user_id} ({connection_id[:20]}...) - {status}")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения владельца: {e}")
            return False

    async def get_business_owner(self, connection_id: str) -> Optional[int]:
        """
        Получает owner_user_id для данного connection_id

        Args:
            connection_id: ID Business Connection

        Returns:
            owner_user_id или None если не найден
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    'SELECT owner_user_id FROM business_connections WHERE connection_id = ? AND is_active = 1',
                    (connection_id,)
                )
                row = await cursor.fetchone()

                if row:
                    logger.debug(f"✅ Найден владелец для connection {connection_id[:20]}...: user_id={row[0]}")
                    return row[0]
                else:
                    logger.debug(f"⚠️ Владелец не найден для connection {connection_id[:20]}...")
                    return None

        except Exception as e:
            logger.error(f"❌ Ошибка получения владельца: {e}")
            return None

    async def is_owner_message(self, connection_id: str, user_id: int) -> bool:
        """
        Проверяет, является ли сообщение от владельца Business Connection

        Args:
            connection_id: ID Business Connection
            user_id: Telegram User ID отправителя

        Returns:
            True если это сообщение от владельца, False иначе
        """
        owner_id = await self.get_business_owner(connection_id)

        if owner_id is None:
            logger.warning(f"⚠️ Владелец не найден для connection {connection_id[:20]}..., считаем что это клиент")
            return False

        is_owner = str(user_id) == str(owner_id)

        if is_owner:
            logger.info(f"🚫 Сообщение от ВЛАДЕЛЬЦА аккаунта (user_id={user_id})")
        else:
            logger.info(f"✅ Сообщение от КЛИЕНТА (user_id={user_id}, owner_id={owner_id})")

        return is_owner

    async def get_all_owners(self) -> List[Dict]:
        """
        Получает список всех активных владельцев Business Connections

        Returns:
            Список словарей с информацией о владельцах
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT connection_id, owner_user_id, owner_name, owner_username, created_at, updated_at
                    FROM business_connections
                    WHERE is_active = 1
                    ORDER BY updated_at DESC
                ''')
                rows = await cursor.fetchall()

                owners = [
                    {
                        'connection_id': row['connection_id'],
                        'owner_user_id': row['owner_user_id'],
                        'owner_name': row['owner_name'],
                        'owner_username': row['owner_username'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                    for row in rows
                ]

                logger.info(f"📊 Получено {len(owners)} активных владельцев из БД")
                return owners

        except Exception as e:
            logger.error(f"❌ Ошибка получения списка владельцев: {e}")
            return []

    async def deactivate_connection(self, connection_id: str) -> bool:
        """
        Деактивирует Business Connection (при отключении)

        Args:
            connection_id: ID Business Connection

        Returns:
            True если успешно, False при ошибке
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE business_connections
                    SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE connection_id = ?
                ''', (connection_id,))

                await db.commit()
                logger.info(f"❌ Деактивирован Business Connection: {connection_id[:20]}...")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка деактивации connection: {e}")
            return False

    async def get_stats(self) -> Dict:
        """
        Получает статистику по базе данных

        Returns:
            Словарь со статистикой
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Активные соединения
                cursor = await db.execute('SELECT COUNT(*) FROM business_connections WHERE is_active = 1')
                active_count = (await cursor.fetchone())[0]

                # Всего соединений
                cursor = await db.execute('SELECT COUNT(*) FROM business_connections')
                total_count = (await cursor.fetchone())[0]

                # Последнее обновление
                cursor = await db.execute('SELECT MAX(updated_at) FROM business_connections')
                last_update = (await cursor.fetchone())[0]

                stats = {
                    'active_connections': active_count,
                    'total_connections': total_count,
                    'inactive_connections': total_count - active_count,
                    'last_update': last_update,
                    'db_path': self.db_path,
                    'db_exists': os.path.exists(self.db_path),
                    'db_size_bytes': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                }

                logger.info(f"📊 Статистика БД: активных={active_count}, всего={total_count}")
                return stats

        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {
                'error': str(e),
                'active_connections': 0,
                'total_connections': 0
            }
