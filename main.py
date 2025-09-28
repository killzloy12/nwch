#!/usr/bin/env python3
"""
💀 ENHANCED TELEGRAM BOT v3.0 - ПРОСТОЙ ЗАПУСК
🔥 Базовая версия без Ultimate Edition
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

# Основные импорты
try:
    from config_harsh import load_config
    from database import DatabaseService
except ImportError as e:
    print(f"❌ ОШИБКА: Не найден модуль {e.name}")
    print("Создайте файлы config_harsh.py и database.py")
    input("Нажмите Enter для выхода...")
    sys.exit(1)

# Опциональные импорты
modules_available = False
try:
    from app.services.ai_service import AIService
    from app.services.analytics_service import AnalyticsService
    from app.services.crypto_service import CryptoService
    modules_available = True
except ImportError as e:
    print(f"⚠️ Сервисы недоступны: {e}")

# Системы персонажей и кармы
personality_system_available = False
karma_system_available = False

try:
    from app.modules.custom_personality_system import CustomPersonalityManager
    personality_system_available = True
    print("✅ Система персонажей найдена!")
except ImportError as e:
    print(f"⚠️ Система персонажей недоступна: {e}")

try:
    from app.modules.karma_system import KarmaManager
    karma_system_available = True
    print("✅ Система кармы найдена!")
except ImportError as e:
    print(f"⚠️ Система кармы недоступна: {e}")

# Обработчики
handlers_available = False
try:
    from app.handlers.handlers_v3_fixed import register_all_handlers
    handlers_available = True
    print("✅ Обработчики найдены")
except ImportError:
    try:
        from app.handlers.handlers_v3_simple import register_all_handlers
        handlers_available = True
        print("✅ Простые обработчики найдены")
    except ImportError as e:
        print(f"❌ Обработчики недоступны: {e}")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def setup_bot_commands(bot: Bot):
    """⚙️ Настройка команд бота"""
    commands = [
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="help", description="Справка"),
        BotCommand(command="be", description="Установить персонажа"),
        BotCommand(command="reset_persona", description="Сбросить персонажа"),
        BotCommand(command="current_persona", description="Текущий персонаж"),
        BotCommand(command="karma", description="Моя карма"),
    ]

    await bot.set_my_commands(commands)
    logger.info("⚙️ Команды настроены")


async def main():
    """💀 Основная функция запуска"""

    print("🎭 ENHANCED TELEGRAM BOT v3.0 - БАЗОВАЯ ВЕРСИЯ")
    print("=" * 50)

    try:
        # Создаем директории
        directories = ['data/logs', 'data/backups', 'app/services', 'app/modules', 'app/handlers']
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

        # Логирование в файл
        file_handler = logging.FileHandler('data/logs/bot.log', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logging.getLogger().addHandler(file_handler)

        # Загружаем конфигурацию
        config = load_config()

        if not config.bot.token:
            print("❌ ОШИБКА: BOT_TOKEN не найден в .env!")
            return

        if not config.bot.admin_ids:
            print("❌ ОШИБКА: ADMIN_IDS не указаны в .env!")
            return

        print(f"👑 АДМИНЫ: {config.bot.admin_ids}")
        if config.bot.allowed_chat_ids:
            print(f"🔒 РАЗРЕШЕННЫЕ ЧАТЫ: {config.bot.allowed_chat_ids}")

        # Создаем бота
        bot = Bot(
            token=config.bot.token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

        dp = Dispatcher(storage=MemoryStorage())

        # Проверяем подключение
        bot_info = await bot.get_me()
        print(f"🤖 Подключен: @{bot_info.username}")

        # Инициализация базы данных
        print("💾 Инициализация базы данных...")
        db_service = DatabaseService(config.database)
        await db_service.initialize()

        # Словарь модулей
        modules = {
            'config': config,
            'db': db_service,
            'bot': bot
        }

        # Инициализация сервисов
        if modules_available:
            print("🧠 Инициализация сервисов...")
            try:
                modules['ai'] = AIService(config)
                print("  ✅ AI сервис активирован")
            except Exception:
                print("  ❌ AI сервис недоступен")

            try:
                modules['analytics_service'] = AnalyticsService(db_service)
                print("  ✅ Аналитика активирована")
            except Exception:
                print("  ❌ Аналитика недоступна")

            try:
                modules['crypto_service'] = CryptoService(config)
                print("  ✅ Крипто сервис активирован")
            except Exception:
                print("  ❌ Крипто сервис недоступен")

        # Система персонажей
        if personality_system_available:
            print("🎭 Инициализация системы персонажей...")
            modules['custom_personality_manager'] = CustomPersonalityManager(
                db_service, config, modules.get('ai')
            )
            await modules['custom_personality_manager'].initialize()
            print("  ✅ Система персонажей готова")

        # Система кармы
        if karma_system_available:
            print("⚖️ Инициализация системы кармы...")
            modules['karma_manager'] = KarmaManager(db_service, config)
            await modules['karma_manager'].initialize()
            print("  ✅ Система кармы готова")

        # Регистрация обработчиков
        if handlers_available:
            print("🎛️ Регистрация обработчиков...")
            register_all_handlers(dp, modules)
            print("  ✅ Обработчики зарегистрированы")
        else:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Нет обработчиков!")
            return

        # Настройка команд
        await setup_bot_commands(bot)

        # Уведомление админов
        for admin_id in config.bot.admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    f"🎭 <b>ENHANCED BOT v3.0 ЗАПУЩЕН!</b>\n\n"
                    f"<b>Бот:</b> @{bot_info.username}\n"
                    f"<b>Режим:</b> Базовый\n"
                    f"<b>Персонажи:</b> {'✅' if personality_system_available else '❌'}\n"
                    f"<b>Карма:</b> {'✅' if karma_system_available else '❌'}\n\n"
                    f"<b>ГОТОВ К РАБОТЕ!</b>"
                )
                print(f"  📤 Админ уведомлен: {admin_id}")
            except Exception as e:
                print(f"  ⚠️ Не удалось уведомить {admin_id}: {e}")

        print("\n" + "=" * 50)
        print("🎭 ENHANCED BOT v3.0 ЗАПУЩЕН УСПЕШНО!")
        print("=" * 50)
        print("\n💡 Для остановки: Ctrl+C")

        # Запуск поллинга
        await dp.start_polling(bot, skip_updates=True)

    except KeyboardInterrupt:
        print("\n⏸️ Остановка...")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        print(f"💥 ОШИБКА: {e}")
    finally:
        print("🛑 Остановка бота...")
        try:
            if 'modules' in locals():
                if 'crypto_service' in modules:
                    await modules['crypto_service'].close()
                if 'db' in modules:
                    await modules['db'].close()
            if 'bot' in locals():
                await bot.session.close()
        except Exception:
            pass
        print("✅ Бот остановлен")


if __name__ == '__main__':
    asyncio.run(main())
