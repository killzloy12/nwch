#!/usr/bin/env python3
"""
💾 DATABASE SERVICE v3.0 - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
🔥 Исправлены отступы, добавлены таблицы custom_personalities и karma
"""

import asyncio
import logging
import sqlite3
import aiosqlite
from datetime import datetime, timedelta
from typing import Dict, Any
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
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self.connection = await aiosqlite.connect(self.db_path, timeout=30.0)
            
            if self.config.wal_mode:
                await self.connection.execute("PRAGMA journal_mode=WAL")
            
            await self.connection.execute("PRAGMA foreign_keys=ON")
            await self.connection.execute("PRAGMA cache_size=-2000")
            await self.connection.execute("PRAGMA synchronous=NORMAL")
            
            await self._create_tables()
            await self._create_indexes()
            
            logger.info("🚀 База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы данных: {e}")
            raise
    
    async def close(self):
        """🔒 Закрытие соединения"""
        if self.connection:
            await self.connection.close()
            logger.info("🔒 База данных закрыта")
    
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
            # Логи сообщений
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
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # Custom personalities
            """
            CREATE TABLE IF NOT EXISTS custom_personalities (
                id TEXT PRIMARY KEY,
                description TEXT,
                system_prompt TEXT,
                chat_id INTEGER,
                user_id INTEGER,
                created_at TEXT,
                is_active INTEGER DEFAULT 1,
                personality_name TEXT,
                personality_description TEXT,
                is_group_personality INTEGER DEFAULT 0,
                admin_id INTEGER
            )
            """,
            # Karma
            """
            CREATE TABLE IF NOT EXISTS karma (
                user_id INTEGER,
                chat_id INTEGER,
                points INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, chat_id)
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
            "CREATE INDEX IF NOT EXISTS idx_chat_logs_user ON chat_logs(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_chat_logs_chat ON chat_logs(chat_id, timestamp)",
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
    

# =================== ИНИЦИАЛИЗАЦИЯ ===================

async def create_database_service(config) -> DatabaseService:
    """🚀 Создание и инициализация сервиса БД"""
    service = DatabaseService(config)
    await service.initialize()
    return service
