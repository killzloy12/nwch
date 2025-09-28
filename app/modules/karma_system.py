#!/usr/bin/env python3
"""
⚖️ KARMA SYSTEM v3.0
🔥 Работает через таблицу karma в database.py
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class KarmaManager:
    """⚖️ Система кармы"""

    def __init__(self, db):
        self.db = db  # DatabaseService
        logger.info("⚖️ KarmaManager инициализирован")

    async def initialize(self):
        """🚀 Инициализация системы кармы"""
        try:
            # Проверим наличие таблицы (на всякий случай)
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS karma (
                    user_id INTEGER,
                    chat_id INTEGER,
                    points INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, chat_id)
                )
            """)
            logger.info("⚖️ KarmaManager готов к работе")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации кармы: {e}")

    async def get_karma(self, user_id: int, chat_id: int) -> int:
        """🔍 Получить карму пользователя"""
        try:
            row = await self.db.fetch_one(
                "SELECT points FROM karma WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id),
            )
            return row["points"] if row else 0
        except Exception as e:
            logger.error(f"❌ Ошибка получения кармы: {e}")
            return 0

    async def add_karma(self, user_id: int, chat_id: int, delta: int) -> int:
        """➕ Изменить карму пользователя"""
        try:
            current = await self.get_karma(user_id, chat_id)
            new_value = current + delta

            await self.db.execute(
                """
                INSERT OR REPLACE INTO karma (user_id, chat_id, points)
                VALUES (?, ?, ?)
                """,
                (user_id, chat_id, new_value),
            )
            logger.info(f"⚖️ Карма {user_id} в чате {chat_id}: {current} -> {new_value}")
            return new_value
        except Exception as e:
            logger.error(f"❌ Ошибка изменения кармы: {e}")
            return 0

    async def set_karma(self, user_id: int, chat_id: int, value: int) -> bool:
        """📝 Установить карму напрямую"""
        try:
            await self.db.execute(
                """
                INSERT OR REPLACE INTO karma (user_id, chat_id, points)
                VALUES (?, ?, ?)
                """,
                (user_id, chat_id, value),
            )
            logger.info(f"⚖️ Карма {user_id} установлена в {value}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка установки кармы: {e}")
            return False

    async def top_karma(self, chat_id: int, limit: int = 10) -> list:
        """🏆 Топ пользователей по карме в чате"""
        try:
            return await self.db.fetch_all(
                """
                SELECT user_id, points 
                FROM karma 
                WHERE chat_id = ?
                ORDER BY points DESC
                LIMIT ?
                """,
                (chat_id, limit),
            )
        except Exception as e:
            logger.error(f"❌ Ошибка получения топа кармы: {e}")
            return []


# =================== ИНИЦИАЛИЗАЦИЯ ===================

async def create_karma_manager(db) -> KarmaManager:
    """🚀 Создание и инициализация KarmaManager"""
    manager = KarmaManager(db)
    await manager.initialize()
    return manager
