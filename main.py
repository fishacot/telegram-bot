import asyncio
import csv
import os
import time
from datetime import datetime

from aiogram import Bot, Dispatcher, F, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
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
# СОСТОЯНИЯ
# ==============================

STATE_WAIT_NICK = "wait_nick"
STATE_REGISTER = "register"
STATE_MARKET = "market"
STATE_CONF = "conf"
STATE_DM_SEARCH = "dm_search"
STATE_DM_CHAT = "dm_chat"
STATE_DEAL = "deal"
STATE_ADMIN_MSG = "admin_msg"
STATE_COMMON_CHAT = "common_chat"


# ==============================
# ХРАНИЛИЩА
# ==============================

users = {}
user_states = {}
user_messages = {}
start_messages = {}
active_chats = {}

market_timer = {}
conf_timer = {}
chat_timer = {}

MARKET_TIMEOUT = 60
CONF_TIMEOUT = 60
CHAT_TIMEOUT = 5


# ==============================
# КЛАВИАТУРЫ
# ==============================

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Маркет"), KeyboardButton(text="🕵️ Подслушано")],
            [KeyboardButton(text="🗣 Общий чат"), KeyboardButton(text="💬 Личные сообщения")],
            [KeyboardButton(text="🔒 Сделки через гаранта"), KeyboardButton(text="⭐ Рейтинг")],
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
            [KeyboardButton(text="📝 Выставить объявление")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )


def conf_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправить сообщение ✏️")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )


def dm_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Найти пользователя 🔎")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )


def chat_exit():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Выйти из чата")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )


# ==============================
# CSV
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
# TRACK MESSAGES
# ==============================

async def track_message(message: types.Message):
    uid = message.from_user.id

    if uid not in user_messages:
        user_messages[uid] = []

    user_messages[uid].append(message.message_id)


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
# START
# ==============================

@dp.message(CommandStart())
async def start(message: types.Message):

    uid = message.from_user.id
    user_states[uid] = STATE_REGISTER

    await full_cleanup(message)

    msg = await message.answer("Введите анонимный ник:")
    await track_message(msg)

# ==============================
# РЕГИСТРАЦИЯ НИКА
# ==============================

async def handle_nick(message: types.Message):

    uid = message.from_user.id
    nick = message.text.strip()

    for u in users.values():
        if u["nick"].lower() == nick.lower():
            msg = await message.answer("Ник уже занят")
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
    msg2 = await message.answer(
        "Главное меню",
        reply_markup=main_menu()
    )

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
        f"👤 Профиль\n\n"
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
        "Информация в закрепе канала",
        reply_markup=back_button()
    )

    await track_message(msg)
    # ==============================
# МАРКЕТ
# ==============================

@dp.message(F.text == "🛒 Маркет")
async def market_menu_handler(message: types.Message):

    await full_cleanup(message)

    msg = await message.answer(
        "Анонимный маркетплейс",
        reply_markup=market_menu()
    )

    await track_message(msg)


@dp.message(F.text == "📝 Выставить объявление")
async def create_market(message: types.Message):

    uid = message.from_user.id
    user_states[uid] = STATE_MARKET

    await full_cleanup(message)

    msg = await message.answer(
        "Отправьте текст и фото объявления",
        reply_markup=back_button()
    )

    await track_message(msg)


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

    msg = await message.answer(
        "Объявление отправлено",
        reply_markup=main_menu()
    )

    await track_message(msg)


# ==============================
# ПОДСЛУШАНО
# ==============================

@dp.message(F.text == "🕵️ Подслушано")
async def conf_menu_handler(message: types.Message):

    await full_cleanup(message)

    msg = await message.answer(
        "Анонимные сообщения",
        reply_markup=conf_menu()
    )

    await track_message(msg)


@dp.message(F.text == "Отправить сообщение ✏️")
async def create_conf(message: types.Message):

    uid = message.from_user.id
    user_states[uid] = STATE_CONF

    await full_cleanup(message)

    msg = await message.answer(
        "Отправьте сообщение",
        reply_markup=back_button()
    )

    await track_message(msg)


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

    msg = await message.answer(
        "Сообщение отправлено",
        reply_markup=main_menu()
    )

    await track_message(msg)
    # ==============================
# ОБЩИЙ АНОНИМНЫЙ ЧАТ
# ==============================

@dp.message(F.text == "🗣 Общий чат")
async def common_chat(message: types.Message):

    uid = message.from_user.id
    user_states[uid] = STATE_COMMON_CHAT

    await full_cleanup(message)

    msg = await message.answer(
        "Вы вошли в анонимный общий чат",
        reply_markup=chat_exit()
    )

    await track_message(msg)


async def handle_common_chat(message: types.Message):

    uid = message.from_user.id

    if uid in chat_timer:
        if time.time() - chat_timer[uid] < CHAT_TIMEOUT:
            return

    chat_timer[uid] = time.time()

    nick = users[uid]["nick"]

    if message.photo:
        await bot.send_photo(
            CHANNEL_CHAT,
            message.photo[-1].file_id,
            caption=f"{nick}\n{message.caption or ''}"
        )
    else:
        await bot.send_message(
            CHANNEL_CHAT,
            f"{nick}\n{message.text}"
        )


@dp.message(F.text == "❌ Выйти из чата")
async def exit_common_chat(message: types.Message):

    uid = message.from_user.id
    user_states[uid] = None

    await full_cleanup(message)

    msg = await message.answer(
        "Вы вышли из общего чата",
        reply_markup=main_menu()
    )

    await track_message(msg)


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


@dp.message(F.text == "Найти пользователя 🔎")
async def dm_search(message: types.Message):

    uid = message.from_user.id
    user_states[uid] = STATE_DM_SEARCH

    await full_cleanup(message)

    msg = await message.answer(
        "Введите ник пользователя",
        reply_markup=back_button()
    )

    await track_message(msg)


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

    active_chats[uid] = target_id
    active_chats[target_id] = uid

    user_states[uid] = STATE_DM_CHAT

    await full_cleanup(message)

    msg = await message.answer(
        f"Чат с {users[target_id]['nick']}",
        reply_markup=chat_exit()
    )

    await track_message(msg)


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
# СДЕЛКИ ЧЕРЕЗ ГАРАНТА
# ==============================

@dp.message(F.text == "🔒 Сделки через гаранта")
async def deals(message: types.Message):

    uid = message.from_user.id
    user_states[uid] = STATE_DEAL

    await full_cleanup(message)

    msg = await message.answer(
        "Введите ник пользователя для сделки",
        reply_markup=back_button()
    )

    await track_message(msg)


async def handle_deal(message: types.Message):

    uid = message.from_user.id
    nick1 = users[uid]["nick"]
    nick2 = message.text.strip()

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
        f"🔒 Сделка\n"
        f"{nick1} ↔ {nick2}\n"
        f"id1: {uid}\n"
        f"id2: {target_id}"
    )

    user_states[uid] = None

    await full_cleanup(message)

    msg = await message.answer(
        "Запрос отправлен гаранту",
        reply_markup=main_menu()
    )

    await track_message(msg)


# ==============================
# СООБЩЕНИЕ АДМИНУ
# ==============================

@dp.message(F.text == "🚨 Сообщение админу")
async def admin_msg(message: types.Message):

    uid = message.from_user.id
    user_states[uid] = STATE_ADMIN_MSG

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
        f"📩 Сообщение админу\n"
        f"{nick} ({uid})\n\n"
        f"{message.text}"
    )

    user_states[uid] = None

    await full_cleanup(message)

    msg = await message.answer(
        "Сообщение отправлено",
        reply_markup=main_menu()
    )

    await track_message(msg)
    # ==============================
# АДМИН МЕНЮ
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
# ПОИСК ПОЛЬЗОВАТЕЛЯ (АДМИН)
# ==============================

@dp.message(F.text == "🔎 Поиск пользователя")
async def find_user_admin(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    user_states[message.from_user.id] = STATE_ADMIN_SEARCH

    msg = await message.answer("Введите ник пользователя")
    await track_message(msg)


async def handle_admin_search(message: types.Message):

    nick = message.text.strip()

    for uid, data in users.items():
        if data["nick"].lower() == nick.lower():

            msg = await message.answer(
                f"Ник: {data['nick']}\n"
                f"ID: {uid}"
            )
            await track_message(msg)
            return

    msg = await message.answer("Пользователь не найден")
    await track_message(msg)


# ==============================
# СКАЧАТЬ CSV
# ==============================

# ==============================
# СКАЧАТЬ CSV
# ==============================

@dp.message(F.text == "📁 Скачать CSV")
async def download_csv(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    if not os.path.exists("users.csv"):
        msg = await message.answer("Файл пуст")
        await track_message(msg)
        return

    await bot.send_document(
        message.from_user.id,
        types.FSInputFile("users.csv")
    )


# ==============================
# ГЛАВНЫЙ HANDLER
# ==============================

@dp.message()
async def main_handler(message: types.Message):

    uid = message.from_user.id
    state = user_states.get(uid)

    # регистрация ника
    if state == STATE_REGISTER:
        await handle_nick(message)
        return

    # маркет
    if state == STATE_MARKET:
        await handle_market(message)
        return

    # подслушано
    if state == STATE_CONF:
        await handle_conf(message)
        return

    # общий чат
    if state == STATE_COMMON_CHAT:
        await handle_common_chat(message)
        return

    # поиск ЛС
    if state == STATE_DM_SEARCH:
        await handle_dm_search(message)
        return

    # чат ЛС
    if state == STATE_DM_CHAT:
        await handle_dm_chat(message)
        return

    # сделки
    if state == STATE_DEAL:
        await handle_deal(message)
        return

    # сообщение админу
    if state == STATE_ADMIN_MSG:
        await handle_admin_msg(message)
        return

    # поиск админ
    if state == STATE_ADMIN_SEARCH:
        await handle_admin_search(message)
        return


# ==============================
# ЗАПУСК БОТА
# ==============================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
