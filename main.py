import asyncio
import sqlite3
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
last_bot_messages = {}

MARKET_LINK = "https://t.me/VnykovoAnonMarket"
CONF_LINK = "https://t.me/podslyshenoVnykovo"
FAQ_LINK = "https://t.me/abouuttanonvnykovo11"

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Маркет объявлений")],
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
        keyboard=[
            [KeyboardButton(text="❌ Закрыть чат")]
        ],
        resize_keyboard=True
    )

async def send_clean(message: types.Message, text, reply_markup=None):
    msg = await message.answer(text, reply_markup=reply_markup)
    last_bot_messages[message.from_user.id] = msg.message_id


@dp.message(Command("start"))
async def start(message: types.Message):

    cursor.execute("SELECT * FROM users WHERE id=?", (message.from_user.id,))
    user = cursor.fetchone()

    if not user:
        user_states[message.from_user.id] = "nickname"
        await send_clean(message,
"""Приветствуем в самом скрытном уголке района Внуково 🕵️‍♀️
Здесь можно быть кем угодно или не быть никем. Ваш анонимный никнейм это ваше альтер-эго, ваш аккаунт не будет высвечиваться ни при публикации объявлений, ни при участии обсуждения на форумах 🛡️
Впишите свой анонимный никнейм :
""")
        return

    await send_clean(message, "Главное меню", main_menu())


@dp.message(F.text == "Назад ⏪")
async def back(message: types.Message):
    user_states.pop(message.from_user.id, None)
    await send_clean(message, "Главное меню", main_menu())


# МАРКЕТ
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

    await send_clean(message,
"""👋Добро пожаловать в анонимный маркетплейс!
Здесь вы можете опубликовать пост о продаже/покупке любого товара или услуге!
""", kb)


@dp.message(F.text == "🛍️ Перейти в маркет")
async def go_market(message: types.Message):
    await send_clean(message, MARKET_LINK, main_menu())


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
    await send_clean(message, "Выберите тип объявления", kb)


@dp.message(F.text.in_(["💵 Выставить пост о продаже","🛒 Выставить пост о покупке"]))
async def market_text(message: types.Message):
    user_states[message.from_user.id] = "market"
    await send_clean(
        message,
        "Введите ваше объявление",
        back_btn()
    )


# ПОДСЛУШАНО
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
"""Добро пожаловать в «Подслушано»! 🤫
""",
        kb
    )


@dp.message(F.text == "Перейти в подслушано🤫")
async def go_conf(message: types.Message):
    await send_clean(message, CONF_LINK, main_menu())


@dp.message(F.text == "Отправить сообщение ✏️")
async def send_conf(message: types.Message):
    user_states[message.from_user.id] = "conf"
    await send_clean(message, "Отправьте сообщение", back_btn())


# ЛИЧНЫЕ СООБЩЕНИЯ
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
        kb
    )


@dp.message(F.text == "Введите анонимный никнейм пользователя🔎")
async def find_user(message: types.Message):
    user_states[message.from_user.id] = "find_user"
    await send_clean(message, "Введите ник", back_btn())


@dp.message(F.text == "Личные чаты 📂")
async def chat_list(message: types.Message):

    cursor.execute(
        "SELECT user1,user2 FROM chats WHERE user1=? OR user2=?",
        (message.from_user.id, message.from_user.id)
    )

    rows = cursor.fetchall()

    if not rows:
        await send_clean(message, "Чатов пока нет", back_btn())
        return

    buttons = []

    for r in rows:
        other = r[1] if r[0] == message.from_user.id else r[0]
        cursor.execute("SELECT nickname FROM users WHERE id=?", (other,))
        nick = cursor.fetchone()[0]
        buttons.append([KeyboardButton(text=f"💬 {nick}")])

    buttons.append([KeyboardButton(text="Назад ⏪")])

    kb = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    await send_clean(message, "Ваши чаты:", kb)


# ОБЩИЙ ХЕНДЛЕР
@dp.message()
async def handler(message: types.Message):

    state = user_states.get(message.from_user.id)

    if state == "nickname":

        cursor.execute("SELECT id FROM users WHERE nickname=?", (message.text,))
        exists = cursor.fetchone()

        if exists:
            await send_clean(message, "❌ Такой ник уже занят, введите другой")
            return

        cursor.execute(
            "INSERT INTO users(id,nickname) VALUES (?,?)",
            (message.from_user.id, message.text)
        )
        conn.commit()
        await send_clean(message, "Ник сохранен", main_menu())
        return


    if state == "market":

        cursor.execute("SELECT nickname FROM users WHERE id=?", (message.from_user.id,))
        nick = cursor.fetchone()[0]

        text = f"{message.text}\n\nНик: {nick}"

        if message.photo:
            await bot.send_photo(
                CHANNEL_MARKET,
                message.photo[-1].file_id,
                caption=text
            )
        else:
            await bot.send_message(CHANNEL_MARKET, text)

        await send_clean(message, "Объявление опубликовано", main_menu())
        return


    if state == "conf":

        if message.photo:
            await bot.send_photo(
                CHANNEL_CONFESSIONS,
                message.photo[-1].file_id,
                caption=message.caption or ""
            )
        else:
            await bot.send_message(CHANNEL_CONFESSIONS, message.text)

        await send_clean(message, "Сообщение опубликовано", main_menu())
        return


    if state == "find_user":

        cursor.execute(
            "SELECT id FROM users WHERE nickname=?",
            (message.text,)
        )

        user = cursor.fetchone()

        if not user:
            await send_clean(
                message,
                "🤷пользователь не найден❌",
                back_btn()
            )
            return

        target = user[0]

        if target == message.from_user.id:
            await send_clean(message, "Нельзя написать самому себе")
            return

        chat_targets[message.from_user.id] = target
        chat_targets[target] = message.from_user.id

        cursor.execute(
            "SELECT * FROM chats WHERE (user1=? AND user2=?) OR (user1=? AND user2=?)",
            (message.from_user.id, target, target, message.from_user.id)
        )

        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO chats VALUES (?,?)",
                (message.from_user.id, target)
            )
            conn.commit()

        user_states[message.from_user.id] = "chat"
        user_states[target] = "chat"

        await send_clean(
            message,
            "Чат открыт",
            chat_keyboard()
        )
        return


    if state == "chat":

        if message.text == "❌ Закрыть чат":
            user_states.pop(message.from_user.id, None)
            await send_clean(message, "Чат закрыт", main_menu())
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


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
