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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/")
@app.route("/health")
def health():
    return jsonify({"status": "ok", "bot": "running"}), 200

@app.route('/ping')
def ping():
    return 'pong', 200

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

from telebot import apihelper
apihelper.CONNECT_TIMEOUT = 30
apihelper.READ_TIMEOUT = 30

init_db()
register_admin_handlers(bot)
register_shop_handlers(bot)

bot_thread_started = False

def run_bot():
    logger.info("Bot polling started...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60, interval=0.3)
        except Exception as e:
            logger.error(f"Polling crashed: {e}")
            time.sleep(5)

def start_bot_thread():
    global bot_thread_started
    if not bot_thread_started:
        bot_thread_started = True
        t = threading.Thread(target=run_bot, daemon=True)
        t.start()
        logger.info("Bot thread launched.")

lock_file = os.path.join(os.path.dirname(__file__), 'bot.lock')
if os.path.exists(lock_file):
    os.remove(lock_file)
open(lock_file, 'w').close()
start_bot_thread()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

import atexit
atexit.register(lambda: os.path.exists(lock_file) and os.remove(lock_file))