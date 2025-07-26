from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from models import SubscriptionForm
from db import subscriptions_collection
from utils.save_subsctiption import save_subscription

router = Router()


def format_subscription_preview(data: dict) -> str:
    return (
        f"Подписка:\n"
        f"- ключевые слова: {data.get('keywords')}\n"
        f"- уровень: {data.get('level', 'не указан')}\n"
        f"- регион: {data.get('area', 'не указан')}\n"
        f"- частота: {data.get('frequency')}"
    )

@router.message(F.text.startswith("/subscribe"))
async def handle_subscribe(message: types.Message, state: FSMContext):
    await message.answer("Укажи ключевые слова (например: python backend):")
    await state.set_state(SubscriptionForm.keywords)

@router.message(SubscriptionForm.keywords)
async def handle_keywords(message: types.Message, state: FSMContext):
    await state.update_data(keywords=message.text)
    await message.answer("Укажи уровень (например: junior, middle, senior) или пропусти /skip:")
    await state.set_state(SubscriptionForm.level)

@router.message(SubscriptionForm.level)
async def handle_level(message: types.Message, state: FSMContext):
    if message.text.strip().lower() != "/skip":
        await state.update_data(level=message.text.strip().lower())
    await message.answer("Укажи регион (area id, например: 113 для всей России) или пропусти /skip:")
    await state.set_state(SubscriptionForm.area)

@router.message(SubscriptionForm.area)
async def handle_area(message: types.Message, state: FSMContext):
    if message.text.strip().lower() != "/skip":
        await state.update_data(area=message.text.strip())
    await message.answer("Как часто присылать вакансии? (daily/weekly):")
    await state.set_state(SubscriptionForm.frequency)

@router.message(SubscriptionForm.frequency)
async def handle_frequency(message: types.Message, state: FSMContext):
    freq = message.text.strip().lower()
    if freq not in ("daily", "weekly"):
        await message.answer("Пожалуйста, введи 'daily' или 'weekly'.")
        return

    await state.update_data(frequency=freq, last_sent=None)

    data = await state.get_data()
    preview = format_subscription_preview(data)

    await message.answer(preview + "\n\nПодтверди подписку командой /confirm или /cancel")
    await state.set_state(SubscriptionForm.confirm)

@router.message(F.text == "/confirm", SubscriptionForm.confirm)
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

@router.message(F.text == "/cancel")
async def cancel_subscription(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Подписка отменена.")

@router.message(F.text == "/show_subscriptions")
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

