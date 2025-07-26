import requests
from datetime import datetime, timedelta, timezone
from logger import logger  # централизованный логгер

# Заголовки для имитации обычного браузера (некоторые API отказывают ботам)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TelegramBot/1.0; +http://example.com/bot)"
}

def fetch_vacancies(level=None, keywords=None, area=None, per_page=5, since_minutes_ago=None):
    """
    Выполняет запрос к API hh.ru для получения вакансий по заданным параметрам.

    Параметры:
        level (str): уровень вакансии (например, junior, middle, senior)
        keywords (str): ключевые слова поиска (например, "python developer")
        area (str): ID региона (например, "1" — Москва)
        per_page (int): количество вакансий на странице (по умолчанию 5)
        since_minutes_ago (int): если задано — фильтрует вакансии, опубликованные за последние N минут

    Возвращает:
        list: список словарей с данными о вакансиях

    Исключения:
        requests.exceptions.RequestException: если запрос завершился с ошибкой
    """
    query_parts = []

    # Собираем текст запроса из уровня и ключевых слов
    if level:
        query_parts.append(level)
    if keywords:
        query_parts.append(keywords)

    params = {
        "per_page": per_page
    }

    if query_parts:
        params["text"] = " ".join(query_parts)

    if area:
        params["area"] = area

    # Если указан интервал времени — фильтруем по дате публикации
    if since_minutes_ago:
        date_from = (datetime.now(timezone.utc) - timedelta(minutes=since_minutes_ago)).isoformat()
        params["date_from"] = date_from
        params["order_by"] = "publication_time"

    try:
        logger.debug(f"[HH API] Выполняется запрос с параметрами: {params}")
        response = requests.get("https://api.hh.ru/vacancies", params=params, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        logger.info(f"[HH API] Получено {len(data.get('items', []))} вакансий")
        return data.get("items", [])
    except requests.exceptions.RequestException as e:
        logger.exception(f"[HH API] Ошибка при выполнении запроса: {e}")
        raise
