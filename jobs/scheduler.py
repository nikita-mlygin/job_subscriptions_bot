import asyncio
from datetime import datetime, timezone
from db import subscriptions_collection
from utils.hh_api import fetch_vacancies
from aiogram import Bot
from logger import logger

# функция проверяет, нужно ли пропустить отправку подписки на основе частоты и времени последней отправки
def should_skip_sending(frequency: str, last_sent: datetime | None, now: datetime) -> tuple[bool, int]:
    """
    Определяет, следует ли пропустить отправку вакансий по частоте рассылки.

    Параметры:
        frequency (str): Частота рассылки ("daily", "weekly").
        last_sent (datetime | None): Время последней отправки вакансий.
        now (datetime): Текущее время.

    Возвращает:
        tuple[bool, int]: 
            - Нужно ли пропустить отправку (True/False).
            - Количество минут, прошедших с последней отправки или дефолтное значение для частоты.
    """

    # словарь: сколько минут соответствует каждой частоте
    delta_minutes = {
        "daily": 24 * 60,
        "weekly": 7 * 24 * 60
    }

    # если частота не указана корректно, логируем и возвращаем, что не надо пропускать, но не фильтруем по времени
    if frequency not in delta_minutes:
        logger.warning(f"[SUB] Неизвестная частота: {frequency}")
        return False, 0

    # если есть значение последней отправки — сравниваем время
    if last_sent:
        # считаем, сколько минут прошло
        elapsed = (now - last_sent).total_seconds() / 60
        # если прошло меньше, чем надо — пропускаем
        if elapsed < delta_minutes[frequency]:
            return True, int(elapsed)
        # если прошло достаточно — не пропускаем
        return False, int(elapsed)
    else:
        # если ещё не было отправок — не пропускаем
        return False, delta_minutes[frequency]

async def send_vacancies_for_subscription(bot: Bot, sub: dict):
    """
    Выполняет отправку новых вакансий пользователю по его подписке.

    Параметры:
        bot (Bot): Экземпляр Telegram-бота.
        sub (dict): Подписка пользователя, содержащая user_id, параметры фильтрации, частоту, дату последней отправки и др.

    Логика:
        - Проверяет, нужно ли пропустить рассылку в зависимости от частоты и времени.
        - Получает актуальные вакансии.
        - Отправляет сообщения пользователю, если вакансии найдены.
        - Обновляет в базе данных время последней отправки.
        - Логирует шаги и возможные ошибки.
    """
    # получаем user_id и текущий момент времени (в UTC)
    user_id = sub["user_id"]
    now = datetime.now(timezone.utc)

    # достаём параметры из подписки
    last_sent = sub.get("last_sent")
    frequency = sub.get("frequency")
    keywords = sub.get("keywords")
    level = sub.get("level")
    area = sub.get("area")

    # логируем текущие параметры подписки
    logger.info(f"[SUB {user_id}] Проверка: frequency={frequency}, last_sent={last_sent}, now={now}")

    # решаем, нужно ли пропускать отправку
    skip, minutes_since_last = should_skip_sending(frequency, last_sent, now)
    if skip:
        logger.info(f"[SUB {user_id}] Интервал ещё не прошёл ({minutes_since_last:.0f} мин)")
        return

    try:
        # получаем список новых вакансий
        items = fetch_vacancies(
            level=level,
            keywords=keywords,
            area=area,
            per_page=5,  # ограничим до 5 вакансий
            since_minutes_ago=minutes_since_last  # фильтруем по времени
        )

        # если вакансий нет — логируем и выходим
        if not items:
            logger.info(f"[SUB {user_id}] Новых вакансий нет.")
            return

        # логируем количество найденных вакансий
        logger.info(f"[SUB {user_id}] Найдено {len(items)} вакансий.")
        # отправляем каждую вакансию пользователю
        for v in items:
            await bot.send_message(user_id, f"<b>{v['name']}</b>\n{v['alternate_url']}")

        # обновляем поле last_sent в БД, чтобы не слать повторно
        subscriptions_collection.update_one(
            {"_id": sub["_id"]},
            {"$set": {"last_sent": now}}
        )
        logger.info(f"[SUB {user_id}] Подписка обновлена: last_sent={now}")

    # если произошла ошибка — логируем с трейсом
    except Exception as e:
        logger.exception(f"[SUB {user_id}] Ошибка при рассылке: {e}")

# фоновая задача, которая запускается раз в сутки
async def daily_job_sending(bot: Bot):
    """
    Запускает фоновую задачу рассылки вакансий по всем активным подпискам.

    Параметры:
        bot (Bot): Экземпляр Telegram-бота.

    Логика:
        - Проходит по всем подпискам.
        - Пытается отправить подходящие вакансии каждому пользователю.
        - Повторяет цикл каждые 24 часа.
        - Логирует выполнение и ошибки.
    """
    while True:
        # логируем начало задачи
        logger.info("Запуск фоновой задачи рассылки...")

        # достаём все подписки из базы
        subscriptions = list(subscriptions_collection.find({}))

        # проходим по каждой подписке
        for sub in subscriptions:
            try:
                # отправляем вакансии для каждой подписки
                await send_vacancies_for_subscription(bot, sub)
            except Exception as e:
                # если при обработке подписки возникла ошибка — логируем
                logger.exception(f"Ошибка при обработке подписки: user_id={sub.get('user_id')}")

        # логируем паузу и ждём 24 часа
        logger.info("Ожидание следующего запуска через 24 часа...")
        await asyncio.sleep(60 * 60 * 24)
