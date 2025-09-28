# Создайте файл app/modules/custom_wake_words.py

#!/usr/bin/env python3
"""
🔤 CUSTOM WAKE WORDS SYSTEM v4.0
Гибкая система кастомных слов для призыва бота
"""

import logging
import re
import json
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class WakeWord:
    word: str
    chat_id: int
    creator_id: int
    is_regex: bool = False
    case_sensitive: bool = False
    whole_word_only: bool = True
    response_probability: float = 1.0
    custom_greeting: Optional[str] = None
    created_at: datetime = None
    usage_count: int = 0

class CustomWakeWordsSystem:
    """🔤 Система кастомных слов призыва"""
    
    def __init__(self, db_service, config):
        self.db = db_service
        self.config = config
        
        # Стандартные слова призыва (глобальные)
        self.default_wake_words = {
            "бот", "bot", "робот", "макс", "max", "эй", "слушай", 
            "помощник", "assistant", "ai", "ай", "хей", "hey"
        }
        
        # Кэш кастомных слов по чатам
        self.custom_words_cache: Dict[int, Set[WakeWord]] = {}
        self.cache_last_update = {}
        
        logger.info("🔤 Custom Wake Words System инициализирован")
    
    async def initialize(self):
        """Инициализация системы"""
        await self._create_tables()
        await self._load_all_wake_words()
        
    async def _create_tables(self):
        """Создает таблицы"""
        
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS custom_wake_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            chat_id INTEGER NOT NULL,
            creator_id INTEGER NOT NULL,
            is_regex BOOLEAN DEFAULT 0,
            case_sensitive BOOLEAN DEFAULT 0,
            whole_word_only BOOLEAN DEFAULT 1,
            response_probability REAL DEFAULT 1.0,
            custom_greeting TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usage_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            
            UNIQUE(word, chat_id),
            INDEX(chat_id),
            INDEX(creator_id),
            INDEX(is_active)
        )
        ''')
        
        # Статистика использования слов призыва
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS wake_words_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            word_used TEXT NOT NULL,
            message_text TEXT,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            INDEX(chat_id),
            INDEX(used_at),
            FOREIGN KEY(word_id) REFERENCES custom_wake_words(id)
        )
        ''')
    
    async def add_wake_word(self, word: str, chat_id: int, creator_id: int, 
                           **options) -> Tuple[bool, str]:
        """➕ Добавляет кастомное слово призыва"""
        
        try:
            # Валидация
            word = word.strip()
            if not word:
                return False, "❌ Пустое слово призыва"
            
            if len(word) > 50:
                return False, "❌ Слово слишком длинное (макс. 50 символов)"
            
            # Проверяем regex если включен
            is_regex = options.get('is_regex', False)
            if is_regex:
                try:
                    re.compile(word)
                except re.error as e:
                    return False, f"❌ Неверное регулярное выражение: {str(e)}"
            
            # Проверяем существование
            existing = await self.db.fetch_one('''
            SELECT id FROM custom_wake_words 
            WHERE word = ? AND chat_id = ? AND is_active = 1
            ''', (word, chat_id))
            
            if existing:
                return False, f"❌ Слово '{word}' уже добавлено в этом чате"
            
            # Добавляем в БД
            wake_word = WakeWord(
                word=word,
                chat_id=chat_id,
                creator_id=creator_id,
                is_regex=is_regex,
                case_sensitive=options.get('case_sensitive', False),
                whole_word_only=options.get('whole_word_only', True),
                response_probability=options.get('response_probability', 1.0),
                custom_greeting=options.get('custom_greeting'),
                created_at=datetime.now()
            )
            
            await self.db.execute('''
            INSERT INTO custom_wake_words 
            (word, chat_id, creator_id, is_regex, case_sensitive, 
             whole_word_only, response_probability, custom_greeting)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                wake_word.word, wake_word.chat_id, wake_word.creator_id,
                wake_word.is_regex, wake_word.case_sensitive, wake_word.whole_word_only,
                wake_word.response_probability, wake_word.custom_greeting
            ))
            
            # Обновляем кэш
            await self._update_chat_cache(chat_id)
            
            success_msg = f"✅ Слово призыва **{word}** добавлено!\n\n"
            
            if is_regex:
                success_msg += "🔍 Тип: Регулярное выражение\n"
            else:
                success_msg += "📝 Тип: Обычное слово\n"
            
            if not wake_word.case_sensitive:
                success_msg += "🔤 Регистр: Не важен\n"
            
            if wake_word.response_probability < 1.0:
                success_msg += f"🎲 Вероятность ответа: {int(wake_word.response_probability * 100)}%\n"
            
            if wake_word.custom_greeting:
                success_msg += f"👋 Кастомное приветствие: {wake_word.custom_greeting}\n"
            
            return True, success_msg
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления слова призыва: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    async def remove_wake_word(self, word: str, chat_id: int, user_id: int) -> Tuple[bool, str]:
        """➖ Удаляет кастомное слово призыва"""
        
        try:
            # Проверяем существование и права
            existing = await self.db.fetch_one('''
            SELECT id, creator_id FROM custom_wake_words 
            WHERE word = ? AND chat_id = ? AND is_active = 1
            ''', (word, chat_id))
            
            if not existing:
                return False, f"❌ Слово '{word}' не найдено"
            
            # Проверяем права (создатель или админ)
            if existing[1] != user_id and user_id not in self.config.bot.admin_ids:
                return False, "❌ Только создатель слова или админ может его удалить"
            
            # Удаляем (деактивируем)
            await self.db.execute('''
            UPDATE custom_wake_words SET is_active = 0 
            WHERE word = ? AND chat_id = ?
            ''', (word, chat_id))
            
            # Обновляем кэш
            await self._update_chat_cache(chat_id)
            
            return True, f"✅ Слово призыва '{word}' удалено"
            
        except Exception as e:
            logger.error(f"❌ Ошибка удаления слова призыва: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    async def check_wake_words(self, text: str, chat_id: int, user_id: int, 
                             bot_username: str = None) -> Tuple[bool, Optional[WakeWord], str]:
        """🔍 Проверяет сообщение на слова призыва"""
        
        try:
            # Проверяем упоминание бота
            if bot_username and f"@{bot_username.lower()}" in text.lower():
                await self._log_usage(None, chat_id, user_id, f"@{bot_username}", text)
                return True, None, "mention"
            
            # Проверяем стандартные слова
            text_lower = text.lower()
            for default_word in self.default_wake_words:
                if self._check_word_match(default_word, text_lower, 
                                        case_sensitive=False, whole_word_only=True):
                    await self._log_usage(None, chat_id, user_id, default_word, text)
                    return True, None, "default"
            
            # Проверяем кастомные слова
            custom_words = await self._get_chat_wake_words(chat_id)
            
            for wake_word in custom_words:
                if self._check_wake_word_match(wake_word, text):
                    # Проверяем вероятность ответа
                    if wake_word.response_probability < 1.0:
                        import random
                        if random.random() > wake_word.response_probability:
                            continue
                    
                    # Обновляем статистику
                    await self._update_word_usage(wake_word, chat_id, user_id, text)
                    
                    return True, wake_word, "custom"
            
            return False, None, ""
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки слов призыва: {e}")
            return False, None, ""
    
    def _check_wake_word_match(self, wake_word: WakeWord, text: str) -> bool:
        """Проверяет совпадение кастомного слова призыва"""
        
        try:
            if wake_word.is_regex:
                # Регулярное выражение
                flags = 0 if wake_word.case_sensitive else re.IGNORECASE
                return bool(re.search(wake_word.word, text, flags))
            else:
                # Обычное слово
                check_text = text if wake_word.case_sensitive else text.lower()
                check_word = wake_word.word if wake_word.case_sensitive else wake_word.word.lower()
                
                return self._check_word_match(check_word, check_text, 
                                            wake_word.case_sensitive, wake_word.whole_word_only)
        
        except Exception as e:
            logger.error(f"❌ Ошибка проверки слова призыва: {e}")
            return False
    
    def _check_word_match(self, word: str, text: str, case_sensitive: bool, whole_word_only: bool) -> bool:
        """Проверяет совпадение обычного слова"""
        
        if whole_word_only:
            # Проверяем как отдельное слово
            pattern = r'\b' + re.escape(word) + r'\b'
            flags = 0 if case_sensitive else re.IGNORECASE
            return bool(re.search(pattern, text, flags))
        else:
            # Проверяем вхождение
            return word in text
    
    async def list_wake_words(self, chat_id: int) -> Tuple[List[str], List[WakeWord]]:
        """📋 Получает список всех слов призыва для чата"""
        
        try:
            # Стандартные слова
            default_words = list(self.default_wake_words)
            
            # Кастомные слова
            custom_words = await self._get_chat_wake_words(chat_id)
            
            return default_words, custom_words
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка слов призыва: {e}")
            return [], []
    
    async def get_wake_words_stats(self, chat_id: int, days: int = 7) -> Dict[str, any]:
        """📊 Получает статистику использования слов призыва"""
        
        try:
            from_date = datetime.now() - timedelta(days=days)
            
            # Общая статистика
            total_usage = await self.db.fetch_one('''
            SELECT COUNT(*) FROM wake_words_usage 
            WHERE chat_id = ? AND used_at >= ?
            ''', (chat_id, from_date))
            
            # Топ слов
            top_words = await self.db.fetch_all('''
            SELECT word_used, COUNT(*) as count
            FROM wake_words_usage 
            WHERE chat_id = ? AND used_at >= ?
            GROUP BY word_used 
            ORDER BY count DESC 
            LIMIT 10
            ''', (chat_id, from_date))
            
            # Топ пользователей
            top_users = await self.db.fetch_all('''
            SELECT user_id, COUNT(*) as count
            FROM wake_words_usage 
            WHERE chat_id = ? AND used_at >= ?
            GROUP BY user_id 
            ORDER BY count DESC 
            LIMIT 10
            ''', (chat_id, from_date))
            
            return {
                'total_usage': total_usage[0] if total_usage else 0,
                'top_words': [{'word': row[0], 'count': row[1]} for row in top_words],
                'top_users': [{'user_id': row[0], 'count': row[1]} for row in top_users],
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики слов призыва: {e}")
            return {}
    
    async def _get_chat_wake_words(self, chat_id: int) -> List[WakeWord]:
        """Получает кастомные слова призыва для чата"""
        
        # Проверяем кэш
        if chat_id in self.custom_words_cache:
            cache_age = datetime.now() - self.cache_last_update.get(chat_id, datetime.min)
            if cache_age.total_seconds() < 300:  # 5 минут
                return list(self.custom_words_cache[chat_id])
        
        # Загружаем из БД
        await self._update_chat_cache(chat_id)
        return list(self.custom_words_cache.get(chat_id, set()))
    
    async def _update_chat_cache(self, chat_id: int):
        """Обновляет кэш слов призыва для чата"""
        
        try:
            words_data = await self.db.fetch_all('''
            SELECT word, creator_id, is_regex, case_sensitive, whole_word_only,
                   response_probability, custom_greeting, created_at, usage_count
            FROM custom_wake_words 
            WHERE chat_id = ? AND is_active = 1
            ''', (chat_id,))
            
            words_set = set()
            for row in words_data:
                wake_word = WakeWord(
                    word=row[0],
                    chat_id=chat_id,
                    creator_id=row[1],
                    is_regex=bool(row[2]),
                    case_sensitive=bool(row[3]),
                    whole_word_only=bool(row[4]),
                    response_probability=row[5],
                    custom_greeting=row[6],
                    created_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    usage_count=row[8]
                )
                words_set.add(wake_word)
            
            self.custom_words_cache[chat_id] = words_set
            self.cache_last_update[chat_id] = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления кэша слов призыва: {e}")
    
    async def _update_word_usage(self, wake_word: WakeWord, chat_id: int, user_id: int, text: str):
        """Обновляет статистику использования слова"""
        
        try:
            # Увеличиваем счетчик в основной таблице
            await self.db.execute('''
            UPDATE custom_wake_words SET usage_count = usage_count + 1
            WHERE word = ? AND chat_id = ?
            ''', (wake_word.word, chat_id))
            
            # Логируем использование
            await self._log_usage(None, chat_id, user_id, wake_word.word, text)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления статистики слова: {e}")
    
    async def _log_usage(self, word_id: Optional[int], chat_id: int, user_id: int, 
                        word_used: str, message_text: str):
        """Логирует использование слова призыва"""
        
        try:
            await self.db.execute('''
            INSERT INTO wake_words_usage (word_id, chat_id, user_id, word_used, message_text)
            VALUES (?, ?, ?, ?, ?)
            ''', (word_id, chat_id, user_id, word_used, message_text[:200]))  # Ограничиваем длину
            
        except Exception as e:
            logger.error(f"❌ Ошибка логирования использования: {e}")

# ЭКСПОРТ
__all__ = ["CustomWakeWordsSystem", "WakeWord"]
