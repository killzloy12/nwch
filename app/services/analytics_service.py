#!/usr/bin/env python3
"""
📊 ANALYTICS SERVICE v2.0
📈 Продвинутый сервис аналитики и метрик

Анализ поведения пользователей, статистика использования и инсайты
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class AnalyticsService:
    """📊 Сервис аналитики"""
    
    def __init__(self, db_service):
        self.db = db_service
        
        # Кэш метрик
        self.metrics_cache = {}
        self.cache_ttl = {}
        
        # Конфигурация аналитики
        self.config = {
            'cache_duration_minutes': 15,
            'top_users_limit': 10,
            'activity_days_range': 30,
            'insights_limit': 5
        }
        
        logger.info("📊 Analytics Service инициализирован")
    
    async def track_user_activity(self, user_id: int, chat_id: int, 
                                activity_type: str, metadata: Dict = None) -> bool:
        """📋 Отслеживание активности пользователя"""
        
        try:
            # Записываем событие в базу данных
            success = await self.db.track_event(
                user_id, chat_id, activity_type, metadata
            )
            
            if success:
                # Очищаем кэш для этого пользователя
                self._invalidate_user_cache(user_id)
                
                logger.debug(f"📊 Отслежена активность: {activity_type} для пользователя {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка отслеживания активности: {e}")
            return False
    
    async def get_user_analytics(self, user_id: int) -> Dict[str, Any]:
        """👤 Получение аналитики пользователя"""
        
        try:
            # Проверяем кэш
            cache_key = f"user_analytics_{user_id}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Получаем базовую статистику
            user_stats = await self.db.get_user_stats(user_id)
            
            # Анализируем активность
            activity_analysis = await self._analyze_user_activity(user_id)
            
            # Генерируем инсайты
            insights = await self._generate_user_insights(user_id, user_stats, activity_analysis)
            
            analytics = {
                'user_id': user_id,
                'basic_stats': user_stats.get('base_stats', {}),
                'activity_analysis': activity_analysis,
                'insights': insights,
                'generated_at': datetime.now().isoformat()
            }
            
            # Сохраняем в кэш
            self._save_to_cache(cache_key, analytics)
            
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения аналитики пользователя: {e}")
            return {'error': str(e)}
    
    async def _analyze_user_activity(self, user_id: int) -> Dict[str, Any]:
        """🔍 Анализ активности пользователя"""
        
        try:
            # В реальной реализации это был бы сложный анализ событий из БД
            # Для демонстрации возвращаем структурированные данные
            
            analysis = {
                'activity_level': 'moderate',
                'most_active_time': 'evening',
                'communication_frequency': 'regular',
                'engagement_score': 0.75,
                'preferred_features': ['basic_chat', 'commands'],
                'activity_trend': 'stable'
            }
            
            # Определяем уровень активности
            message_count = 10  # Заглушка - в реальности из БД
            
            if message_count >= 100:
                analysis['activity_level'] = 'high'
                analysis['engagement_score'] = 0.9
            elif message_count >= 50:
                analysis['activity_level'] = 'moderate'
                analysis['engagement_score'] = 0.7
            elif message_count >= 10:
                analysis['activity_level'] = 'low'
                analysis['engagement_score'] = 0.5
            else:
                analysis['activity_level'] = 'minimal'
                analysis['engagement_score'] = 0.3
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа активности: {e}")
            return {'activity_level': 'unknown', 'engagement_score': 0.5}
    
    async def _generate_user_insights(self, user_id: int, stats: Dict, 
                                    analysis: Dict) -> List[str]:
        """💡 Генерация инсайтов для пользователя"""
        
        try:
            insights = []
            
            activity_level = analysis.get('activity_level', 'unknown')
            engagement_score = analysis.get('engagement_score', 0.5)
            message_count = stats.get('base_stats', {}).get('message_count', 0)
            
            # Инсайты по активности
            if activity_level == 'high':
                insights.append("🔥 Вы очень активный пользователь! Продолжайте в том же духе.")
            elif activity_level == 'moderate':
                insights.append("👍 У вас стабильная активность в боте.")
            elif activity_level == 'low':
                insights.append("📈 Попробуйте изучить больше возможностей бота!")
            
            # Инсайты по вовлеченности
            if engagement_score >= 0.8:
                insights.append("⭐ Высокий уровень вовлеченности - вы знаете как пользоваться ботом!")
            elif engagement_score >= 0.6:
                insights.append("👌 Хороший уровень взаимодействия с ботом.")
            else:
                insights.append("💡 Есть возможности для улучшения взаимодействия с ботом.")
            
            # Инсайты по сообщениям
            if message_count > 0:
                avg_length = stats.get('base_stats', {}).get('avg_message_length', 0)
                if avg_length > 50:
                    insights.append("📝 Вы пишете подробные сообщения - это помогает боту лучше понимать вас.")
                elif avg_length > 20:
                    insights.append("✍️ Оптимальная длина сообщений для эффективного общения.")
                else:
                    insights.append("💬 Краткие сообщения - иногда полезно добавить больше деталей.")
            
            # Рекомендации
            preferred_features = analysis.get('preferred_features', [])
            if 'ai_chat' not in preferred_features:
                insights.append("🤖 Попробуйте команду /ai для умного общения!")
            
            if 'crypto' not in preferred_features:
                insights.append("₿ Используйте /crypto для отслеживания криптовалют!")
            
            return insights[:self.config['insights_limit']]
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации инсайтов: {e}")
            return ["💡 Продолжайте использовать бота для получения персональных рекомендаций!"]
    
    async def get_global_analytics(self) -> Dict[str, Any]:
        """🌍 Глобальная аналитика бота"""
        
        try:
            cache_key = "global_analytics"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # В реальной реализации это были бы запросы к БД
            global_stats = {
                'total_users': 150,
                'active_users_today': 25,
                'total_messages': 5420,
                'messages_today': 180,
                'top_commands': [
                    {'command': '/start', 'usage': 120},
                    {'command': '/help', 'usage': 85},
                    {'command': '/ai', 'usage': 60},
                    {'command': '/crypto', 'usage': 45},
                    {'command': '/stats', 'usage': 30}
                ],
                'user_engagement': {
                    'high': 20,
                    'moderate': 65,
                    'low': 40,
                    'minimal': 25
                },
                'growth_metrics': {
                    'new_users_today': 5,
                    'returning_users': 20,
                    'user_retention_rate': 0.68
                },
                'feature_usage': {
                    'ai_service': 180,
                    'crypto_service': 120,
                    'analytics': 50,
                    'basic_commands': 380
                }
            }
            
            # Сохраняем в кэш
            self._save_to_cache(cache_key, global_stats)
            
            return global_stats
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения глобальной аналитики: {e}")
            return {'error': str(e)}
    
    async def get_chat_analytics(self, chat_id: int) -> Dict[str, Any]:
        """💬 Аналитика чата"""
        
        try:
            cache_key = f"chat_analytics_{chat_id}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # В реальной реализации это были бы запросы к БД
            chat_stats = {
                'chat_id': chat_id,
                'total_messages': 420,
                'unique_users': 15,
                'messages_today': 35,
                'most_active_users': [
                    {'user_id': 123, 'message_count': 85, 'name': 'Пользователь1'},
                    {'user_id': 456, 'message_count': 72, 'name': 'Пользователь2'},
                    {'user_id': 789, 'message_count': 58, 'name': 'Пользователь3'}
                ],
                'activity_by_hour': self._generate_hourly_activity(),
                'top_words': [
                    'привет', 'спасибо', 'бот', 'помощь', 'хорошо'
                ],
                'average_message_length': 25.5,
                'chat_health_score': 0.82
            }
            
            self._save_to_cache(cache_key, chat_stats)
            
            return chat_stats
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения аналитики чата: {e}")
            return {'error': str(e)}
    
    def _generate_hourly_activity(self) -> Dict[int, int]:
        """⏰ Генерация почасовой активности (заглушка)"""
        
        import random
        
        hourly_activity = {}
        for hour in range(24):
            # Моделируем реальную активность
            if 9 <= hour <= 12:  # Утренний пик
                activity = random.randint(15, 25)
            elif 14 <= hour <= 18:  # Дневной пик
                activity = random.randint(20, 35)
            elif 19 <= hour <= 23:  # Вечерний пик
                activity = random.randint(25, 40)
            else:  # Ночь
                activity = random.randint(2, 8)
            
            hourly_activity[hour] = activity
        
        return hourly_activity
    
    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """📋 Получение данных из кэша"""
        
        try:
            if key in self.metrics_cache:
                cache_time = self.cache_ttl.get(key)
                if cache_time and datetime.now() < cache_time:
                    return self.metrics_cache[key]
                else:
                    # Кэш истек
                    del self.metrics_cache[key]
                    if key in self.cache_ttl:
                        del self.cache_ttl[key]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка чтения кэша: {e}")
            return None
    
    def _save_to_cache(self, key: str, data: Dict):
        """💾 Сохранение данных в кэш"""
        
        try:
            self.metrics_cache[key] = data
            self.cache_ttl[key] = datetime.now() + timedelta(
                minutes=self.config['cache_duration_minutes']
            )
            
            # Ограничиваем размер кэша
            if len(self.metrics_cache) > 100:
                oldest_key = min(self.cache_ttl.keys(), key=lambda k: self.cache_ttl[k])
                del self.metrics_cache[oldest_key]
                del self.cache_ttl[oldest_key]
                
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в кэш: {e}")
    
    def _invalidate_user_cache(self, user_id: int):
        """🗑️ Очистка кэша пользователя"""
        
        try:
            keys_to_remove = [
                key for key in self.metrics_cache.keys() 
                if f"user_analytics_{user_id}" in key
            ]
            
            for key in keys_to_remove:
                if key in self.metrics_cache:
                    del self.metrics_cache[key]
                if key in self.cache_ttl:
                    del self.cache_ttl[key]
                    
        except Exception as e:
            logger.error(f"❌ Ошибка очистки кэша: {e}")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """📊 Статистика сервиса аналитики"""
        
        return {
            'cache_size': len(self.metrics_cache),
            'cached_items': list(self.metrics_cache.keys()),
            'cache_hit_ratio': 0.75,  # В реальной реализации это был бы реальный расчет
            'service_status': 'active'
        }


__all__ = ["AnalyticsService"]