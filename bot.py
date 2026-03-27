import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo, FSInputFile, InputMediaPhoto, InputMediaVideo
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
    "*Здарова, братан! Это Лёха 🐔*\n"
    "*Смотри видео сверху за 30 секунд* — там всё показано: как зарегаться, пополнить и найти Курицу\\.\n\n"
    "*Как начать кормиться с Курицы:*\n"
    "1\\. Смотри видео \\(там всё по шагам\\)\n"
    "2\\. Жми кнопку «ИГРАТЬ В КУРИЦУ» ниже\n"
    "3\\. Пополняй от 1000р \\(лучше с 2000, чтоб нормально поиграть\\)\n"
    "4\\. Забирай иксы и сразу выводи на карту, не жадничай\\!\n\n"
    "*Если что\\-то не получается — пиши сразу мне: @alexdavc*"
)

REMINDER_TEXT = (
    "*Брат, важно, послушай\\!*\n\n"
    "Иногда происходит выход из вашего аккаунт, *ради вашей безопасности*\\.\n"
    "Если у тебя *уже был аккаунт*, но тебя выкинуло или просит регистрацию заново — \n"
    "*НЕ создавай новый аккаунт\\!*\n"
    "Просто пролистай чуть ниже — там будет кнопка *\"Войти\"*\\. Жми её\\.\n\n"
    "Так все твои бабки и выигрыши останутся на месте\\.\n"
    "Сделал новый по ошибке — сразу пиши мне @alexdavc, разберём и починим\\."
)

# FSM states for broadcast
class BroadcastStates(StatesGroup):
    waiting_text = State()
    waiting_media = State()
    waiting_buttons = State()
    confirm = State()

broadcast_data = {}

async def send_reminder(chat_id: int):
    await asyncio.sleep(1800)  # 30 minutes
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=REMINDER_TEXT,
            parse_mode="MarkdownV2",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logging.error(f"Failed to send reminder to {chat_id}: {e}")

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = str(message.from_user.id)
    users = load_users()

    # Try to delete the /start message
    try:
        await message.delete()
    except Exception:
        pass

    if user_id in users:
        # Repeat visit
        await bot.send_message(
            chat_id=message.chat.id,
            text="Здарова снова, братан\\! Жми *ИГРАТЬ* 👇",
            parse_mode="MarkdownV2",
            reply_markup=get_main_keyboard()
        )
        return

    # New user — save
    users[user_id] = {
        "first_seen": datetime.now().isoformat(),
        "username": message.from_user.username or ""
    }
    save_users(users)

    # Send welcome with video
    video_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "start.mp4")
    try:
        video = FSInputFile(video_path)
        await bot.send_video(
            chat_id=message.chat.id,
            video=video,
            caption=WELCOME_TEXT,
            parse_mode="MarkdownV2",
            reply_markup=get_main_keyboard()
        )
    except FileNotFoundError:
        await bot.send_message(
            chat_id=message.chat.id,
            text=WELCOME_TEXT,
            parse_mode="MarkdownV2",
            reply_markup=get_main_keyboard()
        )

    # Schedule reminder in 30 minutes
    asyncio.create_task(send_reminder(message.chat.id))

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    users = load_users()
    await message.answer(
        f"👑 *Админ\\-панель*\n\n👥 Всего пользователей: *{len(users)}*",
        parse_mode="MarkdownV2",
        reply_markup=get_admin_keyboard()
    )

@dp.callback_query(F.data == "admin_count")
async def admin_count(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    users = load_users()
    await callback.message.edit_text(
        f"👑 *Админ\\-панель*\n\n👥 Всего пользователей: *{len(users)}*",
        parse_mode="MarkdownV2",
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
        "📢 *Рассылка*\n\nОтправь текст сообщения для рассылки\\.\n"
        "Поддерживается MarkdownV2\\.",
        parse_mode="MarkdownV2"
    )
    await state.set_state(BroadcastStates.waiting_text)
    await callback.answer()

@dp.message(BroadcastStates.waiting_text)
async def broadcast_get_text(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.update_data(text=message.text or message.caption or "")
    await message.answer(
        "📎 Прикрепи фото или видео \\(или напиши /skip\\)",
        parse_mode="MarkdownV2"
    )
    await state.set_state(BroadcastStates.waiting_media)

@dp.message(BroadcastStates.waiting_media, Command("skip"))
async def broadcast_skip_media(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.update_data(media=None, media_type=None)
    await message.answer(
        "🔘 Добавить кнопки\\? Отправь в формате:\n"
        "`Текст кнопки|https://url.com`\n"
        "Каждая кнопка с новой строки\\. Или /skip",
        parse_mode="MarkdownV2"
    )
    await state.set_state(BroadcastStates.waiting_buttons)

@dp.message(BroadcastStates.waiting_media, F.photo)
async def broadcast_get_photo(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.update_data(media=message.photo[-1].file_id, media_type="photo")
    await message.answer(
        "🔘 Добавить кнопки\\? Отправь в формате:\n"
        "`Текст кнопки|https://url.com`\n"
        "Каждая кнопка с новой строки\\. Или /skip",
        parse_mode="MarkdownV2"
    )
    await state.set_state(BroadcastStates.waiting_buttons)

@dp.message(BroadcastStates.waiting_media, F.video)
async def broadcast_get_video(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.update_data(media=message.video.file_id, media_type="video")
    await message.answer(
        "🔘 Добавить кнопки\\? Отправь в формате:\n"
        "`Текст кнопки|https://url.com`\n"
        "Каждая кнопка с новой строки\\. Или /skip",
        parse_mode="MarkdownV2"
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

def parse_buttons(buttons_text: str) -> InlineKeyboardMarkup | None:
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
    buttons_raw = data.get("buttons")
    kb = parse_buttons(buttons_raw) if buttons_raw else None

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
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
