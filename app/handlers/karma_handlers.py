#!/usr/bin/env python3
"""
⚖️ KARMA HANDLERS v3.0
🔥 Обработчики команд /karma и /topkarma
"""

import logging
from aiogram import Router, types
from aiogram.filters import Command

from app.modules.karma_system import KarmaManager

logger = logging.getLogger(__name__)

router = Router()


def setup_karma_handlers(dp, karma_manager: KarmaManager):
    """🎛️ Регистрация всех обработчиков кармы"""

    @router.message(Command("karma"))
    async def cmd_karma(message: types.Message):
        """⚖️ Показать карму пользователя"""
        user_id = message.from_user.id
        chat_id = message.chat.id

        points = await karma_manager.get_karma(user_id, chat_id)
        await message.reply(f"⚖️ Ваша карма: {points}")

    @router.message(Command("topkarma"))
    async def cmd_topkarma(message: types.Message):
        """🏆 Топ пользователей по карме"""
        chat_id = message.chat.id
        top = await karma_manager.top_karma(chat_id, limit=10)

        if not top:
            await message.reply("⚖️ Пока в этом чате нет данных о карме.")
            return

        text = "🏆 Топ по карме:\n\n"
        for i, row in enumerate(top, start=1):
            text += f"{i}. user_id {row['user_id']} → {row['points']} очков\n"

        await message.reply(text)

    dp.include_router(router)
    logger.info("✅ KARMA обработчики зарегистрированы")
