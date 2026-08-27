"""Модуль обработчиков сообщений ВКонтакте (vkbottle).

Так как событие callback (message_event) в группе недоступно через Long Poll,
нажатия кнопок поступают как входящие сообщения (message_new) с payload.
Логика: приветствие при обычном тексте и навигация по каталогу при
наличии payload-кнопки.

Объект Message в vkbottle уже содержит API-клиент, поэтому отправка
выполняется напрямую через message.answer(...).
"""

import json
import logging
from typing import Any, Dict

from vkbottle.bot import Message

import keyboards
import services

logger = logging.getLogger(__name__)

# Название салона для приветственного сообщения
SALON_NAME = "Гармония"


def _parse_payload(raw: Any) -> Dict[str, Any] | None:
    """Распарсить payload кнопки.

    В vkbottle поле message.payload приходит как строка JSON. Поддерживаем
    как готовый словарь, так и JSON-строку.

    Args:
        raw: Исходный payload из сообщения.

    Returns:
        Dict[str, Any] | None: Словарь с данными кнопки или None.
    """
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else None
    return None


async def handle_message(message: Message) -> None:
    """Обработать входящее сообщение.

    Если сообщение пришло от нажатия кнопки (содержит payload с 'action'),
    выполняется соответствующая навигация. Иначе отправляется приветствие
    и главное меню.

    Args:
        message: Объект входящего сообщения vkbottle.
    """
    payload: Dict[str, Any] | None = _parse_payload(message.payload)

    # Нажатие кнопки (регулярная клавиатура передаёт payload)
    if isinstance(payload, dict) and payload.get("action"):
        await _dispatch(payload, message)
        return

    # Приветствие для произвольного текстового сообщения
    greeting = (
        f"👋 Добро пожаловать в салон красоты «{SALON_NAME}»!\n\n"
        "Я — ваш виртуальный консультант. Выберите интересующую вас "
        "категорию услуг, и я покажу полный перечень с ценами.\n\n"
        "Если у вас возникнут вопросы — нажмите кнопку "
        "«Обратиться к менеджеру», и мы свяжемся с вами "
        "в ближайшее время. ✨"
    )
    await message.answer(greeting, keyboard=keyboards.main_menu_keyboard())


async def _dispatch(payload: Dict[str, Any], message: Message) -> None:
    """Разобрать payload кнопки и выполнить действие.

    Args:
        payload: Данные кнопки (словарь с 'action').
        message: Объект входящего сообщения (для ответа).
    """
    try:
        action = payload.get("action")

        if action == "category":
            await _show_category(payload, message, page=0)
        elif action == "category_page":
            await _show_category(payload, message, page=int(payload.get("page", 0)))
        elif action == "service_detail":
            await _show_service_detail(payload, message)
        elif action == "back_to_main":
            await message.answer(
                "Выберите категорию услуг:",
                keyboard=keyboards.main_menu_keyboard(),
            )
        elif action == "back_to_category":
            await _show_category(payload, message, page=0)
        elif action == "book":
            await _show_book(payload, message)
        elif action == "manager":
            await _show_manager(message)
        else:
            raise ValueError(f"Неизвестное действие: {action}")
    except (KeyError, IndexError, ValueError) as exc:
        logger.error("Ошибка обработки действия %s: %s", payload.get("action"), exc)
        await message.answer(
            "⚠️ Произошла ошибка. Пожалуйста, начните сначала.",
            keyboard=keyboards.main_menu_keyboard(),
        )


async def _show_category(
    payload: Dict[str, Any], message: Message, page: int
) -> None:
    """Показать подменю выбранной категории (с учётом страницы).

    Args:
        payload: Данные кнопки (должны содержать 'category').
        message: Объект входящего сообщения.
        page: Номер страницы подменю.
    """
    category_name: str = payload["category"]
    if category_name not in services.SERVICES:
        raise KeyError(f"Категория не найдена: {category_name}")

    icon = services.SERVICES[category_name]["icon"]
    text = f"{icon} Категория: {category_name}\n\nВыберите услугу из списка ниже:"
    await message.answer(text, keyboard=keyboards.category_keyboard(category_name, page))


async def _show_service_detail(payload: Dict[str, Any], message: Message) -> None:
    """Показать карточку конкретной услуги.

    Args:
        payload: Данные кнопки (category, service_index).
        message: Объект входящего сообщения.
    """
    category_name: str = payload["category"]
    service_index: int = int(payload["service_index"])
    item = services.SERVICES[category_name]["items"][service_index]

    text = (
        f"▫ Услуга: {item['name']}\n"
        f"▫ Цена: {item['price']}\n"
        f"▫ Длительность: {item['duration']}\n\n"
        f"📝 Описание: {item['description']}"
    )
    await message.answer(
        text,
        keyboard=keyboards.service_detail_keyboard(category_name, service_index),
    )


async def _show_book(payload: Dict[str, Any], message: Message) -> None:
    """Обработать запись на выбранную услугу.

    Args:
        payload: Данные кнопки (category, service_index).
        message: Объект входящего сообщения.
    """
    category_name: str = payload["category"]
    service_index: int = int(payload["service_index"])
    item = services.SERVICES[category_name]["items"][service_index]

    await message.answer(
        f"✅ Вы выбрали: {item['name']}. "
        "Менеджер свяжется с вами для подтверждения записи!",
        keyboard=keyboards.main_menu_keyboard(),
    )


async def _show_manager(message: Message) -> None:
    """Обработать обращение к менеджеру.

    Args:
        message: Объект входящего сообщения.
    """
    await message.answer(
        "📞 Ваш запрос передан менеджеру. Ожидайте ответа в течение "
        "15 минут в рабочее время (10:00–21:00).",
        keyboard=keyboards.main_menu_keyboard(),
    )
