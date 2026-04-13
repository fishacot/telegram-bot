import asyncio
import sqlite3
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import *

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================= БАЗА =================

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

conn.commit()

# ================= СОСТОЯНИЯ =================

user_states = {}
chat_targets = {}
user_messages = {}

# ================= ТАЙМЕРЫ =================

MARKET_COOLDOWN = 60 * 60 * 2.5
CONF_COOLDOWN = 60 * 60 * 2.5

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
# ================= КЛАВИАТУРЫ =================

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Маркет")],
            [KeyboardButton(text="🕵️ Подслушано")],
            [KeyboardButton(text="💬 Личные сообщения")],
            [KeyboardButton(text="⭐ Рейтинг")],
            [KeyboardButton(text="👤 Профиль")],
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


# ================= ОТСЛЕЖИВАНИЕ СООБЩЕНИЙ =================

async def track_user_message(message: types.Message):
    user_messages.setdefault(message.from_user.id, [])
    user_messages[message.from_user.id].append(message.message_id)


# ================= ОЧИСТКА ДО 3 СООБЩЕНИЙ =================

async def clear_to_three(message: types.Message):
    msgs = user_messages.get(message.from_user.id, [])

    if len(msgs) <= 3:
        return

    for msg_id in msgs[:-3]:
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except:
            pass

    user_messages[message.from_user.id] = msgs[-3:]


async def send_clean(message: types.Message, text, kb=None, clear=False):
    if clear:
        await clear_to_three(message)

    msg = await message.answer(text, reply_markup=kb)
    await track_user_message(msg)


# ================= ТАЙМЕРЫ =================

def check_market(user_id):
    now = time.time()
    last = market_cooldowns.get(user_id)

    if not last:
        return True

    return now - last >= MARKET_COOLDOWN


def check_conf(user_id):
    now = time.time()
    last = conf_cooldowns.get(user_id)

    if not last:
        return True

    return now - last >= CONF_COOLDOWN
    # ================= START =================

@dp.message(Command("start"))
async def start(message: types.Message):

    cursor.execute(
        "SELECT id FROM users WHERE id=?",
        (message.from_user.id,)
    )
    user = cursor.fetchone()

    # если новый пользователь
    if not user:
        user_states[message.from_user.id] = "nickname"

        msg = await message.answer(START_TEXT)
        await track_user_message(msg)
        return

    # если уже зарегистрирован
    msg = await message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu()
    )
    await track_user_message(msg)


# ================= НАЗАД =================

@dp.message(F.text == "Назад ⏪")
async def back(message: types.Message):

    user_states.pop(message.from_user.id, None)

    await clear_to_three(message)

    msg = await message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu()
    )
    await track_user_message(msg)


# ================= РЕГИСТРАЦИЯ НИКА =================

@dp.message()
async def nickname_handler(message: types.Message):

    state = user_states.get(message.from_user.id)

    if state != "nickname":
        return

    cursor.execute(
        "SELECT id FROM users WHERE nickname=?",
        (message.text,)
    )
    exists = cursor.fetchone()

    if exists:
        msg = await message.answer("❌ Такой ник уже занят")
        await track_user_message(msg)
        return

    cursor.execute(
        "INSERT INTO users(id,nickname) VALUES (?,?)",
        (message.from_user.id, message.text)
    )
    conn.commit()

    user_states.pop(message.from_user.id, None)

    msg = await message.answer("Ник сохранен")
    await track_user_message(msg)

    msg = await message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu()
    )
    await track_user_message(msg)
    # ================= МАРКЕТ =================

@dp.message(F.text == "🛒 Маркет")
async def market(message: types.Message):

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Разместить объявление")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )

    msg = await message.answer(MARKET_TEXT, reply_markup=kb)
    await track_user_message(msg)


@dp.message(F.text == "📝 Разместить объявление")
async def market_post(message: types.Message):

    user_states[message.from_user.id] = "market"

    msg = await message.answer(
        "Введите текст объявления",
        reply_markup=back_btn()
    )
    await track_user_message(msg)


# ================= ПОДСЛУШАНО =================

@dp.message(F.text == "🕵️ Подслушано")
async def conf(message: types.Message):

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✏️ Написать")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )

    msg = await message.answer(CONF_TEXT, reply_markup=kb)
    await track_user_message(msg)


@dp.message(F.text == "✏️ Написать")
async def conf_post(message: types.Message):

    user_states[message.from_user.id] = "conf"

    msg = await message.answer(
        "Введите сообщение",
        reply_markup=back_btn()
    )
    await track_user_message(msg)
    # ================= ЛИЧНЫЕ СООБЩЕНИЯ =================

@dp.message(F.text == "💬 Личные сообщения")
async def private_menu(message: types.Message):

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔎 Найти пользователя")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )

    msg = await message.answer(
        "Введите ник пользователя для начала общения",
        reply_markup=kb
    )
    await track_user_message(msg)


@dp.message(F.text == "🔎 Найти пользователя")
async def find_user(message: types.Message):

    user_states[message.from_user.id] = "find_user"

    msg = await message.answer(
        "Введите ник",
        reply_markup=back_btn()
    )
    await track_user_message(msg)


# ================= ОТКРЫТИЕ ЧАТА =================

async def open_chat(user1, user2):
    chat_targets[user1] = user2
    chat_targets[user2] = user1

    user_states[user1] = "chat"
    user_states[user2] = "chat"


# ================= ЧАТ HANDLER =================

@dp.message()
async def chat_handler(message: types.Message):

    await track_user_message(message)

    state = user_states.get(message.from_user.id)

    # ---------- поиск пользователя ----------
    if state == "find_user":

        cursor.execute(
            "SELECT id FROM users WHERE nickname=?",
            (message.text,)
        )
        user = cursor.fetchone()

        if not user:
            msg = await message.answer(
                "Пользователь не найден",
                reply_markup=back_btn()
            )
            await track_user_message(msg)
            return

        target = user[0]

        if target == message.from_user.id:
            msg = await message.answer("Нельзя написать самому себе")
            await track_user_message(msg)
            return

        await open_chat(message.from_user.id, target)

        msg = await message.answer(
            "Чат открыт",
            reply_markup=chat_keyboard()
        )
        await track_user_message(msg)
        return

    # ---------- чат ----------
    if state == "chat":

        if message.text == "❌ Закрыть чат":
            user_states.pop(message.from_user.id, None)

            await clear_to_three(message)

            msg = await message.answer(
                "🏠 Главное меню",
                reply_markup=main_menu()
            )
            await track_user_message(msg)
            return

        target = chat_targets.get(message.from_user.id)

        if not target:
            return

        cursor.execute(
            "SELECT nickname FROM users WHERE id=?",
            (message.from_user.id,)
        )
        nick = cursor.fetchone()[0]

        text = f"💬 {nick}:\n{message.text}"

        await bot.send_message(target, text)
        return
        # ================= ОСНОВНОЙ HANDLER =================

@dp.message()
async def main_handler(message: types.Message):

    await track_user_message(message)

    state = user_states.get(message.from_user.id)

    # ================= MARKET =================
    if state == "market":

        if not check_market(message.from_user.id):
            msg = await message.answer(
                "⏳ Объявление можно размещать раз в 2.5 часа"
            )
            await track_user_message(msg)
            return

        cursor.execute(
            "SELECT nickname FROM users WHERE id=?",
            (message.from_user.id,)
        )
        nick = cursor.fetchone()[0]

        text = f"{message.text}\n\nНик: {nick}"

        await bot.send_message(CHANNEL_MARKET, text)

        market_cooldowns[message.from_user.id] = time.time()

        user_states.pop(message.from_user.id, None)

        await clear_to_three(message)

        msg = await message.answer(
            "Объявление опубликовано",
            reply_markup=main_menu()
        )
        await track_user_message(msg)
        return


    # ================= CONF =================
    if state == "conf":

        if not check_conf(message.from_user.id):
            msg = await message.answer(
                "⏳ Сообщение можно отправлять раз в 2.5 часа"
            )
            await track_user_message(msg)
            return

        cursor.execute(
            "SELECT nickname FROM users WHERE id=?",
            (message.from_user.id,)
        )
        nick = cursor.fetchone()[0]

        text = f"{message.text}\n\nНик: {nick}"

        await bot.send_message(CHANNEL_CONFESSIONS, text)

        conf_cooldowns[message.from_user.id] = time.time()

        user_states.pop(message.from_user.id, None)

        await clear_to_three(message)

        msg = await message.answer(
            "Сообщение отправлено",
            reply_markup=main_menu()
        )
        await track_user_message(msg)
        return

# ================= ЗАПУСК =================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())



