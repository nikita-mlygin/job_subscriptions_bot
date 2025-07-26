from db import subscriptions_collection
from logger import logger  # централизованный логгер приложения

def save_subscription(subscription: dict):
    """
    Сохраняет новую подписку в базу данных.

    Аргументы:
    subscription (dict): словарь с данными подписки, должен содержать ключ 'user_id'.

    Исключения:
    ValueError: если 'user_id' отсутствует в словаре подписки.

    Логирует процесс сохранения и ошибки.
    """
    user_id = subscription.get("user_id")  # пытаемся получить user_id из подписки
    if not user_id:
        logger.error("Ошибка сохранения подписки: user_id отсутствует в данных")
        raise ValueError("user_id обязателен")

    try:
        # Вставляем подписку в коллекцию MongoDB
        subscriptions_collection.insert_one(subscription)
        logger.info(f"[Subscriptions] Подписка сохранена для пользователя {user_id}")
    except Exception as e:
        # Логируем ошибку вставки, не поднимаем исключение выше
        logger.exception(f"[Subscriptions] Ошибка при сохранении подписки для пользователя {user_id}: {e}")
