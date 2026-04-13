import asyncio
import sqlite3
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import *

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

ADMIN_ID = 554529638

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

# ---------------- ПОЛНАЯ ОЧИСТКА ДО /START ----------------

async def full_clear(message: types.Message):
    try:
        for i in range(message.message_id, message.message_id - 200, -1):
            try:
                await bot.delete_message(message.chat.id, i)
            except:
                pass
    except:
        pass


async def show_main_three(message: types.Message):
    await full_clear(message)

    msg1 = await message.answer(
        get_text("welcome",
"""Приветствуем в самом скрытном уголке района Внуково 🕵️‍♀️

Здесь можно быть кем угодно или не быть никем. Ваш анонимный никнейм это ваше альтер-эго, ваш аккаунт не будет высвечиваться ни при публикации объявлений, ни при участии обсуждения на форумах 🛡️

Впишите свой анонимный никнейм :
""")
    )

    msg2 = await message.answer("✅ Ник сохранен")

    msg3 = await message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu()
    )


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


# ---------------- ТЕКСТЫ ИЗ БД ----------------

def get_text(key, default):
    cursor.execute(
        "SELECT text FROM admin_texts WHERE key=?",
        (key,)
    )
    row = cursor.fetchone()
    return row[0] if row else default
    # ---------------- START ----------------

@dp.message(Command("start"))
async def start(message: types.Message):
    cursor.execute("SELECT * FROM users WHERE id=?", (message.from_user.id,))
    user = cursor.fetchone()

    if not user:
        user_states[message.from_user.id] = "nickname"

        await full_clear(message)

        await message.answer(
            get_text("welcome",
"""Приветствуем в самом скрытном уголке района Внуково 🕵️‍♀️

Здесь можно быть кем угодно или не быть никем. Ваш анонимный никнейм это ваше альтер-эго, ваш аккаунт не будет высвечиваться ни при публикации объявлений, ни при участии обсуждения на форумах 🛡️

Впишите свой анонимный никнейм :
""")
        )
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

    text = get_text(
        "market",
"""👋Добро пожаловать в анонимный маркетплейс!
Здесь вы можете опубликовать пост о продаже/покупке любого товара или услуге!"""
    )

    cursor.execute("SELECT file_id FROM admin_photos WHERE key='market'")
    photo = cursor.fetchone()

    if photo:
        await bot.send_photo(message.chat.id, photo[0], caption=text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


@dp.message(F.text == "🛍️ Перейти в маркет")
async def go_market(message: types.Message):
    await message.answer(MARKET_LINK)


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
    await message.answer("Выберите тип объявления", reply_markup=kb)


@dp.message(F.text.in_(["💵 Продажа", "🛒 Покупка"]))
async def market_input(message: types.Message):
    user_states[message.from_user.id] = "market"

    await full_clear(message)
    await message.answer(
        "Введите текст объявления (можно фото)",
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

    await full_clear(message)

    text = get_text(
        "conf",
"""Добро пожаловать в «Подслушано»!
Мы решили перенести этот легендарный формат в наш анонимный форум! 🤫
Здесь ты можешь без лишних глаз поделиться самой горячей сплетней или топовой новостью. Твой секрет — наш контент! 👇"""
    )

    cursor.execute("SELECT file_id FROM admin_photos WHERE key='conf'")
    photo = cursor.fetchone()

    if photo:
        await bot.send_photo(message.chat.id, photo[0], caption=text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


@dp.message(F.text == "Перейти в подслушано🤫")
async def go_conf(message: types.Message):
    await message.answer(CONF_LINK)


@dp.message(F.text == "Отправить сообщение ✏️")
async def conf_input(message: types.Message):
    user_states[message.from_user.id] = "conf"

    await full_clear(message)
    await message.answer(
        "Введите сообщение",
        reply_markup=back_btn()
    )
    # ---------------- ПРОФИЛЬ ----------------

@dp.message(F.text == "👤 Профиль")
async def profile(message: types.Message):
    cursor.execute(
        "SELECT nickname,rating,deals FROM users WHERE id=?",
        (message.from_user.id,)
    )
    nick, rating, deals = cursor.fetchone()

    await full_clear(message)

    await message.answer(
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


@dp.message(F.text == "✏️ Изменить ник")
async def change_nick(message: types.Message):
    user_states[message.from_user.id] = "change_nick"

    await full_clear(message)
    await message.answer(
        "Введите новый ник",
        reply_markup=back_btn()
    )


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
    await message.answer(text, reply_markup=back_btn())


# ---------------- FAQ ----------------

@dp.message(F.text == "FAQ")
async def faq(message: types.Message):
    await full_clear(message)
    await message.answer(FAQ_LINK, reply_markup=back_btn())


# ---------------- СООБЩЕНИЕ АДМИНУ ----------------

@dp.message(F.text == "🚨 Сообщение админу")
async def admin_msg(message: types.Message):
    user_states[message.from_user.id] = "admin_msg"

    await full_clear(message)
    await message.answer(
        "Введите сообщение для администратора",
        reply_markup=back_btn()
    )


# ---------------- СДЕЛКИ ----------------

@dp.message(F.text == "🔒 Сделки через гаранта")
async def deals(message: types.Message):
    user_states[message.from_user.id] = "deal"

    await full_clear(message)
    await message.answer(
        "Введите ник пользователя для сделки",
        reply_markup=back_btn()
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

    await full_clear(message)
    await message.answer(
        "Выберите действие",
        reply_markup=kb
    )


@dp.message(F.text == "Введите анонимный никнейм пользователя🔎")
async def find_user(message: types.Message):
    user_states[message.from_user.id] = "find_user"

    await full_clear(message)
    await message.answer(
        "Введите ник пользователя",
        reply_markup=back_btn()
    )
    # ---------------- АДМИН ПАНЕЛЬ ----------------

def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📔 Тексты"), KeyboardButton(text="📸 Фото")],
            [KeyboardButton(text="🤖 Сообщения админу"), KeyboardButton(text="📕 Заявки")],
            [KeyboardButton(text="📈 Количество пользователей")],
            [KeyboardButton(text="👥 Список пользователей")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )


@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    await full_clear(message)
    await message.answer("Админ панель", reply_markup=admin_menu())


# ---------------- АДМИН ТЕКСТЫ ----------------

@dp.message(F.text == "📔 Тексты")
async def admin_texts(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="welcome"), KeyboardButton(text="market")],
            [KeyboardButton(text="conf"), KeyboardButton(text="profile")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )

    await full_clear(message)
    await message.answer("Выберите текст", reply_markup=kb)


@dp.message(F.text.in_(["welcome", "market", "conf", "profile"]))
async def choose_text(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    user_states[message.from_user.id] = f"edit_text_{message.text}"

    await full_clear(message)
    await message.answer(
        "Введите новый текст",
        reply_markup=back_btn()
    )


# ---------------- АДМИН ФОТО ----------------

@dp.message(F.text == "📸 Фото")
async def admin_photo(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="welcome"), KeyboardButton(text="market")],
            [KeyboardButton(text="conf"), KeyboardButton(text="profile")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )

    await full_clear(message)
    await message.answer("Куда добавить фото?", reply_markup=kb)


@dp.message(F.text.in_(["welcome", "market", "conf", "profile"]))
async def choose_photo(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    user_states[message.from_user.id] = f"photo_{message.text}"

    await full_clear(message)
    await message.answer(
        "Отправьте фото",
        reply_markup=back_btn()
    )


# ---------------- СООБЩЕНИЯ АДМИНУ ----------------

@dp.message(F.text == "🤖 Сообщения админу")
async def admin_msgs(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT nickname,text FROM admin_messages ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()

    text = "Сообщения:\n\n"
    for row in rows:
        text += f"{row[0]}: {row[1]}\n\n"

    await full_clear(message)
    await message.answer(text, reply_markup=admin_menu())


# ---------------- ЗАЯВКИ ----------------

@dp.message(F.text == "📕 Заявки")
async def admin_deals(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT nick1,nick2,id1,id2 FROM deals ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()

    text = ""
    for r in rows:
        text += f"{r[0]} хочет заключить сделку с {r[1]}\nID1: {r[2]}\nID2: {r[3]}\n\n"

    await full_clear(message)
    await message.answer(text if text else "Нет заявок", reply_markup=admin_menu())


# ---------------- КОЛИЧЕСТВО ПОЛЬЗОВАТЕЛЕЙ ----------------

@dp.message(F.text == "📈 Количество пользователей")
async def users_count(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    await full_clear(message)
    await message.answer(
        f"Всего пользователей: {count}",
        reply_markup=admin_menu()
    )


# ---------------- СПИСОК ПОЛЬЗОВАТЕЛЕЙ ----------------

@dp.message(F.text == "👥 Список пользователей")
async def users_list(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    user_states[message.from_user.id] = "find_user_admin"

    await full_clear(message)
    await message.answer(
        "Введите анонимный ник",
        reply_markup=back_btn()
    )
# ---------------- ОСНОВНОЙ HANDLER ----------------

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
            await message.answer("❌ Ник занят")
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
            await message.answer(f"⏳ Подождите {format_time(remain)}")
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
            await bot.send_message(CHANNEL_MARKET, text)

        market_cooldowns[message.from_user.id] = time.time()
        await show_main_three(message)
        return

    # CONF
    if state == "conf":
        ok, remain = check_conf(message.from_user.id)
        if not ok:
            await message.answer(f"⏳ Подождите {format_time(remain)}")
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

        if not row:
            await message.answer("Пользователь не найден")
            return

        id2 = row[0]

        cursor.execute(
            "SELECT nickname FROM users WHERE id=?",
            (id2,)
        )
        nick2 = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO deals(nick1,nick2,id1,id2) VALUES (?,?,?,?)",
            (nick1, nick2, message.from_user.id, id2)
        )
        conn.commit()

        await show_main_three(message)
        return

    # поиск пользователя админ
    if state == "find_user_admin":
        cursor.execute(
            "SELECT id FROM users WHERE nickname=?",
            (message.text,)
        )
        row = cursor.fetchone()

        if not row:
            await message.answer("Не найден")
            return

        user_id = row[0]

        try:
            chat = await bot.get_chat(user_id)
            username = f"@{chat.username}" if chat.username else "нет"
        except:
            username = "нет"

        await message.answer(
            f"Ник: {message.text}\nID: {user_id}\nUsername: {username}"
        )
        return

    # редактирование текста
    if state and state.startswith("edit_text_"):
        key = state.replace("edit_text_", "")

        cursor.execute(
            "REPLACE INTO admin_texts(key,text) VALUES (?,?)",
            (key, message.text)
        )
        conn.commit()

        await message.answer("Сохранено")
        user_states.pop(message.from_user.id)
        return

    # фото админ
    if state and state.startswith("photo_"):
        if not message.photo:
            await message.answer("Отправьте фото")
            return

        key = state.replace("photo_", "")

        cursor.execute(
            "REPLACE INTO admin_photos(key,file_id) VALUES (?,?)",
            (key, message.photo[-1].file_id)
        )
        conn.commit()

        await message.answer("Фото сохранено")
        user_states.pop(message.from_user.id)
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
            await message.answer("❌ Пользователь не найден")
            return

        target = row[0]

        chat_targets[message.from_user.id] = target
        chat_targets[target] = message.from_user.id

        user_states[message.from_user.id] = "chat"
        user_states[target] = "chat"

        await message.answer(
            "Чат открыт",
            reply_markup=chat_keyboard()
        )

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


# ---------------- ЗАПУСК ----------------

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
