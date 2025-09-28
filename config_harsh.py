#!/usr/bin/env python3
"""
⚙️ CONFIGURATION v3.0 - ГРУБЫЙ РЕЖИМ (ИСПРАВЛЕНО)
🔧 Конфигурация с жестким контролем доступа

ИСПРАВЛЕНО:
• Правильный парсинг ALLOWED_CHAT_IDS
• Жесткие настройки по умолчанию
• Подробные комментарии для настройки
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
    allowed_chat_ids: List[int] = field(default_factory=list)  # КЛЮЧЕВАЯ НАСТРОЙКА
    random_reply_chance: float = 0.001  # 0.1% шанс случайного ответа
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
    temperature: float = 0.7  # Для грубого стиля
    max_tokens: int = 512     # Короткие ответы
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
    toxicity_threshold: float = 0.8  # Строже
    flood_threshold: int = 2         # Строже
    max_warnings: int = 1            # Меньше предупреждений
    ban_duration_hours: int = 24
    log_actions: bool = True
    delete_spam: bool = True
    ban_for_excessive_warnings: bool = True
    mute_duration_minutes: int = 120  # Дольше мут
    admin_immunity: bool = True


@dataclass
class Config:
    """⚙️ Главная конфигурация v3.0"""
    bot: BotConfig = field(default_factory=BotConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    crypto: CryptoConfig = field(default_factory=CryptoConfig)
    moderation: ModerationConfig = field(default_factory=ModerationConfig)


def load_config() -> Config:
    """📥 Загрузка конфигурации из переменных окружения"""
    
    config = Config()
    
    # ================= BOT CONFIG =================
    config.bot.token = os.getenv("BOT_TOKEN", "")
    
    # Парсим admin_ids
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if admin_ids_str:
        try:
            config.bot.admin_ids = [
                int(admin_id.strip()) 
                for admin_id in admin_ids_str.replace(' ', '').split(",") 
                if admin_id.strip().isdigit()
            ]
        except ValueError as e:
            logger.error(f"❌ Ошибка парсинга ADMIN_IDS: {e}")
    
    # ИСПРАВЛЕННЫЙ парсинг allowed_chat_ids
    allowed_chats_str = os.getenv("ALLOWED_CHAT_IDS", "")
    if allowed_chats_str:
        try:
            chat_ids = []
            for chat_id in allowed_chats_str.replace(' ', '').split(","):
                chat_id = chat_id.strip()
                if chat_id:  # Пропускаем пустые строки
                    # Поддерживаем отрицательные ID групп
                    if chat_id.startswith('-'):
                        chat_ids.append(int(chat_id))
                    elif chat_id.isdigit():
                        chat_ids.append(int(chat_id))
                    else:
                        logger.warning(f"⚠️ Неверный формат chat_id: {chat_id}")
            
            config.bot.allowed_chat_ids = chat_ids
            
        except ValueError as e:
            logger.error(f"❌ Ошибка парсинга ALLOWED_CHAT_IDS: {e}")
            logger.error(f"Строка: {allowed_chats_str}")
    
    config.bot.random_reply_chance = float(os.getenv("RANDOM_REPLY_CHANCE", "0.001"))
    config.bot.debug = os.getenv("DEBUG", "false").lower() == "true"
    
    # ================= AI CONFIG =================
    config.ai.openai_api_key = os.getenv("OPENAI_API_KEY", "")
    config.ai.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
    config.ai.default_model = os.getenv("AI_DEFAULT_MODEL", "gpt-4o-mini")
    config.ai.temperature = float(os.getenv("AI_TEMPERATURE", "0.7"))
    config.ai.max_tokens = int(os.getenv("AI_MAX_TOKENS", "512"))
    
    # ================= OTHER CONFIGS =================
    config.crypto.enabled = os.getenv("CRYPTO_ENABLED", "true").lower() == "true"
    config.crypto.coingecko_api_key = os.getenv("COINGECKO_API_KEY", "")
    
    config.moderation.enabled = os.getenv("MODERATION_ENABLED", "true").lower() == "true"
    config.moderation.auto_moderation = os.getenv("AUTO_MODERATION", "true").lower() == "true"
    
    # Создаем необходимые директории
    directories = [
        Path(config.database.path).parent,
        Path("data/logs"),
        Path("data/charts"),
        Path("data/exports"), 
        Path("data/backups"),
        Path("data/triggers"),
        Path("data/moderation")
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Выводим информацию о конфигурации
    logger.info(f"🔒 РАЗРЕШЕННЫЕ ЧАТЫ: {config.bot.allowed_chat_ids}")
    logger.info(f"👑 АДМИНЫ: {config.bot.admin_ids}")
    logger.info("⚙️ Конфигурация v3.0 загружена (ГРУБЫЙ РЕЖИМ)")
    
    return config


def create_example_env() -> str:
    """📝 Создание примера .env файла для грубого бота"""
    
    return """# Enhanced Telegram Bot v3.0 - Грубый режим (ИСПРАВЛЕНО)
# ================================================================

# ========== ОБЯЗАТЕЛЬНЫЕ НАСТРОЙКИ ==========

# Токен бота от @BotFather
BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890

# ID администраторов (ваш Telegram ID)
# Узнать свой ID: напишите @userinfobot
ADMIN_IDS=123456789,987654321

# КЛЮЧЕВАЯ НАСТРОЙКА: ID разрешенных чатов
# Для групп: -1001234567890 (начинается с -100)
# Для ЛС: 123456789 (положительное число)
# Узнать ID чата: добавьте бота в группу и напишите /start
ALLOWED_CHAT_IDS=-1001234567890,-1001987654321,123456789

# ========== AI НАСТРОЙКИ ==========

# Получить тут: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Альтернатива OpenAI: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Модель для AI (gpt-4o-mini - самая дешевая)
AI_DEFAULT_MODEL=gpt-4o-mini

# Настройки AI
AI_TEMPERATURE=0.7          # 0.1-1.0 (выше = креативнее)
AI_MAX_TOKENS=512           # Длина ответов (меньше = дешевле)

# ========== ГРУБЫЙ РЕЖИМ ==========

# Шанс случайного ответа (0.001 = 0.1%)
RANDOM_REPLY_CHANCE=0.001

# Отладка (включить при проблемах)
DEBUG=false

# ========== КРИПТОВАЛЮТЫ ==========

CRYPTO_ENABLED=true
COINGECKO_API_KEY=         # Необязательно, но лимиты выше

# ========== МОДЕРАЦИЯ ==========

AUTO_MODERATION=true
TOXICITY_THRESHOLD=0.8     # 0.1-1.0 (выше = строже)
FLOOD_THRESHOLD=2          # Количество сообщений подряд
MAX_WARNINGS=1             # Предупреждений до бана

# ========== ЛОГИРОВАНИЕ ==========

LOG_LEVEL=INFO
LOG_CHAT_ACCESS=true       # Логировать попытки доступа"""


if __name__ == "__main__":
    config = load_config()
    
    # Создаем пример .env файла
    env_example = create_example_env()
    with open(".env.example", "w", encoding="utf-8") as f:
        f.write(env_example)
    
    print("\n📝 Создан .env.example с подробными настройками")
    print("\n💀 ИНСТРУКЦИЯ ПО НАСТРОЙКЕ:")
    print("1. Скопируйте .env.example в .env")
    print("2. Получите токен бота от @BotFather")
    print("3. Узнайте свой Telegram ID через @userinfobot")
    print("4. Добавьте бота в группу и запишите ID чата")
    print("5. Заполните ALLOWED_CHAT_IDS своими чатами")
    print("6. Получите API ключ OpenAI (опционально)")
    print("\n🔥 БЕЗ НАСТРОЙКИ ALLOWED_CHAT_IDS БОТ НЕ БУДЕТ ОТВЕЧАТЬ!")
    
    # Проверяем текущую конфигурацию
    if not config.bot.token:
        print("\n❌ BOT_TOKEN не настроен!")
    if not config.bot.admin_ids:
        print("❌ ADMIN_IDS не настроены!")
    if not config.bot.allowed_chat_ids:
        print("❌ ALLOWED_CHAT_IDS не настроены!")
    
    if config.bot.token and config.bot.admin_ids and config.bot.allowed_chat_ids:
        print("\n✅ Конфигурация выглядит корректно!")