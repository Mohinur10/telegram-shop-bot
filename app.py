import os
import time
import logging
import threading
import telebot
from flask import Flask, jsonify
from dotenv import load_dotenv

from models import init_db
from admin_handlers import register_admin_handlers
from shop_handlers import register_shop_handlers

load_dotenv()

# ---------- LOGGING ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ---------- FLASK (health-check + UptimeRobot ping uchun) ----------
app = Flask(__name__)

@app.route("/")
@app.route("/health")
def health():
    return jsonify({"status": "ok", "bot": "running"}), 200

# ---------- TELEGRAM BOT ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set — add it in Render Environment Variables!")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

from telebot import apihelper
apihelper.CONNECT_TIMEOUT = 30
apihelper.READ_TIMEOUT = 30

# Database va handlerlarni registratsiya qilish
logger.info("Initializing database...")
init_db()
logger.info("Database ready.")

register_admin_handlers(bot)
register_shop_handlers(bot)

# ---------- BOT POLLING ALOHIDA THREADDA ----------
bot_thread_started = False

def run_bot():
    logger.info("Bot polling started...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60, interval=1)
        except Exception as e:
            logger.error(f"Polling crashed: {e}")
            logger.info("Restarting polling in 5 seconds...")
            time.sleep(5)

def start_bot_thread():
    global bot_thread_started
    if not bot_thread_started:
        bot_thread_started = True
        t = threading.Thread(target=run_bot, daemon=True)
        t.start()
        logger.info("Bot thread launched.")

# Bot threadini ishga tushirish (gunicorn yoki to'g'ridan-to'g'ri run uchun)
start_bot_thread()

# ---------- LOCAL ISHGA TUSHIRISH ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)