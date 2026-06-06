import os
import time
import telebot
from dotenv import load_dotenv
from models import init_db
from admin_handlers import register_admin_handlers
from shop_handlers import register_shop_handlers

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env")

# Botni sozlamalar bilan yaratish (faqat qo‘llab-quvvatlanadigan parametrlar)
bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)

# API helper sozlamalari (timeoutlarni oshirish)
from telebot import apihelper
apihelper.CONNECT_TIMEOUT = 30
apihelper.READ_TIMEOUT = 30

print("[INFO] Initializing database...")
init_db()
print("[INFO] Database ready.")

register_admin_handlers(bot)
register_shop_handlers(bot)

print("[INFO] Bot is running...")

# Cheksiz qayta ulanish bilan polling
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60, interval=1)
    except Exception as e:
        print(f"[ERROR] Polling crashed: {e}")
        print("[INFO] Restarting polling in 5 seconds...")
        time.sleep(5)