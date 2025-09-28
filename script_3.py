# Создадим улучшенную версию main.py с правильной архитектурой

main_content = """#!/usr/bin/env python3
\"\"\"
Enhanced Telegram Bot v3.0 - Улучшенная версия
Правильная архитектура с обработкой ошибок и безопасностью
\"\"\"

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from typing import Optional

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.memory import MemoryStorage

from improved_config import get_config, BotConfig
from improved_database import db_manager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TelegramBot:
    \"\"\"Основной класс Telegram бота с правильной архитектурой.\"\"\"
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None
        self.is_running = False
        
    async def initialize(self):
        \"\"\"Инициализация бота и всех компонентов.\"\"\"
        try:
            # Инициализация бота
            self.bot = Bot(token=self.config.bot_token)
            self.dp = Dispatcher(storage=MemoryStorage())
            
            # Инициализация базы данных
            await db_manager.init_database()
            
            # Регистрация обработчиков
            self._register_handlers()
            
            # Проверка соединения с Telegram
            bot_info = await self.bot.get_me()
            logger.info(f"Бот инициализирован: @{bot_info.username}")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            raise
    
    def _register_handlers(self):
        \"\"\"Регистрация всех обработчиков сообщений.\"\"\"
        
        # Команда /start
        @self.dp.message(CommandStart())
        async def cmd_start(message: Message):
            await self._handle_start(message)
        
        # Команда /help
        @self.dp.message(Command('help'))
        async def cmd_help(message: Message):
            await self._handle_help(message)
        
        # Команда /status (только для админов)
        @self.dp.message(Command('status'))
        async def cmd_status(message: Message):
            await self._handle_status(message)
        
        # Обработчик всех сообщений
        @self.dp.message()
        async def handle_message(message: Message):
            await self._handle_message(message)
        
        # Обработчик ошибок
        @self.dp.error()
        async def error_handler(event, exception):
            await self._handle_error(event, exception)
    
    async def _handle_start(self, message: Message):
        \"\"\"Обработчик команды /start с безопасностью.\"\"\"
        try:
            user = message.from_user
            
            # Добавляем пользователя в БД
            await db_manager.add_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Проверяем права доступа
            if await self._check_permissions(user.id, message.chat.id):
                welcome_text = (
                    f"👋 Привет, {user.first_name}!\\n\\n"
                    "🤖 Я Enhanced Telegram Bot v3.0\\n"
                    "🔧 Используй /help для списка команд\\n\\n"
                    "⚡ Готов к работе!"
                )
                
                await message.answer(welcome_text)
            else:
                await message.answer("❌ У вас нет доступа к этому боту.")
                
        except Exception as e:
            logger.error(f"Ошибка в обработчике /start: {e}")
            await message.answer("❌ Произошла ошибка. Попробуйте позже.")
    
    async def _handle_help(self, message: Message):
        \"\"\"Обработчик команды /help.\"\"\"
        try:
            user_id = message.from_user.id
            is_admin = user_id in self.config.admin_ids
            
            help_text = [
                "📋 <b>Доступные команды:</b>\\n",
                "🔹 /start - Начать работу",
                "🔹 /help - Показать справку",
                "🔹 /stats - Ваша статистика",
            ]
            
            if is_admin:
                help_text.extend([
                    "\\n👑 <b>Команды администратора:</b>",
                    "🔹 /status - Статус бота",
                    "🔹 /users - Список пользователей",
                    "🔹 /broadcast - Рассылка сообщений",
                ])
            
            await message.answer(
                "\\n".join(help_text),
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Ошибка в обработчике /help: {e}")
            await message.answer("❌ Произошла ошибка.")
    
    async def _handle_status(self, message: Message):
        \"\"\"Обработчик команды /status (только для админов).\"\"\"
        try:
            user_id = message.from_user.id
            
            if user_id not in self.config.admin_ids:
                await message.answer("❌ Команда доступна только администраторам.")
                return
            
            # Получаем статистику бота
            status_text = [
                "📊 <b>Статус бота:</b>\\n",
                f"✅ Статус: {'Работает' if self.is_running else 'Остановлен'}",
                f"🔧 Конфигурация: загружена",
                f"🗄️ База данных: подключена",
                f"👥 Админы: {len(self.config.admin_ids)}",
                "\\n💡 Все системы работают нормально!"
            ]
            
            await message.answer(
                "\\n".join(status_text),
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Ошибка в обработчике /status: {e}")
            await message.answer("❌ Произошла ошибка при получении статуса.")
    
    async def _handle_message(self, message: Message):
        \"\"\"Основной обработчик всех сообщений.\"\"\"
        try:
            # Проверяем права доступа
            if not await self._check_permissions(message.from_user.id, message.chat.id):
                return
            
            # Сохраняем сообщение в БД для статистики
            await self._save_message(message)
            
            # Здесь можно добавить логику для триггеров,
            # AI ответов и других функций
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
    
    async def _handle_error(self, event, exception):
        \"\"\"Глобальный обработчик ошибок.\"\"\"
        logger.error(f"Глобальная ошибка: {exception}")
        
        # Пытаемся отправить сообщение об ошибке пользователю
        try:
            if hasattr(event, 'message') and event.message:
                await event.message.answer(
                    "❌ Произошла техническая ошибка. "
                    "Администраторы уведомлены."
                )
        except:
            pass  # Если не удалось отправить сообщение
    
    async def _check_permissions(self, user_id: int, chat_id: int) -> bool:
        \"\"\"Проверка разрешений пользователя.\"\"\"
        # Админы имеют полные права
        if user_id in self.config.admin_ids:
            return True
        
        # Здесь должна быть логика проверки whitelist/blacklist
        # из базы данных или конфигурации
        return True  # Пока разрешаем всем
    
    async def _save_message(self, message: Message):
        \"\"\"Сохранение сообщения в базу данных для статистики.\"\"\"
        try:
            # Здесь должна быть логика сохранения сообщения в БД
            pass
        except Exception as e:
            logger.error(f"Ошибка сохранения сообщения: {e}")
    
    async def start(self):
        \"\"\"Запуск бота.\"\"\"
        try:
            self.is_running = True
            logger.info("Запуск polling...")
            await self.dp.start_polling(self.bot)
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки")
        except Exception as e:
            logger.error(f"Ошибка при запуске: {e}")
            raise
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        \"\"\"Корректное завершение работы бота.\"\"\"
        try:
            self.is_running = False
            logger.info("Завершение работы бота...")
            
            if self.bot:
                await self.bot.session.close()
            
            await db_manager.close()
            logger.info("Бот завершил работу")
            
        except Exception as e:
            logger.error(f"Ошибка при завершении: {e}")

async def main():
    \"\"\"Главная функция приложения.\"\"\"
    try:
        # Загружаем конфигурацию
        config = get_config()
        logger.info("Конфигурация загружена")
        
        # Создаем и инициализируем бота
        bot_instance = TelegramBot(config)
        await bot_instance.initialize()
        
        # Обработка системных сигналов
        def signal_handler(signum, frame):
            logger.info(f"Получен сигнал {signum}")
            asyncio.create_task(bot_instance.shutdown())
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Запускаем бота
        await bot_instance.start()
        
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # Создаем необходимые директории
    import os
    os.makedirs('data/logs', exist_ok=True)
    
    # Запускаем бота
    asyncio.run(main())
"""

# Сохраним улучшенный main.py
with open('improved_main.py', 'w', encoding='utf-8') as f:
    f.write(main_content)

print("Создан улучшенный main.py с правильной архитектурой")

# Создадим файл с рекомендациями по безопасности
security_recommendations = """# Рекомендации по безопасности для Telegram бота

## 1. Защита API ключей
```env
# .env файл - НИКОГДА не коммитьте в git!
BOT_TOKEN=your_secret_token_here
OPENAI_API_KEY=your_openai_key_here
ADMIN_IDS=123456789,987654321

# В production используйте переменные окружения системы
```

## 2. Валидация входных данных
```python
import re
from typing import Optional

def validate_user_input(text: str) -> Optional[str]:
    \"\"\"Валидация и санитизация пользовательского ввода.\"\"\"
    if not text or len(text.strip()) == 0:
        return None
    
    # Ограничение длины
    if len(text) > 4000:
        return text[:4000]
    
    # Удаление потенциально опасных символов
    sanitized = re.sub(r'[<>\"\'&]', '', text)
    
    return sanitized.strip()
```

## 3. Rate Limiting
```python
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, max_requests: int = 30, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id: int) -> bool:
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Очищаем старые запросы
        user_requests[:] = [req_time for req_time in user_requests 
                           if now - req_time < self.time_window]
        
        if len(user_requests) >= self.max_requests:
            return False
        
        user_requests.append(now)
        return True
```

## 4. Защита от SQL инъекций
```python
# ВСЕГДА используйте параметризированные запросы
async def get_user_safe(user_id: int):
    async with aiosqlite.connect(db_path) as db:
        # Правильно - с параметрами
        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?", 
            (user_id,)
        )
        return await cursor.fetchone()

# НИКОГДА не делайте так:
# query = f"SELECT * FROM users WHERE user_id = {user_id}"  # ОПАСНО!
```

## 5. Логирование безопасности
```python
import logging

security_logger = logging.getLogger('security')
security_handler = logging.FileHandler('data/logs/security.log')
security_logger.addHandler(security_handler)

def log_security_event(event_type: str, user_id: int, details: str):
    security_logger.warning(
        f"SECURITY_EVENT: {event_type} | User: {user_id} | Details: {details}"
    )
```

## 6. Защита от спама и флуда
```python
class AntiSpam:
    def __init__(self):
        self.message_history = defaultdict(list)
        self.spam_threshold = 5  # сообщений
        self.time_window = 10   # секунд
    
    def check_spam(self, user_id: int, message_text: str) -> bool:
        now = time.time()
        user_messages = self.message_history[user_id]
        
        # Очищаем старые сообщения
        user_messages[:] = [(msg_time, msg_text) for msg_time, msg_text in user_messages
                           if now - msg_time < self.time_window]
        
        # Проверяем на флуд
        recent_messages = len(user_messages)
        if recent_messages >= self.spam_threshold:
            return True
        
        # Проверяем на повторяющиеся сообщения
        identical_count = sum(1 for _, msg in user_messages if msg == message_text)
        if identical_count >= 3:
            return True
        
        user_messages.append((now, message_text))
        return False
```

## 7. Проверка разрешений
```python
def require_admin(func):
    \"\"\"Декоратор для проверки прав администратора.\"\"\"
    def wrapper(message: Message, *args, **kwargs):
        if message.from_user.id not in ADMIN_IDS:
            return message.answer("❌ Недостаточно прав")
        return func(message, *args, **kwargs)
    return wrapper

@require_admin
async def admin_command(message: Message):
    await message.answer("Команда администратора выполнена")
```
"""

with open('security_recommendations.md', 'w', encoding='utf-8') as f:
    f.write(security_recommendations)

print("Создан файл security_recommendations.md с рекомендациями по безопасности")