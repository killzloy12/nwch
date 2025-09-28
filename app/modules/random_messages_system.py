# Создайте файл app/modules/random_messages_system.py

#!/usr/bin/env python3
"""
💬 RANDOM MESSAGES SYSTEM v4.0
Система случайных сообщений в чаты с умным планированием
"""

import logging
import asyncio
import random
import json
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class MessageType(Enum):
    FACT = "fact"
    JOKE = "joke"
    MOTIVATION = "motivation"
    WEATHER = "weather"
    NEWS = "news"
    GREETING = "greeting"
    GOODNIGHT = "goodnight"
    CUSTOM = "custom"

@dataclass
class ScheduledMessage:
    message_id: str
    chat_id: int
    message_type: MessageType
    content: str
    schedule_type: str  # once, daily, weekly, monthly
    schedule_time: time
    schedule_days: List[int]  # Дни недели (0-6, 0=понедельник)
    is_active: bool = True
    created_at: datetime = None
    last_sent: Optional[datetime] = None
    send_count: int = 0
    creator_id: Optional[int] = None

@dataclass
class ChatMessageSettings:
    chat_id: int
    enabled: bool = False
    min_interval_hours: int = 6
    max_interval_hours: int = 24
    active_hours_start: int = 9  # 9:00
    active_hours_end: int = 22   # 22:00
    allowed_types: List[MessageType] = None
    custom_messages: List[str] = None
    last_random_message: Optional[datetime] = None

class RandomMessagesSystem:
    """💬 Система случайных сообщений"""
    
    def __init__(self, db_service, bot, config, entertainment_system=None):
        self.db = db_service
        self.bot = bot
        self.config = config
        self.entertainment = entertainment_system
        
        # Настройки чатов
        self.chat_settings: Dict[int, ChatMessageSettings] = {}
        
        # Запланированные сообщения
        self.scheduled_messages: Dict[str, ScheduledMessage] = {}
        
        # Очередь сообщений для отправки
        self.message_queue = asyncio.Queue()
        
        # Контент для разных типов сообщений
        self.content_templates = {
            MessageType.FACT: [
                "🧠 **А вы знали?**\n{content}",
                "💡 **Интересный факт:**\n{content}",
                "🌟 **Удивительно, но факт:**\n{content}"
            ],
            MessageType.JOKE: [
                "😄 **Шутка дня:**\n{content}",
                "🤡 **Время смеяться:**\n{content}",
                "😂 **Анекдот:**\n{content}"
            ],
            MessageType.MOTIVATION: [
                "💪 **Мотивация дня:**\n{content}",
                "🌟 **Вдохновляющая мысль:**\n{content}",
                "🚀 **Заряд позитива:**\n{content}"
            ],
            MessageType.GREETING: [
                "🌅 **Доброе утро, {chat_name}!**\n{content}",
                "☀️ **Отличного дня!**\n{content}",
                "🌤️ **Хорошего утра!**\n{content}"
            ],
            MessageType.GOODNIGHT: [
                "🌙 **Спокойной ночи, {chat_name}!**\n{content}",
                "💫 **Сладких снов!**\n{content}",
                "🌟 **Доброй ночи!**\n{content}"
            ]
        }
        
        # Мотивационные цитаты
        self.motivational_quotes = [
            "Единственный способ сделать великую работу - это любить то, что ты делаешь.",
            "Не бойся отказаться от хорошего ради великого.",
            "Успех - это способность двигаться от неудачи к неудаче, не теряя энтузиазма.",
            "Лучшее время для посадки дерева было 20 лет назад. Второе лучшее время - сейчас.",
            "Не ждите. Время никогда не будет подходящим.",
            "Путь в тысячу миль начинается с одного шага.",
            "Ваша единственная граница - это ваш разум.",
            "Мечты не имеют срока годности.",
            "Будьте собой. Все остальные роли уже заняты.",
            "Жизнь на 10% состоит из того, что с вами происходит, и на 90% из того, как вы на это реагируете."
        ]
        
        logger.info("💬 Random Messages System инициализирован")
    
    async def initialize(self):
        """Инициализация системы"""
        await self._create_tables()
        await self._load_chat_settings()
        await self._load_scheduled_messages()
        
        # Запускаем фоновые задачи
        asyncio.create_task(self._message_sender_loop())
        asyncio.create_task(self._random_message_scheduler())
        asyncio.create_task(self._scheduled_message_checker())
    
    async def _create_tables(self):
        """Создает таблицы для системы сообщений"""
        
        # Настройки чатов
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS chat_message_settings (
            chat_id INTEGER PRIMARY KEY,
            enabled BOOLEAN DEFAULT 0,
            min_interval_hours INTEGER DEFAULT 6,
            max_interval_hours INTEGER DEFAULT 24,
            active_hours_start INTEGER DEFAULT 9,
            active_hours_end INTEGER DEFAULT 22,
            allowed_types TEXT,  -- JSON array
            custom_messages TEXT,  -- JSON array
            last_random_message TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Запланированные сообщения
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_messages (
            message_id TEXT PRIMARY KEY,
            chat_id INTEGER NOT NULL,
            message_type TEXT NOT NULL,
            content TEXT NOT NULL,
            schedule_type TEXT NOT NULL,
            schedule_time TEXT NOT NULL,  -- HH:MM format
            schedule_days TEXT,  -- JSON array of weekdays
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_sent TIMESTAMP,
            send_count INTEGER DEFAULT 0,
            creator_id INTEGER,
            
            INDEX(chat_id),
            INDEX(is_active),
            INDEX(schedule_type)
        )
        ''')
        
        # История отправленных сообщений
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS sent_messages_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            message_type TEXT NOT NULL,
            content_preview TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_scheduled BOOLEAN DEFAULT 0,
            message_id INTEGER,  -- ID сообщения в Telegram
            
            INDEX(chat_id, sent_at),
            INDEX(message_type)
        )
        ''')
        
        # Пользовательский контент
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS user_message_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content_type TEXT NOT NULL,
            content TEXT NOT NULL,
            is_approved BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_by INTEGER,
            approved_at TIMESTAMP,
            
            INDEX(chat_id, content_type),
            INDEX(is_approved)
        )
        ''')
    
    async def enable_random_messages(self, chat_id: int, user_id: int, 
                                   **settings) -> Tuple[bool, str]:
        """🔄 Включает случайные сообщения для чата"""
        
        try:
            # Проверяем права (только админы)
            if user_id not in self.config.bot.admin_ids:
                return False, "🚫 Только админы бота могут управлять случайными сообщениями"
            
            # Настройки по умолчанию
            chat_settings = ChatMessageSettings(
                chat_id=chat_id,
                enabled=True,
                min_interval_hours=settings.get('min_interval', 6),
                max_interval_hours=settings.get('max_interval', 24),
                active_hours_start=settings.get('start_hour', 9),
                active_hours_end=settings.get('end_hour', 22),
                allowed_types=[MessageType.FACT, MessageType.JOKE, MessageType.MOTIVATION],
                custom_messages=[]
            )
            
            # Сохраняем в БД
            await self.db.execute('''
            INSERT OR REPLACE INTO chat_message_settings 
            (chat_id, enabled, min_interval_hours, max_interval_hours, 
             active_hours_start, active_hours_end, allowed_types)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                chat_id, True, chat_settings.min_interval_hours, chat_settings.max_interval_hours,
                chat_settings.active_hours_start, chat_settings.active_hours_end,
                json.dumps([t.value for t in chat_settings.allowed_types])
            ))
            
            # Обновляем кэш
            self.chat_settings[chat_id] = chat_settings
            
            success_msg = f"✅ **Случайные сообщения включены!**\n\n"
            success_msg += f"⏰ **Интервал:** {chat_settings.min_interval_hours}-{chat_settings.max_interval_hours} часов\n"
            success_msg += f"🕐 **Активное время:** {chat_settings.active_hours_start:02d}:00 - {chat_settings.active_hours_end:02d}:00\n"
            success_msg += f"📝 **Типы сообщений:** факты, шутки, мотивация"
            
            return True, success_msg
            
        except Exception as e:
            logger.error(f"❌ Ошибка включения случайных сообщений: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    async def schedule_message(self, chat_id: int, user_id: int, message_type: MessageType,
                             content: str, schedule_time: str, schedule_type: str = "daily",
                             schedule_days: List[int] = None) -> Tuple[bool, str]:
        """📅 Планирует отправку сообщения"""
        
        try:
            # Проверяем права
            if user_id not in self.config.bot.admin_ids:
                return False, "🚫 Только админы бота могут планировать сообщения"
            
            # Валидация времени
            try:
                time_obj = time.fromisoformat(schedule_time)
            except ValueError:
                return False, "❌ Неверный формат времени. Используйте HH:MM (например, 09:30)"
            
            # Валидация типа расписания
            if schedule_type not in ['once', 'daily', 'weekly', 'monthly']:
                return False, "❌ Неверный тип расписания. Используйте: once, daily, weekly, monthly"
            
            # Дни недели по умолчанию (все дни для daily)
            if not schedule_days:
                if schedule_type == 'weekly':
                    schedule_days = [0]  # Понедельник
                else:
                    schedule_days = list(range(7))  # Все дни недели
            
            # Создаем ID сообщения
            message_id = f"sched_{chat_id}_{user_id}_{int(datetime.now().timestamp())}"
            
            # Создаем объект запланированного сообщения
            scheduled_msg = ScheduledMessage(
                message_id=message_id,
                chat_id=chat_id,
                message_type=message_type,
                content=content,
                schedule_type=schedule_type,
                schedule_time=time_obj,
                schedule_days=schedule_days,
                created_at=datetime.now(),
                creator_id=user_id
            )
            
            # Сохраняем в БД
            await self.db.execute('''
            INSERT INTO scheduled_messages 
            (message_id, chat_id, message_type, content, schedule_type, 
             schedule_time, schedule_days, creator_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message_id, chat_id, message_type.value, content, schedule_type,
                schedule_time, json.dumps(schedule_days), user_id
            ))
            
            # Добавляем в активные
            self.scheduled_messages[message_id] = scheduled_msg
            
            # Форматируем ответ
            days_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
            days_str = ", ".join([days_names[day] for day in schedule_days])
            
            success_msg = f"📅 **Сообщение запланировано!**\n\n"
            success_msg += f"🕐 **Время:** {schedule_time}\n"
            success_msg += f"📆 **Тип:** {schedule_type}\n"
            success_msg += f"📋 **Дни:** {days_str}\n"
            success_msg += f"💬 **Контент:** {content[:50]}{'...' if len(content) > 50 else ''}"
            
            return True, success_msg
            
        except Exception as e:
            logger.error(f"❌ Ошибка планирования сообщения: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    async def send_random_message(self, chat_id: int) -> bool:
        """🎲 Отправляет случайное сообщение в чат"""
        
        try:
            # Проверяем настройки чата
            if chat_id not in self.chat_settings or not self.chat_settings[chat_id].enabled:
                return False
            
            settings = self.chat_settings[chat_id]
            
            # Проверяем активное время
            current_hour = datetime.now().hour
            if not (settings.active_hours_start <= current_hour <= settings.active_hours_end):
                return False
            
            # Выбираем тип сообщения
            message_type = random.choice(settings.allowed_types)
            
            # Генерируем контент
            content = await self._generate_content(message_type, chat_id)
            
            if not content:
                return False
            
            # Выбираем шаблон
            templates = self.content_templates.get(message_type, ["{content}"])
            template = random.choice(templates)
            
            # Форматируем сообщение
            chat_name = "друзья"  # Можно получить из настроек чата
            formatted_message = template.format(content=content, chat_name=chat_name)
            
            # Отправляем сообщение
            sent_message = await self.bot.send_message(chat_id, formatted_message, parse_mode="Markdown")
            
            # Обновляем время последнего сообщения
            settings.last_random_message = datetime.now()
            await self._update_chat_settings(settings)
            
            # Логируем отправку
            await self._log_sent_message(chat_id, message_type, content, sent_message.message_id)
            
            logger.info(f"💬 Отправлено случайное сообщение ({message_type.value}) в чат {chat_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки случайного сообщения: {e}")
            return False
    
    async def _generate_content(self, message_type: MessageType, chat_id: int) -> Optional[str]:
        """Генерирует контент для сообщения"""
        
        try:
            if message_type == MessageType.FACT:
                # Получаем факт через entertainment систему или используем встроенный
                if self.entertainment:
                    fact = await self.entertainment.get_random_fact(chat_id, 0)  # 0 = system user
                    # Извлекаем только текст факта без заголовка
                    if fact.startswith("🧠 **Интересный факт**"):
                        lines = fact.split('\n')
                        for line in lines:
                            if line.startswith("💡 "):
                                return line[3:]  # Убираем "💡 "
                
                return self._get_builtin_fact()
            
            elif message_type == MessageType.JOKE:
                # Аналогично для шуток
                if self.entertainment:
                    joke = await self.entertainment.get_random_joke(chat_id, 0)
                    if joke.startswith("😄 **Шутка дня**"):
                        return joke.replace("😄 **Шутка дня**\n\n", "")
                
                return self._get_builtin_joke()
            
            elif message_type == MessageType.MOTIVATION:
                return random.choice(self.motivational_quotes)
            
            elif message_type == MessageType.GREETING:
                return random.choice([
                    "Желаю отличного дня! ☀️",
                    "Пусть день принесет много радости! 🌟",
                    "Начинаем день с позитива! 🚀"
                ])
            
            elif message_type == MessageType.GOODNIGHT:
                return random.choice([
                    "Пусть вам приснятся сладкие сны! 💤",
                    "Отдыхайте хорошо! 🌙",
                    "До встречи завтра! ⭐"
                ])
            
            elif message_type == MessageType.CUSTOM:
                # Получаем пользовательские сообщения
                settings = self.chat_settings.get(chat_id)
                if settings and settings.custom_messages:
                    return random.choice(settings.custom_messages)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации контента: {e}")
            return None
    
    def _get_builtin_fact(self) -> str:
        """Встроенные факты"""
        facts = [
            "Медузы на 95% состоят из воды.",
            "Бананы - это ягоды, а клубника - нет.",
            "Морские выдры держатся за лапы во время сна.",
            "Сердце креветки находится в её голове.",
            "Кошки проводят 70% своей жизни во сне."
        ]
        return random.choice(facts)
    
    def _get_builtin_joke(self) -> str:
        """Встроенные шутки"""
        jokes = [
            "— Доктор, я забываю всё через 5 минут!\n— Это серьёзно. А с каких пор это началось?\n— Что началось?",
            "Программист идёт в душ. Жена кричит:\n— Не забудь помыть голову!\n— Понял, очищу кэш!",
            "— Сколько программистов нужно, чтобы вкрутить лампочку?\n— Ни одного, это аппаратная проблема."
        ]
        return random.choice(jokes)

# ЭКСПОРТ
__all__ = ["RandomMessagesSystem", "MessageType", "ScheduledMessage", "ChatMessageSettings"]
