# Отдельный модуль с базовой логикой кармы (handlers использует)
from datetime import datetime
import random
from typing import Dict

class KarmaSystem:
    """⚖️ Основная логика кармы (используется в handlers)."""
    LEVELS = {
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

    @staticmethod
    def analyze(text: str) -> Dict:
        # Анализ текста возвращает {'change': int, 'reason': str}
        change = random.randint(1, 2)
        reason = "активность"
        return {'change': change, 'reason': reason}
