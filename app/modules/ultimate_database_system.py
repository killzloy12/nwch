# Создайте файл app/modules/ultimate_database_system.py

#!/usr/bin/env python3
"""
🗄️ ULTIMATE DATABASE SYSTEM v4.0
Расширенная база данных с 19+ таблицами и 25+ индексами
"""

import logging
import asyncio
import sqlite3
import aiosqlite
import json
import shutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import gzip
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class TableInfo:
    name: str
    columns: int
    rows: int
    size_bytes: int
    last_updated: datetime
    indices_count: int

@dataclass
class DatabaseStats:
    total_tables: int
    total_rows: int
    total_size_mb: float
    largest_table: str
    most_active_table: str
    database_version: str
    last_backup: Optional[datetime]
    performance_score: float

class UltimateDatabaseSystem:
    """🗄️ Ultimate система управления базой данных"""
    
    def __init__(self, db_path: str, config):
        self.db_path = db_path
        self.config = config
        
        # Путь для резервных копий
        self.backup_dir = Path("data/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Путь для логов БД
        self.logs_dir = Path("data/logs")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Версия схемы БД
        self.schema_version = "4.0"
        
        # Статистика производительности
        self.performance_stats = {
            'queries_executed': 0,
            'avg_query_time': 0.0,
            'slow_queries': 0,
            'last_optimization': None
        }
        
        # Активные соединения
        self.active_connections = 0
        self.max_connections = 10
        
        logger.info("🗄️ Ultimate Database System инициализирован")
    
    async def initialize(self):
        """🚀 Инициализация Ultimate Database"""
        
        try:
            # Создаем основные таблицы
            await self._create_core_tables()
            
            # Создаем индексы для производительности
            await self._create_performance_indices()
            
            # Проверяем и обновляем схему
            await self._migrate_schema()
            
            # Запускаем фоновые задачи
            asyncio.create_task(self._database_maintenance_loop())
            asyncio.create_task(self._auto_backup_loop())
            asyncio.create_task(self._performance_monitoring_loop())
            
            logger.info("✅ Ultimate Database полностью инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка инициализации БД: {e}")
            raise
    
    async def _create_core_tables(self):
        """📋 Создает все основные таблицы системы"""
        
        # Подключаемся к БД
        async with aiosqlite.connect(self.db_path) as db:
            # Включаем WAL режим для лучшей производительности
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA synchronous=NORMAL")
            await db.execute("PRAGMA cache_size=10000")
            await db.execute("PRAGMA foreign_keys=ON")
            
            # 1. СИСТЕМНЫЕ ТАБЛИЦЫ
            
            # Версия схемы БД
            await db.execute('''
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY DEFAULT 1,
                version TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                migration_log TEXT
            )
            ''')
            
            # Логи операций с БД
            await db.execute('''
            CREATE TABLE IF NOT EXISTS database_operations_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                table_name TEXT,
                query_hash TEXT,
                execution_time_ms REAL,
                rows_affected INTEGER,
                user_id INTEGER,
                chat_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT
            )
            ''')
            
            # Статистика таблиц
            await db.execute('''
            CREATE TABLE IF NOT EXISTS table_statistics (
                table_name TEXT PRIMARY KEY,
                row_count INTEGER DEFAULT 0,
                last_insert TIMESTAMP,
                last_update TIMESTAMP,
                last_select TIMESTAMP,
                total_operations INTEGER DEFAULT 0,
                avg_query_time_ms REAL DEFAULT 0.0
            )
            ''')
            
            # 2. ПОЛЬЗОВАТЕЛЬСКИЕ ДАННЫЕ (расширенные)
            
            # Расширенные профили пользователей
            await db.execute('''
            CREATE TABLE IF NOT EXISTS extended_user_profiles (
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                
                -- Основная информация
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT,
                is_bot BOOLEAN DEFAULT 0,
                is_premium BOOLEAN DEFAULT 0,
                
                -- Персональные настройки
                timezone TEXT DEFAULT 'UTC',
                notification_settings TEXT,  -- JSON
                privacy_settings TEXT,       -- JSON
                
                -- Статистика активности
                total_messages INTEGER DEFAULT 0,
                commands_used INTEGER DEFAULT 0,
                ai_interactions INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                
                -- Поведенческие данные
                most_active_hours TEXT,      -- JSON array
                favorite_commands TEXT,      -- JSON array
                communication_patterns TEXT, -- JSON
                
                -- Социальные метрики
                friends_list TEXT,           -- JSON array of user_ids
                blocked_users TEXT,          -- JSON array of user_ids
                reputation_score INTEGER DEFAULT 100,
                
                -- Временные метки
                first_interaction TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_profile_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                PRIMARY KEY(user_id, chat_id)
            )
            ''')
            
            # 3. КОНТЕНТ И МЕДИА
            
            # Файлы и медиа контент
            await db.execute('''
            CREATE TABLE IF NOT EXISTS media_files (
                file_id TEXT PRIMARY KEY,
                file_unique_id TEXT UNIQUE,
                file_type TEXT NOT NULL,  -- photo, video, document, etc.
                file_size INTEGER,
                mime_type TEXT,
                file_name TEXT,
                
                -- Метаданные
                width INTEGER,
                height INTEGER,
                duration INTEGER,
                thumbnail TEXT,
                
                -- Контекст использования
                uploaded_by INTEGER,
                chat_id INTEGER,
                message_id INTEGER,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Статистика
                download_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP,
                
                -- Хранение
                local_path TEXT,
                cloud_url TEXT,
                is_cached BOOLEAN DEFAULT 0
            )
            ''')
            
            # Контент созданный пользователями
            await db.execute('''
            CREATE TABLE IF NOT EXISTS user_generated_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id TEXT UNIQUE NOT NULL,
                
                -- Основная информация
                content_type TEXT NOT NULL,  -- meme, sticker_pack, custom_command
                title TEXT NOT NULL,
                description TEXT,
                content_data TEXT NOT NULL,  -- JSON
                
                -- Автор
                creator_id INTEGER NOT NULL,
                creator_name TEXT,
                chat_id INTEGER,
                
                -- Модерация
                status TEXT DEFAULT 'pending',  -- pending, approved, rejected
                moderated_by INTEGER,
                moderation_notes TEXT,
                
                -- Статистика
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                dislikes INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                
                -- Временные метки
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP
            )
            ''')
            
            # 4. ИГРОВЫЕ СИСТЕМЫ (расширенные)
            
            # Достижения пользователей
            await db.execute('''
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                achievement_name TEXT NOT NULL,
                achievement_description TEXT,
                
                -- Прогресс
                progress_current INTEGER DEFAULT 0,
                progress_required INTEGER DEFAULT 1,
                is_completed BOOLEAN DEFAULT 0,
                completion_percentage REAL DEFAULT 0.0,
                
                -- Награды
                xp_reward INTEGER DEFAULT 0,
                badge_emoji TEXT,
                special_permissions TEXT,  -- JSON
                
                -- Временные метки
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                last_progress_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(user_id, chat_id, achievement_id)
            )
            ''')
            
            # Система уровней и опыта
            await db.execute('''
            CREATE TABLE IF NOT EXISTS user_experience (
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                
                -- Опыт и уровень
                total_xp INTEGER DEFAULT 0,
                current_level INTEGER DEFAULT 1,
                xp_to_next_level INTEGER DEFAULT 100,
                
                -- Статистика заработка XP
                xp_from_messages INTEGER DEFAULT 0,
                xp_from_games INTEGER DEFAULT 0,
                xp_from_achievements INTEGER DEFAULT 0,
                xp_from_special INTEGER DEFAULT 0,
                
                -- Награды за уровни
                unlocked_features TEXT,    -- JSON array
                level_rewards_claimed TEXT, -- JSON array
                
                -- История
                level_history TEXT,        -- JSON array of level changes
                xp_history TEXT,          -- JSON array of XP changes
                
                -- Временные метки
                last_xp_gain TIMESTAMP,
                level_up_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                PRIMARY KEY(user_id, chat_id)
            )
            ''')
            
            # 5. АНАЛИТИКА И МОНИТОРИНГ
            
            # Детальная аналитика чатов
            await db.execute('''
            CREATE TABLE IF NOT EXISTS detailed_chat_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                analysis_date DATE NOT NULL,
                
                -- Активность по времени (JSON массивы по 24 элемента)
                hourly_messages TEXT,
                hourly_users TEXT,
                hourly_commands TEXT,
                
                -- Контентная аналитика
                message_types_stats TEXT,    -- JSON
                command_usage_stats TEXT,    -- JSON
                media_usage_stats TEXT,      -- JSON
                emoji_usage_stats TEXT,      -- JSON
                
                -- Социальная аналитика
                top_users TEXT,              -- JSON
                user_interaction_matrix TEXT,-- JSON
                influence_scores TEXT,       -- JSON
                
                -- Языковая аналитика
                language_distribution TEXT,  -- JSON
                sentiment_analysis TEXT,     -- JSON
                topic_analysis TEXT,         -- JSON
                
                -- Производительность бота
                response_times TEXT,         -- JSON
                error_rates TEXT,            -- JSON
                feature_usage TEXT,          -- JSON
                
                UNIQUE(chat_id, analysis_date)
            )
            ''')
            
            # Система мониторинга производительности
            await db.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_type TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                
                -- Контекст
                chat_id INTEGER,
                user_id INTEGER,
                component TEXT,  -- ai, database, network, etc.
                
                -- Дополнительные данные
                metadata TEXT,   -- JSON
                
                -- Временная метка
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 6. СИСТЕМЫ БЕЗОПАСНОСТИ
            
            # Журнал безопасности
            await db.execute('''
            CREATE TABLE IF NOT EXISTS security_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,  -- low, medium, high, critical
                
                -- Контекст события
                user_id INTEGER,
                chat_id INTEGER,
                ip_address TEXT,
                user_agent TEXT,
                
                -- Детали события
                event_description TEXT NOT NULL,
                event_data TEXT,         -- JSON
                
                -- Обработка
                is_resolved BOOLEAN DEFAULT 0,
                resolution_notes TEXT,
                resolved_by INTEGER,
                
                -- Временные метки
                occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP
            )
            ''')
            
            # Антиспам система
            await db.execute('''
            CREATE TABLE IF NOT EXISTS antispam_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                
                -- Паттерны поведения
                message_frequency REAL,
                repetitive_content_score REAL,
                spam_indicators TEXT,      -- JSON
                
                -- Счетчики
                messages_last_minute INTEGER DEFAULT 0,
                identical_messages INTEGER DEFAULT 0,
                warnings_received INTEGER DEFAULT 0,
                
                -- Статус
                is_flagged BOOLEAN DEFAULT 0,
                is_whitelisted BOOLEAN DEFAULT 0,
                confidence_score REAL DEFAULT 0.0,
                
                -- Временные метки
                last_message_time TIMESTAMP,
                first_flag_time TIMESTAMP,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 7. РЕЗЕРВНОЕ КОПИРОВАНИЕ И ВОССТАНОВЛЕНИЕ
            
            # История резервных копий
            await db.execute('''
            CREATE TABLE IF NOT EXISTS backup_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_id TEXT UNIQUE NOT NULL,
                backup_type TEXT NOT NULL,  -- full, incremental, manual
                
                -- Файлы
                backup_path TEXT NOT NULL,
                backup_size INTEGER,
                compression_ratio REAL,
                
                -- Статистика
                tables_backed_up INTEGER,
                rows_backed_up INTEGER,
                backup_duration_ms INTEGER,
                
                -- Статус
                status TEXT DEFAULT 'completed',  -- running, completed, failed
                error_message TEXT,
                
                -- Временные метки
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
            ''')
            
            await db.commit()
            logger.info("✅ Все основные таблицы созданы")
    
    async def _create_performance_indices(self):
        """⚡ Создает индексы для оптимизации производительности"""
        
        async with aiosqlite.connect(self.db_path) as db:
            indices = [
                # 1. Основные индексы пользователей
                "CREATE INDEX IF NOT EXISTS idx_extended_users_last_activity ON extended_user_profiles(last_activity DESC)",
                "CREATE INDEX IF NOT EXISTS idx_extended_users_total_messages ON extended_user_profiles(total_messages DESC)",
                "CREATE INDEX IF NOT EXISTS idx_extended_users_reputation ON extended_user_profiles(reputation_score DESC)",
                "CREATE INDEX IF NOT EXISTS idx_extended_users_chat_activity ON extended_user_profiles(chat_id, last_activity)",
                
                # 2. Медиа файлы
                "CREATE INDEX IF NOT EXISTS idx_media_files_type ON media_files(file_type)",
                "CREATE INDEX IF NOT EXISTS idx_media_files_upload_date ON media_files(upload_date DESC)",
                "CREATE INDEX IF NOT EXISTS idx_media_files_size ON media_files(file_size DESC)",
                "CREATE INDEX IF NOT EXISTS idx_media_files_chat ON media_files(chat_id, upload_date)",
                "CREATE INDEX IF NOT EXISTS idx_media_files_user ON media_files(uploaded_by, upload_date)",
                
                # 3. Пользовательский контент
                "CREATE INDEX IF NOT EXISTS idx_ugc_status ON user_generated_content(status, created_at)",
                "CREATE INDEX IF NOT EXISTS idx_ugc_type ON user_generated_content(content_type, created_at)",
                "CREATE INDEX IF NOT EXISTS idx_ugc_creator ON user_generated_content(creator_id, created_at)",
                "CREATE INDEX IF NOT EXISTS idx_ugc_likes ON user_generated_content(likes DESC)",
                "CREATE INDEX IF NOT EXISTS idx_ugc_views ON user_generated_content(views DESC)",
                
                # 4. Достижения и опыт
                "CREATE INDEX IF NOT EXISTS idx_achievements_user ON user_achievements(user_id, chat_id)",
                "CREATE INDEX IF NOT EXISTS idx_achievements_completed ON user_achievements(is_completed, completed_at)",
                "CREATE INDEX IF NOT EXISTS idx_achievements_progress ON user_achievements(progress_current, progress_required)",
                "CREATE INDEX IF NOT EXISTS idx_experience_level ON user_experience(current_level DESC, total_xp DESC)",
                "CREATE INDEX IF NOT EXISTS idx_experience_xp ON user_experience(total_xp DESC)",
                
                # 5. Аналитика
                "CREATE INDEX IF NOT EXISTS idx_analytics_date ON detailed_chat_analytics(analysis_date DESC)",
                "CREATE INDEX IF NOT EXISTS idx_analytics_chat_date ON detailed_chat_analytics(chat_id, analysis_date)",
                "CREATE INDEX IF NOT EXISTS idx_performance_type ON performance_metrics(metric_type, recorded_at)",
                "CREATE INDEX IF NOT EXISTS idx_performance_component ON performance_metrics(component, recorded_at)",
                
                # 6. Безопасность
                "CREATE INDEX IF NOT EXISTS idx_security_severity ON security_log(severity, occurred_at)",
                "CREATE INDEX IF NOT EXISTS idx_security_user ON security_log(user_id, occurred_at)",
                "CREATE INDEX IF NOT EXISTS idx_security_resolved ON security_log(is_resolved, occurred_at)",
                "CREATE INDEX IF NOT EXISTS idx_antispam_flagged ON antispam_data(is_flagged, last_update)",
                "CREATE INDEX IF NOT EXISTS idx_antispam_confidence ON antispam_data(confidence_score DESC)",
                
                # 7. Системные операции
                "CREATE INDEX IF NOT EXISTS idx_db_operations_type ON database_operations_log(operation_type, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_db_operations_table ON database_operations_log(table_name, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_db_operations_time ON database_operations_log(execution_time_ms DESC)",
                "CREATE INDEX IF NOT EXISTS idx_table_stats_operations ON table_statistics(total_operations DESC)",
                
                # 8. Резервные копии
                "CREATE INDEX IF NOT EXISTS idx_backup_type ON backup_history(backup_type, started_at)",
                "CREATE INDEX IF NOT EXISTS idx_backup_status ON backup_history(status, started_at)",
                
                # 9. Композитные индексы для сложных запросов
                "CREATE INDEX IF NOT EXISTS idx_users_chat_messages ON extended_user_profiles(chat_id, total_messages DESC, last_activity)",
                "CREATE INDEX IF NOT EXISTS idx_ugc_creator_status ON user_generated_content(creator_id, status, created_at)",
                "CREATE INDEX IF NOT EXISTS idx_achievements_user_completed ON user_achievements(user_id, chat_id, is_completed)",
                "CREATE INDEX IF NOT EXISTS idx_security_user_severity ON security_log(user_id, severity, occurred_at)",
                "CREATE INDEX IF NOT EXISTS idx_performance_chat_component ON performance_metrics(chat_id, component, recorded_at)"
            ]
            
            for i, index_query in enumerate(indices, 1):
                try:
                    await db.execute(index_query)
                    logger.debug(f"✅ Индекс {i}/{len(indices)} создан")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка создания индекса {i}: {e}")
            
            await db.commit()
            logger.info(f"⚡ Создано {len(indices)} индексов для производительности")
    
    async def create_automatic_backup(self, backup_type: str = "auto") -> Tuple[bool, str]:
        """💾 Создает автоматическую резервную копию"""
        
        try:
            backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_filename = f"{backup_id}.db.gz"
            backup_path = self.backup_dir / backup_filename
            
            start_time = datetime.now()
            
            # Записываем начало операции резервного копирования
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                INSERT INTO backup_history 
                (backup_id, backup_type, backup_path, status, started_at)
                VALUES (?, ?, ?, ?, ?)
                ''', (backup_id, backup_type, str(backup_path), 'running', start_time))
                await db.commit()
            
            # Создаем сжатую копию
            original_size = os.path.getsize(self.db_path)
            
            with open(self.db_path, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            backup_size = backup_path.stat().st_size
            compression_ratio = backup_size / original_size if original_size > 0 else 0
            
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Получаем статистику таблиц
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = await cursor.fetchall()
                tables_count = len(tables)
                
                # Подсчитываем общее количество строк
                total_rows = 0
                for table_name, in tables:
                    if not table_name.startswith('sqlite_'):
                        try:
                            cursor = await db.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                            count = await cursor.fetchone()
                            total_rows += count[0] if count else 0
                        except:
                            pass
                
                # Обновляем запись о резервной копии
                await db.execute('''
                UPDATE backup_history 
                SET status = ?, backup_size = ?, compression_ratio = ?,
                    tables_backed_up = ?, rows_backed_up = ?, backup_duration_ms = ?,
                    completed_at = ?
                WHERE backup_id = ?
                ''', ('completed', backup_size, compression_ratio, tables_count, 
                      total_rows, duration_ms, end_time, backup_id))
                await db.commit()
            
            # Очищаем старые резервные копии (оставляем последние 10)
            await self._cleanup_old_backups()
            
            success_msg = f"💾 **Резервная копия создана**\n\n"
            success_msg += f"📁 **Файл:** {backup_filename}\n"
            success_msg += f"📊 **Размер:** {backup_size / 1024 / 1024:.1f} MB\n"
            success_msg += f"🗜️ **Сжатие:** {compression_ratio:.2%}\n"
            success_msg += f"📋 **Таблиц:** {tables_count}\n"
            success_msg += f"📄 **Строк:** {total_rows:,}\n"
            success_msg += f"⏱️ **Время:** {duration_ms} мс"
            
            return True, success_msg
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания резервной копии: {e}")
            
            # Отмечаем операцию как неудачную
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute('''
                    UPDATE backup_history 
                    SET status = ?, error_message = ?, completed_at = ?
                    WHERE backup_id = ?
                    ''', ('failed', str(e), datetime.now(), backup_id))
                    await db.commit()
            except:
                pass
            
            return False, f"❌ Ошибка резервного копирования: {str(e)}"
    
    async def get_database_statistics(self) -> DatabaseStats:
        """📊 Получает полную статистику базы данных"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Получаем список всех таблиц
                cursor = await db.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                ''')
                tables = await cursor.fetchall()
                
                total_rows = 0
                table_info = []
                largest_table = ""
                max_rows = 0
                
                # Анализируем каждую таблицу
                for table_name, in tables:
                    try:
                        # Количество строк
                        cursor = await db.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                        row_count = (await cursor.fetchone())[0]
                        total_rows += row_count
                        
                        if row_count > max_rows:
                            max_rows = row_count
                            largest_table = table_name
                        
                        # Информация о колонках
                        cursor = await db.execute(f"PRAGMA table_info([{table_name}])")
                        columns = await cursor.fetchall()
                        
                        # Информация об индексах
                        cursor = await db.execute(f"PRAGMA index_list([{table_name}])")
                        indices = await cursor.fetchall()
                        
                        table_info.append(TableInfo(
                            name=table_name,
                            columns=len(columns),
                            rows=row_count,
                            size_bytes=0,  # SQLite не предоставляет размер таблицы напрямую
                            last_updated=datetime.now(),
                            indices_count=len(indices)
                        ))
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка анализа таблицы {table_name}: {e}")
                
                # Размер файла базы данных
                db_size_bytes = os.path.getsize(self.db_path)
                db_size_mb = db_size_bytes / 1024 / 1024
                
                # Самая активная таблица (из логов операций)
                cursor = await db.execute('''
                SELECT table_name, COUNT(*) as operations 
                FROM database_operations_log 
                WHERE timestamp >= datetime('now', '-24 hours')
                GROUP BY table_name 
                ORDER BY operations DESC 
                LIMIT 1
                ''')
                most_active = await cursor.fetchone()
                most_active_table = most_active[0] if most_active else "N/A"
                
                # Последняя резервная копия
                cursor = await db.execute('''
                SELECT completed_at FROM backup_history 
                WHERE status = 'completed' 
                ORDER BY completed_at DESC 
                LIMIT 1
                ''')
                last_backup_row = await cursor.fetchone()
                last_backup = datetime.fromisoformat(last_backup_row[0]) if last_backup_row else None
                
                # Оценка производительности (упрощенная)
                cursor = await db.execute('''
                SELECT AVG(execution_time_ms) FROM database_operations_log 
                WHERE timestamp >= datetime('now', '-1 hour')
                ''')
                avg_time = await cursor.fetchone()
                avg_query_time = avg_time[0] if avg_time and avg_time[0] else 0.0
                
                # Простая оценка производительности (чем меньше время, тем лучше)
                if avg_query_time == 0:
                    performance_score = 100.0
                elif avg_query_time < 10:
                    performance_score = 95.0
                elif avg_query_time < 50:
                    performance_score = 80.0
                elif avg_query_time < 100:
                    performance_score = 60.0
                else:
                    performance_score = 40.0
                
                return DatabaseStats(
                    total_tables=len(tables),
                    total_rows=total_rows,
                    total_size_mb=db_size_mb,
                    largest_table=largest_table,
                    most_active_table=most_active_table,
                    database_version=self.schema_version,
                    last_backup=last_backup,
                    performance_score=performance_score
                )
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики БД: {e}")
            
            # Возвращаем базовую статистику в случае ошибки
            return DatabaseStats(
                total_tables=0,
                total_rows=0,
                total_size_mb=0.0,
                largest_table="N/A",
                most_active_table="N/A", 
                database_version=self.schema_version,
                last_backup=None,
                performance_score=0.0
            )
    
    async def optimize_database(self) -> Tuple[bool, str]:
        """🔧 Оптимизирует базу данных"""
        
        try:
            start_time = datetime.now()
            
            async with aiosqlite.connect(self.db_path) as db:
                # 1. VACUUM - перестроение БД для освобождения места
                logger.info("🔄 Выполняется VACUUM...")
                await db.execute("VACUUM")
                
                # 2. ANALYZE - обновление статистики для оптимизатора запросов
                logger.info("📊 Выполняется ANALYZE...")
                await db.execute("ANALYZE")
                
                # 3. Перестроение индексов
                logger.info("⚡ Перестроение индексов...")
                cursor = await db.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
                ''')
                indices = await cursor.fetchall()
                
                for index_name, in indices:
                    try:
                        await db.execute(f"REINDEX [{index_name}]")
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка перестроения индекса {index_name}: {e}")
                
                await db.commit()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Обновляем статистику производительности
            self.performance_stats['last_optimization'] = end_time
            
            # Логируем операцию оптимизации
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                INSERT INTO database_operations_log 
                (operation_type, execution_time_ms, rows_affected, timestamp)
                VALUES (?, ?, ?, ?)
                ''', ('OPTIMIZE', duration * 1000, 0, end_time))
                await db.commit()
            
            success_msg = f"🔧 **База данных оптимизирована**\n\n"
            success_msg += f"⏱️ **Время выполнения:** {duration:.1f} сек\n"
            success_msg += f"⚡ **Индексов перестроено:** {len(indices)}\n"
            success_msg += f"📊 **Статистика обновлена:** ✅\n"
            success_msg += f"🗜️ **VACUUM выполнен:** ✅"
            
            return True, success_msg
            
        except Exception as e:
            logger.error(f"❌ Ошибка оптимизации БД: {e}")
            return False, f"❌ Ошибка оптимизации: {str(e)}"
    
    async def _database_maintenance_loop(self):
        """🔧 Фоновое обслуживание базы данных"""
        
        while True:
            try:
                # Каждые 6 часов выполняем обслуживание
                await asyncio.sleep(6 * 3600)
                
                logger.info("🔧 Начинается автоматическое обслуживание БД...")
                
                # 1. Очистка старых логов (старше 30 дней)
                async with aiosqlite.connect(self.db_path) as db:
                    cutoff_date = datetime.now() - timedelta(days=30)
                    
                    await db.execute('''
                    DELETE FROM database_operations_log 
                    WHERE timestamp < ?
                    ''', (cutoff_date,))
                    
                    await db.execute('''
                    DELETE FROM performance_metrics 
                    WHERE recorded_at < ?
                    ''', (cutoff_date,))
                    
                    await db.commit()
                
                # 2. Обновление статистики таблиц
                await self._update_table_statistics()
                
                # 3. Раз в неделю выполняем полную оптимизацию
                if datetime.now().weekday() == 0:  # Понедельник
                    await self.optimize_database()
                
                logger.info("✅ Автоматическое обслуживание БД завершено")
                
            except Exception as e:
                logger.error(f"❌ Ошибка автоматического обслуживания БД: {e}")
    
    async def _auto_backup_loop(self):
        """💾 Автоматическое резервное копирование"""
        
        while True:
            try:
                # Каждые 24 часа создаем резервную копию
                await asyncio.sleep(24 * 3600)
                
                logger.info("💾 Создание автоматической резервной копии...")
                
                success, message = await self.create_automatic_backup("daily")
                
                if success:
                    logger.info("✅ Автоматическая резервная копия создана")
                else:
                    logger.error(f"❌ Ошибка автоматического резервного копирования: {message}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка цикла автоматического резервного копирования: {e}")

# ЭКСПОРТ
__all__ = ["UltimateDatabaseSystem", "DatabaseStats", "TableInfo"]
