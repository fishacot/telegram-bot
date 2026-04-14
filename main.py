import asyncio
import csv
import os
import time
from datetime import datetime

from aiogram import Bot, Dispatcher, F, types
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)

from aiogram.filters import CommandStart, Command

from config import (
    TOKEN,
    ADMIN_ID,
    CHANNEL_MARKET,
    CHANNEL_CONFESSIONS,
    CHANNEL_CHAT
)

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ==============================
# ХРАНИЛИЩА
# ==============================

users = {}
user_states = {}
user_messages = {}
start_messages = {}
private_chats = {}

texts = {
    "market": """👋Добро пожаловать в анонимный маркетплейс!
Здесь вы можете опубликовать пост о продаже/покупке любого товара или услуге!""",

    "conf": """Добро пожаловать в «Подслушано»!
Мы решили перенести этот легендарный формат в наш анонимный форум! 🤫
Здесь ты можешь поделиться новостью или историей."""
}

photos = {}
# ==============================
# КЛАВИАТУРЫ
# ==============================

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Маркет"), KeyboardButton(text="🕵️ Подслушано")],
            [KeyboardButton(text="🔒 Сделки через гаранта"), KeyboardButton(text="⭐ Рейтинг")],
            [KeyboardButton(text="💬 Личные сообщения")],
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🚨 Сообщение админу")],
            [KeyboardButton(text="FAQ")]
        ],
        resize_keyboard=True
    )


def back_button():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад ⏪")]],
        resize_keyboard=True
    )


def market_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍️ Перейти в маркет")],
            [KeyboardButton(text="📝 Выставить объявление")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )


def conf_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Перейти в подслушано🤫")],
            [KeyboardButton(text="Отправить сообщение ✏️")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )


def dm_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Введите анонимный никнейм пользователя🔎")],
            [KeyboardButton(text="Личные чаты 📂")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )
    # ==============================
# СОХРАНЕНИЕ СООБЩЕНИЙ
# ==============================

async def track_message(message: types.Message):
    uid = message.from_user.id

    if uid not in user_messages:
        user_messages[uid] = []

    user_messages[uid].append(message.message_id)


# ==============================
# ПОЛНАЯ ОЧИСТКА ДО /START
# ==============================

async def full_cleanup(message: types.Message):

    uid = message.from_user.id

    if uid not in user_messages:
        return

    start_ids = start_messages.get(uid, [])

    for msg_id in user_messages[uid]:
        if msg_id not in start_ids:
            try:
                await bot.delete_message(uid, msg_id)
            except:
                pass

    user_messages[uid] = []


# ==============================
# НАЗАД
# ==============================

@dp.message(F.text == "Назад ⏪")
async def back_handler(message: types.Message):

    await full_cleanup(message)

    msg = await message.answer(
        "Главное меню",
        reply_markup=main_menu()
    )

    await track_message(msg)
    # ==============================
# START + РЕГИСТРАЦИЯ
# ==============================

@dp.message(CommandStart())
async def start(message: types.Message):

    uid = message.from_user.id

    user_states[uid] = "wait_nick"

    await full_cleanup(message)

    msg1 = await message.answer("Введите анонимный ник:")

    start_messages[uid] = [msg1.message_id]
    await track_message(msg1)


# ==============================
# СОХРАНЕНИЕ ПОЛЬЗОВАТЕЛЯ CSV
# ==============================

def save_user_csv(nick, uid):

    file_exists = os.path.isfile("users.csv")

    with open("users.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["date", "nickname", "id"])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d"),
            nick,
            uid
        ])


# ==============================
# ВВОД НИКА
# ==============================

@dp.message()
async def nickname_handler(message: types.Message):

    uid = message.from_user.id

    if user_states.get(uid) != "wait_nick":
        return

    nick = message.text.strip()

    for u in users.values():
        if u["nick"] == nick:
            msg = await message.answer("Ник уже занят, попробуйте другой")
            await track_message(msg)
            return

    users[uid] = {
        "nick": nick,
        "rating": 0,
        "deals": 0
    }

    save_user_csv(nick, uid)

    user_states[uid] = None

    await full_cleanup(message)

    msg1 = await message.answer("Ник сохранен")
    msg2 = await message.answer("Главное меню", reply_markup=main_menu())

    start_messages[uid] = [
        msg1.message_id,
        msg2.message_id
    ]

    await track_message(msg1)
    await track_message(msg2)
    # ==============================
# ПРОФИЛЬ
# ==============================

@dp.message(F.text == "👤 Профиль")
async def profile(message: types.Message):

    uid = message.from_user.id

    if uid not in users:
        return

    user = users[uid]

    text = (
        f"👤 Ваш профиль\n\n"
        f"Ник: {user['nick']}\n"
        f"ID: {uid}\n"
        f"Рейтинг: {user['rating']}\n"
        f"Сделки: {user['deals']}"
    )

    await full_cleanup(message)

    msg = await message.answer(
        text,
        reply_markup=back_button()
    )

    await track_message(msg)


# ==============================
# РЕЙТИНГ
# ==============================

@dp.message(F.text == "⭐ Рейтинг")
async def rating(message: types.Message):

    await full_cleanup(message)

    sorted_users = sorted(
        users.items(),
        key=lambda x: x[1]["rating"],
        reverse=True
    )

    text = "⭐ ТОП пользователей\n\n"

    for i, (uid, data) in enumerate(sorted_users[:10], start=1):
        text += f"{i}. {data['nick']} — {data['rating']}\n"

    msg = await message.answer(
        text,
        reply_markup=back_button()
    )

    await track_message(msg)


# ==============================
# FAQ
# ==============================

@dp.message(F.text == "FAQ")
async def faq(message: types.Message):

    await full_cleanup(message)

    msg = await message.answer(
        "Информация доступна в канале",
        reply_markup=back_button()
    )

    await track_message(msg)
    # ==============================
# ТАЙМЕРЫ
# ==============================

MARKET_TIMEOUT = 60
CONF_TIMEOUT = 60

market_timer = {}
conf_timer = {}


# ==============================
# МАРКЕТ
# ==============================

@dp.message(F.text == "🛒 Маркет")
async def market(message: types.Message):

    await full_cleanup(message)

    text = texts["market"]

    msg = await message.answer(
        text,
        reply_markup=market_menu()
    )

    await track_message(msg)


@dp.message(F.text == "📝 Выставить объявление")
async def create_market(message: types.Message):

    uid = message.from_user.id

    user_states[uid] = "market_wait"

    await full_cleanup(message)

    msg = await message.answer(
        "Отправьте текст и фото объявления",
        reply_markup=back_button()
    )

    await track_message(msg)


# ==============================
# ОБРАБОТКА МАРКЕТА
# ==============================

async def handle_market(message: types.Message):

    uid = message.from_user.id

    if uid in market_timer:
        if time.time() - market_timer[uid] < MARKET_TIMEOUT:
            return

    market_timer[uid] = time.time()

    nick = users[uid]["nick"]

    if message.photo:
        await bot.send_photo(
            CHANNEL_MARKET,
            message.photo[-1].file_id,
            caption=f"{nick}\n{message.caption or ''}"
        )
    else:
        await bot.send_message(
            CHANNEL_MARKET,
            f"{nick}\n{message.text}"
        )

    user_states[uid] = None
    await full_cleanup(message)
    # ==============================
# ПОДСЛУШАНО
# ==============================

@dp.message(F.text == "🕵️ Подслушано")
async def conf(message: types.Message):

    await full_cleanup(message)

    text = texts["conf"]

    msg = await message.answer(
        text,
        reply_markup=conf_menu()
    )

    await track_message(msg)


@dp.message(F.text == "Отправить сообщение ✏️")
async def create_conf(message: types.Message):

    uid = message.from_user.id

    user_states[uid] = "conf_wait"

    await full_cleanup(message)

    msg = await message.answer(
        "Отправьте сообщение (текст + фото)",
        reply_markup=back_button()
    )

    await track_message(msg)


# ==============================
# ОБРАБОТКА ПОДСЛУШАНО
# ==============================

async def handle_conf(message: types.Message):

    uid = message.from_user.id

    if uid in conf_timer:
        if time.time() - conf_timer[uid] < CONF_TIMEOUT:
            return

    conf_timer[uid] = time.time()

    nick = users[uid]["nick"]

    if message.photo:
        await bot.send_photo(
            CHANNEL_CONFESSIONS,
            message.photo[-1].file_id,
            caption=f"{nick}\n{message.caption or ''}"
        )
    else:
        await bot.send_message(
            CHANNEL_CONFESSIONS,
            f"{nick}\n{message.text}"
        )

    user_states[uid] = None
    await full_cleanup(message)
    # ==============================
# ЛИЧНЫЕ СООБЩЕНИЯ
# ==============================

@dp.message(F.text == "💬 Личные сообщения")
async def dm_menu_handler(message: types.Message):

    await full_cleanup(message)

    msg = await message.answer(
        "Личные сообщения",
        reply_markup=dm_menu()
    )

    await track_message(msg)


@dp.message(F.text == "Введите анонимный никнейм пользователя🔎")
async def dm_search(message: types.Message):

    uid = message.from_user.id
    user_states[uid] = "dm_search"

    await full_cleanup(message)

    msg = await message.answer(
        "Введите ник пользователя",
        reply_markup=back_button()
    )

    await track_message(msg)


# ==============================
# ПОИСК ПОЛЬЗОВАТЕЛЯ
# ==============================

async def handle_dm_search(message: types.Message):

    uid = message.from_user.id
    nick = message.text.strip()

    target_id = None

    for u_id, data in users.items():
        if data["nick"].lower() == nick.lower():
            target_id = u_id
            break

    if not target_id:
        msg = await message.answer("Пользователь не найден")
        await track_message(msg)
        return

    dialogs.setdefault(uid, [])
    dialogs.setdefault(target_id, [])

    if target_id not in dialogs[uid]:
        dialogs[uid].append(target_id)

    if uid not in dialogs[target_id]:
        dialogs[target_id].append(uid)

    active_chats[uid] = target_id
    active_chats[target_id] = uid

    user_states[uid] = "dm_chat"

    await full_cleanup(message)

    msg = await message.answer(
        f"Чат с {users[target_id]['nick']}",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="❌ Закрыть чат")],
                [KeyboardButton(text="Назад ⏪")]
            ],
            resize_keyboard=True
        )
    )

    await track_message(msg)
    # ==============================
# ПЕРЕСЫЛКА СООБЩЕНИЙ В ЛС
# ==============================

async def handle_dm_chat(message: types.Message):

    uid = message.from_user.id

    if uid not in active_chats:
        return

    target = active_chats[uid]

    if message.photo:
        await bot.send_photo(
            target,
            message.photo[-1].file_id,
            caption=message.caption
        )
    else:
        await bot.send_message(
            target,
            message.text
        )


# ==============================
# ЗАКРЫТЬ ЧАТ
# ==============================

@dp.message(F.text == "❌ Закрыть чат")
async def close_chat(message: types.Message):

    uid = message.from_user.id

    if uid in active_chats:
        target = active_chats[uid]
        active_chats.pop(uid, None)
        active_chats.pop(target, None)

    user_states[uid] = None

    await full_cleanup(message)

    msg = await message.answer(
        "Чат закрыт",
        reply_markup=main_menu()
    )

    await track_message(msg)
    # ==============================
# СДЕЛКИ ЧЕРЕЗ ГАРАНТА
# ==============================

@dp.message(F.text == "🔒 Сделки через гаранта")
async def deals(message: types.Message):

    uid = message.from_user.id
    user_states[uid] = "deal_wait"

    await full_cleanup(message)

    msg = await message.answer(
        "Введите ник пользователя для сделки",
        reply_markup=back_button()
    )

    await track_message(msg)


async def handle_deal(message: types.Message):

    uid = message.from_user.id
    nick1 = users[uid]["nick"]
    nick2 = message.text

    target_id = None

    for u_id, data in users.items():
        if data["nick"].lower() == nick2.lower():
            target_id = u_id
            break

    if not target_id:
        msg = await message.answer("Пользователь не найден")
        await track_message(msg)
        return

    await bot.send_message(
        ADMIN_ID,
        f"{nick1} хочет заключить сделку с {nick2}\n"
        f"id1: {uid}\n"
        f"id2: {target_id}"
    )

    user_states[uid] = None
    await full_cleanup(message)


# ==============================
# СООБЩЕНИЕ АДМИНУ
# ==============================

@dp.message(F.text == "🚨 Сообщение админу")
async def admin_msg(message: types.Message):

    uid = message.from_user.id
    user_states[uid] = "admin_wait"

    await full_cleanup(message)

    msg = await message.answer(
        "Напишите сообщение админу",
        reply_markup=back_button()
    )

    await track_message(msg)


async def handle_admin_msg(message: types.Message):

    uid = message.from_user.id
    nick = users[uid]["nick"]

    await bot.send_message(
        ADMIN_ID,
        f"{nick}: {message.text}"
    )

    user_states[uid] = None
    await full_cleanup(message)
    # ==============================
# АДМИН ПАНЕЛЬ
# ==============================

def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Количество пользователей")],
            [KeyboardButton(text="👥 Список пользователей")],
            [KeyboardButton(text="🔎 Поиск пользователя")],
            [KeyboardButton(text="✏️ Редактор текстов")],
            [KeyboardButton(text="🖼 Редактор фото")],
            [KeyboardButton(text="📁 Скачать CSV")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )


@dp.message(Command("admin"))
async def admin_panel(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    await full_cleanup(message)

    msg = await message.answer(
        "Админ панель",
        reply_markup=admin_menu()
    )

    await track_message(msg)


# ==============================
# КОЛИЧЕСТВО ПОЛЬЗОВАТЕЛЕЙ
# ==============================

@dp.message(F.text == "📊 Количество пользователей")
async def users_count(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    count = len(users)

    msg = await message.answer(f"Пользователей: {count}")
    await track_message(msg)


# ==============================
# СПИСОК ПОЛЬЗОВАТЕЛЕЙ
# ==============================

@dp.message(F.text == "👥 Список пользователей")
async def users_list(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    text = "Пользователи:\n\n"

    for uid, data in users.items():
        text += f"{data['nick']} — {uid}\n"

    msg = await message.answer(text[:4000])
    await track_message(msg)


# ==============================
# ПОИСК ПОЛЬЗОВАТЕЛЯ
# ==============================

@dp.message(F.text == "🔎 Поиск пользователя")
async def find_user_admin(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    user_states[message.from_user.id] = "admin_search"

    msg = await message.answer("Введите ник пользователя")
    await track_message(msg)


async def handle_admin_search(message: types.Message):

    nick = message.text.strip()

    for uid, data in users.items():
        if data["nick"].lower() == nick.lower():

            username = message.from_user.username or "нет"

            msg = await message.answer(
                f"Ник: {data['nick']}\n"
                f"ID: {uid}\n"
                f"Username: @{username}"
            )
            await track_message(msg)
            return

    msg = await message.answer("Пользователь не найден")
    await track_message(msg)
    # ==============================
# РЕДАКТОР ТЕКСТОВ
# ==============================

@dp.message(F.text == "✏️ Редактор текстов")
async def edit_texts(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="market")],
            [KeyboardButton(text="conf")],
            [KeyboardButton(text="faq")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )

    msg = await message.answer("Выберите текст", reply_markup=kb)
    await track_message(msg)


@dp.message(F.text.in_(["market", "conf", "faq"]))
async def choose_text(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    key = message.text
    user_states[message.from_user.id] = f"edit_text_{key}"

    msg = await message.answer("Отправьте новый текст")
    await track_message(msg)


# ==============================
# РЕДАКТОР ФОТО
# ==============================

@dp.message(F.text == "🖼 Редактор фото")
async def edit_photo(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="market_photo")],
            [KeyboardButton(text="conf_photo")],
            [KeyboardButton(text="faq_photo")],
            [KeyboardButton(text="profile_photo")],
            [KeyboardButton(text="admin_photo")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )

    msg = await message.answer("Выберите фото", reply_markup=kb)
    await track_message(msg)


@dp.message(F.text.in_(["market_photo","conf_photo","faq_photo","profile_photo","admin_photo"]))
async def choose_photo(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    key = message.text
    user_states[message.from_user.id] = f"edit_photo_{key}"

    msg = await message.answer("Отправьте фото")
    await track_message(msg)


# ==============================
# СОХРАНЕНИЕ ФОТО
# ==============================

async def handle_photo_save(message: types.Message):

    uid = message.from_user.id
    state = user_states.get(uid)

    if not state or not state.startswith("edit_photo_"):
        return

    key = state.replace("edit_photo_", "")

    if not message.photo:
        return

    photos[key] = message.photo[-1].file_id

    user_states[uid] = None

    msg = await message.answer("Фото сохранено")
    await track_message(msg)


# ==============================
# СОХРАНЕНИЕ ТЕКСТА
# ==============================

async def handle_text_save(message: types.Message):

    uid = message.from_user.id
    state = user_states.get(uid)

    if not state or not state.startswith("edit_text_"):
        return

    key = state.replace("edit_text_", "")

    texts[key] = message.text

    user_states[uid] = None

    msg = await message.answer("Текст сохранен")
    await track_message(msg)
    # ==============================
# ЕДИНЫЙ HANDLER
# ==============================

@dp.message()
async def main_handler(message: types.Message):

    uid = message.from_user.id
    state = user_states.get(uid)

    # регистрация ника
    if state == "register":
        await handle_register(message)
        return

    # маркет
    if state == "market":
        await handle_market(message)
        return

    # подслушано
    if state == "conf":
        await handle_conf(message)
        return

    # поиск ЛС
    if state == "dm_search":
        await handle_dm_search(message)
        return

    # чат ЛС
    if state == "dm_chat":
        await handle_dm_chat(message)
        return

    # сделки
    if state == "deal_wait":
        await handle_deal(message)
        return

    # сообщение админу
    if state == "admin_wait":
        await handle_admin_msg(message)
        return

    # поиск админ
    if state == "admin_search":
        await handle_admin_search(message)
        return

    # редактор текстов
    if state and state.startswith("edit_text_"):
        await handle_text_save(message)
        return

    # редактор фото
    if state and state.startswith("edit_photo_"):
        await handle_photo_save(message)
        return


# ==============================
# ЗАПУСК БОТА
# ==============================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
