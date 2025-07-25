from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram import F
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
import feedparser
from aiogram import types
from hh_api import fetch_vacancies
import asyncio
from aiogram import Router
from datetime import datetime
import random

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import storage

import tempfile
import subprocess
from aiogram import F, types

from aiogram import F, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import json

import asyncio
from datetime import datetime, timedelta, timezone
from pytz import utc  # если нужна временная зона

import tempfile
import subprocess
from pymongo import MongoClient


import config

CITIES = {
    "1": "Москва",
    "2": "Санкт-Петербург",
    "3": "Новосибирск",
    "4": "Екатеринбург",
    "5": "Казань"
}

RSS_URLS = [
    "https://planetpython.org/rss20.xml",
    "https://www.python.org/events/python-events/rss/",
    "https://realpython.com/atom.xml",
    "https://pyfound.blogspot.com/feeds/posts/default",
    "https://pycoders.com/feed/"
]

client = MongoClient("mongodb://localhost:27017/")
db = client["job_bot_db"]
router = Router()
subscriptions_collection = db["subscriptions"]

class SubscriptionForm(StatesGroup):
    keywords = State()
    level = State()
    area = State()
    frequency = State()
    confirm = State()

with open("learning_data.json", encoding="utf-8") as f:
    learning_data = json.load(f)

PYTHON_TIPS = learning_data["tips"]
LEARNING_RESOURCES = learning_data["resources"]




bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()


@dp.message(F.text == "/start")
async def start(message: Message):
    await message.answer("Hello, world!")


@dp.message(F.text.startswith("/vacancies"))
async def vacancies(message: types.Message, state: FSMContext):
    parts = message.text.split(maxsplit=1)
    keywords = parts[1] if len(parts) > 1 else "python"

    data = await state.get_data()
    city_id = data.get("city_id", "1")  # по умолчанию Москва
    level = data.get("level", None)

    display_level = level.capitalize() if level else "любой"
    await message.answer(
        f"Ищу вакансии по запросу: <b>{keywords}</b>, уровень: <b>{display_level}</b>, город: <b>{CITIES.get(city_id, 'Неизвестно')}</b>…"
    )

    try:
        items = fetch_vacancies(keywords=keywords, level=level, area=city_id)
        if not items:
            await message.answer("Вакансий не найдено.")
            return
        for v in items:
            await message.answer(f"<b>{v['name']}</b>\n{v['alternate_url']}")
    except Exception as e:
        await message.answer("Произошла ошибка при получении вакансий 😢")
        print("Ошибка:", e)


@dp.message(F.text == "/settings")
async def settings_main_menu(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="city", callback_data="settings:city")],
        [InlineKeyboardButton(text="level", callback_data="settings:level")],
        [InlineKeyboardButton(text="Мои настройки", callback_data="settings:show")],
    ])
    await message.answer("Настройки:", reply_markup=keyboard)
    
@dp.callback_query(F.data == "settings:city")
async def settings_city(callback: types.CallbackQuery):
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"set_city:{cid}")]
        for cid, name in CITIES.items()
    ]
    buttons.append([InlineKeyboardButton(text="⬅ назад", callback_data="settings:main")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text("Выберите город:", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "settings:level")
async def settings_level(callback: types.CallbackQuery):
    levels = ["junior", "middle", "senior"]
    buttons = [
        [InlineKeyboardButton(text=level.capitalize(), callback_data=f"set_level:{level}")]
        for level in levels
    ]
    buttons.append([InlineKeyboardButton(text="⬅ назад", callback_data="settings:main")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text("Выберите уровень:", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "settings:main")
async def return_to_main_menu(callback: types.CallbackQuery):
    await settings_main_menu(callback.message)
    await callback.answer()
    
@dp.callback_query(F.data.startswith("set_level:"))
async def process_level(callback: types.CallbackQuery, state: FSMContext):
    level = callback.data.split(":")[1]
    await state.update_data(level=level)
    await callback.message.answer(f"Уровень сохранён: {level.capitalize()}")
    await callback.answer()
    
@dp.callback_query(F.data.startswith("set_city:"))
async def process_city(callback: types.CallbackQuery, state: FSMContext):
    city_id = callback.data.split(":")[1]
    await state.update_data(city_id=city_id)
    await callback.message.answer(f"Город сохранён: {CITIES[city_id]}")
    await callback.answer()
    
@dp.callback_query(F.data == "settings:show")
async def show_user_settings(callback: CallbackQuery, state: FSMContext):
    print("getting user data")
    data = await state.get_data()
    print("user data is here")
    city = data.get("city_id", "не выбран")
    level = data.get("level", "не выбран")

    text = f"Ваши текущие настройки:\n\n🌆 Город: {CITIES[city]}\n🎯 Уровень: {level}"
    await callback.message.answer(text)
    
def parse_date(entry):
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6])
    return datetime.min


@dp.message(F.text == "/news")
async def news(message: types.Message):
    all_entries = []

    for url in RSS_URLS:
        feed = feedparser.parse(url)
        all_entries.extend(feed.entries)

    # сортируем по дате (свежие сверху)
    all_entries.sort(key=parse_date, reverse=True)

    if not all_entries:
        await message.answer("Новостей пока нет.")
        return

    for entry in all_entries[:5]:
        title = entry.title
        link = entry.link
        published = entry.get("published", entry.get("updated", "дата неизвестна"))
        await message.answer(f"<b>{title}</b>\n{published}\n{link}")
        
class PylintStates(StatesGroup):
    waiting_for_code = State()

@dp.message(F.text == "/pylint")
async def start_pylint(message: types.Message, state: FSMContext):
    await state.set_state(PylintStates.waiting_for_code)
    await message.answer("Отправь, пожалуйста, код Python в следующем сообщении, оформленный как код.")

@dp.message(PylintStates.waiting_for_code)
async def check_code(message: types.Message, state: FSMContext):
    code = message.text

    # можно добавить очистку от markdown, если нужно
    # например, убрать ```python ... ```
    if code.startswith("```") and code.endswith("```"):
        code = "\n".join(code.split("\n")[1:-1])

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=True) as temp_file:
        temp_file.write(code)
        temp_file.flush()

        result = subprocess.run(
            ["pylint", temp_file.name, "--disable=all", "--enable=E,F,W,C,R"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )

    output = result.stdout.strip()
    if not output:
        await message.answer("Ошибок не найдено! 🎉")
    else:
        if len(output) > 1500:
            output = output[:1500] + "\n\n[вывод обрезан...]"
        await message.answer(f"<pre>{output}</pre>", parse_mode="HTML")

    await state.clear()

@dp.message(F.text == "/tip")
async def send_python_tip(message: types.Message, state: FSMContext):
    data = await state.get_data()
    level = data.get("level", "beginner")
    tip = random.choice(PYTHON_TIPS.get(level, []))
    await message.answer(f"Совет для {level.capitalize()}:\n💡 {tip}")

@dp.message(F.text == "/learn")
async def send_learning_resources(message: types.Message, state: FSMContext):
    data = await state.get_data()
    level = data.get("level", "beginner")
    resources = LEARNING_RESOURCES.get(level, [])
    text = f"Ресурсы для {level.capitalize()}:\n" + "\n".join(f"• {res}" for res in resources)
    await message.answer(text)
    
############    
# ПОДПИСКА #
############

async def daily_job_sending(dp: Dispatcher):
    while True:
        print("Старт проверки подписок и рассылки вакансий")
        now = datetime.now(timezone.utc)
        subscriptions = list(subscriptions_collection.find({}))

        for sub in subscriptions:
            user_id = sub["user_id"]
            keywords = sub.get("keywords")
            level = sub.get("level")
            area = sub.get("area")
            last_sent = sub.get("last_sent")
            frequency = sub.get("frequency")

            if frequency == "weekly":
                if last_sent and (now - last_sent).days < 7:
                    continue
                minutes_since_last = (now - last_sent).total_seconds() / 60 if last_sent else 7 * 24 * 60
            elif frequency == "daily":
                if last_sent and (now - last_sent).days < 1:
                    continue
                minutes_since_last = (now - last_sent).total_seconds() / 60 if last_sent else 24 * 60
            else:
                minutes_since_last = None  # или любое дефолтное значение

            text = " ".join(filter(None, [level, keywords]))
            area_param = area if area else None

            try:
                items = fetch_vacancies(
                    level=level,
                    keywords=keywords,
                    area=area_param,
                    per_page=5,
                    since_minutes_ago=int(minutes_since_last) if minutes_since_last else None
                )
                if not items:
                    continue

                for v in items:
                    url = v.get("alternate_url")
                    name = v.get("name")
                    await bot.send_message(user_id, f"<b>{name}</b>\n{url}")

                subscriptions_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {"last_sent": now}}
                )
            except Exception as e:
                print(f"Ошибка при отправке подписчику {user_id}: {e}")

        await asyncio.sleep(86400)

def save_subscription(subscription: dict):
    user_id = subscription.get("user_id")
    if not user_id:
        raise ValueError("user_id обязателен")
    subscriptions_collection.update_one(
        {"user_id": user_id},
        {"$set": subscription},
        upsert=True
    )

@dp.message(F.text.startswith("/subscribe"))
async def handle_subscribe(message: types.Message, state: FSMContext):
    await message.answer("Укажи ключевые слова (например: python backend):")
    await state.set_state(SubscriptionForm.keywords)

@dp.message(SubscriptionForm.keywords)
async def handle_keywords(message: types.Message, state: FSMContext):
    await state.update_data(keywords=message.text)
    await message.answer("Укажи уровень (например: junior, middle, senior) или пропусти /skip:")
    await state.set_state(SubscriptionForm.level)

@dp.message(SubscriptionForm.level)
async def handle_level(message: types.Message, state: FSMContext):
    if message.text.strip().lower() != "/skip":
        await state.update_data(level=message.text.strip().lower())
    await message.answer("Укажи регион (area id, например: 113 для всей России) или пропусти /skip:")
    await state.set_state(SubscriptionForm.area)

@dp.message(SubscriptionForm.area)
async def handle_area(message: types.Message, state: FSMContext):
    if message.text.strip().lower() != "/skip":
        await state.update_data(area=message.text.strip())
    await message.answer("Как часто присылать вакансии? (daily/weekly):")
    await state.set_state(SubscriptionForm.frequency)

@dp.message(SubscriptionForm.frequency)
async def handle_frequency(message: types.Message, state: FSMContext):
    freq = message.text.strip().lower()
    if freq not in ("daily", "weekly"):
        await message.answer("Пожалуйста, введи 'daily' или 'weekly'.")
        return

    await state.update_data(frequency=freq, last_sent=None)

    data = await state.get_data()
    preview = (
        f"Подписка:\n"
        f"- ключевые слова: {data.get('keywords')}\n"
        f"- уровень: {data.get('level', 'не указан')}\n"
        f"- регион: {data.get('area', 'не указан')}\n"
        f"- частота: {data.get('frequency')}"
    )

    await message.answer(preview + "\n\nПодтверди подписку командой /confirm или /cancel")
    await state.set_state(SubscriptionForm.confirm)

@dp.message(F.text == "/confirm", SubscriptionForm.confirm)
async def confirm_subscription(message: types.Message, state: FSMContext):
    data = await state.get_data()
    subscription = {
        "user_id": message.from_user.id,
        "keywords": data.get("keywords"),
        "level": data.get("level"),
        "area": data.get("area"),
        "frequency": data.get("frequency"),
        "last_sent": None
    }
    save_subscription(subscription)
    await message.answer("Подписка успешно сохранена ✅")
    await state.clear()

@dp.message(F.text == "/cancel")
async def cancel_subscription(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Подписка отменена.")
    
@dp.message(F.text == "/show_subscriptions")
async def show_subscriptions(message: types.Message):
    user_id = message.from_user.id
    subs = list(subscriptions_collection.find({"user_id": user_id}))
    if not subs:
        await message.answer("У тебя пока нет подписок.")
        return

    texts = []
    for i, sub in enumerate(subs, start=1):
        texts.append(
            f"{i}) ключевые слова: {sub.get('keywords', 'не указаны')}\n"
            f"   уровень: {sub.get('level', 'не указан')}\n"
            f"   регион: {sub.get('area', 'не указан')}\n"
            f"   частота: {sub.get('frequency', 'не указана')}\n"
        )

    await message.answer("Твои подписки:\n\n" + "\n".join(texts))


async def main():
    asyncio.create_task(daily_job_sending(dp))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())