import asyncio
import sqlite3
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import *

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================= БАЗА ДАННЫХ =================

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    nickname TEXT UNIQUE,
    rating REAL DEFAULT 0,
    deals INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS chats(
    user1 INTEGER,
    user2 INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS deals(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1 INTEGER,
    user2 INTEGER,
    status TEXT
)
""")

conn.commit()

# ================= СОСТОЯНИЯ =================

user_states = {}
chat_targets = {}
user_messages = {}

# ================= ТАЙМЕРЫ =================

MARKET_COOLDOWN = 60 * 60 * 2.5  # 2.5 часа
CONF_COOLDOWN = 60 * 60 * 2.5    # 2.5 часа

market_cooldowns = {}
conf_cooldowns = {}

# ================= ТЕКСТЫ =================

START_TEXT = """Приветствуем в самом скрытном уголке района Внуково 🕵️‍♀️
Здесь можно быть кем угодно или не быть никем. Ваш анонимный никнейм это ваше альтер-эго, ваш аккаунт не будет высвечиваться ни при публикации объявлений, ни при участии обсуждения на форумах 🛡️
Впишите свой анонимный никнейм :
"""

MARKET_TEXT = """👋 Добро пожаловать в анонимный маркетплейс!
Здесь вы можете опубликовать пост о продаже/покупке любого товара или услуге!
"""

CONF_TEXT = """Добро пожаловать в «Подслушано»! 🤫
Здесь ты можешь без лишних глаз поделиться самой горячей сплетней или топовой новостью.
Твой секрет — наш контент! 👇
"""

COOLDOWN_TEXT = "⏳ Вы уже отправляли сообщение. Попробуйте позже."

SENT_MARKET_TEXT = "✅ Объявление опубликовано"
SENT_CONF_TEXT = "✅ Сообщение отправлено"
SENT_DM_TEXT = "✅ Сообщение отправлено пользователю"
# ================= КЛАВИАТУРЫ =================

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Маркет объявлений")],
            [KeyboardButton(text="🕵️ Подслушано")],
            [KeyboardButton(text="⭐ Рейтинг")],
            [KeyboardButton(text="💬 Личные сообщения")],
            [KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="🚨 Сообщение админу")],
            [KeyboardButton(text="FAQ")]
        ],
        resize_keyboard=True
    )


def back_btn():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад ⏪")]],
        resize_keyboard=True
    )


def chat_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Закрыть чат")]],
        resize_keyboard=True
    )

# ================= ТРЕКИНГ СООБЩЕНИЙ =================

async def track_user_message(message: types.Message):
    user_messages.setdefault(message.from_user.id, [])
    user_messages[message.from_user.id].append(message.message_id)


async def clear_user_messages(chat_id, user_id):
    msgs = user_messages.get(user_id, [])
    for msg_id in msgs:
        try:
            await bot.delete_message(chat_id, msg_id)
        except:
            pass
    user_messages[user_id] = []

# ================= RESET ДО 3 СООБЩЕНИЙ =================

async def reset_dialog(message: types.Message):
    user_states.pop(message.from_user.id, None)

    await clear_user_messages(message.chat.id, message.from_user.id)

    msg1 = await message.answer(START_TEXT)
    msg2 = await message.answer("Ник сохранен")
    msg3 = await message.answer("🏠 Главное меню", reply_markup=main_menu())

    user_messages[message.from_user.id] = [
        msg1.message_id,
        msg2.message_id,
        msg3.message_id
    ]

# ================= SEND CLEAN =================

async def send_clean(message: types.Message, text, reply_markup=None):
    msg = await message.answer(text, reply_markup=reply_markup)
    await track_user_message(msg)
    # ================= START =================

@dp.message(Command("start"))
async def start(message: types.Message):
    cursor.execute("SELECT * FROM users WHERE id=?", (message.from_user.id,))
    user = cursor.fetchone()

    if not user:
        user_states[message.from_user.id] = "nickname"
        msg = await message.answer(START_TEXT)
        await track_user_message(msg)
        return

    await reset_dialog(message)

# ================= СОХРАНЕНИЕ НИКА =================

@dp.message()
async def nickname_handler(message: types.Message):
    if user_states.get(message.from_user.id) != "nickname":
        return

    nickname = message.text.strip()

    cursor.execute(
        "INSERT OR REPLACE INTO users (id, nickname) VALUES (?, ?)",
        (message.from_user.id, nickname)
    )
    conn.commit()

    await reset_dialog(message)

# ================= КНОПКА НАЗАД =================

@dp.message(F.text == "Назад ⏪")
async def back(message: types.Message):
    await reset_dialog(message)
    # ================= МАРКЕТ =================

@dp.message(F.text == "🛒 Маркет объявлений")
async def market(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍️ Перейти в маркет")],
            [KeyboardButton(text="📝 Выставить объявление")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )

    await send_clean(message, MARKET_TEXT, kb)


@dp.message(F.text == "🛍️ Перейти в маркет")
async def go_market(message: types.Message):
    await send_clean(message, MARKET_LINK)


@dp.message(F.text == "📝 Выставить объявление")
async def post_market(message: types.Message):
    user_states[message.from_user.id] = "market"
    await send_clean(message, "Введите текст объявления", back_btn())


# ================= ОТПРАВКА В МАРКЕТ =================

@dp.message()
async def market_handler(message: types.Message):
    if user_states.get(message.from_user.id) != "market":
        return

    now = time.time()
    last = market_cooldowns.get(message.from_user.id, 0)

    if now - last < MARKET_COOLDOWN:
        await send_clean(message, COOLDOWN_TEXT, back_btn())
        return

    cursor.execute(
        "SELECT nickname FROM users WHERE id=?",
        (message.from_user.id,)
    )
    nickname = cursor.fetchone()[0]

    text = f"{message.text}\n\nПользователь: {nickname}"

    if message.photo:
        await bot.send_photo(
            CHANNEL_MARKET,
            message.photo[-1].file_id,
            caption=text
        )
    else:
        await bot.send_message(CHANNEL_MARKET, text)

    market_cooldowns[message.from_user.id] = now

    await reset_dialog(message)
    # ================= ПОДСЛУШАНО =================

@dp.message(F.text == "🕵️ Подслушано")
async def conf(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Перейти в подслушано🤫")],
            [KeyboardButton(text="Отправить сообщение ✏️")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )

    await send_clean(message, CONF_TEXT, kb)


@dp.message(F.text == "Перейти в подслушано🤫")
async def go_conf(message: types.Message):
    await send_clean(message, CONF_LINK)


@dp.message(F.text == "Отправить сообщение ✏️")
async def send_conf(message: types.Message):
    user_states[message.from_user.id] = "conf"
    await send_clean(message, "Введите сообщение", back_btn())


# ================= ОТПРАВКА В ПОДСЛУШАНО =================

@dp.message()
async def conf_handler(message: types.Message):
    if user_states.get(message.from_user.id) != "conf":
        return

    now = time.time()
    last = conf_cooldowns.get(message.from_user.id, 0)

    if now - last < CONF_COOLDOWN:
        await send_clean(message, COOLDOWN_TEXT, back_btn())
        return

    cursor.execute(
        "SELECT nickname FROM users WHERE id=?",
        (message.from_user.id,)
    )
    nickname = cursor.fetchone()[0]

    text = f"{message.text}\n\nПользователь: {nickname}"

    if message.photo:
        await bot.send_photo(
            CHANNEL_CONFESSIONS,
            message.photo[-1].file_id,
            caption=text
        )
    else:
        await bot.send_message(CHANNEL_CONFESSIONS, text)

    conf_cooldowns[message.from_user.id] = now

    await reset_dialog(message)
    # ================= ЛИЧНЫЕ СООБЩЕНИЯ =================

@dp.message(F.text == "💬 Личные сообщения")
async def private_messages(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Написать пользователю ✉️")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )
    await send_clean(message, "Введите ник пользователя", kb)


@dp.message(F.text == "Написать пользователю ✉️")
async def find_user(message: types.Message):
    user_states[message.from_user.id] = "find_user"
    await send_clean(message, "Введите ник", back_btn())


@dp.message()
async def find_user_handler(message: types.Message):
    if user_states.get(message.from_user.id) != "find_user":
        return

    cursor.execute(
        "SELECT id FROM users WHERE nickname=?",
        (message.text,)
    )
    user = cursor.fetchone()

    if not user:
        await send_clean(message, "Пользователь не найден", back_btn())
        return

    chat_targets[message.from_user.id] = user[0]
    user_states[message.from_user.id] = "dm"

    await send_clean(message, "Введите сообщение", back_btn())


# ================= ОТПРАВКА ЛИЧНЫХ СООБЩЕНИЙ =================

@dp.message()
async def dm_handler(message: types.Message):
    if user_states.get(message.from_user.id) != "dm":
        return

    target = chat_targets.get(message.from_user.id)

    if not target:
        await reset_dialog(message)
        return

    cursor.execute(
        "SELECT nickname FROM users WHERE id=?",
        (message.from_user.id,)
    )
    nickname = cursor.fetchone()[0]

    text = f"💬 Новое сообщение\n\n{message.text}\n\nОт: {nickname}"

    try:
        if message.photo:
            await bot.send_photo(
                target,
                message.photo[-1].file_id,
                caption=text
            )
        else:
            await bot.send_message(target, text)

        await reset_dialog(message)

    except:
        await send_clean(message, "Не удалось отправить сообщение", back_btn())


# ================= ЗАПУСК =================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
