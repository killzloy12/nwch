#!/usr/bin/env python3
"""
⚙️ CONFIGURATION v3.0 - ГРУБЫЙ СТИЛЬ
🔧 Конфигурация с разрешенными чатами

НОВОЕ:
• Список разрешенных чатов
• Жесткие ограничения доступа
"""

import os
import logging
from pathlib import Path
from typing import List
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class BotConfig:
    """🤖 Конфигурация бота"""
    token: str = ""
    admin_ids: List[int] = field(default_factory=list)
    allowed_chat_ids: List[int] = field(default_factory=list)  # НОВОЕ: разрешенные чаты
    random_reply_chance: float = 0.01  # Минимум
    debug: bool = False
    smart_responses: bool = True
    mention_responses: bool = True
    reply_responses: bool = True


@dataclass
class DatabaseConfig:
    """💾 Конфигурация базы данных"""
    path: str = "data/bot.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    max_backups: int = 7
    wal_mode: bool = True


@dataclass
class AIConfig:
    """🧠 Конфигурация AI"""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    default_model: str = "gpt-4o-mini"
    daily_limit: int = 1000
    user_limit: int = 50
    temperature: float = 0.3  # Меньше креативности, больше четкости
    max_tokens: int = 1024    # Короткие ответы
    context_memory: bool = True
    adaptive_responses: bool = True


@dataclass
class CryptoConfig:
    """₿ Конфигурация криптовалют"""
    enabled: bool = True
    coingecko_api_key: str = ""
    cache_ttl_seconds: int = 300
    default_vs_currency: str = "usd"
    trending_limit: int = 5
    price_alerts: bool = False


@dataclass
class ModerationConfig:
    """🛡️ Конфигурация модерации"""
    enabled: bool = True
    auto_moderation: bool = True
    toxicity_threshold: float = 0.7  # Строже
    flood_threshold: int = 3         # Строже
    max_warnings: int = 2            # Меньше предупреждений
    ban_duration_hours: int = 24
    log_actions: bool = True
    delete_spam: bool = True
    ban_for_excessive_warnings: bool = True
    mute_duration_minutes: int = 60  # Дольше мут
    admin_immunity: bool = True


@dataclass
class AnalyticsConfig:
    """📊 Конфигурация аналитики"""
    enabled: bool = True
    track_messages: bool = True
    track_activity: bool = True
    retention_days: int = 365
    detailed_stats: bool = True
    behavior_analysis: bool = True
    export_enabled: bool = True


@dataclass
class TriggersConfig:
    """⚡ Конфигурация системы триггеров"""
    enabled: bool = True
    max_triggers_per_user: int = 5    # Меньше для обычных юзеров
    max_triggers_per_admin: int = 100
    allow_regex: bool = True
    allow_global_triggers: bool = False  # Отключено для жесткого контроля
    cooldown_seconds: int = 2
    max_response_length: int = 500


@dataclass
class PermissionsConfig:
    """🔒 Конфигурация разрешений"""
    enabled: bool = True
    use_whitelist: bool = True    # ВКЛЮЧЕНО: только разрешенные чаты
    use_blacklist: bool = True
    strict_mode: bool = True      # ЖЕСТКИЙ РЕЖИМ
    admin_override: bool = True
    log_access_attempts: bool = True


@dataclass
class SmartResponsesConfig:
    """🧠 Конфигурация умных ответов"""
    enabled: bool = True
    mention_detection: bool = True
    reply_detection: bool = True
    keyword_detection: bool = True
    question_detection: bool = True
    min_message_length: int = 3
    response_delay_seconds: float = 0.5  # Быстрее


@dataclass
class LoggingConfig:
    """📝 Конфигурация логирования"""
    level: str = "INFO"
    file_path: str = "data/logs/bot.log"
    max_file_size_mb: int = 10
    backup_count: int = 5
    log_user_messages: bool = False
    log_ai_requests: bool = True
    log_moderation_actions: bool = True
    log_trigger_activations: bool = True
    log_chat_access: bool = True  # НОВОЕ: логирование доступа к чатам


@dataclass
class Config:
    """⚙️ Главная конфигурация v3.0"""
    bot: BotConfig = field(default_factory=BotConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    crypto: CryptoConfig = field(default_factory=CryptoConfig)
    moderation: ModerationConfig = field(default_factory=ModerationConfig)
    analytics: AnalyticsConfig = field(default_factory=AnalyticsConfig)
    triggers: TriggersConfig = field(default_factory=TriggersConfig)
    permissions: PermissionsConfig = field(default_factory=PermissionsConfig)
    smart_responses: SmartResponsesConfig = field(default_factory=SmartResponsesConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


def load_config() -> Config:
    """📥 Загрузка конфигурации из переменных окружения"""
    
    config = Config()
    
    # =================== BOT CONFIG ===================
    config.bot.token = os.getenv("BOT_TOKEN", "")
    
    # Парсим admin_ids
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if admin_ids_str:
        try:
            config.bot.admin_ids = [
                int(admin_id.strip()) 
                for admin_id in admin_ids_str.split(",") 
                if admin_id.strip().isdigit()
            ]
        except ValueError:
            logger.warning("❌ Не удалось разобрать ADMIN_IDS")
    
    # НОВОЕ: Парсим allowed_chat_ids
    allowed_chats_str = os.getenv("ALLOWED_CHAT_IDS", "")
    if allowed_chats_str:
        try:
            config.bot.allowed_chat_ids = [
                int(chat_id.strip()) 
                for chat_id in allowed_chats_str.split(",") 
                if chat_id.strip().lstrip('-').isdigit()  # Учитываем отрицательные ID
            ]
        except ValueError:
            logger.warning("❌ Не удалось разобрать ALLOWED_CHAT_IDS")
    
    config.bot.random_reply_chance = float(os.getenv("RANDOM_REPLY_CHANCE", "0.01"))
    config.bot.debug = os.getenv("DEBUG", "false").lower() == "true"
    config.bot.smart_responses = os.getenv("SMART_RESPONSES", "true").lower() == "true"
    config.bot.mention_responses = os.getenv("MENTION_RESPONSES", "true").lower() == "true"
    config.bot.reply_responses = os.getenv("REPLY_RESPONSES", "true").lower() == "true"
    
    # =================== DATABASE CONFIG ===================
    config.database.path = os.getenv("DATABASE_PATH", "data/bot.db")
    config.database.backup_enabled = os.getenv("DB_BACKUP_ENABLED", "true").lower() == "true"
    config.database.wal_mode = os.getenv("DB_WAL_MODE", "true").lower() == "true"
    
    # =================== AI CONFIG ===================
    config.ai.openai_api_key = os.getenv("OPENAI_API_KEY", "")
    config.ai.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
    config.ai.default_model = os.getenv("AI_DEFAULT_MODEL", "gpt-4o-mini")
    config.ai.daily_limit = int(os.getenv("AI_DAILY_LIMIT", "1000"))
    config.ai.user_limit = int(os.getenv("AI_USER_LIMIT", "50"))
    config.ai.temperature = float(os.getenv("AI_TEMPERATURE", "0.3"))
    config.ai.max_tokens = int(os.getenv("AI_MAX_TOKENS", "1024"))
    config.ai.context_memory = os.getenv("AI_CONTEXT_MEMORY", "true").lower() == "true"
    config.ai.adaptive_responses = os.getenv("AI_ADAPTIVE_RESPONSES", "true").lower() == "true"
    
    # =================== ОСТАЛЬНЫЕ НАСТРОЙКИ ===================
    config.crypto.enabled = os.getenv("CRYPTO_ENABLED", "true").lower() == "true"
    config.crypto.coingecko_api_key = os.getenv("COINGECKO_API_KEY", "")
    config.crypto.cache_ttl_seconds = int(os.getenv("CRYPTO_CACHE_TTL", "300"))
    
    config.moderation.enabled = os.getenv("MODERATION_ENABLED", "true").lower() == "true"
    config.moderation.auto_moderation = os.getenv("AUTO_MODERATION", "true").lower() == "true"
    config.moderation.toxicity_threshold = float(os.getenv("TOXICITY_THRESHOLD", "0.7"))
    config.moderation.flood_threshold = int(os.getenv("FLOOD_THRESHOLD", "3"))
    config.moderation.max_warnings = int(os.getenv("MAX_WARNINGS", "2"))
    
    config.permissions.enabled = os.getenv("PERMISSIONS_ENABLED", "true").lower() == "true"
    config.permissions.use_whitelist = os.getenv("USE_WHITELIST", "true").lower() == "true"
    config.permissions.strict_mode = os.getenv("STRICT_MODE", "true").lower() == "true"
    
    # Создаем необходимые директории
    directories = [
        Path(config.database.path).parent,
        Path(config.logging.file_path).parent,
        Path("data/charts"),
        Path("data/exports"), 
        Path("data/backups"),
        Path("data/triggers"),
        Path("data/moderation")
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Выводим информацию о разрешенных чатах
    if config.bot.allowed_chat_ids:
        logger.info(f"🔒 РАЗРЕШЕННЫЕ ЧАТЫ: {config.bot.allowed_chat_ids}")
        print(f"💀 БОТ РАБОТАЕТ ТОЛЬКО В ЧАТАХ: {config.bot.allowed_chat_ids}")
    else:
        logger.warning("⚠️ НЕТ РАЗРЕШЕННЫХ ЧАТОВ - настройте ALLOWED_CHAT_IDS")
        print("⚠️ ВНИМАНИЕ: НЕ УКАЗАНЫ РАЗРЕШЕННЫЕ ЧАТЫ")
    
    if config.bot.admin_ids:
        logger.info(f"👑 АДМИНЫ: {config.bot.admin_ids}")
        print(f"👑 АДМИНЫ БОТА: {config.bot.admin_ids}")
    else:
        logger.warning("⚠️ НЕТ АДМИНОВ - некоторые функции будут недоступны")
    
    logger.info("⚙️ Конфигурация v3.0 загружена (ГРУБЫЙ РЕЖИМ)")
    
    return config


def create_example_env() -> str:
    """📝 Создание примера .env файла для грубого бота"""
    
    return """# Enhanced Telegram Bot v3.0 - Грубый режим
# ============================================

# ОБЯЗАТЕЛЬНЫЕ НАСТРОЙКИ
BOT_TOKEN=your_bot_token_from_BotFather
ADMIN_IDS=your_telegram_id,another_admin_id

# РАЗРЕШЕННЫЕ ЧАТЫ (НОВОЕ!)
ALLOWED_CHAT_IDS=-1001234567890,-1001234567891,1093943977

# AI СЕРВИСЫ
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
AI_DEFAULT_MODEL=gpt-4o-mini
AI_TEMPERATURE=0.3
AI_MAX_TOKENS=1024

# ГРУБЫЕ НАСТРОЙКИ
RANDOM_REPLY_CHANCE=0.01
STRICT_MODE=true
USE_WHITELIST=true

# МОДЕРАЦИЯ (ЖЕСТЧЕ)
AUTO_MODERATION=true
TOXICITY_THRESHOLD=0.7
FLOOD_THRESHOLD=3
MAX_WARNINGS=2

# ТРИГГЕРЫ (ОГРАНИЧЕННО)
TRIGGERS_ENABLED=true
MAX_TRIGGERS_PER_USER=5

# ЛОГИРОВАНИЕ
LOG_LEVEL=INFO
LOG_CHAT_ACCESS=true
"""


if __name__ == "__main__":
    config = load_config()
    
    # Создаем пример .env файла
    env_example = create_example_env()
    with open(".env.example", "w", encoding="utf-8") as f:
        f.write(env_example)
    
    print("\n📝 Создан .env.example с настройками грубого бота")
    print("\n💀 НАСТРОЙТЕ ALLOWED_CHAT_IDS В .env ФАЙЛЕ!")