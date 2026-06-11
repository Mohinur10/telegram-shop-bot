import os
import telebot
from dotenv import load_dotenv
from models import init_db
from admin_handlers import register_admin_handlers
from shop_handlers import register_shop_handlers

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env")

# Bot instance – used by app.py which runs polling in a separate thread
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Initialize DB and register handlers (no polling here)
init_db()
register_admin_handlers(bot)
register_shop_handlers(bot)

# Note: This file is kept for compatibility; the bot is started via app.py's thread.