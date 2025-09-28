# Создайте файл app/modules/ultimate_triggers.py

#!/usr/bin/env python3
"""
⚡ ULTIMATE TRIGGERS SYSTEM v4.0
6 типов триггеров с продвинутыми настройками
"""

import logging
import re
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TriggerType(Enum):
    EXACT = "exact"           # Точное совпадение
    CONTAINS = "contains"     # Содержит текст
    STARTS_WITH = "starts"    # Начинается с
    ENDS_WITH = "ends"        # Заканчивается на
    REGEX = "regex"           # Регулярное выражение
    SMART = "smart"           # Умный триггер с AI

@dataclass
class TriggerCondition:
    type: TriggerType
    pattern: str
    case_sensitive: bool = False
    whole_words: bool = False

@dataclass 
class TriggerResponse:
    text: str
    reactions: List[str] = None
    delete_trigger: bool = False
    forward_to: Optional[int] = None

@dataclass
class TriggerConfig:
    id: str
    name: str
    chat_id: int
    creator_id: int
    conditions: List[TriggerCondition]
    responses: List[TriggerResponse]
    is_active: bool = True
    cooldown_seconds: int = 0
    max_uses_per_day: int = 0
    probability: float = 1.0  # Вероятность срабатывания 0.0-1.0
    require_mention: bool = False
    admin_only: bool = False
    created_at: datetime = None
    usage_count: int = 0
    last_used: Optional[datetime] = None

class UltimateTriggersSystem:
    """⚡ Ultimate система триггеров v4.0"""
    
    def __init__(self, db_service, config, ai_service=None):
        self.db = db_service
        self.config = config
        self.ai = ai_service
        
        # Кэш триггеров для быстрого доступа
        self.triggers_cache: Dict[int, List[TriggerConfig]] = {}
        self.last_cache_update = {}
        
        # Статистика использования
        self.usage_stats = {}
        
        logger.info("⚡ Ultimate Triggers System v4.0 инициализирован")
    
    async def initialize(self):
        """Инициализация системы"""
        await self._create_tables()
        await self._load_triggers_cache()
        
        # Запускаем фоновые задачи
        asyncio.create_task(self._cleanup_expired_cooldowns())
        
    async def _create_tables(self):
        """Создает таблицы триггеров"""
        
        # Основная таблица триггеров
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS ultimate_triggers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            chat_id INTEGER NOT NULL,
            creator_id INTEGER NOT NULL,
            conditions TEXT NOT NULL,  -- JSON
            responses TEXT NOT NULL,   -- JSON
            is_active BOOLEAN DEFAULT 1,
            cooldown_seconds INTEGER DEFAULT 0,
            max_uses_per_day INTEGER DEFAULT 0,
            probability REAL DEFAULT 1.0,
            require_mention BOOLEAN DEFAULT 0,
            admin_only BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usage_count INTEGER DEFAULT 0,
            last_used TIMESTAMP,
            
            INDEX(chat_id),
            INDEX(creator_id),
            INDEX(is_active),
            INDEX(name)
        )
        ''')
        
        # Таблица использования триггеров
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS trigger_usage_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_id TEXT NOT NULL,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            response_sent TEXT,
            
            INDEX(trigger_id),
            INDEX(chat_id),
            INDEX(triggered_at)
        )
        ''')
        
        # Таблица кулдаунов
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS trigger_cooldowns (
            trigger_id TEXT NOT NULL,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            
            PRIMARY KEY(trigger_id, chat_id, user_id),
            INDEX(expires_at)
        )
        ''')
    
    async def create_trigger(self, name: str, chat_id: int, creator_id: int,
                           pattern: str, response: str, trigger_type: TriggerType = TriggerType.CONTAINS,
                           **options) -> tuple[bool, str]:
        """⚡ Создает новый триггер"""
        
        try:
            # Валидация
            if len(name) > 50:
                return False, "❌ Имя триггера слишком длинное (макс. 50 символов)"
            
            if len(pattern) > 500:
                return False, "❌ Паттерн слишком длинный (макс. 500 символов)"
            
            if len(response) > 1000:
                return False, "❌ Ответ слишком длинный (макс. 1000 символов)"
            
            # Проверяем regex если нужно
            if trigger_type == TriggerType.REGEX:
                try:
                    re.compile(pattern)
                except re.error as e:
                    return False, f"❌ Неверное регулярное выражение: {str(e)}"
            
            # Генерируем ID
            trigger_id = f"trig_{chat_id}_{creator_id}_{abs(hash(name)) % 1000000}"
            
            # Создаем конфигурацию триггера
            condition = TriggerCondition(
                type=trigger_type,
                pattern=pattern,
                case_sensitive=options.get('case_sensitive', False),
                whole_words=options.get('whole_words', False)
            )
            
            response_obj = TriggerResponse(
                text=response,
                reactions=options.get('reactions', []),
                delete_trigger=options.get('delete_trigger', False),
                forward_to=options.get('forward_to')
            )
            
            trigger_config = TriggerConfig(
                id=trigger_id,
                name=name,
                chat_id=chat_id,
                creator_id=creator_id,
                conditions=[condition],
                responses=[response_obj],
                cooldown_seconds=options.get('cooldown', 0),
                max_uses_per_day=options.get('max_uses', 0),
                probability=options.get('probability', 1.0),
                require_mention=options.get('require_mention', False),
                admin_only=options.get('admin_only', False),
                created_at=datetime.now()
            )
            
            # Сохраняем в БД
            await self.db.execute('''
            INSERT INTO ultimate_triggers 
            (id, name, chat_id, creator_id, conditions, responses, cooldown_seconds,
             max_uses_per_day, probability, require_mention, admin_only)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trigger_id, name, chat_id, creator_id,
                json.dumps([condition.__dict__], ensure_ascii=False),
                json.dumps([response_obj.__dict__], ensure_ascii=False),
                trigger_config.cooldown_seconds,
                trigger_config.max_uses_per_day,
                trigger_config.probability,
                trigger_config.require_mention,
                trigger_config.admin_only
            ))
            
            # Обновляем кэш
            await self._update_chat_cache(chat_id)
            
            success_msg = f"⚡ Триггер **{name}** создан!\n\n"
            success_msg += f"🎯 Тип: {trigger_type.value}\n"
            success_msg += f"🔍 Паттерн: `{pattern}`\n"
            success_msg += f"💬 Ответ: {response[:50]}{'...' if len(response) > 50 else ''}\n"
            
            if trigger_config.cooldown_seconds > 0:
                success_msg += f"⏰ Кулдаун: {trigger_config.cooldown_seconds}с\n"
            
            if trigger_config.probability < 1.0:
                success_msg += f"🎲 Вероятность: {int(trigger_config.probability * 100)}%\n"
            
            return True, success_msg
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания триггера: {e}")
            return False, f"❌ Ошибка создания: {str(e)}"
    
    async def process_message(self, chat_id: int, user_id: int, text: str, 
                            is_mention: bool = False, is_admin: bool = False) -> List[TriggerResponse]:
        """🔍 Обрабатывает сообщение на триггеры"""
        
        try:
            triggered_responses = []
            
            # Получаем триггеры для чата
            triggers = await self._get_chat_triggers(chat_id)
            
            for trigger in triggers:
                if not trigger.is_active:
                    continue
                
                # Проверяем права доступа
                if trigger.admin_only and not is_admin:
                    continue
                
                # Проверяем требование упоминания
                if trigger.require_mention and not is_mention:
                    continue
                
                # Проверяем кулдаун
                if await self._is_on_cooldown(trigger.id, chat_id, user_id):
                    continue
                
                # Проверяем дневной лимит
                if trigger.max_uses_per_day > 0:
                    today_usage = await self._get_today_usage(trigger.id, chat_id)
                    if today_usage >= trigger.max_uses_per_day:
                        continue
                
                # Проверяем вероятность
                if trigger.probability < 1.0:
                    import random
                    if random.random() > trigger.probability:
                        continue
                
                # Проверяем условия триггера
                for condition in trigger.conditions:
                    if await self._check_condition(condition, text):
                        # Триггер сработал!
                        
                        # Устанавливаем кулдаун
                        if trigger.cooldown_seconds > 0:
                            await self._set_cooldown(trigger.id, chat_id, user_id, trigger.cooldown_seconds)
                        
                        # Обновляем статистику
                        await self._update_trigger_stats(trigger.id, chat_id, user_id)
                        
                        # Добавляем ответы
                        for response in trigger.responses:
                            # Обрабатываем переменные в ответе
                            processed_response = await self._process_response_variables(
                                response, chat_id, user_id, text
                            )
                            triggered_responses.append(processed_response)
                        
                        break  # Выходим из цикла условий
            
            return triggered_responses
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки триггеров: {e}")
            return []
    
    async def _check_condition(self, condition: TriggerCondition, text: str) -> bool:
        """Проверяет условие триггера"""
        
        try:
            pattern = condition.pattern
            check_text = text if condition.case_sensitive else text.lower()
            check_pattern = pattern if condition.case_sensitive else pattern.lower()
            
            if condition.type == TriggerType.EXACT:
                return check_text == check_pattern
            
            elif condition.type == TriggerType.CONTAINS:
                if condition.whole_words:
                    # Ищем как отдельные слова
                    import re
                    pattern_escaped = re.escape(check_pattern)
                    regex = r'\b' + pattern_escaped + r'\b'
                    return bool(re.search(regex, check_text, re.IGNORECASE if not condition.case_sensitive else 0))
                else:
                    return check_pattern in check_text
            
            elif condition.type == TriggerType.STARTS_WITH:
                return check_text.startswith(check_pattern)
            
            elif condition.type == TriggerType.ENDS_WITH:
                return check_text.endswith(check_pattern)
            
            elif condition.type == TriggerType.REGEX:
                flags = 0 if condition.case_sensitive else re.IGNORECASE
                return bool(re.search(pattern, text, flags))
            
            elif condition.type == TriggerType.SMART:
                # Умная проверка через AI
                if self.ai:
                    prompt = f"""Определи, подходит ли сообщение под описание триггера.

Описание триггера: {pattern}
Сообщение пользователя: {text}

Отвечай только 'ДА' или 'НЕТ'."""
                    
                    ai_response = await self.ai.generate_response(prompt)
                    return ai_response and 'да' in ai_response.lower()
                else:
                    # Fallback: простая проверка по ключевым словам
                    keywords = pattern.lower().split()
                    return any(keyword in text.lower() for keyword in keywords)
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки условия: {e}")
            return False
    
    async def _process_response_variables(self, response: TriggerResponse, 
                                        chat_id: int, user_id: int, trigger_text: str) -> TriggerResponse:
        """Обрабатывает переменные в ответе триггера"""
        
        try:
            processed_text = response.text
            
            # Заменяем переменные
            variables = {
                '{user_id}': str(user_id),
                '{chat_id}': str(chat_id),
                '{trigger_text}': trigger_text,
                '{time}': datetime.now().strftime('%H:%M'),
                '{date}': datetime.now().strftime('%d.%m.%Y'),
                '{random}': str(random.randint(1, 100))
            }
            
            for var, value in variables.items():
                processed_text = processed_text.replace(var, value)
            
            # Создаем новый объект ответа
            return TriggerResponse(
                text=processed_text,
                reactions=response.reactions,
                delete_trigger=response.delete_trigger,
                forward_to=response.forward_to
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки переменных: {e}")
            return response

# ЭКСПОРТ
__all__ = ["UltimateTriggersSystem", "TriggerType", "TriggerConfig"]
