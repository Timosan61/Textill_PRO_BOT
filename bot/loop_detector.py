"""
Защита от бесконечной петли ответов бота

Предотвращает ситуацию когда бот отвечает на свои собственные сообщения,
создавая бесконечный цикл через Business API.
"""

import logging
import hashlib
from datetime import datetime, timedelta
from collections import deque
from typing import Optional, Dict, Set

logger = logging.getLogger(__name__)


class LoopDetector:
    """
    Детектор бесконечных петель ответов

    Использует несколько стратегий:
    1. Проверка текста по шаблонам бота
    2. Проверка временных меток (слишком быстрые ответы)
    3. Отслеживание хешей сообщений для обнаружения дубликатов
    4. Проверка последовательности сообщений от одного пользователя
    """

    # Характерные фразы бота Елены из Textile Pro
    BOT_SIGNATURES = [
        "Елена, Textile Pro",
        "Textile Pro",
        "Текстиль Про",
        "Передала информацию менеджеру",
        "Передам ваше сообщение менеджеру",
        "скоро подключится к диалогу",
        "подключится к диалогу",
        "Поняла, мне нужно немного времени",
        "Скоро вернусь",
    ]

    # Характерные начала ответов бота
    BOT_GREETING_PATTERNS = [
        "Добрый день!",
        "Здравствуйте!",
        "Меня зовут Елена",
        "Я - Елена",
        "консультант компании Textile Pro",
        "консультант Textile Pro",
    ]

    def __init__(
        self,
        min_message_interval: float = 2.0,  # минимальный интервал между сообщениями (секунды)
        max_recent_messages: int = 50,       # количество сохраняемых хешей сообщений
        duplicate_window: int = 300          # окно обнаружения дубликатов (секунды)
    ):
        self.min_message_interval = min_message_interval
        self.max_recent_messages = max_recent_messages
        self.duplicate_window = duplicate_window

        # История сообщений: {chat_id: deque of (timestamp, message_hash)}
        self.message_history: Dict[int, deque] = {}

        # Последнее время сообщения от каждого chat_id
        self.last_message_time: Dict[int, datetime] = {}

        # Множество хешей недавних сообщений для быстрой проверки дубликатов
        self.recent_message_hashes: Set[str] = set()

    def _get_message_hash(self, text: str, chat_id: int) -> str:
        """
        Создает хеш сообщения для обнаружения дубликатов

        Args:
            text: текст сообщения
            chat_id: ID чата

        Returns:
            SHA256 хеш сообщения
        """
        # Нормализуем текст: убираем лишние пробелы, приводим к нижнему регистру
        normalized_text = " ".join(text.lower().split())
        content = f"{chat_id}:{normalized_text}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _is_bot_message_by_text(self, text: str) -> bool:
        """
        Проверяет, похож ли текст на сообщение бота

        Args:
            text: текст для проверки

        Returns:
            True если это похоже на сообщение бота
        """
        text_lower = text.lower()

        # Проверка на характерные подписи
        for signature in self.BOT_SIGNATURES:
            if signature.lower() in text_lower:
                logger.info(f"🔍 Обнаружена подпись бота: '{signature}'")
                return True

        # Проверка на характерные приветствия
        for pattern in self.BOT_GREETING_PATTERNS:
            if text.startswith(pattern) or text_lower.startswith(pattern.lower()):
                logger.info(f"🔍 Обнаружено приветствие бота: '{pattern}'")
                return True

        return False

    def _is_rapid_message(self, chat_id: int) -> bool:
        """
        Проверяет, не слишком ли быстро пришло сообщение

        Args:
            chat_id: ID чата

        Returns:
            True если сообщение пришло слишком быстро
        """
        now = datetime.now()

        if chat_id in self.last_message_time:
            time_diff = (now - self.last_message_time[chat_id]).total_seconds()

            if time_diff < self.min_message_interval:
                logger.warning(f"⚡ Слишком быстрое сообщение от chat {chat_id}: {time_diff:.2f}с < {self.min_message_interval}с")
                return True

        # Обновляем время последнего сообщения
        self.last_message_time[chat_id] = now
        return False

    def _is_duplicate_message(self, text: str, chat_id: int) -> bool:
        """
        Проверяет, не является ли сообщение дубликатом недавнего

        Args:
            text: текст сообщения
            chat_id: ID чата

        Returns:
            True если это дубликат недавнего сообщения
        """
        message_hash = self._get_message_hash(text, chat_id)

        # Проверяем в множестве недавних хешей
        if message_hash in self.recent_message_hashes:
            logger.warning(f"🔄 Обнаружен дубликат сообщения в chat {chat_id}")
            return True

        # Добавляем в историю
        if chat_id not in self.message_history:
            self.message_history[chat_id] = deque(maxlen=self.max_recent_messages)

        now = datetime.now()
        self.message_history[chat_id].append((now, message_hash))

        # Обновляем множество недавних хешей
        self._cleanup_old_hashes()
        self.recent_message_hashes.add(message_hash)

        return False

    def _cleanup_old_hashes(self):
        """Удаляет устаревшие хеши из истории"""
        cutoff_time = datetime.now() - timedelta(seconds=self.duplicate_window)

        # Очищаем историю от старых записей
        for chat_id in list(self.message_history.keys()):
            history = self.message_history[chat_id]

            # Удаляем старые записи
            while history and history[0][0] < cutoff_time:
                old_timestamp, old_hash = history.popleft()
                self.recent_message_hashes.discard(old_hash)

            # Удаляем пустые истории
            if not history:
                del self.message_history[chat_id]

    def should_ignore_message(
        self,
        text: str,
        chat_id: int,
        user_id: int,
        from_business_api: bool = True
    ) -> tuple[bool, Optional[str]]:
        """
        Определяет, нужно ли игнорировать сообщение

        Args:
            text: текст сообщения
            chat_id: ID чата
            user_id: ID пользователя
            from_business_api: пришло ли из Business API

        Returns:
            (should_ignore, reason) - нужно ли игнорировать и причина
        """
        # Если сообщение не из Business API, не проверяем
        if not from_business_api:
            return False, None

        # Проверка 1: Текст похож на сообщение бота
        if self._is_bot_message_by_text(text):
            logger.warning(f"🚫 LOOP DETECTED: Сообщение похоже на ответ бота")
            return True, "bot_message_detected"

        # Проверка 2: Слишком быстрое сообщение
        if self._is_rapid_message(chat_id):
            logger.warning(f"🚫 LOOP DETECTED: Слишком быстрое сообщение")
            return True, "rapid_message"

        # Проверка 3: Дубликат сообщения
        if self._is_duplicate_message(text, chat_id):
            logger.warning(f"🚫 LOOP DETECTED: Дубликат сообщения")
            return True, "duplicate_message"

        # Все проверки пройдены
        logger.debug(f"✅ Сообщение прошло loop detection проверки")
        return False, None

    def track_bot_response(self, text: str, chat_id: int):
        """
        Отслеживает отправленный ответ бота

        Добавляет ответ бота в историю для предотвращения петли,
        если бот случайно получит свое же сообщение обратно.

        Args:
            text: текст ответа бота
            chat_id: ID чата
        """
        message_hash = self._get_message_hash(text, chat_id)

        if chat_id not in self.message_history:
            self.message_history[chat_id] = deque(maxlen=self.max_recent_messages)

        now = datetime.now()
        self.message_history[chat_id].append((now, message_hash))
        self.recent_message_hashes.add(message_hash)

        logger.debug(f"📝 Отслеживаю ответ бота в chat {chat_id}")

    def get_stats(self) -> Dict:
        """
        Получает статистику работы детектора

        Returns:
            Словарь со статистикой
        """
        total_tracked_messages = sum(len(history) for history in self.message_history.values())

        return {
            'tracked_chats': len(self.message_history),
            'total_tracked_messages': total_tracked_messages,
            'recent_hashes_count': len(self.recent_message_hashes),
            'min_message_interval': self.min_message_interval,
            'duplicate_window': self.duplicate_window,
            'last_cleanup': datetime.now().isoformat()
        }
