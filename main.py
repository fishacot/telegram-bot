import asyncio
import sqlite3
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import *

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
nickname TEXT UNIQUE,
rating REAL DEFAULT 0,
deals INTEGER DEFAULT 0
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS chats(
user1 INTEGER,
user2 INTEGER
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS deals(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user1 INTEGER,
user2 INTEGER,
status TEXT
)""")

conn.commit()

user_states = {}
chat_targets = {}
user_messages = {}

post_cooldowns = {}
COOLDOWN = 9000

MARKET_LINK = "https://t.me/VnykovoAnonMarket"
CONF_LINK = "https://t.me/podslyshenoVnykovo"
FAQ_LINK = "https://t.me/abouuttanonvnykovo11"


def check_cooldown(user_id):
    now = time.time()
    last = post_cooldowns.get(user_id)

    if not last:
        return True, 0

    diff = now - last
    if diff >= COOLDOWN:
        return True, 0

    return False, int(COOLDOWN - diff)


def format_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}ч {m}мин"


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Маркет")],
            [KeyboardButton(text="🕵️ Подслушано")],
            [KeyboardButton(text="🔒 Сделки через гаранта")],
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


async def track_user_message(message: types.Message):
    user_messages.setdefault(message.from_user.id, [])
    user_messages[message.from_user.id].append(message.message_id)


# ПОЛНАЯ ОЧИСТКА
async def full_clear(message: types.Message):
    msgs = user_messages.get(message.from_user.id, [])

    for msg_id in msgs:
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except:
            pass

    user_messages[message.from_user.id] = []
# ---------------- СТАРТ ----------------

WELCOME_TEXT = """Приветствуем в самом скрытном уголке района Внуково 🕵️‍♀️

Здесь можно быть кем угодно или не быть никем. Ваш анонимный никнейм это ваше альтер-эго, ваш аккаунт не будет высвечиваться ни при публикации объявлений, ни при участии обсуждения на форумах 🛡️

Впишите свой анонимный никнейм :
"""


async def show_main_three(message: types.Message, nick_saved=False):
    await full_clear(message)

    msg1 = await message.answer(WELCOME_TEXT)
    await track_user_message(msg1)

    if nick_saved:
        msg2 = await message.answer("✅ Ник сохранен")
    else:
        msg2 = await message.answer("Введите ваш анонимный никнейм")
    await track_user_message(msg2)

    msg3 = await message.answer("🏠 Главное меню", reply_markup=main_menu())
    await track_user_message(msg3)


@dp.message(Command("start"))
async def start(message: types.Message):
    cursor.execute("SELECT * FROM users WHERE id=?", (message.from_user.id,))
    user = cursor.fetchone()

    if not user:
        user_states[message.from_user.id] = "nickname"
        await full_clear(message)

        msg1 = await message.answer(WELCOME_TEXT)
        await track_user_message(msg1)

        msg2 = await message.answer("Введите ваш анонимный никнейм")
        await track_user_message(msg2)

        return

    await show_main_three(message, nick_saved=True)


# ---------------- НАЗАД ----------------

@dp.message(F.text == "Назад ⏪")
async def back(message: types.Message):
    user_states.pop(message.from_user.id, None)
    await show_main_three(message, nick_saved=True)

async def send_clean(message: types.Message, text, reply_markup=None, clear=False):
    if clear:
        await full_clear(message)

    msg = await message.answer(text, reply_markup=reply_markup)
    await track_user_message(msg)
    # ---------------- МАРКЕТ ----------------

MARKET_TEXT = """Добро пожаловать в анонимный маркет района Внуково 🛒

Здесь вы можете покупать и продавать товары, не раскрывая свою личность.
Ваш никнейм будет отображаться вместо аккаунта.

Выберите действие ниже:
"""


@dp.message(F.text == "🛒 Маркет")
async def market(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍️ Перейти в маркет")],
            [KeyboardButton(text="📝 Выставить объявление")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )

    await send_clean(
        message,
        MARKET_TEXT,
        kb,
        clear=True
    )


@dp.message(F.text == "🛍️ Перейти в маркет")
async def go_market(message: types.Message):
    await send_clean(message, MARKET_LINK)


@dp.message(F.text == "📝 Выставить объявление")
async def post_market(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💵 Выставить пост о продаже")],
            [KeyboardButton(text="🛒 Выставить пост о покупке")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )

    await send_clean(
        message,
        "Выберите тип объявления:",
        kb,
        clear=True
    )


@dp.message(F.text.in_(["💵 Выставить пост о продаже", "🛒 Выставить пост о покупке"]))
async def market_text(message: types.Message):
    user_states[message.from_user.id] = "market"

    await send_clean(
        message,
        "Введите текст объявления (можно с фото)",
        back_btn(),
        clear=True
    )
    # ---------------- ПОДСЛУШАНО ----------------

CONF_TEXT = """Добро пожаловать в «Подслушано» района Внуково 🤫

Мы решили перенести этот легендарный формат в наш анонимный форум.

Здесь ты можешь:
• поделиться сплетней
• рассказать новость
• задать анонимный вопрос
• высказаться без раскрытия личности

Твой секрет — наш контент 👇
"""


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

    await send_clean(
        message,
        CONF_TEXT,
        kb,
        clear=True
    )


@dp.message(F.text == "Перейти в подслушано🤫")
async def go_conf(message: types.Message):
    await send_clean(message, CONF_LINK)


@dp.message(F.text == "Отправить сообщение ✏️")
async def send_conf(message: types.Message):
    user_states[message.from_user.id] = "conf"

    await send_clean(
        message,
        "Введите сообщение (можно с фото)",
        back_btn(),
        clear=True
    )
    # ---------------- ПРОФИЛЬ ----------------

@dp.message(F.text == "👤 Профиль")
async def profile(message: types.Message):
    cursor.execute(
        "SELECT nickname,rating,deals FROM users WHERE id=?",
        (message.from_user.id,)
    )
    nick, rating, deals = cursor.fetchone()

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✏️ Изменить ник")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )

    await send_clean(
        message,
        f"""👤 Ваш профиль

Ник: {nick}
Рейтинг: {rating}
Сделок: {deals}""",
        kb,
        clear=True
    )


@dp.message(F.text == "✏️ Изменить ник")
async def change_nick(message: types.Message):
    user_states[message.from_user.id] = "change_nick"
    await send_clean(message, "Введите новый ник", back_btn(), clear=True)


# ---------------- РЕЙТИНГ ----------------

@dp.message(F.text == "⭐ Рейтинг")
async def rating(message: types.Message):
    cursor.execute(
        "SELECT nickname,rating FROM users ORDER BY rating DESC LIMIT 10"
    )
    rows = cursor.fetchall()

    text = "⭐ Рейтинг пользователей\n\n"
    for i, row in enumerate(rows, start=1):
        text += f"{i}. {row[0]} — {row[1]}\n"

    await send_clean(message, text, back_btn(), clear=True)


# ---------------- FAQ ----------------

@dp.message(F.text == "FAQ")
async def faq(message: types.Message):
    await send_clean(message, FAQ_LINK, back_btn(), clear=True)


# ---------------- СДЕЛКИ ----------------

@dp.message(F.text == "🔒 Сделки через гаранта")
async def deals_menu(message: types.Message):
    await send_clean(
        message,
        "Раздел сделок через гаранта находится в разработке",
        back_btn(),
        clear=True
    )
    # ---------------- ЛИЧНЫЕ СООБЩЕНИЯ ----------------

@dp.message(F.text == "💬 Личные сообщения")
async def private_menu(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Введите анонимный никнейм пользователя🔎")],
            [KeyboardButton(text="Личные чаты 📂")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )

    await send_clean(
        message,
        "Введите ник пользователя для начала общения",
        kb,
        clear=True
    )


@dp.message(F.text == "Введите анонимный никнейм пользователя🔎")
async def find_user(message: types.Message):
    user_states[message.from_user.id] = "find_user"
    await send_clean(message, "Введите ник", back_btn(), clear=True)


@dp.message()
async def handler(message: types.Message):

    await track_user_message(message)
    state = user_states.get(message.from_user.id)

    # регистрация
    if state == "nickname":
        cursor.execute(
            "SELECT id FROM users WHERE nickname=?",
            (message.text,)
        )
        exists = cursor.fetchone()

        if exists:
            await send_clean(message, "❌ Такой ник уже занят")
            return

        cursor.execute(
            "INSERT INTO users(id,nickname) VALUES (?,?)",
            (message.from_user.id, message.text)
        )
        conn.commit()

        await show_main_three(message, nick_saved=True)
        return

    # смена ника
    if state == "change_nick":
        cursor.execute(
            "UPDATE users SET nickname=? WHERE id=?",
            (message.text, message.from_user.id)
        )
        conn.commit()

        await show_main_three(message, nick_saved=True)
        return

    # MARKET
    if state == "market":
        ok, remain = check_cooldown(message.from_user.id)
        if not ok:
            await send_clean(
                message,
                f"⏳ Публиковать можно раз в 2.5 часа\nОсталось: {format_time(remain)}",
                back_btn(),
                clear=True
            )
            return

        cursor.execute(
            "SELECT nickname FROM users WHERE id=?",
            (message.from_user.id,)
        )
        nick = cursor.fetchone()[0]

        content = message.text if message.text else message.caption
        text = f"{content}\n\nНик: {nick}"

        if message.photo:
            await bot.send_photo(
                CHANNEL_MARKET,
                message.photo[-1].file_id,
                caption=text
            )
        else:
            await bot.send_message(CHANNEL_MARKET, text)

        post_cooldowns[message.from_user.id] = time.time()
        await show_main_three(message, nick_saved=True)
        return

    # CONF
    if state == "conf":
        ok, remain = check_cooldown(message.from_user.id)
        if not ok:
            await send_clean(
                message,
                f"⏳ Публиковать можно раз в 2.5 часа\nОсталось: {format_time(remain)}",
                back_btn(),
                clear=True
            )
            return

        cursor.execute(
            "SELECT nickname FROM users WHERE id=?",
            (message.from_user.id,)
        )
        nick = cursor.fetchone()[0]

        content = message.text if message.text else message.caption
        text = f"{content}\n\nНик: {nick}"

        if message.photo:
            await bot.send_photo(
                CHANNEL_CONFESSIONS,
                message.photo[-1].file_id,
                caption=text
            )
        else:
            await bot.send_message(CHANNEL_CONFESSIONS, text)

        post_cooldowns[message.from_user.id] = time.time()
        await show_main_three(message, nick_saved=True)
        return


# ---------------- ЗАПУСК ----------------

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
