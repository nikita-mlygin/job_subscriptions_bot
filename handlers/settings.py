from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram import types, F, Router
from utils.user_settings_db import get_user_settings, update_user_settings
from config import CITIES
from logger import logger  # централизованный логгер приложения

router = Router()


@router.message(F.text == "/settings")
async def settings_main_menu(message: types.Message):
    """
    Обработчик команды /settings.
    Отправляет главное меню настроек с кнопками выбора города, уровня и просмотра текущих настроек.
    """
    logger.info(f"[Settings] Пользователь {message.from_user.id} открыл меню настроек")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="city", callback_data="settings:city")],
        [InlineKeyboardButton(text="level", callback_data="settings:level")],
        [InlineKeyboardButton(text="Мои настройки", callback_data="settings:show")],
    ])
    # Отправляем сообщение с меню и inline-кнопками
    await message.answer("Настройки:", reply_markup=keyboard)


@router.callback_query(F.data == "settings:city")
async def settings_city(callback: types.CallbackQuery):
    """
    Обработчик callback для выбора города.
    Отправляет список городов с кнопками для выбора, а также кнопку назад в главное меню.
    """
    user_id = callback.from_user.id
    logger.info(f"[Settings] Пользователь {user_id} выбрал меню городов")

    # Формируем кнопки с городами, каждый callback_data содержит id города
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"set_city:{cid}")] for cid, name in CITIES.items()]
    # Добавляем кнопку "назад" для возврата в главное меню настроек
    buttons.append([InlineKeyboardButton(text="⬅ назад", callback_data="settings:main")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    # Редактируем сообщение, чтобы показать список городов с кнопками
    await callback.message.edit_text("Выберите город:", reply_markup=keyboard)
    # Подтверждаем обработку callback (убирает "часики" в интерфейсе Telegram)
    await callback.answer()


@router.callback_query(F.data == "settings:level")
async def settings_level(callback: types.CallbackQuery):
    """
    Обработчик callback для выбора уровня.
    Отправляет список уровней с кнопками, и кнопку назад в главное меню.
    """
    user_id = callback.from_user.id
    logger.info(f"[Settings] Пользователь {user_id} выбрал меню уровней")

    levels = ["junior", "middle", "senior"]
    # Кнопки с названиями уровней и callback_data с выбранным уровнем
    buttons = [[InlineKeyboardButton(text=level.capitalize(), callback_data=f"set_level:{level}")] for level in levels]
    # Кнопка назад
    buttons.append([InlineKeyboardButton(text="⬅ назад", callback_data="settings:main")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    # Редактируем сообщение с выбором уровня
    await callback.message.edit_text("Выберите уровень:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "settings:main")
async def return_to_main_menu(callback: types.CallbackQuery):
    """
    Обработчик callback для возврата в главное меню настроек.
    Просто вызывает функцию отправки главного меню.
    """
    user_id = callback.from_user.id
    logger.info(f"[Settings] Пользователь {user_id} вернулся в главное меню настроек")

    await settings_main_menu(callback.message)
    await callback.answer()


@router.callback_query(F.data.startswith("set_level:"))
async def process_level(callback: types.CallbackQuery):
    """
    Обработчик выбора уровня.
    Обновляет в базе данных уровень пользователя, отправляет подтверждение.
    """
    user_id = callback.from_user.id
    level = callback.data.split(":")[1]
    logger.info(f"[Settings] Пользователь {user_id} установил уровень: {level}")

    # Обновляем данные пользователя в БД
    await update_user_settings(user_id, level=level)
    # Сообщаем пользователю об успешном сохранении
    await callback.message.answer(f"Уровень сохранён: {level.capitalize()}")
    await callback.answer()


@router.callback_query(F.data.startswith("set_city:"))
async def process_city(callback: types.CallbackQuery):
    """
    Обработчик выбора города.
    Обновляет в базе данных выбранный город, отправляет подтверждение.
    """
    user_id = callback.from_user.id
    city_id = callback.data.split(":")[1]
    city_name = CITIES.get(city_id, "неизвестно")
    logger.info(f"[Settings] Пользователь {user_id} установил город: {city_name} ({city_id})")

    # Обновляем данные пользователя в БД
    await update_user_settings(user_id, city_id=city_id)
    # Сообщаем пользователю об успешном сохранении
    await callback.message.answer(f"Город сохранён: {city_name}")
    await callback.answer()


@router.callback_query(F.data == "settings:show")
async def show_user_settings(callback: CallbackQuery):
    """
    Обработчик команды показать текущие настройки пользователя.
    Получает настройки из БД и отправляет пользователю.
    """
    user_id = callback.from_user.id
    logger.info(f"[Settings] Пользователь {user_id} запросил просмотр своих настроек")

    # Получаем настройки из базы
    settings = await get_user_settings(user_id)
    city = settings.get("city_id")
    level = settings.get("level")

    # Формируем текст с текущими настройками, подставляя понятные значения
    text = f"Ваши текущие настройки:\n\n🌆 Город: {CITIES.get(city, 'не выбран')}\n🎯 Уровень: {level if level else 'не выбран'}"
    # Отправляем пользователю
    await callback.message.answer(text)
