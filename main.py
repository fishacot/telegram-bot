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

@dp.message(Command("start"))
async def start(message: types.Message):

    cursor.execute("SELECT * FROM users WHERE id=?", (message.from_user.id,))
    user = cursor.fetchone()

    if not user:
        user_states[message.from_user.id] = "nickname"
        await message.answer(
"""Приветствуем в самом скрытном уголке района Внуково 🕵️‍♀️
Здесь можно быть кем угодно или не быть никем. Ваш анонимный никнейм это ваше альтер-эго, ваш аккаунт не будет высвечиваться ни при публикации объявлений, ни при участии обсуждения на форумах 🛡️
Впишите свой анонимный никнейм :
""")
        return

    await message.answer("Главное меню", reply_markup=main_menu())

@dp.message(F.text == "Назад ⏪")
async def back(message: types.Message):
    user_states.pop(message.from_user.id, None)
    await message.answer("Главное меню", reply_markup=main_menu())

# ---------------- МАРКЕТ ----------------

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

    await message.answer(
"""👋Добро пожаловать в анонимный маркетплейс!
Здесь вы можете опубликовать пост о продаже/покупке любого товара или услуге!
""", reply_markup=kb)

@dp.message(F.text == "🛍️ Перейти в маркет")
async def go_market(message: types.Message):
    await message.answer(f"https://t.me/c/{str(CHANNEL_MARKET)[4:]}")

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
    await message.answer("Выберите тип объявления", reply_markup=kb)

@dp.message(F.text.in_(["💵 Выставить пост о продаже","🛒 Выставить пост о покупке"]))
async def market_text(message: types.Message):
    user_states[message.from_user.id] = "market"
    await message.answer(
"Введите ваше объявление, в конце вашего объявления укажите ваш анонимный никнейм для связи 🤝",
reply_markup=back_btn()
)

# ---------------- ПОДСЛУШАНО ----------------

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

    await message.answer(
"""Добро пожаловать в «Подслушано»! 
Мы решили перенести этот легендарный формат в наш анонимный форум! 🤫
Здесь ты можешь без лишних глаз поделиться самой горячей сплетней или топовой новостью. Твой секрет — наш контент! 👇
""", reply_markup=kb)

@dp.message(F.text == "Перейти в подслушано🤫")
async def go_conf(message: types.Message):
    await message.answer(f"https://t.me/c/{str(CHANNEL_CONFESSIONS)[4:]}")

@dp.message(F.text == "Отправить сообщение ✏️")
async def send_conf(message: types.Message):
    user_states[message.from_user.id] = "conf"
    await message.answer("Отправьте сообщение", reply_markup=back_btn())

# ---------------- ПРОФИЛЬ ----------------

@dp.message(F.text == "👤 Профиль")
async def profile(message: types.Message):
    cursor.execute("SELECT nickname,deals FROM users WHERE id=?",(message.from_user.id,))
    user = cursor.fetchone()

    await message.answer(
f"""ID: {message.from_user.id}
Ник: {user[0]}
Сделок: {user[1]}
""", reply_markup=back_btn())

# ---------------- FAQ ----------------

@dp.message(F.text == "FAQ")
async def faq(message: types.Message):
    await message.answer(f"https://t.me/c/{str(INFO_CHANNEL)[4:]}")

# ---------------- ОБЩИЙ ХЕНДЛЕР ----------------

@dp.message()
async def handler(message: types.Message):

    state = user_states.get(message.from_user.id)

    if state == "nickname":
        cursor.execute(
            "INSERT INTO users(id,nickname) VALUES (?,?)",
            (message.from_user.id, message.text)
        )
        conn.commit()
        await message.answer("Ник сохранен", reply_markup=main_menu())

    elif state == "market":

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

        await message.answer("Объявление опубликовано", reply_markup=main_menu())

    elif state == "conf":

        if message.photo:
            await bot.send_photo(
                CHANNEL_CONFESSIONS,
                message.photo[-1].file_id,
                caption=message.caption or ""
            )
        else:
            await bot.send_message(CHANNEL_CONFESSIONS, message.text)

        await message.answer("Сообщение опубликовано", reply_markup=main_menu())


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
