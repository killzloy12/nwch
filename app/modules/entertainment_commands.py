# Создайте файл app/modules/entertainment_commands.py

#!/usr/bin/env python3
"""
🎲 ENTERTAINMENT COMMANDS SYSTEM v4.0
Полная система развлекательных команд: факты, анекдоты, игры
"""

import logging
import random
import asyncio
import json
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class GameType(Enum):
    COIN_FLIP = "coin_flip"
    DICE_ROLL = "dice_roll"
    RANDOM_NUMBER = "random_number"
    MAGIC_8_BALL = "magic_8_ball"
    RIDDLE = "riddle"
    QUIZ = "quiz"

@dataclass
class GameSession:
    game_id: str
    chat_id: int
    user_id: int
    game_type: GameType
    current_state: Dict[str, Any]
    score: int = 0
    started_at: datetime = None
    last_activity: datetime = None
    is_active: bool = True

@dataclass
class EntertainmentStats:
    chat_id: int
    total_games_played: int = 0
    facts_requested: int = 0
    jokes_requested: int = 0
    most_popular_game: Optional[str] = None
    top_players: List[Dict] = None

class EntertainmentSystem:
    """🎲 Система развлекательных команд"""
    
    def __init__(self, db_service, config):
        self.db = db_service
        self.config = config
        
        # Активные игровые сессии
        self.active_games: Dict[str, GameSession] = {}
        
        # Кэш фактов и шуток
        self.facts_cache = []
        self.jokes_cache = []
        self.riddles_cache = []
        
        # Статистика
        self.stats_cache = {}
        
        logger.info("🎲 Entertainment System инициализирован")
    
    async def initialize(self):
        """Инициализация системы"""
        await self._create_tables()
        await self._load_content()
        
        # Запускаем фоновые задачи
        asyncio.create_task(self._cleanup_inactive_games())
        asyncio.create_task(self._update_content_cache())
    
    async def _create_tables(self):
        """Создает таблицы развлечений"""
        
        # Игровые сессии
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS game_sessions (
            game_id TEXT PRIMARY KEY,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            game_type TEXT NOT NULL,
            current_state TEXT,  -- JSON
            score INTEGER DEFAULT 0,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            
            INDEX(chat_id),
            INDEX(user_id),
            INDEX(game_type),
            INDEX(is_active)
        )
        ''')
        
        # Статистика развлечений
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS entertainment_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            command_type TEXT NOT NULL,  -- fact, joke, game, etc.
            command_details TEXT,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            INDEX(chat_id),
            INDEX(user_id),
            INDEX(command_type),
            INDEX(used_at)
        )
        ''')
        
        # Пользовательский контент
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS user_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content_type TEXT NOT NULL,  -- fact, joke, riddle
            content_text TEXT NOT NULL,
            is_approved BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            INDEX(chat_id),
            INDEX(content_type),
            INDEX(is_approved)
        )
        ''')
        
        # Рейтинги игроков
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS player_ratings (
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            game_type TEXT NOT NULL,
            total_score INTEGER DEFAULT 0,
            games_played INTEGER DEFAULT 0,
            best_score INTEGER DEFAULT 0,
            last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            PRIMARY KEY(chat_id, user_id, game_type),
            INDEX(total_score),
            INDEX(games_played)
        )
        ''')
    
    async def coin_flip(self, chat_id: int, user_id: int, 
                       bet: Optional[str] = None) -> Tuple[str, bool]:
        """🪙 Орел или решка"""
        
        try:
            # Подбрасываем монету
            result = random.choice(['орел', 'решка'])
            
            # Проверяем ставку
            win = False
            if bet and bet.lower() in ['орел', 'решка']:
                win = (bet.lower() == result)
            
            # Обновляем статистику
            await self._log_entertainment_usage(chat_id, user_id, 'coin_flip', 
                                              f"result:{result},bet:{bet},win:{win}")
            
            # Формируем ответ
            coin_emoji = "🦅" if result == "орел" else "👑"
            
            response = f"🪙 **Подбрасываю монету...**\n\n{coin_emoji} **{result.upper()}!**"
            
            if bet:
                if win:
                    response += f"\n\n🎉 **Поздравляю!** Вы угадали! Ваша ставка '{bet}' выиграла!"
                    
                    # Добавляем очки
                    await self._update_player_rating(chat_id, user_id, GameType.COIN_FLIP, 10)
                else:
                    response += f"\n\n😔 **Не повезло!** Ваша ставка '{bet}' не сыграла."
            else:
                response += "\n\n💡 *Подсказка: можете делать ставки!*\n`/flip орел` или `/flip решка`"
            
            return response, win
            
        except Exception as e:
            logger.error(f"❌ Ошибка подбрасывания монеты: {e}")
            return "❌ Ошибка при подбрасывании монеты", False
    
    async def roll_dice(self, chat_id: int, user_id: int, 
                       sides: int = 6, count: int = 1) -> str:
        """🎲 Бросок кубиков"""
        
        try:
            # Валидация
            if count > 10:
                count = 10
            if sides > 100:
                sides = 100
            if sides < 2:
                sides = 6
            
            # Бросаем кубики
            rolls = [random.randint(1, sides) for _ in range(count)]
            total = sum(rolls)
            
            # Формируем ответ
            dice_emoji = "🎲" * min(count, 5)
            
            response = f"{dice_emoji} **Бросок кубика**\n\n"
            
            if count == 1:
                response += f"🎯 **Результат:** {rolls[0]}"
                
                # Специальные случаи для 6-стороннего кубика
                if sides == 6:
                    if rolls[0] == 6:
                        response += " 🏆 **МАКСИМУМ!**"
                    elif rolls[0] == 1:
                        response += " 😅 **Не повезло...**"
            else:
                rolls_str = " + ".join(map(str, rolls))
                response += f"🎯 **Броски:** {rolls_str}\n"
                response += f"📊 **Сумма:** {total}"
                
                # Бонус за все максимальные значения
                if all(roll == sides for roll in rolls):
                    response += " 🔥 **ВСЕ МАКСИМУМЫ!**"
                    await self._update_player_rating(chat_id, user_id, GameType.DICE_ROLL, 50)
            
            # Обновляем статистику
            await self._log_entertainment_usage(chat_id, user_id, 'dice_roll', 
                                              f"sides:{sides},count:{count},total:{total}")
            
            # Обычные очки
            await self._update_player_rating(chat_id, user_id, GameType.DICE_ROLL, total)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка броска кубика: {e}")
            return "❌ Ошибка при броске кубика"
    
    async def magic_8_ball(self, chat_id: int, user_id: int, question: str) -> str:
        """🎱 Магический шар 8"""
        
        try:
            # Ответы шара
            answers = [
                # Положительные
                "✅ Определенно да",
                "✅ Можешь быть уверен",
                "✅ Да, безусловно",
                "✅ Скорее всего да",
                "✅ Знаки указывают на да",
                "✅ Да",
                
                # Нейтральные
                "🤔 Спроси позже",
                "🤔 Лучше не говорить сейчас",
                "🤔 Не могу предсказать",
                "🤔 Сосредоточься и спроси снова",
                "🤔 Туманно, попробуй еще раз",
                
                # Отрицательные
                "❌ Не рассчитывай на это",
                "❌ Мой ответ - нет",
                "❌ Мои источники говорят нет",
                "❌ Весьма сомнительно",
                "❌ Определенно нет"
            ]
            
            # Выбираем случайный ответ
            answer = random.choice(answers)
            
            # Обновляем статистику
            await self._log_entertainment_usage(chat_id, user_id, 'magic_8_ball', 
                                              f"question_length:{len(question)}")
            
            response = f"🎱 **Магический шар 8**\n\n"
            response += f"❓ **Вопрос:** {question}\n\n"
            response += f"🔮 **Ответ:** {answer}"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка магического шара: {e}")
            return "❌ Магический шар сломался 🎱💥"
    
    async def get_random_fact(self, chat_id: int, user_id: int, 
                            category: Optional[str] = None) -> str:
        """🧠 Случайный факт"""
        
        try:
            # Сначала пробуем загрузить из API
            fact = await self._fetch_external_fact(category)
            
            # Если не получилось, берем из кэша
            if not fact and self.facts_cache:
                fact = random.choice(self.facts_cache)
            
            # Если и кэш пуст, используем встроенные факты
            if not fact:
                fact = self._get_builtin_fact()
            
            # Обновляем статистику
            await self._log_entertainment_usage(chat_id, user_id, 'fact', 
                                              f"category:{category},length:{len(fact)}")
            
            response = f"🧠 **Интересный факт**\n\n"
            if category:
                response += f"📂 **Категория:** {category}\n\n"
            response += f"💡 {fact}"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения факта: {e}")
            return "❌ Не удалось получить факт"
    
    async def get_random_joke(self, chat_id: int, user_id: int) -> str:
        """😄 Случайная шутка"""
        
        try:
            # Пробуем загрузить из API
            joke = await self._fetch_external_joke()
            
            # Если не получилось, берем из кэша
            if not joke and self.jokes_cache:
                joke = random.choice(self.jokes_cache)
            
            # Встроенные шутки как fallback
            if not joke:
                joke = self._get_builtin_joke()
            
            # Обновляем статистику
            await self._log_entertainment_usage(chat_id, user_id, 'joke', 
                                              f"length:{len(joke)}")
            
            response = f"😄 **Шутка дня**\n\n{joke}"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения шутки: {e}")
            return "❌ Шутки закончились 😅"
    
    async def start_quiz(self, chat_id: int, user_id: int, 
                        category: str = "general") -> str:
        """🧩 Начало викторины"""
        
        try:
            # Создаем новую игровую сессию
            game_id = f"quiz_{chat_id}_{user_id}_{int(datetime.now().timestamp())}"
            
            # Загружаем вопросы
            questions = await self._get_quiz_questions(category)
            
            if not questions:
                return "❌ Вопросы для викторины не найдены"
            
            # Создаем сессию
            game_session = GameSession(
                game_id=game_id,
                chat_id=chat_id,
                user_id=user_id,
                game_type=GameType.QUIZ,
                current_state={
                    'category': category,
                    'questions': questions,
                    'current_question': 0,
                    'correct_answers': 0,
                    'total_questions': len(questions)
                },
                started_at=datetime.now(),
                last_activity=datetime.now()
            )
            
            self.active_games[game_id] = game_session
            
            # Сохраняем в БД
            await self._save_game_session(game_session)
            
            # Показываем первый вопрос
            return await self._show_quiz_question(game_session)
            
        except Exception as e:
            logger.error(f"❌ Ошибка начала викторины: {e}")
            return "❌ Не удалось начать викторину"
    
    async def answer_quiz(self, chat_id: int, user_id: int, answer: str) -> str:
        """✅ Ответ на вопрос викторины"""
        
        try:
            # Ищем активную игру пользователя
            game_session = None
            for game in self.active_games.values():
                if (game.chat_id == chat_id and game.user_id == user_id and 
                    game.game_type == GameType.QUIZ and game.is_active):
                    game_session = game
                    break
            
            if not game_session:
                return "❌ У вас нет активной викторины. Начните новую командой `/quiz`"
            
            # Получаем текущий вопрос
            state = game_session.current_state
            questions = state['questions']
            current_q = state['current_question']
            
            if current_q >= len(questions):
                return "❌ Викторина уже завершена"
            
            question = questions[current_q]
            correct_answer = question['correct_answer'].lower().strip()
            user_answer = answer.lower().strip()
            
            # Проверяем ответ
            is_correct = user_answer == correct_answer
            
            response = ""
            if is_correct:
                response += "✅ **Правильно!**\n\n"
                state['correct_answers'] += 1
                game_session.score += 10
            else:
                response += f"❌ **Неправильно!**\n\n"
                response += f"💡 **Правильный ответ:** {question['correct_answer']}\n\n"
            
            # Переходим к следующему вопросу
            state['current_question'] += 1
            game_session.last_activity = datetime.now()
            
            # Проверяем, закончилась ли викторина
            if state['current_question'] >= state['total_questions']:
                # Викторина завершена
                game_session.is_active = False
                
                correct = state['correct_answers']
                total = state['total_questions']
                percentage = int((correct / total) * 100)
                
                response += f"🏁 **Викторина завершена!**\n\n"
                response += f"📊 **Результат:** {correct}/{total} ({percentage}%)\n"
                response += f"🏆 **Очки:** {game_session.score}\n\n"
                
                # Оценка результата
                if percentage >= 90:
                    response += "🌟 **Отличный результат!**"
                elif percentage >= 70:
                    response += "👍 **Хороший результат!**"
                elif percentage >= 50:
                    response += "👌 **Неплохо!**"
                else:
                    response += "📚 **Есть над чем поработать!**"
                
                # Обновляем рейтинг
                await self._update_player_rating(chat_id, user_id, GameType.QUIZ, game_session.score)
                
                # Удаляем из активных игр
                del self.active_games[game_session.game_id]
            else:
                # Показываем следующий вопрос
                response += await self._show_quiz_question(game_session)
            
            # Обновляем сессию в БД
            await self._save_game_session(game_session)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка ответа на викторину: {e}")
            return "❌ Ошибка при обработке ответа"
    
    async def get_player_stats(self, chat_id: int, user_id: int) -> str:
        """📊 Статистика игрока"""
        
        try:
            # Получаем рейтинги по всем играм
            ratings = await self.db.fetch_all('''
            SELECT game_type, total_score, games_played, best_score, last_played
            FROM player_ratings 
            WHERE chat_id = ? AND user_id = ?
            ORDER BY total_score DESC
            ''', (chat_id, user_id))
            
            if not ratings:
                return "📊 **Статистика пуста**\n\nВы еще не играли в игры!"
            
            response = "📊 **Ваша статистика**\n\n"
            
            total_score = 0
            total_games = 0
            
            for rating in ratings:
                game_type, score, games, best, last_played = rating
                total_score += score
                total_games += games
                
                game_names = {
                    'coin_flip': '🪙 Орел/Решка',
                    'dice_roll': '🎲 Кубики',
                    'quiz': '🧩 Викторина',
                    'magic_8_ball': '🎱 Магический шар'
                }
                
                game_name = game_names.get(game_type, game_type)
                
                response += f"**{game_name}**\n"
                response += f"└ Очки: {score} | Игр: {games} | Лучший: {best}\n\n"
            
            response += f"🏆 **Общий счет:** {total_score}\n"
            response += f"🎮 **Всего игр:** {total_games}"
            
            # Уровень игрока
            level = self._calculate_player_level(total_score)
            response += f"\n⭐ **Уровень:** {level}"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики игрока: {e}")
            return "❌ Не удалось получить статистику"
    
    async def get_leaderboard(self, chat_id: int, game_type: Optional[str] = None) -> str:
        """🏆 Таблица лидеров"""
        
        try:
            if game_type:
                # Лидеры по конкретной игре
                leaders = await self.db.fetch_all('''
                SELECT user_id, total_score, games_played, best_score
                FROM player_ratings 
                WHERE chat_id = ? AND game_type = ?
                ORDER BY total_score DESC 
                LIMIT 10
                ''', (chat_id, game_type))
                
                game_names = {
                    'coin_flip': '🪙 Орел/Решка',
                    'dice_roll': '🎲 Кубики', 
                    'quiz': '🧩 Викторина'
                }
                
                title = f"🏆 **Лидеры - {game_names.get(game_type, game_type)}**"
            else:
                # Общие лидеры
                leaders = await self.db.fetch_all('''
                SELECT user_id, SUM(total_score) as total, SUM(games_played) as games
                FROM player_ratings 
                WHERE chat_id = ?
                GROUP BY user_id 
                ORDER BY total DESC 
                LIMIT 10
                ''', (chat_id,))
                
                title = "🏆 **Общая таблица лидеров**"
            
            if not leaders:
                return f"{title}\n\n🤷‍♂️ Пока никто не играл!"
            
            response = f"{title}\n\n"
            
            for i, leader in enumerate(leaders, 1):
                user_id = leader[0]
                score = leader[1]
                
                # Эмодзи для позиций
                position_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
                
                response += f"{position_emoji} ID {user_id}: **{score}** очков\n"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения таблицы лидеров: {e}")
            return "❌ Не удалось получить таблицу лидеров"
    
    def _get_builtin_fact(self) -> str:
        """Встроенные факты"""
        
        facts = [
            "Сердце синего кита настолько большое, что через его артерии может проплыть маленькая рыба.",
            "Банан - это ягода, а клубника - нет.",
            "Октопусы имеют три сердца и голубую кровь.",
            "Мед никогда не портится. Археологи находили съедобный мед в египетских гробницах возрастом 3000 лет.",
            "Группа фламинго называется 'flamboyance' (показность).",
            "Акулы существуют дольше деревьев - более 400 миллионов лет.",
            "В космосе нельзя плакать, потому что слезы не падают вниз из-за отсутствия гравитации.",
            "Морские выдры держатся за лапы во время сна, чтобы не потеряться в океане.",
            "Стрекозы могут двигаться в шести направлениях: вверх, вниз, вперед, назад, влево и вправо.",
            "Пингвины могут прыгать на высоту до 2 метров из воды."
        ]
        
        return random.choice(facts)
    
    def _get_builtin_joke(self) -> str:
        """Встроенные шутки"""
        
        jokes = [
            "— Доктор, я забываю все через 5 минут!\n— Это серьезно. С каких пор это началось?\n— Что началось?",
            "Программист моет посуду в ванной. Жена кричит:\n— Зачем в ванной?!\n— А там больше оперативки!",
            "— Алло, это служба поддержки?\n— Да.\n— У меня проблема с компьютером.\n— Он включен?\n— Конечно! Думаете, я идиот?\n— Нет, просто проверяю. Опишите проблему.\n— Ну, я нажимаю на любую кнопку, а он ничего не делает.\n— Попробуйте нажать на кнопку питания.\n— На какую кнопку? У меня тут только подстаканник выдвигается...",
            "Встречаются два программиста:\n— Как дела?\n— Как в жизни — сплошные баги.\n— А дома?\n— Дома жена постоянно ругается.\n— Это тоже баг?\n— Нет, это фича!",
            "— Почему программисты путают Хэллоуин с Рождеством?\n— Потому что 31 OCT = 25 DEC!"
        ]
        
        return random.choice(jokes)

# ЭКСПОРТ
__all__ = ["EntertainmentSystem", "GameType", "GameSession"]
