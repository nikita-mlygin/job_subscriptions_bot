from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB_NAME
import logging

logger = logging.getLogger(__name__)

# создаём клиент MongoDB с учётом часового пояса (tz_aware=True)
client = MongoClient(MONGO_URI, tz_aware=True)

# выбираем базу данных по имени из конфигурации
db = client[MONGO_DB_NAME]

# коллекция для хранения подписок пользователей
subscriptions_collection = db["subscriptions"]

# коллекция для хранения настроек пользователей
user_settings_collection = db["user_settings"]

logger.info(f"Подключение к базе данных '{MONGO_DB_NAME}' установлено. Коллекции: subscriptions, user_settings")
