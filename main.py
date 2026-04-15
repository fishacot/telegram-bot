import asyncio
import sqlite3
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import *

bot = Bot(token=8734934956:AAFM9DunvR8CMMdqiklqGoklSJ825izn1nk)
dp = Dispatcher()

ADMIN_ID = 554529638

# ---------------- БД ----------------

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

cursor.execute("""CREATE TABLE IF NOT EXISTS admin_texts(
key TEXT PRIMARY KEY,
text TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS admin_photos(
key TEXT PRIMARY KEY,
file_id TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS admin_messages(
id INTEGER PRIMARY KEY AUTOINCREMENT,
nickname TEXT,
text TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS deals(
id INTEGER PRIMARY KEY AUTOINCREMENT,
nick1 TEXT,
nick2 TEXT,
id1 INTEGER,
id2 INTEGER
)""")

conn.commit()

# ---------------- STATE ----------------

user_states = {}
chat_targets = {}

# ---------------- ТАЙМЕРЫ ----------------

market_cooldowns = {}
conf_cooldowns = {}

COOLDOWN = 9000

# ---------------- ССЫЛКИ ----------------

MARKET_LINK = "https://t.me/VnykovoAnonMarket"
CONF_LINK = "https://t.me/podslyshenoVnykovo"
FAQ_LINK = "https://t.me/abouuttanonvnykovo11"

# ---------------- ОТСЛЕЖИВАНИЕ СООБЩЕНИЙ ----------------

user_messages = {}

async def track(msg: types.Message):
    user_messages.setdefault(msg.chat.id, [])
    user_messages[msg.chat.id].append(msg.message_id)

# ---------------- ПОЛНАЯ ОЧИСТКА ----------------

async def full_clear(message: types.Message):
    msgs = user_messages.get(message.chat.id, [])

    for msg_id in msgs:
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except:
            pass

    user_messages[message.chat.id] = []

# ---------------- КНОПКИ ----------------

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
        keyboard=[
            [KeyboardButton(text="❌ Закрыть чат")]
        ],
        resize_keyboard=True
    )

# ---------------- 3 СТАРТОВЫХ СООБЩЕНИЯ ----------------

async def show_main_three(message: types.Message):
    await full_clear(message)

    msg1 = await message.answer(
"""Приветствуем в самом скрытном уголке района Внуково 🕵️‍♀️

Здесь можно быть кем угодно или не быть никем. Ваш анонимный никнейм это ваше альтер-эго, ваш аккаунт не будет высвечиваться ни при публикации объявлений, ни при участии обсуждения на форумах 🛡️
"""
    )
    await track(msg1)

    msg2 = await message.answer("✅ Ник сохранен")
    await track(msg2)

    msg3 = await message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu()
    )
    await track(msg3)

# ---------------- ТАЙМЕРЫ ----------------

def check_market(user_id):
    last = market_cooldowns.get(user_id)
    if not last:
        return True, 0

    diff = time.time() - last
    if diff >= COOLDOWN:
        return True, 0

    return False, int(COOLDOWN - diff)


def check_conf(user_id):
    last = conf_cooldowns.get(user_id)
    if not last:
        return True, 0

    diff = time.time() - last
    if diff >= COOLDOWN:
        return True, 0

    return False, int(COOLDOWN - diff)


def format_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}ч {m}мин"
    # ---------------- START ----------------

@dp.message(Command("start"))
async def start(message: types.Message):
    cursor.execute("SELECT * FROM users WHERE id=?", (message.from_user.id,))
    user = cursor.fetchone()

    if not user:
        user_states[message.from_user.id] = "nickname"

        await full_clear(message)

        msg = await message.answer(
"""Приветствуем в самом скрытном уголке района Внуково 🕵️‍♀️

Здесь можно быть кем угодно или не быть никем. Ваш анонимный никнейм это ваше альтер-эго, ваш аккаунт не будет высвечиваться ни при публикации объявлений, ни при участии обсуждения на форумах 🛡️

Введите ваш анонимный никнейм :
"""
        )
        await track(msg)
        return

    await show_main_three(message)


# ---------------- НАЗАД ----------------

@dp.message(F.text == "Назад ⏪")
async def back(message: types.Message):
    user_states.pop(message.from_user.id, None)
    await show_main_three(message)


# ---------------- МАРКЕТ ----------------

@dp.message(F.text == "🛒 Маркет")
async def market(message: types.Message):

    await full_clear(message)

    text = """👋Добро пожаловать в анонимный маркетплейс!
Здесь вы можете опубликовать пост о продаже/покупке любого товара или услуге!"""

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍️ Перейти в маркет")],
            [KeyboardButton(text="📝 Выставить объявление")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )

    msg = await message.answer(text, reply_markup=kb)
    await track(msg)


@dp.message(F.text == "🛍️ Перейти в маркет")
async def go_market(message: types.Message):
    msg = await message.answer(MARKET_LINK)
    await track(msg)


@dp.message(F.text == "📝 Выставить объявление")
async def market_type(message: types.Message):

    await full_clear(message)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💵 Продажа")],
            [KeyboardButton(text="🛒 Покупка")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )

    msg = await message.answer("Выберите тип объявления", reply_markup=kb)
    await track(msg)


@dp.message(F.text.in_(["💵 Продажа", "🛒 Покупка"]))
async def market_input(message: types.Message):
    user_states[message.from_user.id] = "market"

    await full_clear(message)

    msg = await message.answer(
        "Введите текст объявления (можно фото)",
        reply_markup=back_btn()
    )
    await track(msg)


# ---------------- ПОДСЛУШАНО ----------------

@dp.message(F.text == "🕵️ Подслушано")
async def conf(message: types.Message):

    await full_clear(message)

    text = """Добро пожаловать в «Подслушано»!
Мы решили перенести этот легендарный формат в наш анонимный форум! 🤫
Здесь ты можешь без лишних глаз поделиться самой горячей сплетней или топовой новостью. Твой секрет — наш контент! 👇"""

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Перейти в подслушано🤫")],
            [KeyboardButton(text="Отправить сообщение ✏️")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )

    msg = await message.answer(text, reply_markup=kb)
    await track(msg)


@dp.message(F.text == "Перейти в подслушано🤫")
async def go_conf(message: types.Message):
    msg = await message.answer(CONF_LINK)
    await track(msg)


@dp.message(F.text == "Отправить сообщение ✏️")
async def conf_input(message: types.Message):
    user_states[message.from_user.id] = "conf"

    await full_clear(message)

    msg = await message.answer(
        "Введите сообщение",
        reply_markup=back_btn()
    )
    await track(msg)
    # ---------------- ПРОФИЛЬ ----------------

@dp.message(F.text == "👤 Профиль")
async def profile(message: types.Message):
    cursor.execute(
        "SELECT nickname,rating,deals FROM users WHERE id=?",
        (message.from_user.id,)
    )
    nick, rating, deals = cursor.fetchone()

    await full_clear(message)

    msg = await message.answer(
        f"""👤 Профиль

Ник: {nick}
ID: {message.from_user.id}
Рейтинг: {rating}
Сделок: {deals}""",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✏️ Изменить ник")],
                [KeyboardButton(text="Назад ⏪")]
            ],
            resize_keyboard=True
        )
    )
    await track(msg)


@dp.message(F.text == "✏️ Изменить ник")
async def change_nick(message: types.Message):
    user_states[message.from_user.id] = "change_nick"

    await full_clear(message)

    msg = await message.answer(
        "Введите новый ник",
        reply_markup=back_btn()
    )
    await track(msg)


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

    await full_clear(message)

    msg = await message.answer(text, reply_markup=back_btn())
    await track(msg)


# ---------------- FAQ ----------------

@dp.message(F.text == "FAQ")
async def faq(message: types.Message):
    await full_clear(message)

    msg = await message.answer(FAQ_LINK, reply_markup=back_btn())
    await track(msg)


# ---------------- СООБЩЕНИЕ АДМИНУ ----------------

@dp.message(F.text == "🚨 Сообщение админу")
async def admin_msg(message: types.Message):
    user_states[message.from_user.id] = "admin_msg"

    await full_clear(message)

    msg = await message.answer(
        "Введите сообщение для администратора",
        reply_markup=back_btn()
    )
    await track(msg)


# ---------------- СДЕЛКИ ----------------

@dp.message(F.text == "🔒 Сделки через гаранта")
async def deals(message: types.Message):
    user_states[message.from_user.id] = "deal"

    await full_clear(message)

    msg = await message.answer(
        "Введите ник пользователя для сделки",
        reply_markup=back_btn()
    )
    await track(msg)
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

    await full_clear(message)

    msg = await message.answer(
        "Выберите действие",
        reply_markup=kb
    )
    await track(msg)


@dp.message(F.text == "Введите анонимный никнейм пользователя🔎")
async def find_user(message: types.Message):
    user_states[message.from_user.id] = "find_user"

    await full_clear(message)

    msg = await message.answer(
        "Введите ник пользователя",
        reply_markup=back_btn()
    )
    await track(msg)
    # ---------------- АДМИН ПАНЕЛЬ ----------------

def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📈 Количество пользователей")],
            [KeyboardButton(text="👥 Список пользователей")],
            [KeyboardButton(text="📕 Заявки")],
            [KeyboardButton(text="🤖 Сообщения админу")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )


@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    await full_clear(message)

    msg = await message.answer(
        "Админ панель",
        reply_markup=admin_menu()
    )
    await track(msg)


@dp.message(F.text == "📈 Количество пользователей")
async def users_count(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    await full_clear(message)

    msg = await message.answer(
        f"Всего пользователей: {count}",
        reply_markup=admin_menu()
    )
    await track(msg)


@dp.message(F.text == "👥 Список пользователей")
async def users_list(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    user_states[message.from_user.id] = "find_user_admin"

    await full_clear(message)

    msg = await message.answer(
        "Введите анонимный ник",
        reply_markup=back_btn()
    )
    await track(msg)


@dp.message(F.text == "📕 Заявки")
async def admin_deals(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT nick1,nick2,id1,id2 FROM deals")
    rows = cursor.fetchall()

    text = ""
    for r in rows:
        text += f"{r[0]} хочет заключить сделку с {r[1]}\nID1: {r[2]}\nID2: {r[3]}\n\n"

    await full_clear(message)

    msg = await message.answer(text if text else "Нет заявок", reply_markup=admin_menu())
    await track(msg)


@dp.message(F.text == "🤖 Сообщения админу")
async def admin_msgs(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT nickname,text FROM admin_messages")
    rows = cursor.fetchall()

    text = ""
    for r in rows:
        text += f"{r[0]}: {r[1]}\n\n"

    await full_clear(message)

    msg = await message.answer(text if text else "Нет сообщений", reply_markup=admin_menu())
    await track(msg)
    # ---------------- HANDLER ----------------

@dp.message()
async def handler(message: types.Message):

    state = user_states.get(message.from_user.id)

    # регистрация
    if state == "nickname":
        cursor.execute(
            "SELECT id FROM users WHERE nickname=?",
            (message.text,)
        )
        if cursor.fetchone():
            msg = await message.answer("❌ Ник занят")
            await track(msg)
            return

        cursor.execute(
            "INSERT INTO users(id,nickname) VALUES (?,?)",
            (message.from_user.id, message.text)
        )
        conn.commit()

        await show_main_three(message)
        return

    # смена ника
    if state == "change_nick":
        cursor.execute(
            "UPDATE users SET nickname=? WHERE id=?",
            (message.text, message.from_user.id)
        )
        conn.commit()

        await show_main_three(message)
        return

    # MARKET
    if state == "market":
        ok, remain = check_market(message.from_user.id)
        if not ok:
            msg = await message.answer(f"⏳ Подождите {format_time(remain)}")
            await track(msg)
            return

        cursor.execute(
            "SELECT nickname FROM users WHERE id=?",
            (message.from_user.id,)
        )
        nick = cursor.fetchone()[0]

        text = message.text if message.text else message.caption
        text = f"{text}\n\nНик: {nick}"

        if message.photo:
            await bot.send_photo(CHANNEL_MARKET, message.photo[-1].file_id, caption=text)
        else:
            await bot.send_message(CHANNEL_MARKET, text)

        market_cooldowns[message.from_user.id] = time.time()
        await show_main_three(message)
        return

    # CONF
    if state == "conf":
        ok, remain = check_conf(message.from_user.id)
        if not ok:
            msg = await message.answer(f"⏳ Подождите {format_time(remain)}")
            await track(msg)
            return

        cursor.execute(
            "SELECT nickname FROM users WHERE id=?",
            (message.from_user.id,)
        )
        nick = cursor.fetchone()[0]

        text = message.text if message.text else message.caption
        text = f"{text}\n\nНик: {nick}"

        if message.photo:
            await bot.send_photo(CHANNEL_CONFESSIONS, message.photo[-1].file_id, caption=text)
        else:
            await bot.send_message(CHANNEL_CONFESSIONS, text)

        conf_cooldowns[message.from_user.id] = time.time()
        await show_main_three(message)
        return

    # сообщение админу
    if state == "admin_msg":
        cursor.execute(
            "SELECT nickname FROM users WHERE id=?",
            (message.from_user.id,)
        )
        nick = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO admin_messages(nickname,text) VALUES (?,?)",
            (nick, message.text)
        )
        conn.commit()

        await show_main_three(message)
        return

    # сделки
    if state == "deal":
        cursor.execute("SELECT nickname FROM users WHERE id=?", (message.from_user.id,))
        nick1 = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM users WHERE nickname=?", (message.text,))
        row = cursor.fetchone()

        if not row:
            msg = await message.answer("Пользователь не найден")
            await track(msg)
            return

        id2 = row[0]

        cursor.execute("SELECT nickname FROM users WHERE id=?", (id2,))
        nick2 = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO deals(nick1,nick2,id1,id2) VALUES (?,?,?,?)",
            (nick1, nick2, message.from_user.id, id2)
        )
        conn.commit()

        await show_main_three(message)
        return
        # ---------------- ЛИЧНЫЕ СООБЩЕНИЯ ----------------

@dp.message()
async def private_chat_handler(message: types.Message):

    state = user_states.get(message.from_user.id)

    # поиск пользователя
    if state == "find_user":
        cursor.execute(
            "SELECT id FROM users WHERE nickname=?",
            (message.text,)
        )
        row = cursor.fetchone()

        if not row:
            msg = await message.answer("❌ Пользователь не найден")
            await track(msg)
            return

        target = row[0]

        chat_targets[message.from_user.id] = target
        chat_targets[target] = message.from_user.id

        user_states[message.from_user.id] = "chat"
        user_states[target] = "chat"

        msg = await message.answer(
            "Чат открыт",
            reply_markup=chat_keyboard()
        )
        await track(msg)

        try:
            await bot.send_message(
                target,
                "С вами начали анонимный чат",
                reply_markup=chat_keyboard()
            )
        except:
            pass

        return

    # закрыть чат
    if message.text == "❌ Закрыть чат":
        chat_targets.pop(message.from_user.id, None)
        user_states.pop(message.from_user.id, None)

        await show_main_three(message)
        return

    # пересылка сообщений
    if state == "chat":
        target = chat_targets.get(message.from_user.id)
        if not target:
            return

        cursor.execute(
            "SELECT nickname FROM users WHERE id=?",
            (message.from_user.id,)
        )
        nick = cursor.fetchone()[0]

        if message.photo:
            await bot.send_photo(
                target,
                message.photo[-1].file_id,
                caption=f"{nick}:\n{message.caption or ''}"
            )
        else:
            await bot.send_message(
                target,
                f"{nick}:\n{message.text}"
            )

        return


# ---------------- ПОИСК ПОЛЬЗОВАТЕЛЯ АДМИН ----------------

@dp.message()
async def admin_find_user(message: types.Message):

    state = user_states.get(message.from_user.id)

    if state != "find_user_admin":
        return

    cursor.execute(
        "SELECT id FROM users WHERE nickname=?",
        (message.text,)
    )
    row = cursor.fetchone()

    if not row:
        msg = await message.answer("Пользователь не найден")
        await track(msg)
        return

    user_id = row[0]

    try:
        chat = await bot.get_chat(user_id)
        username = f"@{chat.username}" if chat.username else "нет"
    except:
        username = "нет"

    msg = await message.answer(
        f"Ник: {message.text}\nID: {user_id}\nUsername: {username}"
    )
    await track(msg)

    user_states.pop(message.from_user.id)

# ---------------- ЗАПУСК ----------------

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
