
# Примеры исправлений для Telegram бота

## 1. Базовая структура main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

## 2. Обработчик команды /start
@dp.message(Command('start'))
async def cmd_start(message: Message):
    try:
        await message.answer(
            f"Привет, {message.from_user.first_name}! 👋\n"
            "Я готов помочь тебе!"
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике start: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

## 3. Основная функция
async def main():
    try:
        logger.info("Запуск бота...")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
