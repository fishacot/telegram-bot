import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
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

cursor.execute("""CREATE TABLE IF NOT EXISTS texts(
key TEXT PRIMARY KEY,
value TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS media(
key TEXT PRIMARY KEY,
file_id TEXT
)""")

conn.commit()

user_states = {}

def get_text(key, default):
    cursor.execute("SELECT value FROM texts WHERE key=?", (key,))
    row = cursor.fetchone()
    return row[0] if row else default

def get_media(key):
    cursor.execute("SELECT file_id FROM media WHERE key=?", (key,))
    row = cursor.fetchone()
    return row[0] if row else None

def menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Маркет объявлений")],
            [KeyboardButton(text="🕵️ Подслушано")],
            [KeyboardButton(text="🔒 Сделки через гаранта")],
            [KeyboardButton(text="⭐ Рейтинг учеников")],
            [KeyboardButton(text="🚨 Жалобы админу")],
            [KeyboardButton(text="👤 Профиль")]
        ],
        resize_keyboard=True
    )

@dp.message(Command("start"))
async def start(message: types.Message):

    cursor.execute("SELECT * FROM users WHERE id=?", (message.from_user.id,))
    user = cursor.fetchone()

    if not user:
        user_states[message.from_user.id] = "nickname"
        await message.answer("Введите ваш анонимный ник")
        return

    text = get_text("start","Добро пожаловать")
    photo = get_media("start")

    if photo:
        await message.answer_photo(photo, caption=text, reply_markup=menu())
    else:
        await message.answer(text, reply_markup=menu())

@dp.message(Command("admin"))
async def admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Тексты")],
            [KeyboardButton(text="🖼 Фото")]
        ],
        resize_keyboard=True
    )

    await message.answer("Админ панель", reply_markup=kb)

@dp.message(F.text == "📝 Тексты")
async def texts(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="start")],
            [KeyboardButton(text="market")],
            [KeyboardButton(text="conf")],
            [KeyboardButton(text="garant")],
            [KeyboardButton(text="rating")],
            [KeyboardButton(text="complaint")]
        ],
        resize_keyboard=True
    )

    await message.answer("Выберите раздел")

@dp.message(F.text == "🖼 Фото")
async def photos(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="start_photo")],
            [KeyboardButton(text="market_photo")],
            [KeyboardButton(text="conf_photo")],
            [KeyboardButton(text="garant_photo")],
            [KeyboardButton(text="rating_photo")],
            [KeyboardButton(text="complaint_photo")]
        ],
        resize_keyboard=True
    )

    await message.answer("Выберите раздел")

@dp.message(F.text == "🛒 Маркет объявлений")
async def market(message: types.Message):
    user_states[message.from_user.id] = "market"
    text = get_text("market","Отправьте объявление")
    photo = get_media("market")

    if photo:
        await message.answer_photo(photo, caption=text)
    else:
        await message.answer(text)

@dp.message(F.text == "🕵️ Подслушано")
async def conf(message: types.Message):
    user_states[message.from_user.id] = "conf"
    text = get_text("conf","Отправьте сообщение")
    photo = get_media("conf")

    if photo:
        await message.answer_photo(photo, caption=text)
    else:
        await message.answer(text)

@dp.message(F.text == "🔒 Сделки через гаранта")
async def garant(message: types.Message):
    user_states[message.from_user.id] = "garant"
    text = get_text("garant","Введите ник второго участника")
    photo = get_media("garant")

    if photo:
        await message.answer_photo(photo, caption=text)
    else:
        await message.answer(text)

@dp.message(F.text == "⭐ Рейтинг учеников")
async def rating(message: types.Message):

    cursor.execute("SELECT nickname,rating,deals FROM users ORDER BY rating DESC LIMIT 10")
    top = cursor.fetchall()

    text = get_text("rating","🏆 Рейтинг\n\n")

    for i,user in enumerate(top,start=1):
        text += f"{i}. {user[0]} ⭐{user[1]} ({user[2]} сделок)\n"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔎 Найти по нику", callback_data="search")]
        ]
    )

    photo = get_media("rating")

    if photo:
        await message.answer_photo(photo, caption=text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)

@dp.callback_query(F.data == "search")
async def search(call: types.CallbackQuery):
    user_states[call.from_user.id] = "search"
    await call.message.answer("Введите ник")

@dp.message(F.text == "🚨 Жалобы админу")
async def complaint(message: types.Message):
    user_states[message.from_user.id] = "complaint"
    text = get_text("complaint","Опишите проблему")
    photo = get_media("complaint")

    if photo:
        await message.answer_photo(photo, caption=text)
    else:
        await message.answer(text)

@dp.message()
async def handler(message: types.Message):

    state = user_states.get(message.from_user.id)

    if state == "nickname":
        cursor.execute("INSERT INTO users(id,nickname) VALUES (?,?)",(message.from_user.id,message.text))
        conn.commit()
        await message.answer("Ник сохранен", reply_markup=menu())

    elif state == "market":
        await bot.send_message(ADMIN_ID,f"Маркет:\n{message.text}\nID:{message.from_user.id}")

    elif state == "conf":
        await bot.send_message(ADMIN_ID,f"Подслушано:\n{message.text}")

    elif state == "garant":
        await bot.send_message(ADMIN_ID,
        f"Сделка гарант\n"
        f"ID:{message.from_user.id}\n"
        f"Username:@{message.from_user.username}\n"
        f"Второй:{message.text}")

    elif state == "complaint":
        await bot.send_message(ADMIN_ID,f"Жалоба:\n{message.text}")

    elif state == "search":
        cursor.execute("SELECT nickname,rating,deals FROM users WHERE nickname=?",(message.text,))
        user = cursor.fetchone()

        if user:
            await message.answer(f"{user[0]}\n⭐{user[1]}\nСделок:{user[2]}")
        else:
            await message.answer("Не найден")

    elif state and state.endswith("_photo"):
        if message.photo:
            key = state.replace("_photo","")
            cursor.execute("INSERT OR REPLACE INTO media VALUES (?,?)",(key,message.photo[-1].file_id))
            conn.commit()
            await message.answer("Фото сохранено")

    elif state in ["start","market","conf","garant","rating","complaint"]:
        cursor.execute("INSERT OR REPLACE INTO texts VALUES (?,?)",(state,message.text))
        conn.commit()
        await message.answer("Текст сохранён")

@dp.message(F.text.in_(["start","market","conf","garant","rating","complaint"]))
async def edit_text(message: types.Message):
    user_states[message.from_user.id] = message.text
    await message.answer("Отправьте новый текст")

@dp.message(F.text.in_(["start_photo","market_photo","conf_photo","garant_photo","rating_photo","complaint_photo"]))
async def edit_photo(message: types.Message):
    user_states[message.from_user.id] = message.text
    await message.answer("Отправьте фото")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())