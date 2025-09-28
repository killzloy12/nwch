#!/usr/bin/env python3
"""
💾 DATABASE SERVICE v3.0 - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
🔥 ИСПРАВЛЕНО: все отступы, методы логирования, таблицы

ФИНАЛЬНЫЕ ИСПРАВЛЕНИЯ:
• Исправлены все отступы
• Добавлено логирование сообщений
• Добавлена статистика пользователей
• Исправлены все таблицы
• Убраны ошибки синтаксиса
"""

import asyncio
import logging
import sqlite3
import aiosqlite
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class DatabaseService:
    """💾 Сервис работы с базой данных"""
    
    def __init__(self, config):
        self.config = config
        self.db_path = config.path
        self.connection = None
        logger.info("💾 DatabaseService инициализирован")
    
    async def initialize(self):
        """🚀 Инициализация базы данных"""
        try:
            # Создаем директорию если не существует
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Подключение к базе
            self.connection = await aiosqlite.connect(
                self.db_path,
                timeout=30.0
            )
            
            # Включаем WAL режим если настроено
            if self.config.wal_mode:
                await self.connection.execute("PRAGMA journal_mode=WAL")
            
            # Настройки производительности
            await self.connection.execute("PRAGMA foreign_keys=ON")
            await self.connection.execute("PRAGMA cache_size=-2000")
            await self.connection.execute("PRAGMA synchronous=NORMAL")
            
            # Создаем таблицы
            await self._create_tables()
            await self._create_indexes()
            
            logger.info("🚀 База данных инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы данных: {e}")
            raise
    
    async def close(self):
        """🔒 Закрытие соединения"""
        try:
            if self.connection:
                await self.connection.close()
                logger.info("🔒 База данных закрыта")
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия БД: {e}")
    
    async def _create_tables(self):
        """📋 Создание всех таблиц"""
        tables = [
            # Пользователи
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                full_name TEXT,
                language_code TEXT,
                is_premium BOOLEAN DEFAULT FALSE,
                is_bot BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Чаты
            """
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT,
                username TEXT,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # ЛОГИРОВАНИЕ СООБЩЕНИЙ (НОВАЯ ТАБЛИЦА)
            """
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                text TEXT,
                message_type TEXT DEFAULT 'text',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Сообщения
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                text TEXT,
                message_type TEXT DEFAULT 'text',
                reply_to_message_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (chat_id) REFERENCES chats (id)
            )
            """,
            
            # Действия пользователей
            """
            CREATE TABLE IF NOT EXISTS user_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (chat_id) REFERENCES chats (id)
            )
            """,
            
            # Системные настройки
            """
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_by INTEGER,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # AI взаимодействия
            """
            CREATE TABLE IF NOT EXISTS ai_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER,
                prompt TEXT NOT NULL,
                response TEXT,
                model_used TEXT,
                tokens_used INTEGER,
                response_time REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (chat_id) REFERENCES chats (id)
            )
            """,
            
            # Память диалогов
            """
            CREATE TABLE IF NOT EXISTS memory_contexts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER,
                context_key TEXT NOT NULL,
                context_value TEXT NOT NULL,
                expires_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (chat_id) REFERENCES chats (id)
            )
            """,
            
            # Триггеры
            """
            CREATE TABLE IF NOT EXISTS triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER NOT NULL,
                trigger_text TEXT NOT NULL,
                response_text TEXT NOT NULL,
                is_regex BOOLEAN DEFAULT FALSE,
                is_global BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                usage_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (chat_id) REFERENCES chats (id)
            )
            """,
            
            # Модерация - баны
            """
            CREATE TABLE IF NOT EXISTS bans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER,
                admin_id INTEGER NOT NULL,
                reason TEXT,
                ban_type TEXT DEFAULT 'permanent',
                expires_at DATETIME,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (chat_id) REFERENCES chats (id),
                FOREIGN KEY (admin_id) REFERENCES users (id)
            )
            """,
            
            # Модерация - предупреждения
            """
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                admin_id INTEGER NOT NULL,
                reason TEXT,
                severity_level INTEGER DEFAULT 1,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (chat_id) REFERENCES chats (id),
                FOREIGN KEY (admin_id) REFERENCES users (id)
            )
            """,
            
            # Аналитика поведения
            """
            CREATE TABLE IF NOT EXISTS behavior_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        ]
        
        for table_sql in tables:
            try:
                await self.connection.execute(table_sql)
            except Exception as e:
                logger.error(f"❌ Ошибка создания таблицы: {e}")
        
        await self.connection.commit()
        logger.info("📋 Все таблицы созданы")
    
    async def _create_indexes(self):
        """🚀 Создание индексов"""
        indexes = [
            # Индексы для логирования
            "CREATE INDEX IF NOT EXISTS idx_chat_logs_user ON chat_logs(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_chat_logs_chat ON chat_logs(chat_id, timestamp)",
            
            # Основные индексы
            "CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_user_actions_user ON user_actions(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_ai_interactions_user ON ai_interactions(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_memory_contexts_user ON memory_contexts(user_id, chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_triggers_active ON triggers(is_active, chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_bans_active ON bans(is_active, user_id, chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_warnings_active ON warnings(is_active, user_id, chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_behavior_user ON behavior_patterns(user_id, pattern_type)"
        ]
        
        for index_sql in indexes:
            try:
                await self.connection.execute(index_sql)
            except Exception as e:
                logger.error(f"❌ Ошибка создания индекса: {e}")
        
        await self.connection.commit()
        logger.info("🚀 Индексы созданы")
    
    # =================== ОСНОВНЫЕ CRUD ОПЕРАЦИИ ===================
    
    async def execute(self, query: str, params: tuple = None):
        """⚡ Выполнение запроса"""
        try:
            if params:
                await self.connection.execute(query, params)
            else:
                await self.connection.execute(query)
            await self.connection.commit()
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения запроса: {e}")
            raise
    
    async def fetch_one(self, query: str, params: tuple = None):
        """📝 Получение одной записи"""
        try:
            if params:
                cursor = await self.connection.execute(query, params)
            else:
                cursor = await self.connection.execute(query)
            
            row = await cursor.fetchone()
            if row:
                # Преобразуем в словарь
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения записи: {e}")
            return None
    
    async def fetch_all(self, query: str, params: tuple = None):
        """📋 Получение всех записей"""
        try:
            if params:
                cursor = await self.connection.execute(query, params)
            else:
                cursor = await self.connection.execute(query)
            
            rows = await cursor.fetchall()
            if rows:
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            return []
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения записей: {e}")
            return []
    
    # =================== ПОЛЬЗОВАТЕЛИ ===================
    
    async def save_user(self, user_data: Dict[str, Any]) -> bool:
        """👤 Сохранение пользователя"""
        try:
            await self.connection.execute("""
                INSERT OR REPLACE INTO users 
                (id, username, first_name, last_name, full_name, language_code, is_premium, is_bot, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_data['id'],
                user_data.get('username'),
                user_data.get('first_name'),
                user_data.get('last_name'),
                user_data.get('full_name'),
                user_data.get('language_code'),
                user_data.get('is_premium', False),
                user_data.get('is_bot', False),
                datetime.now()
            ))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения пользователя: {e}")
            return False
    
    async def save_chat(self, chat_data: Dict[str, Any]) -> bool:
        """💬 Сохранение чата"""
        try:
            await self.connection.execute("""
                INSERT OR REPLACE INTO chats 
                (id, type, title, username, description, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                chat_data['id'],
                chat_data['type'],
                chat_data.get('title'),
                chat_data.get('username'),
                chat_data.get('description'),
                datetime.now()
            ))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения чата: {e}")
            return False
    
    # =================== ЛОГИРОВАНИЕ СООБЩЕНИЙ (НОВОЕ) ===================
    
    async def log_message(self, chat_id: int, user_id: int, username: str, full_name: str, 
                          text: str, message_type: str = 'text', timestamp=None):
        """📝 Логирование сообщения пользователя"""
        if timestamp is None:
            timestamp = datetime.now()
        
        try:
            await self.connection.execute("""
                INSERT INTO chat_logs (chat_id, user_id, username, full_name, text, message_type, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (chat_id, user_id, username, full_name, text, message_type, timestamp))
            
            await self.connection.commit()
            
        except Exception as e:
            logger.error(f"❌ Ошибка логирования сообщения: {e}")
    
    async def get_user_stats(self, user_id: int) -> dict:
        """📊 Получение статистики пользователя"""
        try:
            result = await self.fetch_one("""
                SELECT 
                    COUNT(*) as total_messages,
                    MIN(timestamp) as first_seen,
                    MAX(timestamp) as last_seen
                FROM chat_logs 
                WHERE user_id = ?
            """, (user_id,))
            
            if result:
                return {
                    'total_messages': result['total_messages'],
                    'first_seen': result['first_seen'],
                    'last_seen': result['last_seen']
                }
            else:
                return {'total_messages': 0, 'first_seen': 'неизвестно', 'last_seen': 'никогда'}
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {'total_messages': 0, 'first_seen': 'ошибка', 'last_seen': 'ошибка'}
    
    async def export_recent_logs(self, limit: int = 1000) -> list:
        """📤 Экспорт последних логов"""
        try:
            results = await self.fetch_all("""
                SELECT chat_id, user_id, username, full_name, text, message_type, timestamp
                FROM chat_logs 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            return results if results else []
            
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта логов: {e}")
            return []
    
    # =================== AI ВЗАИМОДЕЙСТВИЯ ===================
    
    async def save_ai_interaction(self, interaction_data: Dict[str, Any]) -> bool:
        """🧠 Сохранение AI взаимодействия"""
        try:
            await self.connection.execute("""
                INSERT INTO ai_interactions 
                (user_id, chat_id, prompt, response, model_used, tokens_used, response_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                interaction_data['user_id'],
                interaction_data.get('chat_id'),
                interaction_data['prompt'],
                interaction_data['response'],
                interaction_data.get('model_used'),
                interaction_data.get('tokens_used'),
                interaction_data.get('response_time')
            ))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения AI взаимодействия: {e}")
            return False
    
    # =================== ПАМЯТЬ КОНТЕКСТОВ ===================
    
    async def save_memory_context(self, user_id: int, chat_id: int, context_key: str, 
                                  context_value: str, expires_at: datetime = None) -> bool:
        """🧠 Сохранение контекста в памяти"""
        try:
            await self.connection.execute("""
                INSERT OR REPLACE INTO memory_contexts 
                (user_id, chat_id, context_key, context_value, expires_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, chat_id, context_key, context_value, expires_at, datetime.now()))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения контекста: {e}")
            return False
    
    async def get_memory_context(self, user_id: int, chat_id: int, context_key: str) -> str:
        """🧠 Получение контекста из памяти"""
        try:
            result = await self.fetch_one("""
                SELECT context_value FROM memory_contexts 
                WHERE user_id = ? AND chat_id = ? AND context_key = ?
                AND (expires_at IS NULL OR expires_at > ?)
            """, (user_id, chat_id, context_key, datetime.now()))
            
            return result['context_value'] if result else None
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения контекста: {e}")
            return None
    
    # =================== АНАЛИТИКА ===================
    
    async def track_user_action(self, user_id: int, chat_id: int, action: str, details: Dict = None):
        """📊 Трекинг действия пользователя"""
        try:
            await self.connection.execute("""
                INSERT INTO user_actions (user_id, chat_id, action, details)
                VALUES (?, ?, ?, ?)
            """, (user_id, chat_id, action, json.dumps(details) if details else None))
            
            await self.connection.commit()
            
        except Exception as e:
            logger.error(f"❌ Ошибка трекинга действия: {e}")
    
    # =================== СИСТЕМНЫЕ НАСТРОЙКИ ===================
    
    async def get_setting(self, key: str) -> str:
        """⚙️ Получение системной настройки"""
        try:
            result = await self.fetch_one("SELECT value FROM system_settings WHERE key = ?", (key,))
            return result['value'] if result else None
        except Exception as e:
            logger.error(f"❌ Ошибка получения настройки {key}: {e}")
            return None
    
    async def set_setting(self, key: str, value: str, updated_by: int = None) -> bool:
        """⚙️ Установка системной настройки"""
        try:
            await self.connection.execute("""
                INSERT OR REPLACE INTO system_settings (key, value, updated_by, updated_at)
                VALUES (?, ?, ?, ?)
            """, (key, value, updated_by, datetime.now()))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка установки настройки {key}: {e}")
            return False
    
    # =================== ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ ===================
    
    async def cleanup_expired_data(self):
        """🧹 Очистка устаревших данных"""
        try:
            # Удаляем устаревшие контексты
            await self.connection.execute("""
                DELETE FROM memory_contexts 
                WHERE expires_at IS NOT NULL AND expires_at < ?
            """, (datetime.now(),))
            
            # Удаляем старые логи (старше 30 дней)
            await self.connection.execute("""
                DELETE FROM chat_logs 
                WHERE timestamp < ?
            """, (datetime.now() - timedelta(days=30),))
            
            await self.connection.commit()
            logger.info("🧹 Очистка устаревших данных завершена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки данных: {e}")
    
    async def get_database_stats(self) -> Dict[str, int]:
        """📊 Статистика базы данных"""
        try:
            stats = {}
            
            tables = ['users', 'chats', 'chat_logs', 'messages', 'ai_interactions', 
                     'memory_contexts', 'triggers', 'user_actions']
            
            for table in tables:
                result = await self.fetch_one(f"SELECT COUNT(*) as count FROM {table}")
                stats[table] = result['count'] if result else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики БД: {e}")
            return {}


# =================== ИНИЦИАЛИЗАЦИЯ ===================

async def create_database_service(config) -> DatabaseService:
    """🚀 Создание и инициализация сервиса БД"""
    service = DatabaseService(config)
    await service.initialize()

#!/usr/bin/env python3
"""
💾 DATABASE SERVICE v3.0 - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
🔥 ИСПРАВЛЕНО: все отступы, методы логирования, таблицы

ФИНАЛЬНЫЕ ИСПРАВЛЕНИЯ:
• Исправлены все отступы
• Добавлено логирование сообщений
• Добавлена статистика пользователей
• Исправлены все таблицы
• Убраны ошибки синтаксиса
"""

import asyncio
import logging
import sqlite3
import aiosqlite
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class DatabaseService:
    """💾 Сервис работы с базой данных"""
    
    def __init__(self, config):
        self.config = config
        self.db_path = config.path
        self.connection = None
        logger.info("💾 DatabaseService инициализирован")
    
    async def initialize(self):
        """🚀 Инициализация базы данных"""
        try:
            # Создаем директорию если не существует
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Подключение к базе
            self.connection = await aiosqlite.connect(
                self.db_path,
                timeout=30.0
            )
            
            # Включаем WAL режим если настроено
            if self.config.wal_mode:
                await self.connection.execute("PRAGMA journal_mode=WAL")
            
            # Настройки производительности
            await self.connection.execute("PRAGMA foreign_keys=ON")
            await self.connection.execute("PRAGMA cache_size=-2000")
            await self.connection.execute("PRAGMA synchronous=NORMAL")
            
            # Создаем таблицы
            await self._create_tables()
            await self._create_indexes()
            
            logger.info("🚀 База данных инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы данных: {e}")
            raise
    
    async def close(self):
        """🔒 Закрытие соединения"""
        try:
            if self.connection:
                await self.connection.close()
                logger.info("🔒 База данных закрыта")
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия БД: {e}")
    
    async def _create_tables(self):
        """📋 Создание всех таблиц"""
        tables = [
            # Пользователи
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                full_name TEXT,
                language_code TEXT,
                is_premium BOOLEAN DEFAULT FALSE,
                is_bot BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Чаты
            """
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT,
                username TEXT,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # ЛОГИРОВАНИЕ СООБЩЕНИЙ (НОВАЯ ТАБЛИЦА)
            """
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                text TEXT,
                message_type TEXT DEFAULT 'text',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Сообщения
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                text TEXT,
                message_type TEXT DEFAULT 'text',
                reply_to_message_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (chat_id) REFERENCES chats (id)
            )
            """,
            
            # Действия пользователей
            """
            CREATE TABLE IF NOT EXISTS user_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (chat_id) REFERENCES chats (id)
            )
            """,
            
            # Системные настройки
            """
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_by INTEGER,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # AI взаимодействия
            """
            CREATE TABLE IF NOT EXISTS ai_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER,
                prompt TEXT NOT NULL,
                response TEXT,
                model_used TEXT,
                tokens_used INTEGER,
                response_time REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (chat_id) REFERENCES chats (id)
            )
            """,
            
            # Память диалогов
            """
            CREATE TABLE IF NOT EXISTS memory_contexts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER,
                context_key TEXT NOT NULL,
                context_value TEXT NOT NULL,
                expires_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (chat_id) REFERENCES chats (id)
            )
            """,
            
            # Триггеры
            """
            CREATE TABLE IF NOT EXISTS triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER NOT NULL,
                trigger_text TEXT NOT NULL,
                response_text TEXT NOT NULL,
                is_regex BOOLEAN DEFAULT FALSE,
                is_global BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                usage_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (chat_id) REFERENCES chats (id)
            )
            """,
            
            # Модерация - баны
            """
            CREATE TABLE IF NOT EXISTS bans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER,
                admin_id INTEGER NOT NULL,
                reason TEXT,
                ban_type TEXT DEFAULT 'permanent',
                expires_at DATETIME,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (chat_id) REFERENCES chats (id),
                FOREIGN KEY (admin_id) REFERENCES users (id)
            )
            """,
            
            # Модерация - предупреждения
            """
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                admin_id INTEGER NOT NULL,
                reason TEXT,
                severity_level INTEGER DEFAULT 1,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (chat_id) REFERENCES chats (id),
                FOREIGN KEY (admin_id) REFERENCES users (id)
            )
            """,
            
            # Аналитика поведения
            """
            CREATE TABLE IF NOT EXISTS behavior_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        ]
        
        for table_sql in tables:
            try:
                await self.connection.execute(table_sql)
            except Exception as e:
                logger.error(f"❌ Ошибка создания таблицы: {e}")
        
        await self.connection.commit()
        logger.info("📋 Все таблицы созданы")
    
    async def _create_indexes(self):
        """🚀 Создание индексов"""
        indexes = [
            # Индексы для логирования
            "CREATE INDEX IF NOT EXISTS idx_chat_logs_user ON chat_logs(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_chat_logs_chat ON chat_logs(chat_id, timestamp)",
            
            # Основные индексы
            "CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_user_actions_user ON user_actions(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_ai_interactions_user ON ai_interactions(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_memory_contexts_user ON memory_contexts(user_id, chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_triggers_active ON triggers(is_active, chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_bans_active ON bans(is_active, user_id, chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_warnings_active ON warnings(is_active, user_id, chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_behavior_user ON behavior_patterns(user_id, pattern_type)"
        ]
        
        for index_sql in indexes:
            try:
                await self.connection.execute(index_sql)
            except Exception as e:
                logger.error(f"❌ Ошибка создания индекса: {e}")
        
        await self.connection.commit()
        logger.info("🚀 Индексы созданы")
    
    # =================== ОСНОВНЫЕ CRUD ОПЕРАЦИИ ===================
    
    async def execute(self, query: str, params: tuple = None):
        """⚡ Выполнение запроса"""
        try:
            if params:
                await self.connection.execute(query, params)
            else:
                await self.connection.execute(query)
            await self.connection.commit()
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения запроса: {e}")
            raise
    
    async def fetch_one(self, query: str, params: tuple = None):
        """📝 Получение одной записи"""
        try:
            if params:
                cursor = await self.connection.execute(query, params)
            else:
                cursor = await self.connection.execute(query)
            
            row = await cursor.fetchone()
            if row:
                # Преобразуем в словарь
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения записи: {e}")
            return None
    
    async def fetch_all(self, query: str, params: tuple = None):
        """📋 Получение всех записей"""
        try:
            if params:
                cursor = await self.connection.execute(query, params)
            else:
                cursor = await self.connection.execute(query)
            
            rows = await cursor.fetchall()
            if rows:
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            return []
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения записей: {e}")
            return []
    
    # =================== ПОЛЬЗОВАТЕЛИ ===================
    
    async def save_user(self, user_data: Dict[str, Any]) -> bool:
        """👤 Сохранение пользователя"""
        try:
            await self.connection.execute("""
                INSERT OR REPLACE INTO users 
                (id, username, first_name, last_name, full_name, language_code, is_premium, is_bot, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_data['id'],
                user_data.get('username'),
                user_data.get('first_name'),
                user_data.get('last_name'),
                user_data.get('full_name'),
                user_data.get('language_code'),
                user_data.get('is_premium', False),
                user_data.get('is_bot', False),
                datetime.now()
            ))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения пользователя: {e}")
            return False
    
    async def save_chat(self, chat_data: Dict[str, Any]) -> bool:
        """💬 Сохранение чата"""
        try:
            await self.connection.execute("""
                INSERT OR REPLACE INTO chats 
                (id, type, title, username, description, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                chat_data['id'],
                chat_data['type'],
                chat_data.get('title'),
                chat_data.get('username'),
                chat_data.get('description'),
                datetime.now()
            ))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения чата: {e}")
            return False
    
    # =================== ЛОГИРОВАНИЕ СООБЩЕНИЙ (НОВОЕ) ===================
    
    async def log_message(self, chat_id: int, user_id: int, username: str, full_name: str, 
                          text: str, message_type: str = 'text', timestamp=None):
        """📝 Логирование сообщения пользователя"""
        if timestamp is None:
            timestamp = datetime.now()
        
        try:
            await self.connection.execute("""
                INSERT INTO chat_logs (chat_id, user_id, username, full_name, text, message_type, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (chat_id, user_id, username, full_name, text, message_type, timestamp))
            
            await self.connection.commit()
            
        except Exception as e:
            logger.error(f"❌ Ошибка логирования сообщения: {e}")
    
    async def get_user_stats(self, user_id: int) -> dict:
        """📊 Получение статистики пользователя"""
        try:
            result = await self.fetch_one("""
                SELECT 
                    COUNT(*) as total_messages,
                    MIN(timestamp) as first_seen,
                    MAX(timestamp) as last_seen
                FROM chat_logs 
                WHERE user_id = ?
            """, (user_id,))
            
            if result:
                return {
                    'total_messages': result['total_messages'],
                    'first_seen': result['first_seen'],
                    'last_seen': result['last_seen']
                }
            else:
                return {'total_messages': 0, 'first_seen': 'неизвестно', 'last_seen': 'никогда'}
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {'total_messages': 0, 'first_seen': 'ошибка', 'last_seen': 'ошибка'}
    
    async def export_recent_logs(self, limit: int = 1000) -> list:
        """📤 Экспорт последних логов"""
        try:
            results = await self.fetch_all("""
                SELECT chat_id, user_id, username, full_name, text, message_type, timestamp
                FROM chat_logs 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            return results if results else []
            
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта логов: {e}")
            return []
    
    # =================== AI ВЗАИМОДЕЙСТВИЯ ===================
    
    async def save_ai_interaction(self, interaction_data: Dict[str, Any]) -> bool:
        """🧠 Сохранение AI взаимодействия"""
        try:
            await self.connection.execute("""
                INSERT INTO ai_interactions 
                (user_id, chat_id, prompt, response, model_used, tokens_used, response_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                interaction_data['user_id'],
                interaction_data.get('chat_id'),
                interaction_data['prompt'],
                interaction_data['response'],
                interaction_data.get('model_used'),
                interaction_data.get('tokens_used'),
                interaction_data.get('response_time')
            ))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения AI взаимодействия: {e}")
            return False
    
    # =================== ПАМЯТЬ КОНТЕКСТОВ ===================
    
    async def save_memory_context(self, user_id: int, chat_id: int, context_key: str, 
                                  context_value: str, expires_at: datetime = None) -> bool:
        """🧠 Сохранение контекста в памяти"""
        try:
            await self.connection.execute("""
                INSERT OR REPLACE INTO memory_contexts 
                (user_id, chat_id, context_key, context_value, expires_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, chat_id, context_key, context_value, expires_at, datetime.now()))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения контекста: {e}")
            return False
    
    async def get_memory_context(self, user_id: int, chat_id: int, context_key: str) -> str:
        """🧠 Получение контекста из памяти"""
        try:
            result = await self.fetch_one("""
                SELECT context_value FROM memory_contexts 
                WHERE user_id = ? AND chat_id = ? AND context_key = ?
                AND (expires_at IS NULL OR expires_at > ?)
            """, (user_id, chat_id, context_key, datetime.now()))
            
            return result['context_value'] if result else None
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения контекста: {e}")
            return None
    
    # =================== АНАЛИТИКА ===================
    
    async def track_user_action(self, user_id: int, chat_id: int, action: str, details: Dict = None):
        """📊 Трекинг действия пользователя"""
        try:
            await self.connection.execute("""
                INSERT INTO user_actions (user_id, chat_id, action, details)
                VALUES (?, ?, ?, ?)
            """, (user_id, chat_id, action, json.dumps(details) if details else None))
            
            await self.connection.commit()
            
        except Exception as e:
            logger.error(f"❌ Ошибка трекинга действия: {e}")
    
    # =================== СИСТЕМНЫЕ НАСТРОЙКИ ===================
    
    async def get_setting(self, key: str) -> str:
        """⚙️ Получение системной настройки"""
        try:
            result = await self.fetch_one("SELECT value FROM system_settings WHERE key = ?", (key,))
            return result['value'] if result else None
        except Exception as e:
            logger.error(f"❌ Ошибка получения настройки {key}: {e}")
            return None
    
    async def set_setting(self, key: str, value: str, updated_by: int = None) -> bool:
        """⚙️ Установка системной настройки"""
        try:
            await self.connection.execute("""
                INSERT OR REPLACE INTO system_settings (key, value, updated_by, updated_at)
                VALUES (?, ?, ?, ?)
            """, (key, value, updated_by, datetime.now()))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка установки настройки {key}: {e}")
            return False
    
    # =================== ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ ===================
    
    async def cleanup_expired_data(self):
        """🧹 Очистка устаревших данных"""
        try:
            # Удаляем устаревшие контексты
            await self.connection.execute("""
                DELETE FROM memory_contexts 
                WHERE expires_at IS NOT NULL AND expires_at < ?
            """, (datetime.now(),))
            
            # Удаляем старые логи (старше 30 дней)
            await self.connection.execute("""
                DELETE FROM chat_logs 
                WHERE timestamp < ?
            """, (datetime.now() - timedelta(days=30),))
            
            await self.connection.commit()
            logger.info("🧹 Очистка устаревших данных завершена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки данных: {e}")
    
    async def get_database_stats(self) -> Dict[str, int]:
        """📊 Статистика базы данных"""
        try:
            stats = {}
            
            tables = ['users', 'chats', 'chat_logs', 'messages', 'ai_interactions', 
                     'memory_contexts', 'triggers', 'user_actions']
            
            for table in tables:
                result = await self.fetch_one(f"SELECT COUNT(*) as count FROM {table}")
                stats[table] = result['count'] if result else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики БД: {e}")
            return {}


# =================== ИНИЦИАЛИЗАЦИЯ ===================

async def create_database_service(config) -> DatabaseService:
    """🚀 Создание и инициализация сервиса БД"""
    service = DatabaseService(config)
    await service.initialize()
    return service