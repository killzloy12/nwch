#!/usr/bin/env python3
"""
🧠 AI SERVICE v2.0
🤖 Продвинутый AI сервис с поддержкой GPT-4 и Claude-3

Интеграция с OpenAI и Anthropic API для генерации умных ответов
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import aiohttp
from cachetools import TTLCache

logger = logging.getLogger(__name__)


class AIService:
    """🧠 Сервис искусственного интеллекта"""
    
    def __init__(self, config):
        self.config = config
        self.ai_config = config.ai
        
        # Кэш ответов
        self.response_cache = TTLCache(maxsize=100, ttl=3600)  # 1 час
        
        # Счетчики лимитов
        self.daily_usage = {}
        self.user_usage = {}
        
        # Доступные модели
        self.openai_models = [
            'gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'
        ]
        
        self.anthropic_models = [
            'claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307', 'claude-3-opus-20240229'
        ]
        
        logger.info("🧠 AI Service инициализирован")
    
    async def generate_response(self, prompt: str, user_id: int = None, 
                              context: Dict = None) -> Optional[str]:
        """🎯 Генерация ответа от AI"""
        
        try:
            # Проверяем лимиты
            if not self._check_limits(user_id):
                return "❌ Превышен лимит запросов к AI. Попробуйте позже."
            
            # Проверяем кэш
            cache_key = self._generate_cache_key(prompt, context)
            if cache_key in self.response_cache:
                logger.debug("📋 Ответ получен из кэша")
                return self.response_cache[cache_key]
            
            # Подготавливаем промпт с контекстом
            enhanced_prompt = self._enhance_prompt(prompt, context)
            
            # Генерируем ответ
            response = None
            
            # Пробуем OpenAI
            if self.ai_config.openai_api_key:
                response = await self._call_openai(enhanced_prompt)
            
            # Если OpenAI не сработал, пробуем Anthropic
            if not response and self.ai_config.anthropic_api_key:
                response = await self._call_anthropic(enhanced_prompt)
            
            if not response:
                return "❌ AI сервисы временно недоступны. Проверьте настройки API ключей."
            
            # Сохраняем в кэш
            self.response_cache[cache_key] = response
            
            # Учитываем использование
            self._track_usage(user_id)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации ответа: {e}")
            return "❌ Произошла ошибка при обращении к AI. Попробуйте позже."
    
    async def _call_openai(self, prompt: str) -> Optional[str]:
        """🔵 Вызов OpenAI API"""
        
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.ai_config.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.ai_config.default_model,
                "messages": [
                    {
                        "role": "system", 
                        "content": "Ты - продвинутый AI помощник в Telegram боте Enhanced Telegram Bot v2.0. Отвечай полезно, дружелюбно и информативно. Используй эмодзи для украшения ответов."
                    },
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": self.ai_config.max_tokens,
                "temperature": self.ai_config.temperature
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=30) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result['choices'][0]['message']['content'].strip()
                    else:
                        logger.error(f"OpenAI API ошибка {resp.status}: {await resp.text()}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Ошибка вызова OpenAI: {e}")
            return None
    
    async def _call_anthropic(self, prompt: str) -> Optional[str]:
        """🟠 Вызов Anthropic Claude API"""
        
        try:
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": self.ai_config.anthropic_api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            # Определяем модель Claude
            model = "claude-3-5-sonnet-20241022"
            if "haiku" in self.ai_config.default_model.lower():
                model = "claude-3-haiku-20240307"
            elif "opus" in self.ai_config.default_model.lower():
                model = "claude-3-opus-20240229"
            
            data = {
                "model": model,
                "max_tokens": self.ai_config.max_tokens,
                "temperature": self.ai_config.temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Ты - продвинутый AI помощник в Telegram боте Enhanced Telegram Bot v2.0. Отвечай полезно, дружелюбно и информативно. Используй эмодзи для украшения ответов.\n\nВопрос: {prompt}"
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=30) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result['content'][0]['text'].strip()
                    else:
                        logger.error(f"Anthropic API ошибка {resp.status}: {await resp.text()}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Ошибка вызова Anthropic: {e}")
            return None
    
    def _enhance_prompt(self, prompt: str, context: Dict = None) -> str:
        """💡 Улучшение промпта с контекстом"""
        
        try:
            enhanced = prompt
            
            if context:
                # Добавляем информацию о пользователе
                behavior_analysis = context.get('behavior_analysis', {})
                if behavior_analysis:
                    user_type = behavior_analysis.get('user_type', 'regular_user')
                    communication_style = behavior_analysis.get('communication_style', 'neutral')
                    
                    enhanced += f"\n\n[Контекст: пользователь типа '{user_type}', стиль общения '{communication_style}']"
                
                # Добавляем историю диалога
                memory = context.get('memory', [])
                if memory:
                    recent_memory = memory[-6:]  # Последние 3 обмена
                    memory_text = "\n".join(recent_memory)
                    enhanced = f"Контекст диалога:\n{memory_text}\n\nТекущий вопрос: {prompt}"
            
            return enhanced
            
        except Exception as e:
            logger.error(f"❌ Ошибка улучшения промпта: {e}")
            return prompt
    
    def _generate_cache_key(self, prompt: str, context: Dict = None) -> str:
        """🔑 Генерация ключа для кэша"""
        
        try:
            # Создаем ключ на основе промпта и контекста
            key_parts = [prompt[:100]]  # Первые 100 символов промпта
            
            if context:
                behavior = context.get('behavior_analysis', {})
                if behavior:
                    key_parts.append(behavior.get('user_type', ''))
                    key_parts.append(behavior.get('communication_style', ''))
            
            return "|".join(key_parts)
            
        except Exception:
            return prompt[:50]
    
    def _check_limits(self, user_id: int = None) -> bool:
        """🚦 Проверка лимитов использования"""
        
        try:
            today = datetime.now().date()
            
            # Проверяем дневной лимит
            daily_count = self.daily_usage.get(today, 0)
            if daily_count >= self.ai_config.daily_limit:
                return False
            
            # Проверяем лимит пользователя
            if user_id:
                user_today_key = f"{user_id}_{today}"
                user_count = self.user_usage.get(user_today_key, 0)
                if user_count >= self.ai_config.user_limit:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки лимитов: {e}")
            return True  # Разрешаем в случае ошибки
    
    def _track_usage(self, user_id: int = None):
        """📊 Отслеживание использования"""
        
        try:
            today = datetime.now().date()
            
            # Увеличиваем дневной счетчик
            self.daily_usage[today] = self.daily_usage.get(today, 0) + 1
            
            # Увеличиваем счетчик пользователя
            if user_id:
                user_today_key = f"{user_id}_{today}"
                self.user_usage[user_today_key] = self.user_usage.get(user_today_key, 0) + 1
            
            # Очищаем старые записи
            self._cleanup_old_usage()
            
        except Exception as e:
            logger.error(f"❌ Ошибка отслеживания использования: {e}")
    
    def _cleanup_old_usage(self):
        """🧹 Очистка старых данных об использовании"""
        
        try:
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            # Удаляем старые дневные записи
            to_remove = [date for date in self.daily_usage.keys() if date < yesterday]
            for date in to_remove:
                del self.daily_usage[date]
            
            # Удаляем старые пользовательские записи
            to_remove = [key for key in self.user_usage.keys() if yesterday.isoformat() not in key and today.isoformat() not in key]
            for key in to_remove:
                del self.user_usage[key]
                
        except Exception as e:
            logger.error(f"❌ Ошибка очистки старых данных: {e}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """📊 Статистика использования"""
        
        try:
            today = datetime.now().date()
            
            return {
                'daily_usage': self.daily_usage.get(today, 0),
                'daily_limit': self.ai_config.daily_limit,
                'cache_size': len(self.response_cache),
                'openai_available': bool(self.ai_config.openai_api_key),
                'anthropic_available': bool(self.ai_config.anthropic_api_key),
                'default_model': self.ai_config.default_model
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}


__all__ = ["AIService"]