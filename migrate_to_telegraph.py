import os
import time
import telebot
from dotenv import load_dotenv
from models import Session, Product, News
from utils import upload_to_telegraph

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env")

bot = telebot.TeleBot(BOT_TOKEN)

def migrate():
    session = Session()
    print("Starting migration to Telegra.ph...")
    
    # Migrate Products
    products = session.query(Product).all()
    for p in products:
        file_id = p.image_file_id
        if not file_id and p.image and not p.image.startswith("http"):
            # Fallback if image was stored as file_id in the old column
            file_id = p.image
            
        if file_id and not file_id.startswith("http"):
            print(f"[Product ID {p.id}] Uploading file_id: {file_id[:15]}...")
            url = upload_to_telegraph(file_id, bot)
            if url:
                p.image_file_id = url
                p.image = url  # Keep in sync
                print(f"[Product ID {p.id}] Success -> {url}")
            else:
                print(f"[Product ID {p.id}] Failed to upload.")
            time.sleep(1) # Prevent rate limiting

    # Migrate News
    news_items = session.query(News).all()
    for n in news_items:
        file_id = n.image_file_id
        if file_id and not file_id.startswith("http"):
            print(f"[News ID {n.id}] Uploading file_id: {file_id[:15]}...")
            url = upload_to_telegraph(file_id, bot)
            if url:
                n.image_file_id = url
                print(f"[News ID {n.id}] Success -> {url}")
            else:
                print(f"[News ID {n.id}] Failed to upload.")
            time.sleep(1)
            
    session.commit()
    session.close()
    print("Migration finished!")

if __name__ == "__main__":
    migrate()
