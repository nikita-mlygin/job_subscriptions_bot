from db import user_settings_collection
from pymongo import ReturnDocument
import logging

logger = logging.getLogger(__name__)

async def get_user_settings(user_id: int) -> dict:
    """
    получает настройки пользователя из базы данных по user_id

    :param user_id: уникальный идентификатор пользователя
    :return: словарь с настройками пользователя (если нет в базе — возвращает значения по умолчанию)
    """
    try:
        # пытаемся найти документ с настройками пользователя
        doc = user_settings_collection.find_one({"user_id": user_id})
        if doc:
            logger.info(f"Настройки пользователя {user_id} успешно загружены")
            return doc
        else:
            logger.info(f"Настройки пользователя {user_id} не найдены, возвращаем значения по умолчанию")
            return {"user_id": user_id, "city_id": None, "level": None}
    except Exception as e:
        logger.error(f"Ошибка при получении настроек пользователя {user_id}: {e}")
        # возвращаем значения по умолчанию при ошибке чтения
        return {"user_id": user_id, "city_id": None, "level": None}

async def update_user_settings(user_id: int, **kwargs):
    """
    обновляет настройки пользователя в базе данных или создаёт новый документ, если его нет

    :param user_id: уникальный идентификатор пользователя
    :param kwargs: ключевые параметры для обновления (например, city_id, level)
    """
    try:
        result = user_settings_collection.find_one_and_update(
            {"user_id": user_id},
            {"$set": kwargs},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        logger.info(f"Настройки пользователя {user_id} обновлены: {kwargs}")
        return result
    except Exception as e:
        # Логируем ошибку вставки, не поднимаем исключение выше
        logger.error(f"Ошибка при обновлении настроек пользователя {user_id}: {e}")
