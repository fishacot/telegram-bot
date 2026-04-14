import asyncio
import sqlite3
import csv
import time
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)

from config import (
    TOKEN,
    ADMIN_ID,
    CHANNEL_MARKET,
    CHANNEL_CONFESSIONS,
    CHANNEL_CHAT,
    INFO_CHANNEL
)

MARKET_TIMEOUT = 300
CONF_TIMEOUT = 300
CHAT_TIMEOUT = 60

bot = Bot(token=TOKEN)
dp = Dispatcher()

conn = sqlite3.connect("bot.db")
cursor = conn.cursor()

user_states = {}
chat_targets = {}
user_messages = {}

market_cooldowns = {}
conf_cooldowns = {}
chat_cooldowns = {}
