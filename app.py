import os
import time
import threading
import telebot
from flask import Flask
from dotenv import load_dotenv

from models import init_db
from admin_handlers import register_admin_handlers
from shop_handlers import register_shop_handlers

load_dotenv()

# ---------- FLASK (health check uchun) ----------
app_flask = Flask(__name__)

@app_flask.route('/')
@app_flask.route('/health')
def health():
    return "OK", 200

# ---------- TELEGRAM BOTNI ALOHIDA THREADDA ISHGA TUSHIRISH ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Database va handlerlarni registratsiya qilish
init_db()
register_admin_handlers(bot)
register_shop_handlers(bot)

def run_bot():
    print("[INFO] Bot polling started...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60, interval=1)
        except Exception as e:
            print(f"[ERROR] Polling crashed: {e}")
            print("[INFO] Restarting polling in 5 seconds...")
            time.sleep(5)

# Bot pollingni alohida threadda ishga tushirish
threading.Thread(target=run_bot, daemon=True).start()

# ---------- FLASK SERVERNI ISHGA TUSHIRISH ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app_flask.run(host="0.0.0.0", port=port)