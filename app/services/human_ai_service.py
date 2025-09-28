#!/usr/bin/env python3
"""
🧠 CASUAL AI SERVICE v3.1 - МЕНЕЕ ВЕЖЛИВЫЙ AI
🚀 Живые, менее формальные ответы без излишней вежливости

УЛУЧШЕНИЯ:
• Менее вежливые, более живые ответы
• Убраны навязчивые вопросы
• Более короткие реплики
• Сленговый стиль общения
• Умные fallback ответы
"""

import logging
import asyncio
import random
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import openai
import anthropic

logger = logging.getLogger(__name__)


@dataclass
class BotPersonality:
    """🎭 Личность бота (менее вежливая)"""
    name: str = "Макс"
    age: int = 25
    personality_traits: List[str] = None
    interests: List[str] = None
    speech_style: str = "casual_direct"  # Менее формальный
    humor_level: float = 0.8
    sarcasm_level: float = 0.7
    empathy_level: float = 0.6  # Меньше эмпатии
    knowledge_depth: str = "expert"
    formality_level: float = 0.3  # Низкая формальность
    
    def __post_init__(self):
        if self.personality_traits is None:
            self.personality_traits = [
                "прямолинейный", "живой", "остроумный", "непосредственный",
                "дружелюбный", "расслабленный", "уверенный", "ироничный"
            ]
        
        if self.interests is None:
            self.interests = [
                "технологии", "программирование", "игры", "мемы", "музыка",
                "фильмы", "спорт", "путешествия", "еда", "книги"
            ]


@dataclass
class ConversationContext:
    """💭 Контекст разговора (менее формальный)"""
    user_id: int
    chat_id: int
    topic: str = ""
    mood: str = "neutral"
    formality_level: float = 0.3  # Низкая формальность
    conversation_depth: int = 1
    last_messages: List[Dict] = None
    user_preferences: Dict = None
    relationship_level: str = "buddy"  # Более дружелюбный по умолчанию
    
    def __post_init__(self):
        if self.last_messages is None:
            self.last_messages = []
        if self.user_preferences is None:
            self.user_preferences = {}


class CasualResponseGenerator:
    """😎 Генератор менее вежливых ответов"""
    
    def __init__(self):
        self.casual_greetings = {
            'утро': [
                "Утречко! ☀️ Как спалось?",
                "Доброе утро! 😊 Рано встаешь, молодец!",
                "Утро! Кофе уже пил? ☕"
            ],
            'день': [
                "Дарова! 👋 Че как дела?",
                "Привет! 😄 Что нового?",
                "Йо! Как жизнь?",
                "Салют! Что происходит?"
            ],
            'вечер': [
                "Вечер! 🌆 Как денек прошел?",
                "Привет! День был норм? 😊",
                "Вечерочек! Отдыхаешь уже?"
            ],
            'ночь': [
                "Привет, сова! 🦉 Не спишь поздно?",
                "Ночной житель! 🌙 Что делаешь?",
                "Бессонница? 😄"
            ]
        }
        
        self.topic_responses = {
            'технологии': [
                "О, тех тема! 💻 Что интересует?",
                "Технологии - мое! 🚀 В чем вопрос?",
                "IT тема! Какие проблемы?"
            ],
            'программирование': [
                "Код! 👨‍💻 На чем пишешь?",
                "Программинг! Какой язык?",
                "Кодинг - это жизнь! 😄 Что изучаешь?"
            ],
            'работа': [
                "Работка... 💼 Как дела на фронте?",
                "Офисные будни? Что тревожит?",
                "Работа есть работа 🤷‍♂️"
            ],
            'отношения': [
                "Дела сердечные? 💕 Расскажи",
                "Отношения штука сложная... Что случилось?",
                "Личная жизнь? Слушаю"
            ],
            'игры': [
                "Геймер! 🎮 Во что играешь?",
                "Игры рулят! Какая любимая?",
                "Гейминг тема! 🕹️"
            ]
        }
        
        self.emotion_responses = {
            'радость': [
                "Круто! 🎉 Рад за тебя!",
                "Отлично! 😄",
                "Вот это да! Супер!"
            ],
            'грусть': [
                "Понимаю... 😔",
                "Бывает такое",
                "Держись, все наладится 💪"
            ],
            'злость': [
                "Понятно, что бесит 😤",
                "Да, такое раздражает...",
                "Нормальная реакция"
            ],
            'благодарность': [
                "Не за что! 😊",
                "Пожалуйста! 👍",
                "Всегда рад помочь!"
            ]
        }
        
        self.short_responses = [
            "Понятно",
            "Ясно",
            "Окей",
            "Норм",
            "Ага",
            "Угу",
            "Точно",
            "Именно",
            "Так и есть",
            "Правда"
        ]
        
        self.question_responses = [
            "Хороший вопрос! 🤔",
            "Интересно спрашиваешь!",
            "Хм, сложно сказать",
            "А что сам думаешь?",
            "Давай разберем"
        ]
    
    def get_time_of_day(self) -> str:
        """🕐 Определение времени суток"""
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return "утро"
        elif 12 <= hour < 18:
            return "день"
        elif 18 <= hour < 22:
            return "вечер"
        else:
            return "ночь"
    
    def generate_casual_response(self, message: str, emotion: str, topic: str, context: ConversationContext) -> str:
        """😎 Генерация менее вежливого ответа"""
        
        message_lower = message.lower()
        
        # 1. Приветствия
        if any(word in message_lower for word in ['привет', 'здрав', 'дарова', 'хай', 'салют']):
            time_of_day = self.get_time_of_day()
            responses = self.casual_greetings.get(time_of_day, self.casual_greetings['день'])
            return random.choice(responses)
        
        # 2. Короткие ответы на простые сообщения
        if len(message.split()) <= 2 or message_lower in ['да', 'нет', 'ок', 'хорошо', 'плохо']:
            return random.choice(self.short_responses)
        
        # 3. Благодарности
        if emotion == 'благодарность':
            return random.choice(self.emotion_responses['благодарность'])
        
        # 4. Вопросы (короткие ответы)
        if '?' in message:
            return random.choice(self.question_responses)
        
        # 5. Эмоции
        if emotion in self.emotion_responses:
            return random.choice(self.emotion_responses[emotion])
        
        # 6. Темы (без лишних вопросов)
        if 'программ' in message_lower or 'код' in message_lower:
            return random.choice(self.topic_responses['программирование'])
        
        if topic in self.topic_responses:
            return random.choice(self.topic_responses[topic])
        
        # 7. Специальные случаи
        if any(word in message_lower for word in ['помоги', 'помощь']):
            return "Помогу! 💪 В чем дело?"
        
        if any(word in message_lower for word in ['скучно', 'нечем заняться']):
            return "Понимаю 😄 Хочешь поговорить о чем-то?"
        
        if any(word in message_lower for word in ['устал', 'замучился']):
            return "Отдохни! ☕ Здоровье дороже"
        
        # 8. Общие короткие ответы
        general_responses = [
            "Интересно!",
            "Понимаю",
            "Ага, так и есть",
            "Норм тема",
            "И как тебе?",
            "Понял",
            "Хм",
            "Любопытно"
        ]
        
        return random.choice(general_responses)


class HumanLikeAI:
    """🧠 Менее вежливый AI (главный класс)"""
    
    def __init__(self, config):
        self.config = config
        self.personality = BotPersonality()
        self.response_generator = CasualResponseGenerator()
        
        # Эмоциональные паттерны (из предыдущей версии)
        self.emotion_patterns = {
            'радость': ['рад', 'счастлив', 'весел', '😄', '😊', '🎉', 'отлично', 'супер', 'классно'],
            'грусть': ['грустн', 'печальн', 'расстроен', '😢', '😭', 'плохо', 'ужасно'],
            'злость': ['злой', 'бесит', 'раздражает', '😠', '😡', 'достал', 'ненавижу'],
            'благодарность': ['спасибо', 'благодар', 'сенк', 'мерси', 'thanks']
        }
        
        self.topic_keywords = {
            'технологии': ['технолог', 'программирование', 'код', 'ai', 'компьютер', 'интернет'],
            'программирование': ['программ', 'код', 'python', 'javascript', 'разработка', 'баг'],
            'работа': ['работа', 'карьера', 'офис', 'начальник', 'зарплата'],
            'игры': ['игра', 'игру', 'играл', 'геймер', 'пс5', 'xbox'],
            'отношения': ['отношения', 'любовь', 'семья', 'девушка', 'парень']
        }
        
        # OpenAI клиент (опционально)
        self.openai_client = None
        if config.ai.openai_api_key and config.ai.openai_api_key.startswith('sk-'):
            try:
                self.openai_client = openai.OpenAI(api_key=config.ai.openai_api_key)
                logger.info("🧠 OpenAI клиент инициализирован")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI недоступен: {e}")
                self.openai_client = None
        
        logger.info("🧠 Human-like AI инициализирован")
    
    def analyze_emotion(self, text: str) -> Tuple[str, float]:
        """🔍 Анализ эмоции"""
        text_lower = text.lower()
        
        for emotion, patterns in self.emotion_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return emotion, 0.8
        
        return 'нейтральная', 0.5
    
    def classify_topic(self, text: str) -> Tuple[str, float]:
        """📚 Классификация темы"""
        text_lower = text.lower()
        
        for topic, keywords in self.topic_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return topic, 0.7
        
        return 'общение', 0.3
    
    async def generate_human_response(self, message: str, context: ConversationContext) -> str:
        """🗣️ Генерация менее вежливого ответа"""
        try:
            # Анализируем эмоции и тему
            emotion, emotion_confidence = self.analyze_emotion(message)
            topic, topic_confidence = self.classify_topic(message)
            
            # Обновляем контекст
            context.topic = topic
            context.mood = emotion
            
            logger.info(f"🧠 Анализ: эмоция={emotion}, тема={topic}")
            
            # Пробуем OpenAI если доступно
            if self.openai_client:
                try:
                    response = await self._generate_openai_response(message, context, emotion, topic)
                    if response:
                        # Делаем ответ менее вежливым
                        return self._make_less_polite(response)
                except Exception as e:
                    logger.warning(f"⚠️ OpenAI ошибка: {e}")
            
            # Fallback - менее вежливый ответ
            response = self.response_generator.generate_casual_response(message, emotion, topic, context)
            
            logger.info(f"🧠 Ответ сгенерирован: тема={topic}, эмоция={emotion}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации ответа: {e}")
            return self._generate_error_response()
    
    async def _generate_openai_response(self, message: str, context: ConversationContext, emotion: str, topic: str) -> Optional[str]:
        """🤖 OpenAI с менее вежливым промптом"""
        try:
            system_prompt = f"""Ты - {self.personality.name}, 25-летний парень с живым характером.

ТВОЯ ЛИЧНОСТЬ:
• Стиль: живой, прямой, менее формальный
• НЕ задавай много вопросов в конце
• Отвечай коротко и по делу
• Используй сленг и разговорный стиль
• Без излишней вежливости

КОНТЕКСТ:
• Тема: {topic}
• Эмоция: {emotion}

Ответь естественно, коротко, без лишних вопросов. Максимум 1-2 предложения."""

            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.config.ai.default_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.9,  # Больше креативности
                max_tokens=100    # Короче ответы
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ Ошибка OpenAI: {e}")
            return None
    
    def _make_less_polite(self, text: str) -> str:
        """😎 Делаем ответ менее вежливым"""
        
        # Убираем излишне вежливые фразы
        polite_phrases = [
            "Было бы интересно узнать", "Хотелось бы услышать",
            "Не могли бы вы", "Будьте добры", "Позвольте",
            "Если не возражаете", "С вашего позволения"
        ]
        
        for phrase in polite_phrases:
            text = text.replace(phrase, "")
        
        # Убираем лишние вопросы
        if text.count('?') > 1:
            parts = text.split('?')
            if len(parts) > 2:
                # Оставляем только первый вопрос или убираем все
                if random.choice([True, False]):
                    text = parts[0] + '.'
                else:
                    text = '?'.join(parts[:2])
        
        # Заменяем формальные фразы
        replacements = {
            "Очень интересно!": "Прикольно!",
            "Замечательно!": "Круто!",
            "Превосходно!": "Отлично!",
            "Что вы думаете": "Что думаешь",
            "Расскажите": "Расскажи",
            "Поделитесь": "Поделись",
            "вам": "тебе",
            "Вам": "Тебе"
        }
        
        for formal, casual in replacements.items():
            text = text.replace(formal, casual)
        
        return text.strip()
    
    def _generate_error_response(self) -> str:
        """❌ Ответ при ошибке"""
        error_responses = [
            "Не понял... 😅",
            "Что?",
            "Хм?",
            "Повтори?",
            "Не въехал",
            "Еще раз?"
        ]
        return random.choice(error_responses)
    
    async def update_context(self, context: ConversationContext, message: str, response: str):
        """📝 Обновление контекста"""
        context.last_messages.append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now()
        })
        
        context.last_messages.append({
            'role': 'assistant', 
            'content': response,
            'timestamp': datetime.now()
        })
        
        # Ограничиваем историю
        if len(context.last_messages) > 10:
            context.last_messages = context.last_messages[-10:]
        
        context.conversation_depth = min(10, context.conversation_depth + 1)


def create_conversation_context(user_id: int, chat_id: int) -> ConversationContext:
    """💭 Создание менее формального контекста"""
    return ConversationContext(
        user_id=user_id, 
        chat_id=chat_id,
        formality_level=0.3,  # Низкая формальность
        relationship_level="buddy"  # Дружелюбный стиль
    )


# =================== ЭКСПОРТ ===================

__all__ = [
    "HumanLikeAI", 
    "ConversationContext", 
    "BotPersonality",
    "CasualResponseGenerator",
    "create_conversation_context"
]