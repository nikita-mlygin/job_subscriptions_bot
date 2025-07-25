import requests
from datetime import datetime, timedelta, timezone

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TelegramBot/1.0; +http://example.com/bot)"
}

def fetch_vacancies(level=None, keywords=None, area=None, per_page=5, since_minutes_ago=None):
    """
    Получает вакансии с hh.ru.
    :param level: строка-фильтр уровня (например, 'junior')
    :param keywords: ключевые слова (например, 'python')
    :param area: ID региона (например, 113 — Россия)
    :param per_page: количество вакансий
    :param since_minutes_ago: только вакансии, опубликованные за последние N минут
    """
    query_parts = []

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

    if since_minutes_ago:
        date_from = (datetime.now(timezone.utc) - timedelta(minutes=since_minutes_ago)).isoformat()
        params["date_from"] = date_from
        params["order_by"] = "publication_time"

    response = requests.get("https://api.hh.ru/vacancies", params=params, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("items", [])
