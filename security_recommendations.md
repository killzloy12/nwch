# Рекомендации по безопасности для Telegram бота

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
    """Валидация и санитизация пользовательского ввода."""
    if not text or len(text.strip()) == 0:
        return None

    # Ограничение длины
    if len(text) > 4000:
        return text[:4000]

    # Удаление потенциально опасных символов
    sanitized = re.sub(r'[<>"'&]', '', text)

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
    """Декоратор для проверки прав администратора."""
    def wrapper(message: Message, *args, **kwargs):
        if message.from_user.id not in ADMIN_IDS:
            return message.answer("❌ Недостаточно прав")
        return func(message, *args, **kwargs)
    return wrapper

@require_admin
async def admin_command(message: Message):
    await message.answer("Команда администратора выполнена")
```
