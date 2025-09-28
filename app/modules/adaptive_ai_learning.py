# Создайте файл app/modules/adaptive_ai_learning.py

#!/usr/bin/env python3
"""
🧠 ADAPTIVE AI LEARNING SYSTEM v4.0
Система адаптивного обучения AI на основе общения
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    user_id: int
    chat_id: int
    communication_style: str = "neutral"  # friendly, formal, casual, rude
    interests: List[str] = None
    preferred_topics: List[str] = None
    response_length_preference: str = "medium"  # short, medium, long
    humor_level: float = 0.5  # 0.0 - serious, 1.0 - very humorous
    technical_level: str = "medium"  # basic, medium, advanced
    language_complexity: str = "medium"  # simple, medium, complex
    activity_times: List[int] = None  # Часы активности
    last_updated: datetime = None
    interaction_count: int = 0

@dataclass
class ConversationContext:
    chat_id: int
    current_topic: Optional[str] = None
    mood: str = "neutral"  # positive, neutral, negative
    formality_level: str = "casual"  # formal, casual, informal
    participants: List[int] = None
    recent_messages: deque = None
    topic_history: List[str] = None
    last_updated: datetime = None

@dataclass
class LearningPattern:
    pattern_id: str
    chat_id: int
    user_id: Optional[int]
    pattern_type: str  # response_style, topic_preference, timing, etc.
    pattern_data: Dict[str, Any]
    confidence: float = 0.0  # 0.0 - 1.0
    usage_count: int = 0
    success_rate: float = 0.0
    created_at: datetime = None
    last_used: datetime = None

class AdaptiveAILearning:
    """🧠 Система адаптивного обучения AI"""
    
    def __init__(self, db_service, ai_service, config):
        self.db = db_service
        self.ai = ai_service
        self.config = config
        
        # Кэш профилей пользователей
        self.user_profiles: Dict[Tuple[int, int], UserProfile] = {}
        
        # Контексты разговоров
        self.conversation_contexts: Dict[int, ConversationContext] = {}
        
        # Паттерны обучения
        self.learning_patterns: Dict[str, LearningPattern] = {}
        
        # Очереди сообщений для анализа
        self.message_queues: Dict[int, deque] = defaultdict(lambda: deque(maxlen=50))
        
        # Статистика обучения
        self.learning_stats = {
            'patterns_learned': 0,
            'successful_adaptations': 0,
            'user_profiles_created': 0
        }
        
        logger.info("🧠 Adaptive AI Learning System инициализирован")
    
    async def initialize(self):
        """Инициализация системы"""
        await self._create_tables()
        await self._load_user_profiles()
        await self._load_learning_patterns()
        
        # Запускаем фоновые задачи
        asyncio.create_task(self._periodic_learning_analysis())
        asyncio.create_task(self._cleanup_old_data())
    
    async def _create_tables(self):
        """Создает таблицы для обучения"""
        
        # Профили пользователей
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS user_ai_profiles (
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            communication_style TEXT DEFAULT 'neutral',
            interests TEXT,  -- JSON array
            preferred_topics TEXT,  -- JSON array
            response_length_preference TEXT DEFAULT 'medium',
            humor_level REAL DEFAULT 0.5,
            technical_level TEXT DEFAULT 'medium',
            language_complexity TEXT DEFAULT 'medium',
            activity_times TEXT,  -- JSON array of hours
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            interaction_count INTEGER DEFAULT 0,
            
            PRIMARY KEY(user_id, chat_id),
            INDEX(chat_id),
            INDEX(last_updated)
        )
        ''')
        
        # Контексты разговоров
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS conversation_contexts (
            chat_id INTEGER PRIMARY KEY,
            current_topic TEXT,
            mood TEXT DEFAULT 'neutral',
            formality_level TEXT DEFAULT 'casual',
            participants TEXT,  -- JSON array
            recent_messages TEXT,  -- JSON array
            topic_history TEXT,  -- JSON array
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Паттерны обучения
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS ai_learning_patterns (
            pattern_id TEXT PRIMARY KEY,
            chat_id INTEGER NOT NULL,
            user_id INTEGER,
            pattern_type TEXT NOT NULL,
            pattern_data TEXT NOT NULL,  -- JSON
            confidence REAL DEFAULT 0.0,
            usage_count INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP,
            
            INDEX(chat_id),
            INDEX(pattern_type),
            INDEX(confidence),
            INDEX(last_used)
        )
        ''')
        
        # История взаимодействий для анализа
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS ai_interaction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            user_message TEXT NOT NULL,
            bot_response TEXT,
            response_quality REAL,  -- Оценка качества ответа
            context_data TEXT,  -- JSON с контекстом
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            INDEX(chat_id),
            INDEX(user_id),
            INDEX(timestamp),
            INDEX(response_quality)
        )
        ''')
    
    async def learn_from_interaction(self, chat_id: int, user_id: int, 
                                   user_message: str, bot_response: str,
                                   feedback_score: Optional[float] = None) -> bool:
        """📚 Обучение на основе взаимодействия"""
        
        try:
            # Добавляем сообщение в очередь для анализа
            self.message_queues[chat_id].append({
                'user_id': user_id,
                'message': user_message,
                'response': bot_response,
                'timestamp': datetime.now(),
                'feedback': feedback_score
            })
            
            # Обновляем профиль пользователя
            await self._update_user_profile(chat_id, user_id, user_message, feedback_score)
            
            # Обновляем контекст разговора
            await self._update_conversation_context(chat_id, user_message, user_id)
            
            # Сохраняем в историю взаимодействий
            await self.db.execute('''
            INSERT INTO ai_interaction_history 
            (chat_id, user_id, user_message, bot_response, response_quality, context_data)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                chat_id, user_id, user_message, bot_response, feedback_score,
                json.dumps({'context': 'interaction'}, ensure_ascii=False)
            ))
            
            # Анализируем паттерны если накопилось достаточно сообщений
            if len(self.message_queues[chat_id]) >= 10:
                asyncio.create_task(self._analyze_patterns(chat_id))
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обучения на взаимодействии: {e}")
            return False
    
    async def get_adaptive_prompt(self, chat_id: int, user_id: int, 
                                user_message: str) -> str:
        """🎯 Создает адаптивный промпт для AI"""
        
        try:
            # Получаем профиль пользователя
            user_profile = await self._get_user_profile(chat_id, user_id)
            
            # Получаем контекст разговора
            conv_context = await self._get_conversation_context(chat_id)
            
            # Базовый промпт
            base_prompt = "Ты умный AI-помощник в Telegram боте. "
            
            # Адаптируем под пользователя
            if user_profile:
                # Стиль общения
                style_prompts = {
                    'friendly': "Будь дружелюбным и теплым в общении. Используй эмодзи умеренно.",
                    'formal': "Общайся формально и профессионально. Избегай сленга.",
                    'casual': "Общайся непринужденно и расслабленно. Можно использовать сленг.",
                    'rude': "Будь прямолинейным и немного дерзким, но не переходи границы."
                }
                
                base_prompt += style_prompts.get(user_profile.communication_style, 
                                               "Общайся естественно и дружелюбно. ")
                
                # Длина ответа
                length_prompts = {
                    'short': "Отвечай кратко и по сути, максимум 1-2 предложения. ",
                    'medium': "Отвечай развернуто, но не слишком длинно. 2-4 предложения. ",
                    'long': "Давай подробные и развернутые ответы с примерами. "
                }
                
                base_prompt += length_prompts.get(user_profile.response_length_preference,
                                                length_prompts['medium'])
                
                # Уровень юмора
                if user_profile.humor_level > 0.7:
                    base_prompt += "Добавляй юмор и шутки в свои ответы. "
                elif user_profile.humor_level < 0.3:
                    base_prompt += "Будь серьезным, избегай шуток. "
                
                # Технический уровень
                tech_prompts = {
                    'basic': "Объясняй простыми словами, избегай технических терминов. ",
                    'medium': "Используй умеренное количество технических терминов с объяснениями. ",
                    'advanced': "Можешь использовать сложные технические термины и концепции. "
                }
                
                base_prompt += tech_prompts.get(user_profile.technical_level,
                                              tech_prompts['medium'])
                
                # Интересы пользователя
                if user_profile.interests:
                    interests_str = ", ".join(user_profile.interests[:3])
                    base_prompt += f"Учти, что пользователь интересуется: {interests_str}. "
            
            # Адаптируем под контекст разговора
            if conv_context:
                # Текущая тема
                if conv_context.current_topic:
                    base_prompt += f"Текущая тема разговора: {conv_context.current_topic}. "
                
                # Настроение
                mood_prompts = {
                    'positive': "Поддерживай позитивную атмосферу. ",
                    'negative': "Будь понимающим и поддерживающим. ",
                    'neutral': ""
                }
                
                base_prompt += mood_prompts.get(conv_context.mood, "")
            
            # Добавляем актуальный вопрос
            base_prompt += f"\n\nВопрос пользователя: {user_message}\n\nОтветь в соответствии с указанным стилем:"
            
            return base_prompt
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания адаптивного промпта: {e}")
            return f"Ответь на вопрос пользователя: {user_message}"
    
    async def _update_user_profile(self, chat_id: int, user_id: int, 
                                 message: str, feedback: Optional[float]):
        """Обновляет профиль пользователя"""
        
        try:
            # Получаем или создаем профиль
            profile = await self._get_user_profile(chat_id, user_id)
            if not profile:
                profile = UserProfile(
                    user_id=user_id,
                    chat_id=chat_id,
                    interests=[],
                    preferred_topics=[],
                    activity_times=[],
                    last_updated=datetime.now()
                )
            
            # Анализируем стиль общения
            new_style = self._analyze_communication_style(message)
            if new_style != 'neutral':
                # Обновляем стиль с учетом истории
                profile.communication_style = self._blend_styles(profile.communication_style, new_style)
            
            # Определяем предпочтения по длине ответа
            message_length = len(message.split())
            if message_length < 5:
                profile.response_length_preference = 'short'
            elif message_length > 20:
                profile.response_length_preference = 'long'
            else:
                profile.response_length_preference = 'medium'
            
            # Анализируем технический уровень
            tech_level = self._analyze_technical_level(message)
            profile.technical_level = tech_level
            
            # Обновляем время активности
            current_hour = datetime.now().hour
            if current_hour not in profile.activity_times:
                profile.activity_times.append(current_hour)
                profile.activity_times = profile.activity_times[-24:]  # Храним последние 24 записи
            
            # Увеличиваем счетчик взаимодействий
            profile.interaction_count += 1
            profile.last_updated = datetime.now()
            
            # Сохраняем в БД
            await self._save_user_profile(profile)
            
            # Обновляем кэш
            self.user_profiles[(user_id, chat_id)] = profile
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления профиля пользователя: {e}")
    
    def _analyze_communication_style(self, message: str) -> str:
        """Анализирует стиль общения по сообщению"""
        
        message_lower = message.lower()
        
        # Индикаторы разных стилей
        friendly_indicators = ['спасибо', 'пожалуйста', '😊', '😄', '❤️', 'круто', 'отлично']
        formal_indicators = ['уважаемый', 'благодарю', 'прошу', 'извините', 'позвольте']
        casual_indicators = ['привет', 'ок', 'норм', 'кул', 'че как', 'здарова']
        rude_indicators = ['тупой', 'дурак', 'идиот', 'нах', 'блин', 'черт']
        
        # Подсчитываем совпадения
        scores = {
            'friendly': sum(1 for ind in friendly_indicators if ind in message_lower),
            'formal': sum(1 for ind in formal_indicators if ind in message_lower),
            'casual': sum(1 for ind in casual_indicators if ind in message_lower),
            'rude': sum(1 for ind in rude_indicators if ind in message_lower)
        }
        
        # Возвращаем стиль с максимальным счетом
        max_style = max(scores.items(), key=lambda x: x[1])
        return max_style[0] if max_style[1] > 0 else 'neutral'
    
    def _analyze_technical_level(self, message: str) -> str:
        """Анализирует технический уровень сообщения"""
        
        message_lower = message.lower()
        
        # Технические термины разного уровня
        basic_terms = ['компьютер', 'интернет', 'сайт', 'программа', 'файл']
        medium_terms = ['сервер', 'база данных', 'api', 'фреймворк', 'библиотека']
        advanced_terms = ['архитектура', 'микросервисы', 'контейнеризация', 'kubernetes', 'devops']
        
        # Подсчитываем совпадения
        basic_count = sum(1 for term in basic_terms if term in message_lower)
        medium_count = sum(1 for term in medium_terms if term in message_lower)
        advanced_count = sum(1 for term in advanced_terms if term in message_lower)
        
        if advanced_count > 0:
            return 'advanced'
        elif medium_count > 0:
            return 'medium'
        elif basic_count > 0:
            return 'basic'
        else:
            return 'medium'  # По умолчанию
    
    async def get_learning_stats(self, chat_id: Optional[int] = None) -> Dict[str, Any]:
        """📊 Получает статистику обучения"""
        
        try:
            stats = {}
            
            # Общие статистики
            if chat_id:
                # Статистика для конкретного чата
                user_profiles_count = await self.db.fetch_one('''
                SELECT COUNT(*) FROM user_ai_profiles WHERE chat_id = ?
                ''', (chat_id,))
                
                patterns_count = await self.db.fetch_one('''
                SELECT COUNT(*) FROM ai_learning_patterns WHERE chat_id = ?
                ''', (chat_id,))
                
                interactions_count = await self.db.fetch_one('''
                SELECT COUNT(*) FROM ai_interaction_history WHERE chat_id = ?
                ''', (chat_id,))
                
                stats['chat_id'] = chat_id
                stats['user_profiles'] = user_profiles_count[0] if user_profiles_count else 0
                stats['learned_patterns'] = patterns_count[0] if patterns_count else 0
                stats['total_interactions'] = interactions_count[0] if interactions_count else 0
            else:
                # Глобальная статистика
                stats.update(self.learning_stats)
                
                total_profiles = await self.db.fetch_one('SELECT COUNT(*) FROM user_ai_profiles')
                total_patterns = await self.db.fetch_one('SELECT COUNT(*) FROM ai_learning_patterns')
                total_interactions = await self.db.fetch_one('SELECT COUNT(*) FROM ai_interaction_history')
                
                stats['total_user_profiles'] = total_profiles[0] if total_profiles else 0
                stats['total_patterns'] = total_patterns[0] if total_patterns else 0
                stats['total_interactions'] = total_interactions[0] if total_interactions else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики обучения: {e}")
            return {}

# ЭКСПОРТ  
__all__ = ["AdaptiveAILearning", "UserProfile", "ConversationContext"]
