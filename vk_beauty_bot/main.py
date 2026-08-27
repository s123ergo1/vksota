"""Точка входа VK-бота консультанта салона красоты (vkbottle).

Инициализирует бота на базе фреймворка vkbottle, регистрирует обработчик
входящих сообщений (включая нажатия кнопок, приходящие как message_new
с payload) и запускает Long Poll.
"""

import logging
import sys

from vkbottle.bot import Bot, Message

import config
import handlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("vk_beauty_bot")


def main() -> None:
    """Запустить бота.

    Загружает токен, создаёт экземпляр Bot, регистрирует обработчики
    и запускает поллинг Long Poll.
    """
    if not config.VK_TOKEN:
        logger.error(
            "Не задан VK_TOKEN. Укажите его в файле .env и перезапустите бота."
        )
        sys.exit(1)

    # Создание бота (фреймворк vkbottle)
    bot = Bot(token=config.VK_TOKEN)

    # Обработка любого входящего сообщения. Нажатия кнопок приходят сюда же
    # как message_new с payload (событие message_event в Long Poll недоступно),
    # поэтому вся логика навигации реализована в handle_message.
    @bot.on.message()
    async def on_message(message: Message) -> None:
        await handlers.handle_message(message)

    logger.info("Бот запущен. Ожидание событий...")
    # Запуск Long Poll (синхронная обёртка, блокирует выполнение)
    bot.run()


if __name__ == "__main__":
    main()
