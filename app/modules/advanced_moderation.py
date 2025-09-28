# Создайте файл app/modules/advanced_moderation.py

#!/usr/bin/env python3
"""
🛡️ ULTIMATE MODERATION SYSTEM v4.0
Полная система модерации: баны, муты, кики, предупреждения
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ModerationAction(Enum):
    WARN = "warn"
    MUTE = "mute" 
    KICK = "kick"
    BAN = "ban"
    UNBAN = "unban"
    UNMUTE = "unmute"

@dataclass
class ModerationCase:
    id: str
    chat_id: int
    user_id: int
    moderator_id: int
    action: ModerationAction
    reason: str
    duration: Optional[timedelta]
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool = True

class UltimateModerationSystem:
    """🛡️ Система модерации Ultimate Edition"""
    
    def __init__(self, db_service, bot, config):
        self.db = db_service
        self.bot = bot
        self.config = config
        
        # Автоматические действия по предупреждениям
        self.auto_actions = {
            3: ModerationAction.MUTE,    # 3 предупреждения = мут на час
            5: ModerationAction.KICK,    # 5 предупреждений = кик
            7: ModerationAction.BAN      # 7 предупреждений = бан
        }
        
        # Длительности по умолчанию
        self.default_durations = {
            ModerationAction.MUTE: timedelta(hours=1),
            ModerationAction.BAN: timedelta(days=1)
        }
        
        logger.info("🛡️ Ultimate Moderation System инициализирован")
    
    async def initialize(self):
        """Инициализация БД"""
        await self._create_tables()
        await self._load_active_restrictions()
    
    async def _create_tables(self):
        """Создает таблицы модерации"""
        
        # Таблица кейсов модерации
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS moderation_cases (
            id TEXT PRIMARY KEY,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            moderator_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            reason TEXT NOT NULL,
            duration_minutes INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            
            INDEX(chat_id),
            INDEX(user_id),
            INDEX(action),
            INDEX(expires_at),
            INDEX(is_active)
        )
        ''')
        
        # Таблица предупреждений
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS user_warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            moderator_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            
            INDEX(chat_id, user_id),
            INDEX(is_active)
        )
        ''')
        
        # Таблица настроек модерации для чатов
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS chat_moderation_settings (
            chat_id INTEGER PRIMARY KEY,
            auto_moderation BOOLEAN DEFAULT 1,
            max_warnings INTEGER DEFAULT 3,
            mute_duration_minutes INTEGER DEFAULT 60,
            ban_duration_hours INTEGER DEFAULT 24,
            delete_spam BOOLEAN DEFAULT 1,
            antispam_enabled BOOLEAN DEFAULT 1,
            antiflood_enabled BOOLEAN DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
    
    async def warn_user(self, chat_id: int, user_id: int, moderator_id: int, 
                       reason: str = "Нарушение правил") -> Tuple[bool, str, Optional[ModerationAction]]:
        """⚠️ Выдает предупреждение пользователю"""
        
        try:
            # Добавляем предупреждение
            await self.db.execute('''
            INSERT INTO user_warnings (chat_id, user_id, moderator_id, reason)
            VALUES (?, ?, ?, ?)
            ''', (chat_id, user_id, moderator_id, reason))
            
            # Считаем общее количество предупреждений
            result = await self.db.fetch_one('''
            SELECT COUNT(*) FROM user_warnings 
            WHERE chat_id = ? AND user_id = ? AND is_active = 1
            ''', (chat_id, user_id))
            
            warnings_count = result[0] if result else 0
            
            # Проверяем нужно ли автоматическое действие
            auto_action = None
            if warnings_count in self.auto_actions:
                auto_action = self.auto_actions[warnings_count]
                
                # Выполняем автоматическое действие
                if auto_action == ModerationAction.MUTE:
                    await self.mute_user(chat_id, user_id, moderator_id, 
                                       f"Автомут за {warnings_count} предупреждений", 
                                       self.default_durations[ModerationAction.MUTE])
                elif auto_action == ModerationAction.KICK:
                    await self.kick_user(chat_id, user_id, moderator_id, 
                                       f"Автокик за {warnings_count} предупреждений")
                elif auto_action == ModerationAction.BAN:
                    await self.ban_user(chat_id, user_id, moderator_id, 
                                      f"Автобан за {warnings_count} предупреждений",
                                      self.default_durations[ModerationAction.BAN])
            
            success_msg = f"⚠️ Предупреждение выдано!\n\nВсего предупреждений: {warnings_count}"
            if auto_action:
                success_msg += f"\n🤖 Автоматическое действие: {auto_action.value}"
            
            return True, success_msg, auto_action
            
        except Exception as e:
            logger.error(f"❌ Ошибка выдачи предупреждения: {e}")
            return False, f"❌ Ошибка: {str(e)}", None
    
    async def mute_user(self, chat_id: int, user_id: int, moderator_id: int, 
                       reason: str, duration: timedelta = None) -> Tuple[bool, str]:
        """🔇 Мутит пользователя"""
        
        try:
            if not duration:
                duration = self.default_durations[ModerationAction.MUTE]
            
            expires_at = datetime.now() + duration
            case_id = f"mute_{chat_id}_{user_id}_{int(datetime.now().timestamp())}"
            
            # Сохраняем в БД
            await self.db.execute('''
            INSERT INTO moderation_cases 
            (id, chat_id, user_id, moderator_id, action, reason, duration_minutes, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (case_id, chat_id, user_id, moderator_id, ModerationAction.MUTE.value, 
                  reason, int(duration.total_seconds() / 60), expires_at))
            
            # Мутим в Telegram
            try:
                from aiogram.types import ChatPermissions
                await self.bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=expires_at
                )
            except Exception as e:
                logger.warning(f"⚠️ Не удалось замутить в Telegram: {e}")
            
            # Планируем размут
            asyncio.create_task(self._schedule_unmute(case_id, chat_id, user_id, duration))
            
            duration_str = self._format_duration(duration)
            return True, f"🔇 Пользователь замучен на {duration_str}\n\nПричина: {reason}"
            
        except Exception as e:
            logger.error(f"❌ Ошибка мута: {e}")
            return False, f"❌ Ошибка мута: {str(e)}"
    
    async def ban_user(self, chat_id: int, user_id: int, moderator_id: int, 
                      reason: str, duration: timedelta = None) -> Tuple[bool, str]:
        """🚫 Банит пользователя"""
        
        try:
            expires_at = None
            if duration:
                expires_at = datetime.now() + duration
            
            case_id = f"ban_{chat_id}_{user_id}_{int(datetime.now().timestamp())}"
            
            # Сохраняем в БД
            duration_minutes = int(duration.total_seconds() / 60) if duration else None
            await self.db.execute('''
            INSERT INTO moderation_cases 
            (id, chat_id, user_id, moderator_id, action, reason, duration_minutes, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (case_id, chat_id, user_id, moderator_id, ModerationAction.BAN.value, 
                  reason, duration_minutes, expires_at))
            
            # Баним в Telegram
            try:
                await self.bot.ban_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    until_date=expires_at
                )
            except Exception as e:
                logger.warning(f"⚠️ Не удалось забанить в Telegram: {e}")
            
            # Планируем разбан если есть длительность
            if duration:
                asyncio.create_task(self._schedule_unban(case_id, chat_id, user_id, duration))
                duration_str = self._format_duration(duration)
                return True, f"🚫 Пользователь забанен на {duration_str}\n\nПричина: {reason}"
            else:
                return True, f"🚫 Пользователь забанен навсегда\n\nПричина: {reason}"
            
        except Exception as e:
            logger.error(f"❌ Ошибка бана: {e}")
            return False, f"❌ Ошибка бана: {str(e)}"
    
    async def kick_user(self, chat_id: int, user_id: int, moderator_id: int, 
                       reason: str) -> Tuple[bool, str]:
        """👢 Кикает пользователя"""
        
        try:
            case_id = f"kick_{chat_id}_{user_id}_{int(datetime.now().timestamp())}"
            
            # Сохраняем в БД
            await self.db.execute('''
            INSERT INTO moderation_cases 
            (id, chat_id, user_id, moderator_id, action, reason)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (case_id, chat_id, user_id, moderator_id, ModerationAction.KICK.value, reason))
            
            # Кикаем в Telegram
            try:
                await self.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
                await asyncio.sleep(0.1)  # Небольшая задержка
                await self.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
            except Exception as e:
                logger.warning(f"⚠️ Не удалось кикнуть в Telegram: {e}")
            
            return True, f"👢 Пользователь кикнут\n\nПричина: {reason}"
            
        except Exception as e:
            logger.error(f"❌ Ошибка кика: {e}")
            return False, f"❌ Ошибка кика: {str(e)}"
    
    def _format_duration(self, duration: timedelta) -> str:
        """Форматирует длительность"""
        
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds} сек"
        elif total_seconds < 3600:
            return f"{total_seconds // 60} мин"
        elif total_seconds < 86400:
            return f"{total_seconds // 3600} ч"
        else:
            return f"{total_seconds // 86400} дн"
    
    async def _schedule_unmute(self, case_id: str, chat_id: int, user_id: int, duration: timedelta):
        """Планирует размут"""
        await asyncio.sleep(duration.total_seconds())
        await self.unmute_user(chat_id, user_id, case_id)
    
    async def _schedule_unban(self, case_id: str, chat_id: int, user_id: int, duration: timedelta):
        """Планирует разбан"""
        await asyncio.sleep(duration.total_seconds())
        await self.unban_user(chat_id, user_id, case_id)
    
    async def unmute_user(self, chat_id: int, user_id: int, case_id: str = None) -> Tuple[bool, str]:
        """🔊 Размучивает пользователя"""
        
        try:
            # Размучиваем в Telegram
            try:
                from aiogram.types import ChatPermissions
                default_permissions = ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True
                )
                await self.bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    permissions=default_permissions
                )
            except Exception as e:
                logger.warning(f"⚠️ Не удалось размутить в Telegram: {e}")
            
            # Обновляем БД
            if case_id:
                await self.db.execute('''
                UPDATE moderation_cases SET is_active = 0 WHERE id = ?
                ''', (case_id,))
            
            return True, "🔊 Пользователь размучен"
            
        except Exception as e:
            logger.error(f"❌ Ошибка размута: {e}")
            return False, f"❌ Ошибка размута: {str(e)}"
    
    async def unban_user(self, chat_id: int, user_id: int, case_id: str = None) -> Tuple[bool, str]:
        """♻️ Разбанивает пользователя"""
        
        try:
            # Разбаниваем в Telegram
            try:
                await self.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
            except Exception as e:
                logger.warning(f"⚠️ Не удалось разбанить в Telegram: {e}")
            
            # Обновляем БД
            if case_id:
                await self.db.execute('''
                UPDATE moderation_cases SET is_active = 0 WHERE id = ?
                ''', (case_id,))
            
            return True, "♻️ Пользователь разбанен"
            
        except Exception as e:
            logger.error(f"❌ Ошибка разбана: {e}")
            return False, f"❌ Ошибка разбана: {str(e)}"
    
    async def get_user_warnings(self, chat_id: int, user_id: int) -> int:
        """Получает количество предупреждений пользователя"""
        
        try:
            result = await self.db.fetch_one('''
            SELECT COUNT(*) FROM user_warnings 
            WHERE chat_id = ? AND user_id = ? AND is_active = 1
            ''', (chat_id, user_id))
            
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения предупреждений: {e}")
            return 0
    
    async def clear_user_warnings(self, chat_id: int, user_id: int, moderator_id: int) -> Tuple[bool, str]:
        """Очищает предупреждения пользователя"""
        
        try:
            result = await self.db.execute('''
            UPDATE user_warnings SET is_active = 0 
            WHERE chat_id = ? AND user_id = ? AND is_active = 1
            ''', (chat_id, user_id))
            
            return True, f"✅ Предупреждения очищены"
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки предупреждений: {e}")
            return False, f"❌ Ошибка: {str(e)}"

# ЭКСПОРТ
__all__ = ["UltimateModerationSystem", "ModerationAction", "ModerationCase"]
