from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram import F
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
import asyncio
from utils.user_settings_db import get_user_settings;
from utils.user_settings_db import update_user_settings;
from aiogram.types import BotCommandScopeDefault

from config import CITIES

from config import BOT_TOKEN
from handlers import subscribe
from handlers import pylint
from handlers import news
from handlers import tips_and_learn
from handlers import vacancies
from handlers import settings
from jobs.scheduler import daily_job_sending

from aiogram.types import BotCommand

commands = [
    BotCommand(command="settings", description="Изменить город и уровень"),
    BotCommand(command="subscribe", description="Оформить подписку на вакансии"),
    BotCommand(command="unsubscribe", description="Удалить подписку"),
    BotCommand(command="vacancies", description="Поиск вакансий по ключевым словам"),
    BotCommand(command="news", description="Текущие новости из IT"),
    BotCommand(command="pylint", description="Полезные советы по Python-коду"),
    BotCommand(command="tip", description="Случайный совет для программиста"),
    BotCommand(command="learn", description="Ресурсы и материалы для обучения"),
    BotCommand(command="show_subscriptions", description="Показать все мои подписки"),
]
# === Константы и глобальные объекты ===

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

dp.include_router(subscribe.router)
dp.include_router(pylint.router)
dp.include_router(news.router)
dp.include_router(tips_and_learn.router)
dp.include_router(vacancies.router)
dp.include_router(settings.router)

# === Хэндлеры ===


async def main():
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    asyncio.create_task(daily_job_sending(bot))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
