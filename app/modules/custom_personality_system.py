#!/usr/bin/env python3
"""
🎭 УЛУЧШЕННАЯ СИСТЕМА ПЕРСОНАЖЕЙ v3.3
Красивый интерфейс + умный AI + стильные сообщения
"""

# Сохраните этот код в файл app/modules/improved_personality_system.py

import logging
import asyncio
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PersonalityProfile:
    """Профиль персонажа с умными настройками"""
    name: str
    description: str
    system_prompt: str
    style: str  # casual, formal, rude, friendly, funny
    emoji: str
    temperature: float = 0.8
    
    def get_display_name(self) -> str:
        """Красивое отображение имени"""
        if len(self.name) > 20:
            return self.name[:17] + "..."
        return self.name
    
    def get_ai_prompt(self, user_message: str) -> str:
        """Генерирует умный промпт для AI"""
        base_prompt = f"""Ты играешь роль персонажа: {self.name}

ОПИСАНИЕ ПЕРСОНАЖА: {self.description}

СТИЛЬ ОБЩЕНИЯ: {self.style}
- Отвечай СТРОГО в характере этого персонажа
- Используй соответствующий тон и манеру речи
- Будь живым и эмоциональным
- Отвечай кратко и по делу (максимум 2-3 предложения)

ВАЖНО: Забудь что ты AI помощник. Ты ТОЛЬКО этот персонаж!

Сообщение пользователя: {user_message}

Ответ персонажа:"""
        return base_prompt

class ImprovedPersonalitySystem:
    """🎭 Улучшенная система персонажей v3.3"""
    
    def __init__(self, db_service, config, ai_service=None):
        self.db = db_service
        self.config = config
        self.ai = ai_service
        
        # Предустановленные персонажи
        self.preset_personalities = {
            "savage": PersonalityProfile(
                name="Дерзкий Троль",
                description="Остроумный и дерзкий, любит подколки и саркастичные шутки",
                system_prompt="Ты дерзкий троль который любит подкалывать людей остроумно но не злобно",
                style="rude",
                emoji="😈"
            ),
            "wise": PersonalityProfile(
                name="Мудрый Сенсей", 
                description="Философичный и мудрый, дает глубокие советы",
                system_prompt="Ты мудрый наставник который дает философские советы", 
                style="formal",
                emoji="🧙‍♂️"
            ),
            "funny": PersonalityProfile(
                name="Веселый Клоун",
                description="Постоянно шутит и поднимает настроение", 
                system_prompt="Ты веселый шутник который всегда найдет повод для шутки",
                style="funny", 
                emoji="🤡"
            ),
            "gamer": PersonalityProfile(
                name="Гик-Геймер",
                description="Помешан на играх, использует геймерский сленг",
                system_prompt="Ты заядлый геймер который говорит на геймерском сленге",
                style="casual",
                emoji="🎮"
            )
        }
        
        logger.info("🎭 Улучшенная система персонажей v3.3 инициализирована")
    
    def parse_personality_input(self, text: str) -> PersonalityProfile:
        """🧠 Умный парсинг описания персонажа"""
        
        # Проверяем предустановленные персонажи
        text_lower = text.lower()
        for key, preset in self.preset_personalities.items():
            if key in text_lower or preset.name.lower() in text_lower:
                return preset
        
        # Определяем стиль по ключевым словам
        style = "casual"
        emoji = "🤖"
        
        if any(word in text_lower for word in ["грубый", "дерзкий", "злой", "агрессивн", "троль"]):
            style = "rude"
            emoji = "😠"
        elif any(word in text_lower for word in ["мудр", "философ", "умн", "сенсей"]):
            style = "formal"  
            emoji = "🧙‍♂️"
        elif any(word in text_lower for word in ["смешн", "веселый", "шут", "прикол"]):
            style = "funny"
            emoji = "😄"
        elif any(word in text_lower for word in ["геймер", "игрок", "гик"]):
            style = "casual"
            emoji = "🎮"
        elif any(word in text_lower for word in ["добр", "милый", "ласков"]):
            style = "friendly"
            emoji = "😊"
        
        # Генерируем короткое имя
        name = self._generate_short_name(text)
        
        return PersonalityProfile(
            name=name,
            description=text[:100] + ("..." if len(text) > 100 else ""),
            system_prompt=f"Ты {text}. Веди себя в полном соответствии с этим описанием.",
            style=style,
            emoji=emoji
        )
    
    def _generate_short_name(self, description: str) -> str:
        """Генерирует короткое имя из описания"""
        
        # Удаляем лишние слова
        words = description.lower().split()
        skip_words = {"ты", "он", "она", "который", "которая", "что", "как", "и", "в", "на", "с", "по", "для", "от"}
        
        good_words = [w for w in words if w not in skip_words and len(w) > 2][:3]
        
        if not good_words:
            return "Персонаж"
        
        # Капитализируем первые буквы
        name_parts = [word.capitalize() for word in good_words]
        return " ".join(name_parts)
    
    async def set_personality_improved(self, user_id: int, chat_id: int, description: str) -> Tuple[bool, str]:
        """🎭 Улучшенная установка персонажа"""
        
        try:
            # Проверяем права
            if user_id not in self.config.bot.admin_ids:
                return False, "🚫 Только админы могут устанавливать персонажи"
            
            # Парсим описание
            personality = self.parse_personality_input(description)
            
            # Сохраняем в БД
            personality_id = f"improved_{user_id}_{abs(hash(description)) % 10000000}"
            
            await self.db.execute('''
            INSERT OR REPLACE INTO custom_personalities 
            (id, description, system_prompt, chat_id, user_id, created_at, is_active,
             personality_name, personality_description, is_group_personality, admin_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                personality_id,
                personality.description,
                personality.system_prompt, 
                chat_id,
                user_id,
                datetime.now().isoformat(),
                True,
                personality.name,
                personality.description,
                chat_id < 0,  # True для групп
                user_id
            ))
            
            # Красивое сообщение
            chat_type = "группе" if chat_id < 0 else "чате"
            
            success_msg = f"""{personality.emoji} **{personality.name}** активирован!

🎭 **Стиль:** {personality.style}
📝 **Описание:** {personality.description}

🎯 Теперь бот будет отвечать в роли этого персонажа в {chat_type}"""
            
            return True, success_msg
            
        except Exception as e:
            logger.error(f"❌ Ошибка установки персонажа: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    async def get_active_personality_improved(self, chat_id: int) -> Optional[PersonalityProfile]:
        """Получает активный персонаж"""
        
        try:
            result = await self.db.fetch_one('''
            SELECT personality_name, description, system_prompt  
            FROM custom_personalities 
            WHERE chat_id = ? AND is_active = 1
            ORDER BY created_at DESC LIMIT 1
            ''', (chat_id,))
            
            if result:
                return PersonalityProfile(
                    name=result[0] or "Персонаж",
                    description=result[1] or "Дружелюбный помощник",
                    system_prompt=result[2] or "Ты дружелюбный помощник",
                    style="casual", 
                    emoji="🎭"
                )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения персонажа: {e}")
            return None
    
    async def generate_personality_response(self, personality: PersonalityProfile, user_message: str) -> str:
        """🤖 Генерирует ответ от лица персонажа"""
        
        try:
            if not self.ai:
                # Fallback ответы по стилю
                fallback_responses = {
                    "rude": ["Ну и что?", "Скучно...", "Серьезно?", "Мда...", "И че дальше?"],
                    "funny": ["Хах, смешно! 😄", "Ты меня рассмешил!", "Вот это поворот! 😁"],
                    "wise": ["Мудро сказано...", "Это заставляет задуматься", "Интересная мысль"],
                    "casual": ["Круто!", "Понятно", "Ага", "Норм", "Окей"]
                }
                
                responses = fallback_responses.get(personality.style, ["Интересно..."])
                import random
                return random.choice(responses)
            
            # Генерируем умный ответ через AI
            prompt = personality.get_ai_prompt(user_message)
            
            response = await self.ai.generate_response(
                prompt,
                temperature=personality.temperature,
                max_length=150  # Короткие ответы
            )
            
            return response or "Хм... 🤔"
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации ответа персонажа: {e}")
            return "Э... что-то пошло не так 😅"

# ЭКСПОРТ
__all__ = ["ImprovedPersonalitySystem", "PersonalityProfile"]
