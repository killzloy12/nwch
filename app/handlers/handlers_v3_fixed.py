#!/usr/bin/env python3
"""
🚀 PERFECT HANDLERS v9.0 - С УВЕДОМЛЕНИЯМИ О КАРМЕ
"""

import logging
import asyncio
import random
import html
import json
import os
from datetime import datetime
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

logger = logging.getLogger(__name__)

# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
DEFAULT_TRIGGER_WORDS = ["бот", "bot", "робот", "помощник", "assistant", "эй", "слушай", "макс"]
CUSTOM_TRIGGER_WORDS = {}  # {chat_id: [список_слов]}
TRIGGER_WORDS_FILE = "data/trigger_words.json"
chat_stats = {}
bot_info = None

# ПЕРСОНАЖИ И КАРМА
GLOBAL_PERSONAS = {}
PERSONAS_FILE = "data/personas.json"
GLOBAL_KARMA = {}
KARMA_FILE = "data/karma.json"
USER_LAST_MESSAGES = {}

# СЛОВА ДЛЯ КАРМЫ
POSITIVE_WORDS = ["спасибо", "thanks", "круто", "отлично", "супер", "молодец", "хорошо", "лайк", "плюс", "+1"]
NEGATIVE_WORDS = ["дурак", "идиот", "тупой", "хуйня", "говно", "дерьмо", "минус", "плохо", "херня"]
SPAM_WORDS = ["реклама", "продам", "куплю", "заработок", "бизнес"]
HELP_WORDS = ["помог", "помогли", "объяснил", "научил", "подсказал"]

def load_data():
    """Загружает данные"""
    global GLOBAL_PERSONAS, GLOBAL_KARMA
    
    try:
        if os.path.exists(PERSONAS_FILE):
            with open(PERSONAS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                GLOBAL_PERSONAS = {int(k): v for k, v in data.items()}
                logger.info(f"✅ Загружено персонажей: {len(GLOBAL_PERSONAS)}")
        
        if os.path.exists(KARMA_FILE):
            with open(KARMA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                GLOBAL_KARMA = {}
                for key, value in data.items():
                    user_id, chat_id = key.split('_')
                    GLOBAL_KARMA[(int(user_id), int(chat_id))] = value
                logger.info(f"✅ Загружено кармы: {len(GLOBAL_KARMA)}")
        
        # Загружаем слова призыва
        load_trigger_words()
                
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки: {e}")
        GLOBAL_PERSONAS = {}
        GLOBAL_KARMA = {}

def save_data():
    """Сохраняет данные"""
    try:
        Path("data").mkdir(exist_ok=True)
        
        # Персонажи
        personas_data = {str(k): v for k, v in GLOBAL_PERSONAS.items()}
        with open(PERSONAS_FILE, 'w', encoding='utf-8') as f:
            json.dump(personas_data, f, ensure_ascii=False, indent=2, default=str)
        
        # Карма
        karma_data = {}
        for (user_id, chat_id), value in GLOBAL_KARMA.items():
            key = f"{user_id}_{chat_id}"
            karma_data[key] = value
        with open(KARMA_FILE, 'w', encoding='utf-8') as f:
            json.dump(karma_data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения: {e}")


def load_trigger_words():
    """Загружает пользовательские слова призыва"""
    global CUSTOM_TRIGGER_WORDS
    
    try:
        if os.path.exists(TRIGGER_WORDS_FILE):
            with open(TRIGGER_WORDS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                CUSTOM_TRIGGER_WORDS = {int(k): v for k, v in data.items()}
                logger.info(f"✅ Загружено пользовательских слов призыва: {len(CUSTOM_TRIGGER_WORDS)}")
        else:
            CUSTOM_TRIGGER_WORDS = {}
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки слов призыва: {e}")
        CUSTOM_TRIGGER_WORDS = {}

def save_trigger_words():
    """Сохраняет пользовательские слова призыва"""
    try:
        Path("data").mkdir(exist_ok=True)
        
        # Преобразуем ключи в строки для JSON
        data_to_save = {str(k): v for k, v in CUSTOM_TRIGGER_WORDS.items()}
        
        with open(TRIGGER_WORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Сохранено пользовательских слов призыва: {len(CUSTOM_TRIGGER_WORDS)}")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения слов призыва: {e}")

def get_trigger_words(chat_id):
    """Получает слова призыва для конкретного чата"""
    if chat_id in CUSTOM_TRIGGER_WORDS:
        return CUSTOM_TRIGGER_WORDS[chat_id]
    return DEFAULT_TRIGGER_WORDS

def add_trigger_word(chat_id, word):
    """Добавляет слово призыва для чата"""
    if chat_id not in CUSTOM_TRIGGER_WORDS:
        CUSTOM_TRIGGER_WORDS[chat_id] = DEFAULT_TRIGGER_WORDS.copy()
    
    # Ограничение на количество слов
    if len(CUSTOM_TRIGGER_WORDS[chat_id]) >= 50:
        return "limit"
    
    word_lower = word.lower().strip()
    if word_lower and word_lower not in CUSTOM_TRIGGER_WORDS[chat_id]:
        CUSTOM_TRIGGER_WORDS[chat_id].append(word_lower)
        save_trigger_words()
        return True
    return False

def remove_trigger_word(chat_id, word):
    """Удаляет слово призыва для чата"""
    if chat_id not in CUSTOM_TRIGGER_WORDS:
        return False
    
    word_lower = word.lower().strip()
    if word_lower in CUSTOM_TRIGGER_WORDS[chat_id]:
        CUSTOM_TRIGGER_WORDS[chat_id].remove(word_lower)
        save_trigger_words()
        return True
    return False

def reset_trigger_words(chat_id):
    """Сбрасывает слова призыва к стандартным"""
    if chat_id in CUSTOM_TRIGGER_WORDS:
        del CUSTOM_TRIGGER_WORDS[chat_id]
        save_trigger_words()
        return True
    return False

async def send_karma_notification(bot, user_id, from_user_name, amount, new_karma, reason, level_up_info=None):
    """Отправляет уведомление об изменении кармы"""
    try:
        # Формируем уведомление
        if amount > 0:
            emoji = "⬆️"
            action = "увеличил"
            color = "🟢"
        else:
            emoji = "⬇️"
            action = "уменьшил"
            color = "🔴"
        
        notification_text = (
            f"{emoji} **ИЗМЕНЕНИЕ КАРМЫ**\n\n"
            f"👤 **{from_user_name}** {action} вашу карму\n"
            f"{color} **Изменение:** {amount:+d}\n"
            f"⚖️ **Ваша карма:** {new_karma}\n"
            f"📋 **Причина:** {reason}"
        )
        
        # Добавляем информацию о повышении уровня
        if level_up_info:
            notification_text += f"\n\n🎉 **ПОВЫШЕНИЕ УРОВНЯ!**\n{level_up_info['emoji']} **Новый уровень:** {level_up_info['name']}"
        
        # Отправляем уведомление
        await bot.send_message(
            chat_id=user_id,
            text=notification_text,
            parse_mode="Markdown"
        )
        
        logger.info(f"✅ Уведомление о карме отправлено {user_id}: {amount:+d}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Не удалось отправить уведомление о карме {user_id}: {e}")
        return False

def analyze_karma(text, user_id):
    """Анализ кармы"""
    if not text:
        return {"karma_change": 0, "reason": "пустое"}
    
    text_lower = text.lower()
    karma_change = random.randint(1, 2)
    reasons = [f"активность +{karma_change}"]
    
    # Позитив
    positive_count = sum(1 for word in POSITIVE_WORDS if word in text_lower)
    if positive_count > 0:
        bonus = min(positive_count * 3, 10)
        karma_change += bonus
        reasons.append(f"позитив +{bonus}")
    
    # Негатив
    negative_count = sum(1 for word in NEGATIVE_WORDS if word in text_lower)
    if negative_count > 0:
        penalty = min(negative_count * 5, 15)
        karma_change -= penalty
        reasons.append(f"негатив -{penalty}")
    
    # Спам
    spam_count = sum(1 for word in SPAM_WORDS if word in text_lower)
    if spam_count > 0:
        penalty = min(spam_count * 10, 25)
        karma_change -= penalty
        reasons.append(f"спам -{penalty}")
    
    # Помощь
    help_count = sum(1 for word in HELP_WORDS if word in text_lower)
    if help_count > 0:
        bonus = min(help_count * 8, 20)
        karma_change += bonus
        reasons.append(f"помощь +{bonus}")
    
    # Качество
    if len(text) > 100:
        karma_change += 2
        reasons.append("длинный +2")
    
    if text.count('?') >= 1:
        karma_change += 1
        reasons.append("вопрос +1")
    
    # Повторы
    if user_id in USER_LAST_MESSAGES:
        if text in USER_LAST_MESSAGES[user_id]:
            karma_change -= 8
            reasons.append("повтор -8")
        USER_LAST_MESSAGES[user_id].append(text)
        if len(USER_LAST_MESSAGES[user_id]) > 5:
            USER_LAST_MESSAGES[user_id].pop(0)
    else:
        USER_LAST_MESSAGES[user_id] = [text]
    
    karma_change = max(-30, min(karma_change, 50))
    return {"karma_change": karma_change, "reason": ", ".join(reasons)}

def get_karma(user_id, chat_id):
    """Получает карму"""
    key = (user_id, chat_id)
    if key not in GLOBAL_KARMA:
        GLOBAL_KARMA[key] = {
            'karma': random.randint(10, 100),
            'level': 1,
            'messages_count': 0,
            'created_at': datetime.now().isoformat()
        }
        save_data()
    return GLOBAL_KARMA[key]

def add_karma(user_id, chat_id, amount):
    """Добавляет карму"""
    karma_data = get_karma(user_id, chat_id)
    old_level = karma_data['level']
    
    karma_data['karma'] += amount
    karma_data['messages_count'] += 1
    
    if karma_data['karma'] < 0:
        karma_data['karma'] = 0
    
    # Уровни
    if karma_data['karma'] >= 2000:
        karma_data['level'] = 20
    elif karma_data['karma'] >= 1500:
        karma_data['level'] = 15
    elif karma_data['karma'] >= 1000:
        karma_data['level'] = 10
    elif karma_data['karma'] >= 700:
        karma_data['level'] = 8
    elif karma_data['karma'] >= 500:
        karma_data['level'] = 5
    elif karma_data['karma'] >= 300:
        karma_data['level'] = 4
    elif karma_data['karma'] >= 200:
        karma_data['level'] = 3
    elif karma_data['karma'] >= 100:
        karma_data['level'] = 2
    else:
        karma_data['level'] = 1
    
    # Проверяем повышение уровня
    level_up_info = None
    if karma_data['level'] > old_level:
        logger.info(f"🎉 Повышение уровня {user_id}: {old_level} → {karma_data['level']}")
        
        level_info = {
            1: {"name": "Новичок", "emoji": "🌱"},
            2: {"name": "Знакомый", "emoji": "⭐"},
            3: {"name": "Активный", "emoji": "🔥"},
            4: {"name": "Опытный", "emoji": "🔥"},
            5: {"name": "Эксперт", "emoji": "💎"},
            8: {"name": "Гуру", "emoji": "💎"},
            10: {"name": "Мастер", "emoji": "👑"},
            15: {"name": "Звезда", "emoji": "⭐"},
            20: {"name": "Легенда", "emoji": "🏆"}
        }
        
        level_up_info = level_info.get(karma_data['level'], {"name": "Неизвестный", "emoji": "❓"})
    
    save_data()
    return karma_data, level_up_info

async def check_karma_triggers(message):
    """Проверяет специальные триггеры для кармы между пользователями"""
    try:
        if not message.text or not message.reply_to_message:
            return
        
        # Проверяем что отвечают другому пользователю
        if message.reply_to_message.from_user.id == message.from_user.id:
            return  # Не меняем карму самому себе
        
        text_lower = message.text.lower()
        target_user_id = message.reply_to_message.from_user.id
        from_user_id = message.from_user.id
        chat_id = message.chat.id
        
        # СПЕЦИАЛЬНЫЕ КОМАНДЫ КАРМЫ
        karma_commands = {
            # Позитивные
            '+1': 5, 'плюс': 5, 'лайк': 3, 'круто': 4, 'класс': 4, 
            'спасибо': 6, 'благодарю': 6, 'отлично': 5, 'супер': 4,
            'молодец': 5, 'хорошо': 3, 'браво': 4, 'респект': 5,
            
            # Негативные  
            '-1': -5, 'минус': -5, 'дизлайк': -3, 'плохо': -4,
            'херня': -6, 'фигня': -4, 'отстой': -5, 'фуфло': -4
        }
        
        karma_change = 0
        triggered_words = []
        
        for word, value in karma_commands.items():
            if word in text_lower:
                karma_change += value
                triggered_words.append(word)
        
        # Применяем изменения кармы
        if karma_change != 0 and abs(karma_change) >= 3:
            karma_data, level_up_info = add_karma(target_user_id, chat_id, karma_change)
            
            # Получаем имя пользователя, который изменил карму
            from_user_name = message.from_user.first_name or "Пользователь"
            
            # Отправляем уведомление целевому пользователю
            reason = f"от пользователя ({', '.join(triggered_words)})"
            await send_karma_notification(
                message.bot, 
                target_user_id, 
                from_user_name, 
                karma_change, 
                karma_data['karma'], 
                reason, 
                level_up_info
            )
            
            logger.info(f"⚖️ Карма изменена пользователем {from_user_id} → {target_user_id}: {karma_change:+d}")
    
    except Exception as e:
        logger.error(f"❌ Ошибка проверки триггеров кармы: {e}")

def safe_escape(text):
    """Экранирование"""
    if not text:
        return ""
    return html.escape(str(text))

def register_all_handlers(dp, modules):
    """Регистрация PERFECT обработчиков с уведомлениями кармы"""
    
    router = Router()
    global bot_info
    
    load_data()
    
    ultimate_system = modules.get('ultimate')
    is_ultimate_mode = ultimate_system is not None
    
    logger.info(f"🎯 PERFECT РЕЖИМ: {'ULTIMATE' if is_ultimate_mode else 'БАЗОВЫЙ'}")
    
    ai_service = modules.get('ai')
    logger.info(f"🔍 AI: {ai_service}")
    
    async def get_bot_info():
        global bot_info
        try:
            bot_info = await modules['bot'].get_me()
            logger.info(f"🤖 Бот: @{bot_info.username}")
        except Exception as e:
            logger.error(f"❌ Ошибка бота: {e}")
    
    asyncio.create_task(get_bot_info())
    
    async def check_access(message):
        """Проверка доступа"""
        try:
            config = modules['config']
            user_id = message.from_user.id
            chat_id = message.chat.id
            
            if user_id in config.bot.admin_ids:
                return True
                
            if not hasattr(config.bot, 'allowed_chat_ids') or not config.bot.allowed_chat_ids:
                return True
                
            return chat_id in config.bot.allowed_chat_ids
        except:
            return True
    
    async def update_stats(message):
        """Статистика и карма"""
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id
            
            if chat_id not in chat_stats:
                chat_stats[chat_id] = {
                    'messages_count': 0,
                    'unique_users': set(),
                    'last_activity': datetime.now()
                }
            
            chat_stats[chat_id]['messages_count'] += 1
            chat_stats[chat_id]['unique_users'].add(user_id)
            chat_stats[chat_id]['last_activity'] = datetime.now()
            
            # Карма от активности
            if message.text:
                analysis = analyze_karma(message.text, user_id)
                karma_change = analysis["karma_change"]
                
                if karma_change != 0:
                    karma_data, level_up_info = add_karma(user_id, chat_id, karma_change)
                    
                    if abs(karma_change) >= 5:
                        logger.info(f"⚖️ Карма {user_id}: {karma_change:+d} = {karma_data['karma']}")
            
            # Проверяем триггеры кармы между пользователями
            await check_karma_triggers(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка статистики: {e}")
    
    async def check_admin(message, feature="функция"):
        """Проверка админа"""
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply(
                f"🚫 **Доступ запрещен**\n\n"
                f"{feature.capitalize()} только для админов"
            )
            return False
        return True
    
    # КОМАНДЫ
    
    @router.message(CommandStart())
    async def start_handler(message):
        try:
            if not await check_access(message):
                return
            await update_stats(message)
            
            user_name = safe_escape(message.from_user.first_name or "друг")
            greetings = [
                f"🚀 Привет, {user_name}! Karma Edition работает!",
                f"⚡ Йо, {user_name}! Уведомления кармы активны!",
                f"🎯 Дарова, {user_name}! Готов к работе!"
            ]
            
            await message.reply(random.choice(greetings))
            logger.info(f"✅ KARMA /start: {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"❌ /start: {e}")
            await message.reply("👋 Привет!")
    
    @router.message(Command(commands=['help']))
    async def help_handler(message):
        try:
            if not await check_access(message):
                return
            await update_stats(message)
            
            is_admin = message.from_user.id in modules['config'].bot.admin_ids
            
            if is_admin:
                help_text = (
                    "🚀 **ULTIMATE BOT v9.0 - KARMA ADMIN**\n\n"
                    "👤 **Основные команды:**\n"
                    "• `/start` - приветствие\n"
                    "• `/help` - эта справка\n"
                    "• `/karma` - моя карма\n"
                    "• `/karma_help` - как влиять на карму\n\n"
                    "🎭 **Персонажи (админы):**\n"
                    "• `/be описание` - установить персонажа\n"
                    "• `/persona` - информация о персонаже\n\n"
                    "🎲 **Развлечения:**\n"
                    "• `/flip` - орел/решка\n"
                    "• `/dice` - кубик 1-6\n"
                    "• `/joke` - случайная шутка\n"
                    "• `/fact` - интересный факт\n"
                    "• `/8ball вопрос` - магический шар\n\n"
                    "₿ **Криптовалюты:**\n"
                    "• `/crypto BTC` - курс криптовалют\n\n"
                    "🔧 **Система (админы):**\n"
                    "• `/stats` - статистика\n"
                    "• `/debug` - отладочная информация\n\n"
                    "🧠 **AI отвечает на упоминания и реплаи**\n"
                    "⚖️ **Karma Edition v9.0 - уведомления о карме!**"
                )
            else:
                help_text = (
                    "🤖 **ULTIMATE BOT v9.0 - KARMA**\n\n"
                    "👤 **Основные команды:**\n"
                    "• `/start` - приветствие\n"
                    "• `/help` - эта справка\n"
                    "• `/karma` - моя карма\n"
                    "• `/karma_help` - как влиять на карму\n\n"
                    "🎲 **Развлечения:**\n"
                    "• `/flip` - орел/решка\n"
                    "• `/dice` - кубик 1-6\n"
                    "• `/joke` - случайная шутка\n"
                    "• `/fact` - интересный факт\n"
                    "• `/8ball вопрос` - магический шар\n\n"
                    "₿ **Криптовалюты:**\n"
                    "• `/crypto BTC` - курс криптовалют\n\n"
                    "🎭 **AI персонажи:**\n"
                    "Бот отвечает на упоминания и реплаи.\n"
                    "Персонажи устанавливают только админы.\n\n"
                    "⚖️ **Karma Edition v9.0 - уведомления о карме!**"
                )
            
            await message.reply(help_text)
            logger.info(f"✅ KARMA /help: {message.from_user.id} (админ: {is_admin})")
            
        except Exception as e:
            logger.error(f"❌ /help: {e}")
            await message.reply("📖 Справка недоступна")
    
    @router.message(Command(commands=['karma']))
    async def karma_handler(message):
        try:
            if not await check_access(message):
                return
            await update_stats(message)
            
            user_id = message.from_user.id
            chat_id = message.chat.id
            user_name = safe_escape(message.from_user.first_name or "Пользователь")
            
            karma_data = get_karma(user_id, chat_id)
            
            level_info = {
                1: {"name": "Новичок", "emoji": "🌱"},
                2: {"name": "Знакомый", "emoji": "⭐"},
                3: {"name": "Активный", "emoji": "🔥"},
                4: {"name": "Опытный", "emoji": "🔥"},
                5: {"name": "Эксперт", "emoji": "💎"},
                8: {"name": "Гуру", "emoji": "💎"},
                10: {"name": "Мастер", "emoji": "👑"},
                15: {"name": "Звезда", "emoji": "⭐"},
                20: {"name": "Легенда", "emoji": "🏆"}
            }
            
            level = karma_data['level']
            karma_value = karma_data['karma']
            messages_count = karma_data.get('messages_count', 0)
            
            current_level = level_info.get(level, {"name": "Неизвестный", "emoji": "❓"})
            
            text = (
                f"⚖️ **КАРМА {user_name}**\n\n"
                f"🔥 **Карма:** {karma_value}\n"
                f"{current_level['emoji']} **Уровень:** {current_level['name']} (lvl {level})\n"
                f"💬 **Сообщений:** {messages_count}\n\n"
                f"💡 **Карма растет за позитив, падает за негатив**\n"
                f"📱 **Уведомления о карме приходят в личку**"
            )
            
            await message.reply(text)
            logger.info(f"✅ KARMA /karma: {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"❌ /karma: {e}")
            await message.reply("❌ Ошибка кармы")
    
    @router.message(Command(commands=['karma_help']))
    async def karma_help_handler(message):
        try:
            if not await check_access(message):
                return
            await update_stats(message)
            
            help_text = (
                "⚖️ **КАК ВЛИЯТЬ НА КАРМУ ДРУГИХ**\n\n"
                "🎯 **Отвечайте на сообщения пользователей:**\n\n"
                "✅ **Увеличить карму (+3 до +6):**\n"
                "• `+1`, `плюс`, `лайк`\n"
                "• `спасибо`, `благодарю`\n"
                "• `круто`, `класс`, `отлично`, `супер`\n"
                "• `молодец`, `хорошо`, `браво`, `респект`\n\n"
                "❌ **Уменьшить карму (-3 до -6):**\n"
                "• `-1`, `минус`, `дизлайк`\n"
                "• `плохо`, `херня`, `фигня`\n"
                "• `отстой`, `фуфло`\n\n"
                "💡 **Как использовать:**\n"
                "1️⃣ Ответьте на сообщение пользователя\n"
                "2️⃣ Напишите одно из ключевых слов\n"
                "3️⃣ Пользователь получит уведомление в личку\n\n"
                "⚠️ **Правила:**\n"
                "• Нельзя менять карму самому себе\n"
                "• Изменения от +3 до +6 / -3 до -6\n"
                "• Уведомления приходят в личку\n"
                "• Автоматические уведомления о повышении уровня"
            )
            
            await message.reply(help_text)
            logger.info(f"✅ KARMA /karma_help: {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"❌ /karma_help: {e}")
            await message.reply("❌ Ошибка справки по карме")
    
    @router.message(Command(commands=['be']))
    async def be_handler(message):
        try:
            if not await check_access(message):
                return
            await update_stats(message)
            
            if not await check_admin(message, "установка персонажа"):
                return
            
            command_args = message.text.split(' ', 1)
            if len(command_args) < 2:
                await message.reply("🎭 **Использование:** `/be описание персонажа`")
                return
            
            description = command_args[1].strip()
            
            if len(description) < 5:
                await message.reply("❌ Описание слишком короткое")
                return
            
            chat_id = message.chat.id
            words = description.split()[:2]
            persona_name = ' '.join(words).title()
            
            GLOBAL_PERSONAS[chat_id] = {
                'name': persona_name,
                'description': description,
                'created_by': message.from_user.id,
                'created_at': datetime.now().isoformat()
            }
            
            save_data()
            
            response = (
                f"🎭 **Персонаж установлен!**\n\n"
                f"**Имя:** {safe_escape(persona_name)}\n"
                f"**Описание:** {safe_escape(description[:200])}\n\n"
                f"🎯 **Активирован навсегда для этого чата**"
            )
            
            await message.reply(response)
            logger.info(f"✅ KARMA /be: {message.from_user.id} - {persona_name}")
                
        except Exception as e:
            logger.error(f"❌ /be: {e}")
            await message.reply("❌ Ошибка установки персонажа")
    
    @router.message(Command(commands=['persona']))
    async def persona_handler(message):
        try:
            if not await check_access(message):
                return
            await update_stats(message)
            
            chat_id = message.chat.id
            
            if chat_id in GLOBAL_PERSONAS:
                persona = GLOBAL_PERSONAS[chat_id]
                
                response = (
                    f"🎭 **Активный персонаж**\n\n"
                    f"**Имя:** {safe_escape(persona['name'])}\n"
                    f"**Описание:** {safe_escape(persona['description'][:200])}\n\n"
                    f"🎯 **Статус:** ✅ Активен навсегда"
                )
                
            else:
                response = (
                    "🤷‍♂️ **Персонаж не установлен**\n\n"
                    "🎭 Используйте `/be описание`\n"
                    "👑 Только админы могут устанавливать"
                )
            
            await message.reply(response)
            logger.info(f"✅ KARMA /persona: {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"❌ /persona: {e}")
            await message.reply("❌ Ошибка получения персонажа")
    
    @router.message(Command(commands=['flip']))
    async def flip_handler(message):
        try:
            if not await check_access(message):
                return
            await update_stats(message)
            
            result = random.choice(['орел', 'решка'])
            emoji = "🦅" if result == "орел" else "👑"
            await message.reply(f"🪙 **Монета:** {emoji} **{result.upper()}!**")
            logger.info(f"✅ KARMA /flip: {message.from_user.id} - {result}")
            
        except Exception as e:
            logger.error(f"❌ /flip: {e}")
            await message.reply("🪙 Ошибка монеты")
    
    @router.message(Command(commands=['dice']))
    async def dice_handler(message):
        try:
            if not await check_access(message):
                return
            await update_stats(message)
            
            result = random.randint(1, 6)
            await message.reply(f"🎲 **Кубик:** {result}")
            logger.info(f"✅ KARMA /dice: {message.from_user.id} - {result}")
            
        except Exception as e:
            logger.error(f"❌ /dice: {e}")
            await message.reply("🎲 Ошибка кубика")
    
    @router.message(Command(commands=['joke']))
    async def joke_handler(message):
        try:
            if not await check_access(message):
                return
            await update_stats(message)
            
            jokes = [
                "Почему программисты путают Хэллоуин и Рождество? Потому что 31 OCT = 25 DEC!",
                "Как называется программист, который не пьет кофе? Спящий режим.",
                "Почему программисты не любят природу? Слишком много багов.",
                "Два байта встретились на улице. Один говорит: 'Ты выглядишь как NULL'.",
                "Программист пришел в магазин. Жена попросила: 'Купи молоко, если будут яйца - возьми десяток'. Он вернулся с 10 пачками молока."
            ]
            
            joke = random.choice(jokes)
            await message.reply(f"😄 **Шутка дня:**\n\n{joke}")
            logger.info(f"✅ KARMA /joke: {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"❌ /joke: {e}")
            await message.reply("😅 Шутка не удалась")
    
    @router.message(Command(commands=['fact']))
    async def fact_handler(message):
        try:
            if not await check_access(message):
                return
            await update_stats(message)
            
            facts = [
                "Мед никогда не портится. Археологи находили съедобный мед в египетских гробницах.",
                "Банан - это ягода, а клубника - нет.",
                "Осьминоги имеют три сердца и синюю кровь.",
                "Ваш мозг использует около 20% всей энергии тела.",
                "Python получил свое название от британского комедийного шоу 'Летающий цирк Монти Пайтона'.",
                "Первый компьютерный баг был настоящим насекомым, застрявшим в компьютере в 1947 году."
            ]
            
            fact = random.choice(facts)
            await message.reply(f"🧠 **Интересный факт:**\n\n{fact}")
            logger.info(f"✅ KARMA /fact: {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"❌ /fact: {e}")
            await message.reply("🤔 Факт потерялся")
    
    @router.message(Command(commands=['8ball']))
    async def ball_handler(message):
        try:
            if not await check_access(message):
                return
            await update_stats(message)
            
            command_args = message.text.split(' ', 1)
            if len(command_args) < 2:
                help_msg = (
                    "🎱 **Магический шар**\n\n"
                    "**Использование:** `/8ball ваш вопрос?`\n\n"
                    "**Примеры:**\n"
                    "`/8ball Будет ли дождь?`\n"
                    "`/8ball Стоит ли учить Python?`"
                )
                await message.reply(help_msg)
                return
            
            question = command_args[1].strip()
            if len(question) < 3:
                await message.reply("❓ Слишком короткий вопрос")
                return
            
            answers = [
                "Бесспорно!", "Определенно да!", "Без сомнения!", "Можешь быть уверен!",
                "Даже не думай!", "Мой ответ - нет!", "Весьма сомнительно!", "Не рассчитывай на это!",
                "Спроси позже!", "Сейчас нельзя предсказать!", "Неопределенно!", "Попробуй еще раз!"
            ]
            
            answer = random.choice(answers)
            
            response = (
                f"🎱 **Магический шар предсказывает:**\n\n"
                f"**Вопрос:** {safe_escape(question)}\n\n"
                f"**Ответ:** {answer}"
            )
            
            await message.reply(response)
            logger.info(f"✅ KARMA /8ball: {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"❌ /8ball: {e}")
            await message.reply("🎱 Шар сломался")
    
    @router.message(Command(commands=['crypto']))
    async def crypto_handler(message):
        try:
            if not await check_access(message):
                return
            await update_stats(message)
            
            command_args = message.text.split()
            if len(command_args) < 2:
                help_msg = (
                    "₿ **Курс криптовалют**\n\n"
                    "**Использование:**\n"
                    "`/crypto BTC` - курс Bitcoin\n"
                    "`/crypto ETH` - курс Ethereum\n\n"
                    "**Поддерживаемые:** BTC, ETH, BNB, ADA"
                )
                await message.reply(help_msg)
                return
            
            symbol = command_args[1].upper()
            
            # Демонстрационные курсы
            fake_prices = {
                'BTC': {'price': 43250, 'change': '+2.5%', 'name': 'Bitcoin'},
                'ETH': {'price': 2650, 'change': '+1.8%', 'name': 'Ethereum'},
                'BNB': {'price': 245, 'change': '-0.5%', 'name': 'Binance Coin'},
                'ADA': {'price': 0.38, 'change': '+3.2%', 'name': 'Cardano'}
            }
            
            if symbol in fake_prices:
                data = fake_prices[symbol]
                change_emoji = "🟢" if '+' in data['change'] else "🔴"
                
                response = (
                    f"₿ **{data['name']} ({symbol})**\n\n"
                    f"💰 **Цена:** ${data['price']:,}\n"
                    f"{change_emoji} **Изменение:** {data['change']}\n\n"
                    f"⚠️ *Демонстрационные данные*"
                )
                
                await message.reply(response)
            else:
                supported = ", ".join(fake_prices.keys())
                await message.reply(f"❌ **Монета {symbol} не поддерживается**\n\nПоддерживаемые: {supported}")
            
            logger.info(f"✅ KARMA /crypto: {message.from_user.id} - {symbol}")
            
        except Exception as e:
            logger.error(f"❌ /crypto: {e}")
            await message.reply("₿ Ошибка получения курса")
    
    @router.message(Command(commands=['stats']))
    async def stats_handler(message):
        try:
            if not await check_access(message):
                return
            await update_stats(message)
            
            user_name = safe_escape(message.from_user.first_name or "Пользователь")
            user_id = message.from_user.id
            chat_id = message.chat.id
            
            karma_data = get_karma(user_id, chat_id)
            
            if chat_id in chat_stats:
                chat_data = chat_stats[chat_id]
                total_messages = chat_data['messages_count']
                unique_users = len(chat_data['unique_users'])
            else:
                total_messages = 0
                unique_users = 0
            
            response = (
                f"📊 **СТАТИСТИКА {user_name}**\n\n"
                f"⚖️ **Ваша карма:** {karma_data['karma']}\n"
                f"📝 **Ваших сообщений:** {karma_data.get('messages_count', 0)}\n\n"
                f"💬 **Сообщений в чате:** {total_messages}\n"
                f"👥 **Участников чата:** {unique_users}\n\n"
            )
            
            if chat_id in GLOBAL_PERSONAS:
                persona = GLOBAL_PERSONAS[chat_id]
                response += f"🎭 **Персонаж чата:** {persona['name']}"
            else:
                response += f"🎭 **Персонаж:** не установлен"
            
            await message.reply(response)
            logger.info(f"✅ KARMA /stats: {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"❌ /stats: {e}")
            await message.reply("📊 Ошибка статистики")
    
    @router.message(Command(commands=['debug']))
    async def debug_handler(message):
        try:
            if not await check_admin(message, "отладочная информация"):
                return
            await update_stats(message)
            
            debug_info = (
                f"🔧 **KARMA DEBUG v9.0**\n\n"
                f"🤖 **Бот:** @{bot_info.username if bot_info else '?'}\n"
                f"💻 **Режим:** {'Ultimate' if is_ultimate_mode else 'Базовый'}\n"
                f"🧠 **AI:** {'✅' if modules.get('ai') else '❌'}\n\n"
                f"📊 **ДАННЫЕ:**\n"
                f"🎭 **Персонажей:** {len(GLOBAL_PERSONAS)}\n"
                f"⚖️ **Записей кармы:** {len(GLOBAL_KARMA)}\n"
                f"💬 **Активных чатов:** {len(chat_stats)}\n\n"
                f"🕐 **Время:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
                f"⚖️ **Karma Edition v9.0 с уведомлениями активна!**"
            )
            
            await message.reply(debug_info)
            logger.info(f"✅ KARMA /debug: {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"❌ /debug: {e}")
            await message.reply("🔧 Ошибка отладки")
    
    
    @router.message(Command(commands=['wake_words']))
    async def wake_words_handler(message):
        """📝 Просмотр текущих слов призыва"""
        try:
            if not await check_access(message):
                return
            await update_stats(message)
            
            chat_id = message.chat.id
            current_words = get_trigger_words(chat_id)
            is_custom = chat_id in CUSTOM_TRIGGER_WORDS
            
            words_text = "`, `".join(current_words)
            
            response = (
                f"🔤 **СЛОВА ПРИЗЫВА ЧАТА**"
                f"📋 **Текущие слова:** `{words_text}`"
                f"🎯 **Статус:** {'🔧 Настроенные' if is_custom else '📦 Стандартные'}"
                f"📊 **Всего слов:** {len(current_words)}"
                f"💡 **Бот отвечает на эти слова в сообщениях**"
                f"🔧 **Управление (только админы):**"
                f"• `/wake_add слово` - добавить слово"
                f"• `/wake_remove слово` - удалить слово"
                f"• `/wake_reset` - сбросить к стандартным"
                f"• `/wake_help` - подробная справка"
                )
            
            await message.reply(response)
            logger.info(f"✅ WAKE /wake_words: {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"❌ /wake_words: {e}")
            await message.reply("❌ Ошибка получения слов призыва")
    
    @router.message(Command(commands=['wake_add']))
    async def wake_add_handler(message):
        """➕ Добавление слова призыва (только админы)"""
        try:
            if not await check_access(message):
                return
            await update_stats(message)
            
            if not await check_admin(message, "добавление слов призыва"):
                return
            
            command_args = message.text.split(' ', 1)
            if len(command_args) < 2:
                help_msg = (
                    "➕ **Добавление слова призыва**"
                    "**Использование:**"
                    "`/wake_add новое_слово`"
                    "**Примеры:**"
                    "`/wake_add чат`"
                    "`/wake_add ai`"
                    "`/wake_add привет`"
                    "⚠️ **Правила:**"
                    "• Только одно слово за раз"
                    "• Слово должно быть уникальным"
                    "• Минимум 2 символа"
                )
                await message.reply(help_msg)
                return
            
            new_word = command_args[1].strip().lower()
            
            if len(new_word) < 2:
                await message.reply("❌ **Слово слишком короткое**Минимум 2 символа")
                return
            
            if len(new_word) > 20:
                await message.reply("❌ **Слово слишком длинное**Максимум 20 символов")
                return
            
            # Проверяем на недопустимые символы
            if not new_word.replace('_', '').replace('-', '').isalnum():
                await message.reply("❌ **Недопустимые символы**Только буквы, цифры, _ и -")
                return
            
            chat_id = message.chat.id
            
            result = add_trigger_word(chat_id, new_word)
            
            if result == "limit":
                await message.reply("❌ **Достигнут лимит слов**Максимум 50 слов призыва на чат")
            elif result:
                current_words = get_trigger_words(chat_id)
                
                response = (
                    f"✅ **Слово призыва добавлено!**"
                    f"🆕 **Добавлено:** `{new_word}`"
                    f"📊 **Всего слов:** {len(current_words)}"
                    f"💡 **Теперь бот будет реагировать на это слово**"
                    )
                
                await message.reply(response)
                logger.info(f"✅ WAKE добавлено слово {new_word} в чат {chat_id}")
            else:
                await message.reply(f"⚠️ **Слово уже существует**Слово `{new_word}` уже в списке слов призыва")
            
        except Exception as e:
            logger.error(f"❌ /wake_add: {e}")
            await message.reply("❌ Ошибка добавления слова призыва")
    
    @router.message(Command(commands=['wake_remove']))
    async def wake_remove_handler(message):
        """➖ Удаление слова призыва (только админы)"""
        try:
            if not await check_access(message):
                return
            await update_stats(message)
            
            if not await check_admin(message, "удаление слов призыва"):
                return
            
            command_args = message.text.split(' ', 1)
            if len(command_args) < 2:
                help_msg = (
                    "➖ **Удаление слова призыва**"
                    "**Использование:**"
                    "`/wake_remove слово_для_удаления`"
                    "**Примеры:**"
                    "`/wake_remove чат`"
                    "`/wake_remove ai`"
                    "💡 **Посмотреть текущие слова:** `/wake_words`"
                    )
                await message.reply(help_msg)
                return
            
            word_to_remove = command_args[1].strip().lower()
            chat_id = message.chat.id
            
            current_words = get_trigger_words(chat_id)
            
            if word_to_remove not in current_words:
                words_text = "`, `".join(current_words)
                await message.reply(f"❌ **Слово не найдено**Слова `{word_to_remove}` нет в списке**Текущие слова:** `{words_text}`")
                return
            
            if remove_trigger_word(chat_id, word_to_remove):
                updated_words = get_trigger_words(chat_id)
                
                response = (
                    f"✅ **Слово призыва удалено!**"
                    f"🗑️ **Удалено:** `{word_to_remove}`"
                    f"📊 **Осталось слов:** {len(updated_words)}"
                    f"💡 **Бот больше не реагирует на это слово**"
                    )
                
                await message.reply(response)
                logger.info(f"✅ WAKE удалено слово {word_to_remove} из чата {chat_id}")
            else:
                await message.reply("❌ **Ошибка удаления**Не удалось удалить слово из списка")
            
        except Exception as e:
            logger.error(f"❌ /wake_remove: {e}")
            await message.reply("❌ Ошибка удаления слова призыва")
    
    @router.message(Command(commands=['wake_reset']))
    async def wake_reset_handler(message):
        """🔄 Сброс слов призыва к стандартным (только админы)"""
        try:
            if not await check_access(message):
                return
            await update_stats(message)
            
            if not await check_admin(message, "сброс слов призыва"):
                return
            
            chat_id = message.chat.id
            
            if chat_id not in CUSTOM_TRIGGER_WORDS:
                default_words = "`, `".join(DEFAULT_TRIGGER_WORDS)
                await message.reply(f"ℹ️ **Уже используются стандартные слова****Стандартные:** `{default_words}`")
                return
            
            reset_trigger_words(chat_id)
            
            default_words = "`, `".join(DEFAULT_TRIGGER_WORDS)
            
            response = (
                f"🔄 **Слова призыва сброшены!**"
                f"📦 **Восстановлены стандартные слова:**"
                f"`{default_words}`"
                f"📊 **Всего слов:** {len(DEFAULT_TRIGGER_WORDS)}"
                f"💡 **Все пользовательские настройки удалены**"
                )
            
            await message.reply(response)
            logger.info(f"✅ WAKE сброшены слова призыва в чате {chat_id}")
            
        except Exception as e:
            logger.error(f"❌ /wake_reset: {e}")
            await message.reply("❌ Ошибка сброса слов призыва")
    
    @router.message(Command(commands=['wake_help']))
    async def wake_help_handler(message):
        """❓ Подробная справка по словам призыва"""
        try:
            if not await check_access(message):
                return
            await update_stats(message)
            
            help_text = (
                "🔤 **СИСТЕМА СЛОВ ПРИЗЫВА**"
                "🎯 **Что это:**"
                "Слова призыва - это слова, на которые бот реагирует в сообщениях и отвечает через AI."
                "📦 **Стандартные слова:**"
                "`бот`, `bot`, `робот`, `помощник`, `assistant`, `эй`, `слушай`, `макс`"
                "👥 **Команды для всех:**"
                "• `/wake_words` - посмотреть текущие слова"
                "👑 **Команды для админов:**"
                "• `/wake_add слово` - добавить новое слово"
                "• `/wake_remove слово` - удалить слово"
                "• `/wake_reset` - сбросить к стандартным"
                "• `/wake_help` - эта справка"
                "💡 **Примеры использования:**"
                "• `Эй, как дела?` - бот ответит"
                "• `Бот, расскажи шутку` - бот ответит"
                "• `Просто сообщение` - бот не ответит"
                "⚠️ **Правила:**"
                "• Слова от 2 до 20 символов"
                "• Только буквы, цифры, _ и -"
                "• Максимум 50 слов на чат"
                "• Настройки сохраняются для каждого чата отдельно"
                "🔧 **Дополнительные способы вызова:**"
                "• Упоминание @имя_бота"
                "• Ответ на сообщение бота"
                "• Личные сообщения (всегда отвечает)"
                )
            
            await message.reply(help_text)
            logger.info(f"✅ WAKE /wake_help: {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"❌ /wake_help: {e}")
            await message.reply("❌ Ошибка справки по словам призыва")

    # AI ОБРАБОТЧИК
    
    @router.message(F.text & ~F.text.startswith("/"))
    async def ai_handler(message):
        try:
            await update_stats(message)
            
            if not await check_access(message):
                return
            
            text_lower = message.text.lower()
            should_respond = False
            
            # Условия ответа
            if message.reply_to_message and message.reply_to_message.from_user.id == modules['bot'].id:
                should_respond = True
                logger.info("✅ KARMA РЕПЛАЙ")
            elif any(word in text_lower for word in get_trigger_words(message.chat.id)):
                matched_word = next((word for word in get_trigger_words(message.chat.id) if word in text_lower), "")
                should_respond = True
                logger.info(f"✅ KARMA СЛОВО ПРИЗЫВА: {matched_word}")
            elif bot_info and f'@{bot_info.username.lower()}' in text_lower:
                should_respond = True
                logger.info("✅ KARMA УПОМИНАНИЕ")
            elif message.chat.type == 'private':
                should_respond = True
                logger.info("✅ KARMA ЛИЧНЫЙ ЧАТ")
            
            if should_respond:
                logger.info("🧠 KARMA ЗАПУСК AI")
                
                ai_service = modules.get('ai')
                
                if ai_service is None:
                    try:
                        from app.services.ai_service import AIService
                        ai_service = AIService(modules['config'])
                        logger.info("✅ KARMA AI создан")
                    except Exception as e:
                        logger.error(f"❌ KARMA AI недоступен: {e}")
                        await message.reply("❌ AI недоступен")
                        return
                
                # Персонаж
                chat_id = message.chat.id
                active_personality = GLOBAL_PERSONAS.get(chat_id)
                
                if active_personality:
                    persona_name = active_personality['name']
                    persona_desc = active_personality['description']
                    
                    prompt = f"""Ты - {persona_name}. {persona_desc}

Отвечай в роли этого персонажа.
НЕ используй эмодзи в ответах.
Веди себя как живой персонаж.
Отвечай кратко и в характере.

Пользователь: {message.text}
Ответ:"""
                    
                    logger.info(f"🎭 KARMA ПЕРСОНАЖ: {persona_name}")
                    
                else:
                    prompt = f"""Ты - дружелюбный AI помощник.

Отвечай естественно и кратко.
НЕ используй эмодзи в ответах.
Будь полезным.

Пользователь: {message.text}
Ответ:"""
                    
                    logger.info("🤖 KARMA ОБЫЧНЫЙ AI")
                
                try:
                    if hasattr(ai_service, 'generate_response'):
                        response = await ai_service.generate_response(prompt)
                    elif hasattr(ai_service, 'ask'):
                        response = await ai_service.ask(prompt)
                    else:
                        response = None
                    
                    if response and str(response).strip():
                        await message.reply(str(response).strip())
                        logger.info("✅ KARMA AI ответ отправлен")
                        return
                        
                except Exception as e:
                    logger.error(f"💥 KARMA AI ошибка: {e}")
                
                # Fallback
                if active_personality:
                    fallbacks = ["Хм...", "Интересно...", "А?", "Что?"]
                else:
                    fallbacks = ["Да!", "Слышу!", "Привет!", "Окей!"]
                
                await message.reply(random.choice(fallbacks))
                logger.info("✅ KARMA Fallback отправлен")
            
        except Exception as e:
            logger.error(f"💥 KARMA AI handler ошибка: {e}")
    
    # Регистрация
    dp.include_router(router)
    
    logger.info(f"🎛️ KARMA обработчики зарегистрированы ({'Ultimate' if is_ultimate_mode else 'Base'})")
    
    commands = [
        "/start", "/help", "/karma", "/karma_help", "/be", "/persona", "/flip", "/dice", 
        "/joke", "/fact", "/8ball", "/crypto", "/stats", "/debug", "/wake_words", 
        "/wake_add", "/wake_remove", "/wake_reset", "/wake_help"
        ]
    
    logger.info(f"📋 KARMA команды: {', '.join(commands)}")
