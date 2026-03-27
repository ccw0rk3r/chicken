import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo, FSInputFile
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import json
import os

TOKEN = "8750232720:AAHq-UBt7fzvofwJHcQHIG6KXBO1U6hmvI4"
ADMIN_ID = 562290016

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

USERS_FILE = "users.json"

def load_users() -> dict:
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users: dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def get_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="ИГРАТЬ В КУРИЦУ 🐔",
            web_app=WebAppInfo(url="https://lvlx.cc/ttnfxrvi8")
        )],
        [InlineKeyboardButton(
            text="ПОМОЩЬ 🆘",
            url="https://t.me/alexdavc"
        )]
    ])

def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Количество юзеров", callback_data="admin_count")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📥 Скачать юзеров", callback_data="admin_download")]
    ])

WELCOME_TEXT = (
    "<b>Здарова, братан! Это Лёха 🐔</b>\n"
    "<b>Смотри видео сверху за 30 секунд</b> — там всё показано: как зарегаться, пополнить и найти Курицу.\n\n"
    "<b>Как начать кормиться с Курицы:</b>\n"
    "1. Смотри видео (там всё по шагам)\n"
    "2. Жми кнопку «ИГРАТЬ В КУРИЦУ» ниже\n"
    "3. Пополняй от 1000р (лучше с 2000, чтоб нормально поиграть)\n"
    "4. Забирай иксы и сразу выводи на карту, не жадничай!\n\n"
    "<b>Если что-то не получается — пиши сразу мне: @alexdavc</b>"
)

REMINDER_TEXT = (
    "<b>Брат, важно, послушай!</b>\n\n"
    "Иногда происходит выход из вашего аккаунт, <b>ради вашей безопасности</b>.\n"
    "Если у тебя <b>уже был аккаунт</b>, но тебя выкинуло или просит регистрацию заново — \n"
    "<b>НЕ создавай новый аккаунт!</b>\n"
    "Просто пролистай чуть ниже — там будет кнопка <b>\"Войти\"</b>. Жми её.\n\n"
    "Так все твои бабки и выигрыши останутся на месте.\n"
    "Сделал новый по ошибке — сразу пиши мне @alexdavc, разберём и починим."
)

class BroadcastStates(StatesGroup):
    waiting_text = State()
    waiting_media = State()
    waiting_buttons = State()
    confirm = State()

async def send_reminder(chat_id: int):
    await asyncio.sleep(1800)
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=REMINDER_TEXT,
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logging.error(f"Failed to send reminder to {chat_id}: {e}")

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = str(message.from_user.id)
    users = load_users()

    if user_id not in users:
        users[user_id] = {
            "first_seen": datetime.now().isoformat(),
            "username": message.from_user.username or ""
        }
        save_users(users)
        asyncio.create_task(send_reminder(message.chat.id))

    video_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "start.mp4")
    try:
        video = FSInputFile(video_path)
        await bot.send_video(
            chat_id=message.chat.id,
            video=video,
            caption=WELCOME_TEXT,
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
    except FileNotFoundError:
        await bot.send_message(
            chat_id=message.chat.id,
            text=WELCOME_TEXT,
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    users = load_users()
    await message.answer(
        f"👑 <b>Админ-панель</b>\n\n👥 Всего пользователей: <b>{len(users)}</b>",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )

@dp.callback_query(F.data == "admin_count")
async def admin_count(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    users = load_users()
    await callback.message.edit_text(
        f"👑 <b>Админ-панель</b>\n\n👥 Всего пользователей: <b>{len(users)}</b>",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_download")
async def admin_download(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    users = load_users()
    content = "\n".join(users.keys())
    file_path = "/tmp/users_list.txt"
    with open(file_path, "w") as f:
        f.write(content)
    await callback.message.answer_document(
        FSInputFile(file_path, filename="users.txt"),
        caption=f"📥 Список пользователей ({len(users)} чел.)"
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.answer(
        "📢 <b>Рассылка</b>\n\nОтправь текст сообщения для рассылки.\nПоддерживается HTML.",
        parse_mode="HTML"
    )
    await state.set_state(BroadcastStates.waiting_text)
    await callback.answer()

@dp.message(BroadcastStates.waiting_text)
async def broadcast_get_text(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.update_data(text=message.text or message.caption or "")
    await message.answer("📎 Прикрепи фото или видео (или напиши /skip)")
    await state.set_state(BroadcastStates.waiting_media)

@dp.message(BroadcastStates.waiting_media, Command("skip"))
async def broadcast_skip_media(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.update_data(media=None, media_type=None)
    await message.answer(
        "🔘 Добавить кнопки? Отправь в формате:\n<code>Текст кнопки|https://url.com</code>\nКаждая кнопка с новой строки. Или /skip",
        parse_mode="HTML"
    )
    await state.set_state(BroadcastStates.waiting_buttons)

@dp.message(BroadcastStates.waiting_media, F.photo)
async def broadcast_get_photo(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.update_data(media=message.photo[-1].file_id, media_type="photo")
    await message.answer(
        "🔘 Добавить кнопки? Отправь в формате:\n<code>Текст кнопки|https://url.com</code>\nКаждая кнопка с новой строки. Или /skip",
        parse_mode="HTML"
    )
    await state.set_state(BroadcastStates.waiting_buttons)

@dp.message(BroadcastStates.waiting_media, F.video)
async def broadcast_get_video(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.update_data(media=message.video.file_id, media_type="video")
    await message.answer(
        "🔘 Добавить кнопки? Отправь в формате:\n<code>Текст кнопки|https://url.com</code>\nКаждая кнопка с новой строки. Или /skip",
        parse_mode="HTML"
    )
    await state.set_state(BroadcastStates.waiting_buttons)

@dp.message(BroadcastStates.waiting_buttons, Command("skip"))
async def broadcast_skip_buttons(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.update_data(buttons=None)
    await _broadcast_confirm(message, state)

@dp.message(BroadcastStates.waiting_buttons)
async def broadcast_get_buttons(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.update_data(buttons=message.text)
    await _broadcast_confirm(message, state)

async def _broadcast_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    users = load_users()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_confirm"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel")
        ]
    ])
    await message.answer(
        f"📋 Подтверди рассылку:\n\n"
        f"Текст: {data.get('text', '')[:100]}...\n"
        f"Медиа: {'есть' if data.get('media') else 'нет'}\n"
        f"Кнопки: {'есть' if data.get('buttons') else 'нет'}\n"
        f"Получателей: {len(users)}",
        reply_markup=kb
    )
    await state.set_state(BroadcastStates.confirm)

def parse_buttons(buttons_text: str):
    if not buttons_text:
        return None
    rows = []
    for line in buttons_text.strip().split("\n"):
        if "|" in line:
            parts = line.split("|", 1)
            btn_text = parts[0].strip()
            btn_url = parts[1].strip()
            rows.append([InlineKeyboardButton(text=btn_text, url=btn_url)])
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None

@dp.callback_query(F.data == "broadcast_confirm")
async def do_broadcast(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    await state.clear()

    users = load_users()
    text = data.get("text", "")
    media = data.get("media")
    media_type = data.get("media_type")
    kb = parse_buttons(data.get("buttons"))

    sent = 0
    failed = 0
    await callback.message.answer(f"⏳ Начинаю рассылку на {len(users)} пользователей...")

    for user_id in users.keys():
        try:
            if media and media_type == "photo":
                await bot.send_photo(int(user_id), photo=media, caption=text, reply_markup=kb)
            elif media and media_type == "video":
                await bot.send_video(int(user_id), video=media, caption=text, reply_markup=kb)
            else:
                await bot.send_message(int(user_id), text=text, reply_markup=kb)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await callback.message.answer(f"✅ Рассылка завершена!\nОтправлено: {sent}\nОшибок: {failed}")
    await callback.answer()

@dp.callback_query(F.data == "broadcast_cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await callback.message.answer("❌ Рассылка отменена.")
    await callback.answer()

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
