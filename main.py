# ==============================
# IMPORTS
# ==============================

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

STATE_REGISTER = "register"
STATE_MARKET = "market"
STATE_CONF = "conf"
STATE_COMMON_CHAT = "common_chat"
STATE_DM_SEARCH = "dm_search"
STATE_DM_CHAT = "dm_chat"
STATE_DEAL = "deal"
STATE_ADMIN_MSG = "admin_msg"

STATE_ADMIN_SEARCH = "admin_search"
STATE_ADMIN_MUTE = "admin_mute"
STATE_ADMIN_BAN = "admin_ban"
STATE_ADMIN_UNMUTE = "admin_unmute"
STATE_ADMIN_UNBAN = "admin_unban"
STATE_ADMIN_MESSAGE = "admin_message"


# ==============================
# ХРАНИЛИЩА
# ==============================

users = {}
user_states = {}
user_messages = {}
start_messages = {}
active_chats = {}

muted_users = {}
banned_users = {}

market_timer = {}
conf_timer = {}


# ==============================
# ТАЙМЕРЫ
# ==============================

MARKET_TIMEOUT = 3600
CONF_TIMEOUT = 3600
CHAT_TIMEOUT = 0


# ==============================
# LOG SYSTEM
# ==============================

LOG_DIR = "logs"

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


def write_log(filename, text):
    with open(f"{LOG_DIR}/{filename}", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | {text}\n")


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


def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Количество пользователей")],
            [KeyboardButton(text="🔎 Поиск по ID")],
            [KeyboardButton(text="🔇 Мут по ID")],
            [KeyboardButton(text="🔊 Размут по ID")],
            [KeyboardButton(text="🚫 Бан по ID")],
            [KeyboardButton(text="✅ Разбан по ID")],
            [KeyboardButton(text="✉️ Написать пользователю")],
            [KeyboardButton(text="📁 Скачать CSV")],
            [KeyboardButton(text="Назад ⏪")]
        ],
        resize_keyboard=True
    )
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

    if uid in banned_users:
        return

    user_states[uid] = STATE_REGISTER

    await full_cleanup(message)

    msg = await message.answer("Введите анонимный ник:")
    await track_message(msg)


# ==============================
# РЕГИСТРАЦИЯ
# ==============================

async def handle_register(message: types.Message):

    uid = message.from_user.id

    if uid in banned_users:
        return

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
    write_log("registrations.log", f"{uid} | {nick}")

    user_states[uid] = None

    await full_cleanup(message)

    msg1 = await message.answer("Ник сохранён")
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
# ПРОВЕРКА МУТА
# ==============================

def is_muted(uid):
    if uid not in muted_users:
        return False

    if time.time() > muted_users[uid]:
        del muted_users[uid]
        return False

    return True


# ==============================
# ПРОВЕРКА БАНА
# ==============================

def is_banned(uid):
    return uid in banned_users
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

INFO_CHANNEL_LINK = "https://t.me/ВАШ_INFO_КАНАЛ"


@dp.message(F.text == "FAQ")
async def faq(message: types.Message):

    await full_cleanup(message)

    msg = await message.answer(
        f"📌 Вся информация здесь:\n{INFO_CHANNEL_LINK}",
        reply_markup=back_button()
    )

    await track_message(msg)


# ==============================
# СООБЩЕНИЕ АДМИНУ
# ==============================

@dp.message(F.text == "🚨 Сообщение админу")
async def admin_msg(message: types.Message):

    uid = message.from_user.id

    if is_banned(uid):
        return

    user_states[uid] = STATE_ADMIN_MSG

    await full_cleanup(message)

    msg = await message.answer(
        "Напишите сообщение админу",
        reply_markup=back_button()
    )

    await track_message(msg)


async def handle_admin_msg(message: types.Message):

    uid = message.from_user.id

    if is_muted(uid):
        return

    nick = users[uid]["nick"]

    await bot.send_message(
        ADMIN_ID,
        f"📩 Сообщение админу\n"
        f"{nick} ({uid})\n\n"
        f"{message.text}"
    )

    write_log("admin_messages.log", f"{uid} -> admin")

    user_states[uid] = None

    await full_cleanup(message)

    msg = await message.answer(
        "Сообщение отправлено",
        reply_markup=main_menu()
    )

    await track_message(msg)
    # ==============================
# МАРКЕТ
# ==============================

@dp.message(F.text == "🛒 Маркет")
async def market_menu_handler(message: types.Message):

    uid = message.from_user.id

    if is_banned(uid):
        return

    await full_cleanup(message)

    msg = await message.answer(
        "Анонимный маркетплейс",
        reply_markup=market_menu()
    )

    await track_message(msg)


@dp.message(F.text == "📝 Выставить объявление")
async def create_market(message: types.Message):

    uid = message.from_user.id

    if is_banned(uid):
        return

    user_states[uid] = STATE_MARKET

    await full_cleanup(message)

    msg = await message.answer(
        "Отправьте текст или фото объявления",
        reply_markup=back_button()
    )

    await track_message(msg)


async def handle_market(message: types.Message):

    uid = message.from_user.id

    if is_banned(uid):
        return

    if is_muted(uid):
        return

    if uid not in users:
        return

    # таймер 1 час
    if uid in market_timer:
        if time.time() - market_timer[uid] < MARKET_TIMEOUT:
            remaining = int(
                MARKET_TIMEOUT - (time.time() - market_timer[uid])
            )

            msg = await message.answer(
                f"Подождите {remaining // 60} мин."
            )
            await track_message(msg)
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

    write_log("market.log", f"{uid} | {nick}")

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

    uid = message.from_user.id

    if is_banned(uid):
        return

    await full_cleanup(message)

    msg = await message.answer(
        "Анонимные сообщения",
        reply_markup=conf_menu()
    )

    await track_message(msg)


@dp.message(F.text == "Отправить сообщение ✏️")
async def create_conf(message: types.Message):

    uid = message.from_user.id

    if is_banned(uid):
        return

    user_states[uid] = STATE_CONF

    await full_cleanup(message)

    msg = await message.answer(
        "Отправьте сообщение",
        reply_markup=back_button()
    )

    await track_message(msg)


async def handle_conf(message: types.Message):

    uid = message.from_user.id

    if is_banned(uid):
        return

    if is_muted(uid):
        return

    if uid not in users:
        return

    # таймер 1 час
    if uid in conf_timer:
        if time.time() - conf_timer[uid] < CONF_TIMEOUT:
            remaining = int(
                CONF_TIMEOUT - (time.time() - conf_timer[uid])
            )

            msg = await message.answer(
                f"Подождите {remaining // 60} мин."
            )
            await track_message(msg)
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

    write_log("confessions.log", f"{uid} | {nick}")

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

    if is_banned(uid):
        return

    user_states[uid] = STATE_COMMON_CHAT

    await full_cleanup(message)

    msg = await message.answer(
        "Вы вошли в анонимный общий чат",
        reply_markup=chat_exit()
    )

    await track_message(msg)


async def handle_common_chat(message: types.Message):

    uid = message.from_user.id

    if is_banned(uid):
        return

    if uid not in users:
        return

    nick = users[uid]["nick"]

    try:
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

        write_log("chat.log", f"{uid} | {nick}")

    except Exception as e:
        write_log("errors.log", f"chat error {e}")


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
# ОБЩИЙ АНОНИМНЫЙ ЧАТ
# ==============================

@dp.message(F.text == "🗣 Общий чат")
async def common_chat(message: types.Message):

    uid = message.from_user.id

    if is_banned(uid):
        return

    user_states[uid] = STATE_COMMON_CHAT

    await full_cleanup(message)

    msg = await message.answer(
        "Вы вошли в анонимный общий чат",
        reply_markup=chat_exit()
    )

    await track_message(msg)


async def handle_common_chat(message: types.Message):

    uid = message.from_user.id

    if is_banned(uid):
        return

    if uid not in users:
        return

    nick = users[uid]["nick"]

    try:
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

        write_log("chat.log", f"{uid} | {nick}")

    except Exception as e:
        write_log("errors.log", f"chat error {e}")


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

    uid = message.from_user.id

    if is_banned(uid):
        return

    await full_cleanup(message)

    msg = await message.answer(
        "Личные сообщения",
        reply_markup=dm_menu()
    )

    await track_message(msg)


@dp.message(F.text == "Найти пользователя 🔎")
async def dm_search(message: types.Message):

    uid = message.from_user.id

    if is_banned(uid):
        return

    user_states[uid] = STATE_DM_SEARCH

    await full_cleanup(message)

    msg = await message.answer(
        "Введите ник пользователя",
        reply_markup=back_button()
    )

    await track_message(msg)


async def handle_dm_search(message: types.Message):

    uid = message.from_user.id

    if is_banned(uid):
        return

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

    if is_banned(uid):
        return

    if uid not in active_chats:
        return

    target = active_chats[uid]

    try:
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

        write_log("dm.log", f"{uid} -> {target}")

    except Exception as e:
        write_log("errors.log", f"dm error {e}")
        # ==============================
# АДМИН ПАНЕЛЬ
# ==============================

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
async def admin_count(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    msg = await message.answer(
        f"Пользователей: {len(users)}"
    )

    await track_message(msg)


# ==============================
# ПОИСК ПО ID
# ==============================

@dp.message(F.text == "🔎 Поиск по ID")
async def admin_search(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    user_states[ADMIN_ID] = STATE_ADMIN_SEARCH

    msg = await message.answer("Введите ID")
    await track_message(msg)


async def handle_admin_search(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    try:
        uid = int(message.text)
    except:
        return

    if uid not in users:
        msg = await message.answer("Не найден")
        await track_message(msg)
        return

    user = users[uid]

    text = (
        f"Ник: {user['nick']}\n"
        f"ID: {uid}\n"
        f"Рейтинг: {user['rating']}\n"
        f"Сделки: {user['deals']}"
    )

    msg = await message.answer(text)
    await track_message(msg)

    write_log("admin.log", f"search {uid}")


# ==============================
# МУТ
# ==============================

@dp.message(F.text == "🔇 Мут по ID")
async def admin_mute(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    user_states[ADMIN_ID] = STATE_ADMIN_MUTE

    msg = await message.answer("Введите ID для мута")
    await track_message(msg)


async def handle_admin_mute(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    uid = int(message.text)

    muted_users[uid] = time.time() + 3600

    msg = await message.answer("Пользователь замучен на 1 час")
    await track_message(msg)

    write_log("admin.log", f"mute {uid}")


# ==============================
# РАЗМУТ
# ==============================

@dp.message(F.text == "🔊 Размут по ID")
async def admin_unmute(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    user_states[ADMIN_ID] = STATE_ADMIN_UNMUTE

    msg = await message.answer("Введите ID")
    await track_message(msg)


async def handle_admin_unmute(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    uid = int(message.text)

    if uid in muted_users:
        del muted_users[uid]

    msg = await message.answer("Размучен")
    await track_message(msg)

    write_log("admin.log", f"unmute {uid}")


# ==============================
# БАН
# ==============================

@dp.message(F.text == "🚫 Бан по ID")
async def admin_ban(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    user_states[ADMIN_ID] = STATE_ADMIN_BAN

    msg = await message.answer("Введите ID")
    await track_message(msg)


async def handle_admin_ban(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    uid = int(message.text)

    banned_users[uid] = True

    msg = await message.answer("Забанен")
    await track_message(msg)

    write_log("admin.log", f"ban {uid}")


# ==============================
# РАЗБАН
# ==============================

@dp.message(F.text == "✅ Разбан по ID")
async def admin_unban(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    user_states[ADMIN_ID] = STATE_ADMIN_UNBAN

    msg = await message.answer("Введите ID")
    await track_message(msg)


async def handle_admin_unban(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    uid = int(message.text)

    if uid in banned_users:
        del banned_users[uid]

    msg = await message.answer("Разбанен")
    await track_message(msg)

    write_log("admin.log", f"unban {uid}")


# ==============================
# НАПИСАТЬ ПОЛЬЗОВАТЕЛЮ
# ==============================

@dp.message(F.text == "✉️ Написать пользователю")
async def admin_message(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    user_states[ADMIN_ID] = STATE_ADMIN_MESSAGE

    msg = await message.answer("Введите ID и текст через |")
    await track_message(msg)


async def handle_admin_message(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    try:
        uid, text = message.text.split("|", 1)
        uid = int(uid.strip())
    except:
        return

    try:
        await bot.send_message(uid, f"Сообщение от администрации:\n{text}")
    except:
        pass

    msg = await message.answer("Отправлено")
    await track_message(msg)

    write_log("admin.log", f"msg {uid}")
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

    # регистрация
    if state == STATE_REGISTER:
        await handle_register(message)
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

    # админ поиск
    if state == STATE_ADMIN_SEARCH:
        await handle_admin_search(message)
        return

    # мут
    if state == STATE_ADMIN_MUTE:
        await handle_admin_mute(message)
        return

    # размут
    if state == STATE_ADMIN_UNMUTE:
        await handle_admin_unmute(message)
        return

    # бан
    if state == STATE_ADMIN_BAN:
        await handle_admin_ban(message)
        return

    # разбан
    if state == STATE_ADMIN_UNBAN:
        await handle_admin_unban(message)
        return

    # сообщение пользователю
    if state == STATE_ADMIN_MESSAGE:
        await handle_admin_message(message)
        return


# ==============================
# ЗАПУСК
# ==============================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
