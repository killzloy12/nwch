#!/usr/bin/env python3
"""
🎭 CUSTOM PERSONALITY SYSTEM v3.0
🔥 Работает через таблицу custom_personalities в database.py
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class CustomPersonalityManager:
    """🎭 Менеджер кастомных персон в БД"""

    def __init__(self, db):
        self.db = db  # DatabaseService
        logger.info("🎭 CustomPersonalityManager инициализирован")

    async def add_personality(
        self,
        personality_id: str,
        name: str,
        description: str,
        system_prompt: str,
        chat_id: Optional[int],
        user_id: Optional[int],
        admin_id: Optional[int],
        is_group: bool = False,
    ) -> bool:
        """➕ Добавить новую персону"""
        try:
            await self.db.execute(
                """
                INSERT OR REPLACE INTO custom_personalities
                (id, personality_name, personality_description, system_prompt, chat_id, user_id, admin_id, created_at, is_group_personality, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    personality_id,
                    name,
                    description,
                    system_prompt,
                    chat_id,
                    user_id,
                    admin_id,
                    datetime.now().isoformat(),
                    1 if is_group else 0,
                ),
            )
            logger.info(f"✅ Персона {name} добавлена в БД")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка добавления персоны: {e}")
            return False

    async def get_personality(self, personality_id: str) -> Optional[Dict]:
        """🔍 Получить персону по ID"""
        try:
            return await self.db.fetch_one(
                "SELECT * FROM custom_personalities WHERE id = ? AND is_active = 1",
                (personality_id,),
            )
        except Exception as e:
            logger.error(f"❌ Ошибка получения персоны: {e}")
            return None

    async def list_personalities(self, chat_id: Optional[int] = None) -> List[Dict]:
        """📋 Список доступных персон"""
        try:
            if chat_id:
                return await self.db.fetch_all(
                    """
                    SELECT * FROM custom_personalities 
                    WHERE (chat_id = ? OR is_group_personality = 1) AND is_active = 1
                    """,
                    (chat_id,),
                )
            else:
                return await self.db.fetch_all(
                    "SELECT * FROM custom_personalities WHERE is_active = 1"
                )
        except Exception as e:
            logger.error(f"❌ Ошибка списка персон: {e}")
            return []

    async def deactivate_personality(self, personality_id: str) -> bool:
        """🚫 Деактивировать персону"""
        try:
            await self.db.execute(
                "UPDATE custom_personalities SET is_active = 0 WHERE id = ?",
                (personality_id,),
            )
            logger.info(f"🚫 Персона {personality_id} деактивирована")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка деактивации персоны: {e}")
            return False

    async def activate_personality(self, personality_id: str) -> bool:
        """✅ Активировать персону"""
        try:
            await self.db.execute(
                "UPDATE custom_personalities SET is_active = 1 WHERE id = ?",
                (personality_id,),
            )
            logger.info(f"✅ Персона {personality_id} активирована")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка активации персоны: {e}")
            return False

    async def get_active_personality(self, chat_id: Optional[int]) -> Optional[Dict]:
        """🔮 Получить активную персону для чата"""
        try:
            return await self.db.fetch_one(
                """
                SELECT * FROM custom_personalities 
                WHERE is_active = 1 
                AND (chat_id = ? OR is_group_personality = 1)
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (chat_id,),
            )
        except Exception as e:
            logger.error(f"❌ Ошибка получения активной персоны: {e}")
            return None
