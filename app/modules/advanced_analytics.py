# Создайте файл app/modules/advanced_analytics.py

#!/usr/bin/env python3
"""
📊 ADVANCED ANALYTICS SYSTEM v4.0
Полная система аналитики пользователей и чатов
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import calendar

logger = logging.getLogger(__name__)

@dataclass
class UserAnalytics:
    user_id: int
    chat_id: int
    username: Optional[str]
    first_name: Optional[str]
    
    # Статистика сообщений
    total_messages: int = 0
    text_messages: int = 0
    media_messages: int = 0
    command_usage: int = 0
    
    # Временная активность
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    most_active_hour: Optional[int] = None
    most_active_day: Optional[str] = None
    
    # Поведенческие метрики
    avg_message_length: float = 0.0
    emoji_usage: int = 0
    question_marks: int = 0
    exclamation_marks: int = 0
    
    # Социальные метрики
    replies_sent: int = 0
    replies_received: int = 0
    mentions_sent: int = 0
    mentions_received: int = 0
    
    # AI взаимодействия
    ai_requests: int = 0
    ai_rating_avg: float = 0.0

@dataclass
class ChatAnalytics:
    chat_id: int
    chat_title: Optional[str]
    chat_type: str
    
    # Общая активность
    total_messages: int = 0
    total_users: int = 0
    active_users_today: int = 0
    peak_hour: Optional[int] = None
    
    # Контент
    top_commands: List[Tuple[str, int]] = None
    top_words: List[Tuple[str, int]] = None
    emoji_stats: Dict[str, int] = None
    
    # Временные паттерны
    hourly_activity: List[int] = None
    daily_activity: List[int] = None
    weekly_activity: List[int] = None
    
    # Модерация
    moderation_actions: int = 0
    warnings_issued: int = 0
    
    # Развлечения
    games_played: int = 0
    facts_requested: int = 0
    jokes_requested: int = 0

class AdvancedAnalyticsSystem:
    """📊 Система продвинутой аналитики"""
    
    def __init__(self, db_service, config):
        self.db = db_service
        self.config = config
        
        # Кэш аналитики
        self.analytics_cache = {}
        self.cache_expiry = {}
        
        # Счетчики в реальном времени
        self.real_time_stats = defaultdict(lambda: defaultdict(int))
        
        # Слова для анализа (исключаем предлоги и т.д.)
        self.stop_words = {
            'и', 'в', 'на', 'с', 'по', 'для', 'от', 'к', 'за', 'из', 'у', 'о', 'об',
            'я', 'ты', 'он', 'она', 'мы', 'вы', 'они', 'что', 'как', 'где', 'когда',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of'
        }
        
        logger.info("📊 Advanced Analytics System инициализирован")
    
    async def initialize(self):
        """Инициализация системы"""
        await self._create_tables()
        
        # Запускаем фоновые задачи
        asyncio.create_task(self._periodic_analytics_update())
        asyncio.create_task(self._cleanup_old_analytics())
    
    async def _create_tables(self):
        """Создает таблицы аналитики"""
        
        # Аналитика пользователей
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS user_analytics (
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            date DATE NOT NULL,
            
            -- Основная информация
            username TEXT,
            first_name TEXT,
            
            -- Статистика сообщений
            total_messages INTEGER DEFAULT 0,
            text_messages INTEGER DEFAULT 0,
            media_messages INTEGER DEFAULT 0,
            command_usage INTEGER DEFAULT 0,
            
            -- Временная активность
            first_seen TIMESTAMP,
            last_seen TIMESTAMP,
            hourly_activity TEXT,  -- JSON массив с активностью по часам
            
            -- Поведенческие метрики
            avg_message_length REAL DEFAULT 0.0,
            emoji_usage INTEGER DEFAULT 0,
            question_marks INTEGER DEFAULT 0,
            exclamation_marks INTEGER DEFAULT 0,
            
            -- Социальные метрики
            replies_sent INTEGER DEFAULT 0,
            replies_received INTEGER DEFAULT 0,
            mentions_sent INTEGER DEFAULT 0,
            mentions_received INTEGER DEFAULT 0,
            
            -- AI взаимодействия
            ai_requests INTEGER DEFAULT 0,
            ai_rating_sum REAL DEFAULT 0.0,
            ai_rating_count INTEGER DEFAULT 0,
            
            PRIMARY KEY(user_id, chat_id, date),
            INDEX(chat_id, date),
            INDEX(user_id, date),
            INDEX(last_seen)
        )
        ''')
        
        # Аналитика чатов
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS chat_analytics (
            chat_id INTEGER NOT NULL,
            date DATE NOT NULL,
            
            -- Основная информация
            chat_title TEXT,
            chat_type TEXT,
            
            -- Общая активность
            total_messages INTEGER DEFAULT 0,
            unique_users INTEGER DEFAULT 0,
            active_users INTEGER DEFAULT 0,
            
            -- Временные паттерны (JSON)
            hourly_activity TEXT,
            daily_stats TEXT,
            
            -- Контент
            top_commands TEXT,  -- JSON
            word_frequency TEXT,  -- JSON
            emoji_stats TEXT,  -- JSON
            
            -- Модерация
            moderation_actions INTEGER DEFAULT 0,
            warnings_issued INTEGER DEFAULT 0,
            
            -- Развлечения
            games_played INTEGER DEFAULT 0,
            entertainment_requests INTEGER DEFAULT 0,
            
            PRIMARY KEY(chat_id, date),
            INDEX(date),
            INDEX(total_messages)
        )
        ''')
        
        # Детальная статистика сообщений
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS message_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message_date DATE NOT NULL,
            message_hour INTEGER NOT NULL,
            
            -- Характеристики сообщения
            message_length INTEGER,
            word_count INTEGER,
            emoji_count INTEGER,
            has_media BOOLEAN DEFAULT 0,
            is_command BOOLEAN DEFAULT 0,
            is_reply BOOLEAN DEFAULT 0,
            
            -- Тональность и содержание
            contains_question BOOLEAN DEFAULT 0,
            contains_exclamation BOOLEAN DEFAULT 0,
            language_detected TEXT,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            INDEX(chat_id, message_date),
            INDEX(user_id, message_date),
            INDEX(message_hour),
            INDEX(created_at)
        )
        ''')
        
        # Тренды и паттерны
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS analytics_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            trend_type TEXT NOT NULL,  -- daily_growth, user_retention, etc.
            trend_data TEXT NOT NULL,  -- JSON
            period_start DATE NOT NULL,
            period_end DATE NOT NULL,
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            INDEX(chat_id, trend_type),
            INDEX(period_start, period_end)
        )
        ''')
    
    async def track_message(self, chat_id: int, user_id: int, message_text: str,
                          username: Optional[str] = None, first_name: Optional[str] = None,
                          has_media: bool = False, is_command: bool = False,
                          is_reply: bool = False) -> bool:
        """📈 Отслеживает сообщение для аналитики"""
        
        try:
            now = datetime.now()
            today = now.date()
            hour = now.hour
            
            # Анализируем сообщение
            message_length = len(message_text)
            word_count = len(message_text.split())
            emoji_count = self._count_emojis(message_text)
            contains_question = '?' in message_text
            contains_exclamation = '!' in message_text
            
            # Сохраняем детальную статистику
            await self.db.execute('''
            INSERT INTO message_analytics 
            (chat_id, user_id, message_date, message_hour, message_length, word_count,
             emoji_count, has_media, is_command, is_reply, contains_question, contains_exclamation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                chat_id, user_id, today, hour, message_length, word_count,
                emoji_count, has_media, is_command, is_reply, contains_question, contains_exclamation
            ))
            
            # Обновляем аналитику пользователя
            await self._update_user_analytics(
                user_id, chat_id, today, username, first_name,
                message_text, has_media, is_command, is_reply, emoji_count
            )
            
            # Обновляем аналитику чата
            await self._update_chat_analytics(
                chat_id, today, hour, message_text, is_command, has_media
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отслеживания сообщения: {e}")
            return False
    
    async def get_user_analytics(self, chat_id: int, user_id: int, 
                               days: int = 30) -> Optional[UserAnalytics]:
        """👤 Получает аналитику пользователя"""
        
        try:
            start_date = datetime.now().date() - timedelta(days=days)
            
            # Агрегированная статистика за период
            stats = await self.db.fetch_one('''
            SELECT 
                SUM(total_messages) as total_msg,
                SUM(text_messages) as text_msg,
                SUM(media_messages) as media_msg,
                SUM(command_usage) as cmd_usage,
                MIN(first_seen) as first_seen,
                MAX(last_seen) as last_seen,
                AVG(avg_message_length) as avg_len,
                SUM(emoji_usage) as emoji_total,
                SUM(question_marks) as questions,
                SUM(exclamation_marks) as exclamations,
                SUM(replies_sent) as replies_s,
                SUM(replies_received) as replies_r,
                SUM(mentions_sent) as mentions_s,
                SUM(mentions_received) as mentions_r,
                SUM(ai_requests) as ai_req,
                AVG(CASE WHEN ai_rating_count > 0 THEN ai_rating_sum/ai_rating_count ELSE 0 END) as ai_avg
            FROM user_analytics 
            WHERE user_id = ? AND chat_id = ? AND date >= ?
            ''', (user_id, chat_id, start_date))
            
            if not stats or not stats[0]:
                return None
            
            # Получаем имя пользователя из последней записи
            user_info = await self.db.fetch_one('''
            SELECT username, first_name FROM user_analytics 
            WHERE user_id = ? AND chat_id = ? 
            ORDER BY date DESC LIMIT 1
            ''', (user_id, chat_id))
            
            # Вычисляем наиболее активное время
            most_active_hour = await self._get_most_active_hour(user_id, chat_id, start_date)
            most_active_day = await self._get_most_active_day(user_id, chat_id, start_date)
            
            return UserAnalytics(
                user_id=user_id,
                chat_id=chat_id,
                username=user_info[0] if user_info else None,
                first_name=user_info[1] if user_info else None,
                total_messages=stats[0] or 0,
                text_messages=stats[1] or 0,
                media_messages=stats[2] or 0,
                command_usage=stats[3] or 0,
                first_seen=datetime.fromisoformat(stats[4]) if stats[4] else None,
                last_seen=datetime.fromisoformat(stats[5]) if stats[5] else None,
                avg_message_length=stats[6] or 0.0,
                emoji_usage=stats[7] or 0,
                question_marks=stats[8] or 0,
                exclamation_marks=stats[9] or 0,
                replies_sent=stats[10] or 0,
                replies_received=stats[11] or 0,
                mentions_sent=stats[12] or 0,
                mentions_received=stats[13] or 0,
                ai_requests=stats[14] or 0,
                ai_rating_avg=stats[15] or 0.0,
                most_active_hour=most_active_hour,
                most_active_day=most_active_day
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения аналитики пользователя: {e}")
            return None
    
    async def get_chat_analytics(self, chat_id: int, days: int = 30) -> Optional[ChatAnalytics]:
        """💬 Получает аналитику чата"""
        
        try:
            start_date = datetime.now().date() - timedelta(days=days)
            
            # Основная статистика
            main_stats = await self.db.fetch_one('''
            SELECT 
                SUM(total_messages) as total_msg,
                AVG(unique_users) as avg_users,
                MAX(active_users) as peak_users,
                SUM(moderation_actions) as mod_actions,
                SUM(warnings_issued) as warnings,
                SUM(games_played) as games,
                SUM(entertainment_requests) as entertainment
            FROM chat_analytics 
            WHERE chat_id = ? AND date >= ?
            ''', (chat_id, start_date))
            
            # Информация о чате
            chat_info = await self.db.fetch_one('''
            SELECT chat_title, chat_type FROM chat_analytics 
            WHERE chat_id = ? ORDER BY date DESC LIMIT 1
            ''', (chat_id,))
            
            # Активность сегодня
            today = datetime.now().date()
            today_stats = await self.db.fetch_one('''
            SELECT active_users FROM chat_analytics 
            WHERE chat_id = ? AND date = ?
            ''', (chat_id, today))
            
            # Пиковый час активности
            peak_hour = await self._get_chat_peak_hour(chat_id, start_date)
            
            # Топ команды
            top_commands = await self._get_top_commands(chat_id, start_date)
            
            # Почасовая активность
            hourly_activity = await self._get_hourly_activity(chat_id, start_date)
            
            return ChatAnalytics(
                chat_id=chat_id,
                chat_title=chat_info[0] if chat_info else None,
                chat_type=chat_info[1] if chat_info else "unknown",
                total_messages=main_stats[0] or 0,
                total_users=int(main_stats[1] or 0),
                active_users_today=today_stats[0] if today_stats else 0,
                peak_hour=peak_hour,
                moderation_actions=main_stats[2] or 0,
                warnings_issued=main_stats[3] or 0,
                games_played=main_stats[4] or 0,
                facts_requested=main_stats[5] or 0,
                top_commands=top_commands,
                hourly_activity=hourly_activity
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения аналитики чата: {e}")
            return None
    
    async def generate_analytics_report(self, chat_id: int, period: str = "week") -> str:
        """📋 Генерирует отчет по аналитике"""
        
        try:
            # Определяем период
            if period == "day":
                days = 1
                period_name = "за сегодня"
            elif period == "week":
                days = 7
                period_name = "за неделю"
            elif period == "month":
                days = 30
                period_name = "за месяц"
            else:
                days = 7
                period_name = "за неделю"
            
            # Получаем аналитику чата
            chat_analytics = await self.get_chat_analytics(chat_id, days)
            
            if not chat_analytics:
                return f"📊 **Аналитика {period_name}**\n\n❌ Данных пока нет"
            
            # Формируем отчет
            report = f"📊 **Аналитика {period_name}**\n\n"
            
            # Основные показатели
            report += f"💬 **Сообщений:** {chat_analytics.total_messages:,}\n"
            report += f"👥 **Активных пользователей:** {chat_analytics.total_users}\n"
            
            if chat_analytics.peak_hour is not None:
                report += f"⏰ **Пик активности:** {chat_analytics.peak_hour:02d}:00\n"
            
            report += "\n"
            
            # Модерация
            if chat_analytics.moderation_actions > 0:
                report += f"🛡️ **Модерация:**\n"
                report += f"└ Действий: {chat_analytics.moderation_actions}\n"
                report += f"└ Предупреждений: {chat_analytics.warnings_issued}\n\n"
            
            # Развлечения
            if chat_analytics.games_played > 0 or chat_analytics.facts_requested > 0:
                report += f"🎲 **Развлечения:**\n"
                if chat_analytics.games_played > 0:
                    report += f"└ Игр сыграно: {chat_analytics.games_played}\n"
                if chat_analytics.facts_requested > 0:
                    report += f"└ Фактов запрошено: {chat_analytics.facts_requested}\n"
                report += "\n"
            
            # Топ команды
            if chat_analytics.top_commands:
                report += f"🏆 **Популярные команды:**\n"
                for i, (cmd, count) in enumerate(chat_analytics.top_commands[:5], 1):
                    report += f"{i}. `{cmd}` — {count} раз\n"
                report += "\n"
            
            # График активности по часам
            if chat_analytics.hourly_activity:
                report += f"📈 **Активность по часам:**\n"
                
                # Простой график из символов
                max_activity = max(chat_analytics.hourly_activity) if chat_analytics.hourly_activity else 1
                
                for hour in range(0, 24, 4):  # Каждые 4 часа
                    if hour < len(chat_analytics.hourly_activity):
                        activity = chat_analytics.hourly_activity[hour]
                        bar_length = int((activity / max_activity) * 10) if max_activity > 0 else 0
                        bar = "█" * bar_length + "░" * (10 - bar_length)
                        report += f"{hour:02d}:00 {bar} {activity}\n"
                
                report += "\n"
            
            # Топ пользователи
            top_users = await self._get_top_users(chat_id, days)
            if top_users:
                report += f"👑 **Самые активные:**\n"
                for i, (user_id, msg_count, name) in enumerate(top_users[:5], 1):
                    user_name = name or f"ID {user_id}"
                    report += f"{i}. {user_name} — {msg_count} сообщений\n"
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации отчета: {e}")
            return f"❌ Ошибка при создании отчета: {str(e)}"

# ЭКСПОРТ
__all__ = ["AdvancedAnalyticsSystem", "UserAnalytics", "ChatAnalytics"]
