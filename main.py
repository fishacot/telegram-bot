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

TOKEN = "YOUR_TOKEN"

ADMIN_ID = 554529638

CHANNEL_MARKET = -1003723369541
CHANNEL_CONFESSIONS = -1003759412953
CHANNEL_CHAT = -1003974878143


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
