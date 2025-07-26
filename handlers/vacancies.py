from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext

from utils.hh_api import fetch_vacancies
from config import CITIES
from utils.user_settings_db import get_user_settings
from logger import logger  # централизованный логгер

# Роутер для команды /vacancies
router = Router()

@router.message(F.text.startswith("/vacancies"))
async def vacancies(message: types.Message, state: FSMContext):
    """
    Обрабатывает команду /vacancies [ключевые слова].

    Параметры:
        message (types.Message): объект сообщения от пользователя
        state (FSMContext): контекст состояния (не используется напрямую)

    Логика:
        1. Извлекает ключевые слова после команды.
        2. Получает настройки пользователя (город, уровень).
        3. Выводит сообщение с фильтрами.
        4. Запрашивает вакансии через API.
        5. Отправляет пользователю список вакансий или сообщение об ошибке.
    """
    user_id = message.from_user.id
    logger.info(f"[VACANCIES] Пользователь {user_id} запросил вакансии")

    # Извлекаем ключевые слова из сообщения (после команды)
    parts = message.text.split(maxsplit=1)
    keywords = parts[1] if len(parts) > 1 else "python"

    # Получаем пользовательские настройки
    user_settings = await get_user_settings(user_id)
    level = user_settings.get("level")           # junior / middle / senior
    city_id = user_settings.get("city_id", "1")  # по умолчанию Москва

    # Формируем отображаемые данные
    display_level = level.capitalize() if level else "любой"
    city_name = CITIES.get(city_id, "Неизвестно")

    logger.debug(f"[VACANCIES] Ключевые слова: {keywords}, уровень: {display_level}, город: {city_name}")

    await message.answer(
        f"Ищу вакансии по запросу: <b>{keywords}</b>, уровень: <b>{display_level}</b>, город: <b>{city_name}</b>…"
    )

    try:
        # Получаем вакансии с помощью API
        items = fetch_vacancies(keywords=keywords, level=level, area=city_id)

        if not items:
            await message.answer("Вакансий не найдено.")
            logger.info(f"[VACANCIES] Вакансии не найдены для {user_id}")
            return

        logger.info(f"[VACANCIES] Найдено {len(items)} вакансий для {user_id}")

        for v in items:
            await message.answer(f"<b>{v['name']}</b>\n{v['alternate_url']}")
    except Exception as e:
        logger.exception(f"[VACANCIES] Ошибка при получении вакансий для пользователя {user_id}: {e}")
        await message.answer("Произошла ошибка при получении вакансий 😢")
