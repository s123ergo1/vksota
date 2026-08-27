"""Модуль формирования клавиатур ВКонтакте (vkbottle).

Содержит функции генерации клавиатур для главного меню, подменю
категории и карточки услуги. Используются ОБЫЧНЫЕ кнопки (Text) с payload,
поскольку событие callback (message_event) в данной группе недоступно
через Long Poll — нажатия приходят как входящие сообщения (message_new)
с сохранённым payload и обрабатываются в обработчике сообщений.
"""

import math
from typing import Dict, List

from vkbottle import Keyboard, KeyboardButtonColor, Text

import services

# Максимальное число услуг на одной странице подменю.
# Обычная клавиатура допускает до 10 строк, но для компактности
# используем 4 услуги в ряд + строка навигации + строка служебных кнопок.
PAGE_SIZE = 4

# Максимальная длина подписи кнопки в ВК (40 символов)
MAX_LABEL_LEN = 40


def _truncate(label: str, max_len: int = MAX_LABEL_LEN) -> str:
    """Обрезать подпись кнопки до допустимой длины ВК.

    Args:
        label: Исходная подпись.
        max_len: Максимальная длина.

    Returns:
        str: Подпись, умещающаяся в лимит (при необходимости с многоточием).
    """
    if len(label) <= max_len:
        return label
    return label[: max_len - 1].rstrip() + "…"


def main_menu_keyboard() -> str:
    """Сформировать клавиатуру главного меню.

    Каждая категория услуг — отдельная кнопка зелёного цвета (POSITIVE),
    последняя кнопка — обращение к менеджеру (PRIMARY).

    Returns:
        str: JSON-строка клавиатуры для передачи в API ВК.
    """
    kb = Keyboard(inline=False)

    # Кнопки категорий — по одной в ряд
    for category_name in services.SERVICES.keys():
        kb.add(
            Text(
                label=category_name,
                payload={"action": "category", "category": category_name},
            ),
            color=KeyboardButtonColor.POSITIVE,
        )
        kb.row()

    # Кнопка обращения к менеджеру
    kb.add(
        Text(
            label="💬 Обратиться к менеджеру",
            payload={"action": "manager"},
        ),
        color=KeyboardButtonColor.PRIMARY,
    )

    return kb.get_json()


def category_keyboard(category_name: str, page: int = 0) -> str:
    """Сформировать клавиатуру подменю выбранной категории.

    Отображает страницу списка услуг (каждая — отдельная кнопка),
    кнопки постраничной навигации, а также кнопки «Назад в меню»
    и «Обратиться к менеджеру».

    Args:
        category_name: Название категории из словаря SERVICES.
        page: Номер страницы (начиная с 0).

    Returns:
        str: JSON-строка клавиатуры для передачи в API ВК.
    """
    kb = Keyboard(inline=False)

    items: List[Dict[str, str]] = services.SERVICES[category_name]["items"]
    total_pages = max(1, math.ceil(len(items) / PAGE_SIZE))

    # Корректируем номер страницы в допустимых пределах
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE

    # Кнопки услуг текущей страницы
    for index in range(start, min(end, len(items))):
        item = items[index]
        label = _truncate(f"{item['name']} — {item['price']} | {item['duration']}")
        kb.add(
            Text(
                label=label,
                payload={
                    "action": "service_detail",
                    "category": category_name,
                    "service_index": index,
                },
            ),
            color=KeyboardButtonColor.SECONDARY,
        )
        kb.row()

    # Навигация по страницам (если услуг больше одной страницы)
    if total_pages > 1:
        if page > 0:
            kb.add(
                Text(
                    label="⬅ Назад",
                    payload={
                        "action": "category_page",
                        "category": category_name,
                        "page": page - 1,
                    },
                ),
                color=KeyboardButtonColor.SECONDARY,
            )
        if page < total_pages - 1:
            kb.add(
                Text(
                    label="➡ Далее",
                    payload={
                        "action": "category_page",
                        "category": category_name,
                        "page": page + 1,
                    },
                ),
                color=KeyboardButtonColor.SECONDARY,
            )
        kb.row()

    # Кнопка возврата в главное меню и обращения к менеджеру — в одну строку
    kb.add(
        Text(
            label="⬅ Назад в меню",
            payload={"action": "back_to_main"},
        ),
        color=KeyboardButtonColor.PRIMARY,
    )
    kb.add(
        Text(
            label="💬 Обратиться к менеджеру",
            payload={"action": "manager"},
        ),
        color=KeyboardButtonColor.PRIMARY,
    )

    return kb.get_json()


def service_detail_keyboard(category_name: str, service_index: int) -> str:
    """Сформировать клавиатуру карточки конкретной услуги.

    Содержит кнопки записи на услугу, возврата к списку и обращения
    к менеджеру.

    Args:
        category_name: Название категории услуги.
        service_index: Индекс услуги в списке категории.

    Returns:
        str: JSON-строка клавиатуры для передачи в API ВК.
    """
    kb = Keyboard(inline=False)

    # Кнопка записи на услугу
    kb.add(
        Text(
            label="📅 Записаться",
            payload={
                "action": "book",
                "category": category_name,
                "service_index": service_index,
            },
        ),
        color=KeyboardButtonColor.POSITIVE,
    )
    kb.row()

    # Кнопка возврата к списку услуг категории
    kb.add(
        Text(
            label="⬅ Назад к списку",
            payload={"action": "back_to_category", "category": category_name},
        ),
        color=KeyboardButtonColor.PRIMARY,
    )
    kb.row()

    # Кнопка обращения к менеджеру
    kb.add(
        Text(
            label="💬 Обратиться к менеджеру",
            payload={"action": "manager"},
        ),
        color=KeyboardButtonColor.PRIMARY,
    )

    return kb.get_json()
