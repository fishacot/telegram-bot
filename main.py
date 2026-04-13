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


def main_menu(user_id=None):
    buttons = [
        [KeyboardButton(text="🛒 Маркет объявлений")],
        [KeyboardButton(text="🕵️ Подслушано")],
        [KeyboardButton(text="🔒 Сделки через гаранта")],
        [KeyboardButton(text="⭐ Рейтинг")],
        [KeyboardButton(text="💬 Личные сообщения")],
        [KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="🚨 Сообщение админу")],
        [KeyboardButton(text="FAQ")]
    ]

    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="👮 Админ панель")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
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


async def clear_user_messages(message: types.Message):
    msgs = user_messages.get(message.from_user.id, [])
    for msg_id in msgs:
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except:
            pass
    user_messages[message.from_user.id] = []


async def send_clean(message: types.Message, text, reply_markup=None, clear=False):
    if clear:
        await clear_user_messages(message)

    msg = await message.answer(text, reply_markup=reply_markup)
    await track_user_message(msg)


@dp.message(Command("start"))
async def start(message: types.Message):
    cursor.execute("SELECT * FROM users WHERE id=?", (message.from_user.id,))
    user = cursor.fetchone()

    if not user:
        user_states[message.from_user.id] = "nickname"
        await send_clean(
            message,
            "Введите ваш анонимный никнейм"
        )
        return

    await send_clean(
        message,
        "🏠 Главное меню",
        main_menu(message.from_user.id),
        clear=True
    )


@dp.message(F.text == "Назад ⏪")
async def back(message: types.Message):
    user_states.pop(message.from_user.id, None)
    await send_clean(
        message,
        "🏠 Главное меню",
        main_menu(message.from_user.id),
        clear=True
    )
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

    await send_clean(
        message,
        "👋 Добро пожаловать в анонимный маркетплейс!",
        kb
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

    await send_clean(message, "Выберите тип объявления", kb)


@dp.message(F.text.in_(["💵 Выставить пост о продаже", "🛒 Выставить пост о покупке"]))
async def market_text(message: types.Message):
    user_states[message.from_user.id] = "market"
    await send_clean(message, "Введите ваше объявление", back_btn())


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

    await send_clean(
        message,
        "Добро пожаловать в «Подслушано» 🤫",
        kb
    )


@dp.message(F.text == "Перейти в подслушано🤫")
async def go_conf(message: types.Message):
    await send_clean(message, CONF_LINK)


@dp.message(F.text == "Отправить сообщение ✏️")
async def send_conf(message: types.Message):
    user_states[message.from_user.id] = "conf"
    await send_clean(message, "Отправьте сообщение", back_btn())
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
        kb
    )


@dp.message(F.text == "✏️ Изменить ник")
async def change_nick(message: types.Message):
    user_states[message.from_user.id] = "change_nick"
    await send_clean(message, "Введите новый ник", back_btn())


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

    await send_clean(message, text, back_btn())


# ---------------- FAQ ----------------

@dp.message(F.text == "FAQ")
async def faq(message: types.Message):
    await send_clean(message, FAQ_LINK, back_btn())


# ---------------- СДЕЛКИ ----------------

@dp.message(F.text == "🔒 Сделки через гаранта")
async def deals_menu(message: types.Message):
    await send_clean(
        message,
        "Раздел сделок через гаранта находится в разработке",
        back_btn()
    )# ---------------- ЛИЧНЫЕ СООБЩЕНИЯ ----------------

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


# ---------------- АДМИН ПАНЕЛЬ ----------------

@dp.message(F.text == "👮 Админ панель")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="📢 Рассылка")],
            [KeyboardButton(text="🧹 Очистить кд")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )

    await send_clean(message, "Админ панель", kb)


@dp.message(F.text == "📊 Статистика")
async def admin_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM chats")
    chats = cursor.fetchone()[0]

    await send_clean(
        message,
        f"""📊 Статистика

Пользователей: {users}
Чатов: {chats}""",
        back_btn()
    )


@dp.message(F.text == "📢 Рассылка")
async def admin_broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    user_states[message.from_user.id] = "broadcast"
    await send_clean(message, "Введите текст рассылки", back_btn())


@dp.message(F.text == "🧹 Очистить кд")
async def admin_clear_cd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    post_cooldowns.clear()
    await send_clean(message, "Кулдауны очищены", back_btn())
    # ---------------- ГЛАВНЫЙ HANDLER ----------------

@dp.message()
async def handler(message: types.Message):

    await track_user_message(message)
    state = user_states.get(message.from_user.id)

    # ---------- смена ника ----------
    if state == "change_nick":
        cursor.execute(
            "UPDATE users SET nickname=? WHERE id=?",
            (message.text, message.from_user.id)
        )
        conn.commit()

        await send_clean(
            message,
            "Ник изменен",
            main_menu(message.from_user.id),
            clear=True
        )
        return

    # ---------- сообщение админу ----------
    if state == "admin":
        await bot.send_message(
            ADMIN_ID,
            f"Сообщение от {message.from_user.id}:\n{message.text}"
        )

        await send_clean(
            message,
            "Сообщение отправлено",
            main_menu(message.from_user.id),
            clear=True
        )
        return

    # ---------- регистрация ----------
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

        await send_clean(
            message,
            "Ник сохранен",
            main_menu(message.from_user.id),
            clear=True
        )
        return

    # ---------- рассылка ----------
    if state == "broadcast" and message.from_user.id == ADMIN_ID:
        cursor.execute("SELECT id FROM users")
        users = cursor.fetchall()

        for u in users:
            try:
                await bot.send_message(u[0], message.text)
            except:
                pass

        await send_clean(message, "Рассылка отправлена", back_btn())
        return

    # ---------- MARKET ----------
    if state == "market":

        ok, remain = check_cooldown(message.from_user.id)
        if not ok:
            await send_clean(
                message,
                f"⏳ Публиковать можно раз в 2.5 часа\nОсталось: {format_time(remain)}",
                back_btn()
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

        await send_clean(
            message,
            "Объявление опубликовано",
            main_menu(message.from_user.id),
            clear=True
        )
        return

    # ---------- CONF ----------
    if state == "conf":

        ok, remain = check_cooldown(message.from_user.id)
        if not ok:
            await send_clean(
                message,
                f"⏳ Публиковать можно раз в 2.5 часа\nОсталось: {format_time(remain)}",
                back_btn()
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

        await send_clean(
            message,
            "Сообщение опубликовано",
            main_menu(message.from_user.id),
            clear=True
        )
        return

    # ---------- поиск пользователя ----------
    if state == "find_user":

        cursor.execute(
            "SELECT id FROM users WHERE nickname=?",
            (message.text,)
        )
        user = cursor.fetchone()

        if not user:
            await send_clean(message, "Пользователь не найден", back_btn())
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
            chat_keyboard(),
            clear=True
        )
        return

    # ---------- чат ----------
    if state == "chat":

        if message.text == "❌ Закрыть чат":
            user_states.pop(message.from_user.id, None)
            await send_clean(
                message,
                "Чат закрыт",
                main_menu(message.from_user.id),
                clear=True
            )
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


# ---------------- ЗАПУСК ----------------

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
