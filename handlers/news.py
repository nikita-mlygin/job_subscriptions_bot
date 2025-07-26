from datetime import datetime
import feedparser

from aiogram import types, F, Router
from logger import logger

# Создаём роутер для подключения к боту
router = Router()

def parse_date(entry) -> datetime:
    """
    Извлекает дату публикации из RSS-записи.

    Параметры:
        entry: Один элемент из RSS-ленты, полученный через feedparser.

    Возвращает:
        datetime: Дата публикации или datetime.min, если ничего не удалось найти.
    """
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6])
    return datetime.min

# Список RSS-источников по Python
RSS_URLS = [
    "https://planetpython.org/rss20.xml",
    "https://www.python.org/events/python-events/rss/",
    "https://realpython.com/atom.xml",
    "https://pyfound.blogspot.com/feeds/posts/default",
    "https://pycoders.com/feed/"
]

@router.message(F.text == "/news")
async def news(message: types.Message):
    """
    Обрабатывает команду /news: собирает свежие новости из нескольких RSS-источников.

    Параметры:
        message (types.Message): Сообщение от пользователя.

    Логика:
        - Загружает все ленты из списка RSS_URLS.
        - Объединяет записи в один список.
        - Сортирует по дате публикации.
        - Отправляет 5 самых свежих новостей пользователю.
    """
    logger.info(f"[NEWS] Запрос новостей от пользователя {message.from_user.id}")
    all_entries = []

    for url in RSS_URLS:
        logger.debug(f"[NEWS] Парсинг ленты: {url}")
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                logger.warning(f"[NEWS] Лента пуста: {url}")
            all_entries.extend(feed.entries)
        except Exception as e:
            logger.exception(f"[NEWS] Ошибка при парсинге {url}: {e}")

    logger.debug(f"[NEWS] Всего записей собрано: {len(all_entries)}")
    all_entries.sort(key=parse_date, reverse=True)

    if not all_entries:
        await message.answer("Новостей пока нет.")
        logger.info("[NEWS] Нет доступных новостей")
        return

    logger.info(f"[NEWS] Отправляем {min(5, len(all_entries))} свежих новостей пользователю {message.from_user.id}")
    for entry in all_entries[:5]:
        title = entry.title
        link = entry.link
        published = entry.get("published", entry.get("updated", "дата неизвестна"))
        try:
            await message.answer(f"<b>{title}</b>\n{published}\n{link}")
        except Exception as e:
            logger.exception(f"[NEWS] Ошибка при отправке новости '{title}' пользователю {message.from_user.id}: {e}")
