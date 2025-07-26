from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
import json
import random
from logger import logger  # централизованный логгер приложения
from utils.user_settings_db import get_user_settings

router = Router()

# Загружаем обучающие данные из JSON-файла при старте бота
with open("learning_data.json", encoding="utf-8") as f:
    learning_data = json.load(f)

# Извлекаем советы по Python и ресурсы для обучения по уровням
PYTHON_TIPS = learning_data["tips"]
LEARNING_RESOURCES = learning_data["resources"]


@router.message(F.text == "/tip")
async def send_python_tip(message: types.Message, state: FSMContext):
    """
    Обработчик команды /tip.
    Получает уровень пользователя из состояния FSM, выбирает случайный совет из списка для этого уровня,
    и отправляет пользователю.
    """
    user_id = message.from_user.id
    # Получаем данные пользователя из FSM, чтобы знать уровень (если не установлен - по умолчанию junior)
    user_settings = await get_user_settings(user_id)
    level = user_settings.get("level", "junior") # junior / middle / senior

    logger.info(f"[Tip] Пользователь {user_id} запросил совет для уровня '{level}'")

    # Получаем список советов для данного уровня, выбираем случайный
    tips_for_level = PYTHON_TIPS.get(level, [])
    if not tips_for_level:
        # Если для уровня нет советов — логируем предупреждение и уведомляем пользователя
        logger.warning(f"[Tip] Для уровня '{level}' нет советов.")
        await message.answer(f"Советов для уровня {level.capitalize()} пока нет.")
        return

    tip = random.choice(tips_for_level)
    # Отправляем выбранный совет пользователю
    await message.answer(f"Совет для {level.capitalize()}:\n💡 {tip}")


@router.message(F.text == "/learn")
async def send_learning_resources(message: types.Message, state: FSMContext):
    """
    Обработчик команды /learn.
    Получает уровень пользователя из FSM, выбирает список обучающих ресурсов для этого уровня,
    формирует список и отправляет пользователю.
    """
    user_id = message.from_user.id
    # Получаем данные пользователя из FSM, чтобы знать уровень (по умолчанию junior)
    user_settings = await get_user_settings(user_id)
    level = user_settings.get("level", "junior") # junior / middle / senior

    logger.info(f"[Learn] Пользователь {user_id} запросил ресурсы для уровня '{level}'")

    # Получаем ресурсы для данного уровня
    resources_for_level = LEARNING_RESOURCES.get(level, [])
    if not resources_for_level:
        # Если для уровня нет ресурсов — логируем предупреждение и сообщаем пользователю
        logger.warning(f"[Learn] Для уровня '{level}' нет ресурсов.")
        await message.answer(f"Ресурсов для уровня {level.capitalize()} пока нет.")
        return

    # Формируем текст с перечнем ресурсов в виде маркированного списка
    text = f"Ресурсы для {level.capitalize()}:\n" + "\n".join(f"• {res}" for res in resources_for_level)
    # Отправляем список ресурсов пользователю
    await message.answer(text)
