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
nickname TEXT,
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

async def send_clean(message: types.Message, text, reply_markup=None):
    try:
        if message.from_user.id in last_bot_messages:
            await bot.delete_message(
                message.chat.id,
                last_bot_messages[message.from_user.id]
            )
    except:
        pass

    try:
        await message.delete()
    except:
        pass

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
        "Введите ваше объявление, в конце вашего объявления укажите ваш анонимный никнейм для связи 🤝",
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
"""Добро пожаловать в «Подслушано»! 
Мы решили перенести этот легендарный формат в наш анонимный форум! 🤫
Здесь ты можешь без лишних глаз поделиться самой горячей сплетней или топовой новостью. Твой секрет — наш контент! 👇
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

# ПРОФИЛЬ

@dp.message(F.text == "👤 Профиль")
async def profile(message: types.Message):
    cursor.execute("SELECT nickname,deals,rating FROM users WHERE id=?",(message.from_user.id,))
    user = cursor.fetchone()

    await send_clean(
        message,
f"""ID: {message.from_user.id}
Ник: {user[0]}
Сделок: {user[1]}
Рейтинг: {user[2]}
""",
        back_btn()
    )

# FAQ

@dp.message(F.text == "FAQ")
async def faq(message: types.Message):
    await send_clean(message, FAQ_LINK, main_menu())

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
"""На форуме слишком людно? Введи ник собеседника и продолжи общение в секретном чате.
Сообщения работают по схеме 
User A → бот → User B
Твоя анонимность — под надежной защитой🛡️""",
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

    text = "📂 Ваши чаты:\n\n"

    for r in rows:
        other = r[1] if r[0] == message.from_user.id else r[0]
        cursor.execute("SELECT nickname FROM users WHERE id=?", (other,))
        nick = cursor.fetchone()[0]
        text += f"• {nick}\n"

    await send_clean(message, text, back_btn())

# ОБЩИЙ ХЕНДЛЕР

@dp.message()
async def handler(message: types.Message):

    state = user_states.get(message.from_user.id)

    if state == "nickname":
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

        chat_targets[message.from_user.id] = target
        chat_targets[target] = message.from_user.id

        cursor.execute(
            "INSERT INTO chats VALUES (?,?)",
            (message.from_user.id, target)
        )
        conn.commit()

        user_states[message.from_user.id] = "chat"
        user_states[target] = "chat"

        await send_clean(
            message,
            "Чат открыт. Напишите сообщение\n\n❌ Закрыть чат",
            back_btn()
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
