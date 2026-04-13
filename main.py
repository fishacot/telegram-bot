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

# ---------------- БД ----------------

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

conn.commit()

# ---------------- STATE ----------------

user_states = {}
chat_targets = {}
user_messages = {}

# ---------------- ТАЙМЕРЫ ----------------

market_cooldowns = {}
conf_cooldowns = {}

COOLDOWN = 9000  # 2.5 часа

# ---------------- ССЫЛКИ ----------------

MARKET_LINK = "https://t.me/VnykovoAnonMarket"
CONF_LINK = "https://t.me/podslyshenoVnykovo"
FAQ_LINK = "https://t.me/abouuttanonvnykovo11"

# ---------------- ТЕКСТЫ ----------------

WELCOME_TEXT = """Приветствуем в самом скрытном уголке района Внуково 🕵️‍♀️

Здесь можно быть кем угодно или не быть никем. Ваш анонимный никнейм это ваше альтер-эго, ваш аккаунт не будет высвечиваться ни при публикации объявлений, ни при участии обсуждения на форумах 🛡️

Впишите свой анонимный никнейм :
"""

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

# ---------------- ОЧИСТКА ----------------

async def track_user_message(message: types.Message):
    user_messages.setdefault(message.from_user.id, [])
    user_messages[message.from_user.id].append(message.message_id)


async def full_clear(message: types.Message):
    msgs = user_messages.get(message.from_user.id, [])
    for msg_id in msgs:
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except:
            pass
    user_messages[message.from_user.id] = []


async def show_main_three(message: types.Message):
    await full_clear(message)

    msg1 = await message.answer(WELCOME_TEXT)
    await track_user_message(msg1)

    msg2 = await message.answer("✅ Ник сохранен")
    await track_user_message(msg2)

    msg3 = await message.answer("🏠 Главное меню", reply_markup=main_menu())
    await track_user_message(msg3)


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

# ---------------- START ----------------

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

    await show_main_three(message)


# ---------------- НАЗАД ----------------

@dp.message(F.text == "Назад ⏪")
async def back(message: types.Message):
    user_states.pop(message.from_user.id, None)
    await show_main_three(message)


# ---------------- МАРКЕТ ----------------

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

    await full_clear(message)
    msg = await message.answer(
        "Добро пожаловать в маркет",
        reply_markup=kb
    )
    await track_user_message(msg)


@dp.message(F.text == "🛍️ Перейти в маркет")
async def go_market(message: types.Message):
    msg = await message.answer(MARKET_LINK)
    await track_user_message(msg)


@dp.message(F.text == "📝 Выставить объявление")
async def market_type(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💵 Продажа")],
            [KeyboardButton(text="🛒 Покупка")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )

    await full_clear(message)
    msg = await message.answer("Выберите тип", reply_markup=kb)
    await track_user_message(msg)


@dp.message(F.text.in_(["💵 Продажа", "🛒 Покупка"]))
async def market_input(message: types.Message):
    user_states[message.from_user.id] = "market"

    await full_clear(message)
    msg = await message.answer(
        "Введите текст объявления (можно фото)",
        reply_markup=back_btn()
    )
    await track_user_message(msg)


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

    await full_clear(message)
    msg = await message.answer("Подслушано", reply_markup=kb)
    await track_user_message(msg)


@dp.message(F.text == "Перейти в подслушано🤫")
async def go_conf(message: types.Message):
    msg = await message.answer(CONF_LINK)
    await track_user_message(msg)


@dp.message(F.text == "Отправить сообщение ✏️")
async def conf_input(message: types.Message):
    user_states[message.from_user.id] = "conf"

    await full_clear(message)
    msg = await message.answer(
        "Введите сообщение",
        reply_markup=back_btn()
    )
    await track_user_message(msg)
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

    await full_clear(message)
    msg = await message.answer(
        f"""👤 Профиль

Ник: {nick}
Рейтинг: {rating}
Сделок: {deals}""",
        reply_markup=kb
    )
    await track_user_message(msg)


@dp.message(F.text == "✏️ Изменить ник")
async def change_nick(message: types.Message):
    user_states[message.from_user.id] = "change_nick"

    await full_clear(message)
    msg = await message.answer(
        "Введите новый ник",
        reply_markup=back_btn()
    )
    await track_user_message(msg)


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
    await track_user_message(msg)


# ---------------- FAQ ----------------

@dp.message(F.text == "FAQ")
async def faq(message: types.Message):
    await full_clear(message)
    msg = await message.answer(FAQ_LINK, reply_markup=back_btn())
    await track_user_message(msg)


# ---------------- СООБЩЕНИЕ АДМИНУ ----------------

@dp.message(F.text == "🚨 Сообщение админу")
async def admin_message(message: types.Message):
    user_states[message.from_user.id] = "admin_msg"

    await full_clear(message)
    msg = await message.answer(
        "Введите сообщение для администратора",
        reply_markup=back_btn()
    )
    await track_user_message(msg)


# ---------------- СДЕЛКИ ----------------

@dp.message(F.text == "🔒 Сделки через гаранта")
async def deals(message: types.Message):
    user_states[message.from_user.id] = "deal"

    await full_clear(message)
    msg = await message.answer(
        "Введите ник пользователя для сделки",
        reply_markup=back_btn()
    )
    await track_user_message(msg)


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
    await track_user_message(msg)


@dp.message(F.text == "Введите анонимный никнейм пользователя🔎")
async def find_user(message: types.Message):
    user_states[message.from_user.id] = "find_user"

    await full_clear(message)
    msg = await message.answer(
        "Введите ник пользователя",
        reply_markup=back_btn()
    )
    await track_user_message(msg)
def format_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}ч {m}мин"
    # ---------------- ОСНОВНОЙ HANDLER ----------------

@dp.message()
async def handler(message: types.Message):

    await track_user_message(message)
    state = user_states.get(message.from_user.id)

    # регистрация ника
    if state == "nickname":
        cursor.execute(
            "SELECT id FROM users WHERE nickname=?",
            (message.text,)
        )
        if cursor.fetchone():
            msg = await message.answer("❌ Ник занят")
            await track_user_message(msg)
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

    # маркет
    if state == "market":
        ok, remain = check_market(message.from_user.id)
        if not ok:
            msg = await message.answer(
                f"⏳ Подождите {format_time(remain)}"
            )
            await track_user_message(msg)
            return

        cursor.execute(
            "SELECT nickname FROM users WHERE id=?",
            (message.from_user.id,)
        )
        nick = cursor.fetchone()[0]

        text = message.text if message.text else message.caption
        text = f"{text}\n\nНик: {nick}"

        if message.photo:
            await bot.send_photo(
                CHANNEL_MARKET,
                message.photo[-1].file_id,
                caption=text
            )
        else:
            await bot.send_message(
                CHANNEL_MARKET,
                text
            )

        market_cooldowns[message.from_user.id] = time.time()
        await show_main_three(message)
        return

    # подслушано
    if state == "conf":
        ok, remain = check_conf(message.from_user.id)
        if not ok:
            msg = await message.answer(
                f"⏳ Подождите {format_time(remain)}"
            )
            await track_user_message(msg)
            return

        cursor.execute(
            "SELECT nickname FROM users WHERE id=?",
            (message.from_user.id,)
        )
        nick = cursor.fetchone()[0]

        text = message.text if message.text else message.caption
        text = f"{text}\n\nНик: {nick}"

        if message.photo:
            await bot.send_photo(
                CHANNEL_CONFESSIONS,
                message.photo[-1].file_id,
                caption=text
            )
        else:
            await bot.send_message(
                CHANNEL_CONFESSIONS,
                text
            )

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

        text = f"""
🚨 Сообщение админу

Ник: {nick}
ID: {message.from_user.id}
Username: @{message.from_user.username}

Сообщение:
{message.text}
"""

        await bot.send_message(ADMIN_ID, text)

        await show_main_three(message)
        return

    # сделки
    if state == "deal":
        cursor.execute(
            "SELECT nickname FROM users WHERE id=?",
            (message.from_user.id,)
        )
        nick1 = cursor.fetchone()[0]

        cursor.execute(
            "SELECT id FROM users WHERE nickname=?",
            (message.text,)
        )
        row = cursor.fetchone()

        if row:
            user2 = row[0]
        else:
            user2 = "не найден"

        text = f"""
📕 Новая заявка на сделку

Участник 1: {nick1}
Участник 2: {message.text}

ID 1: {message.from_user.id}
ID 2: {user2}
"""

        await bot.send_message(ADMIN_ID, text)

        await show_main_three(message)
        return
            # поиск пользователя для личного чата
    if state == "find_user":
        cursor.execute(
            "SELECT id,nickname FROM users WHERE nickname=?",
            (message.text,)
        )
        row = cursor.fetchone()

        if not row:
            msg = await message.answer("❌ Пользователь не найден")
            await track_user_message(msg)
            return

        target_id = row[0]
        chat_targets[message.from_user.id] = target_id
        chat_targets[target_id] = message.from_user.id

        cursor.execute(
            "INSERT INTO chats(user1,user2) VALUES (?,?)",
            (message.from_user.id, target_id)
        )
        conn.commit()

        msg = await message.answer(
            "💬 Чат открыт",
            reply_markup=chat_keyboard()
        )
        await track_user_message(msg)

        try:
            await bot.send_message(
                target_id,
                "💬 С вами начали анонимный чат",
                reply_markup=chat_keyboard()
            )
        except:
            pass

        user_states[message.from_user.id] = "chat"
        user_states[target_id] = "chat"
        return

    # закрытие чата
    if message.text == "❌ Закрыть чат":
        chat_targets.pop(message.from_user.id, None)
        user_states.pop(message.from_user.id, None)

        await show_main_three(message)
        return

    # пересылка сообщений
    if state == "chat":
        target = chat_targets.get(message.from_user.id)

        if not target:
            await show_main_three(message)
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
                caption=f"💬 {nick}:\n{message.caption if message.caption else ''}"
            )
        else:
            await bot.send_message(
                target,
                f"💬 {nick}:\n{message.text}"
            )
        return
        # ---------------- ЗАПУСК ----------------

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
