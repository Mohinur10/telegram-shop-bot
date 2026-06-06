import telebot.types as types

def admin_main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📂 Kategoriyalar", "📦 Mahsulotlar")
    kb.row("🚚 Yetkazib berish", "💳 To'lov usullari")
    kb.row("📋 Buyurtmalar", "📊 Bir kunlik statistika")
    kb.row("🔑 Parolni o'zgartirish", "🚪 Chiqish")
    return kb

def admin_crud_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Qo'shish", "✏️ Tahrirlash")
    kb.row("🗑 O'chirish", "📋 Ko'rish")
    kb.row("🔙 Ortga")
    return kb

def admin_orders_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("✅ Qabul qilingan", "⏳ Tayyorlanmoqda")
    kb.row("🚚 Yetkazilmoqda", "📦 Yetkazildi")
    kb.row("🔙 Ortga")
    return kb

def order_status_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("✅ Qabul qilingan")
    kb.row("⏳ Tayyorlanmoqda")
    kb.row("🚚 Yetkazilmoqda")
    kb.row("📦 Yetkazildi")
    kb.row("🔙 Ortga")
    return kb

def main_menu_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🛒 Xarid qilish")
    kb.row("🛍 Savatni ko'rish", "📋 Buyurtmalarim")
    kb.row("📞 Bog'lanish")
    return kb

def back_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🔙 Orqaga")
    return kb

def cart_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("✅ Buyurtma berish")
    kb.row("🗑 Savatni tozalash", "🔙 Orqaga")
    return kb

def delivery_kb(deliveries):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for d in deliveries:
        label = f"{d.name} — {d.price:,.0f} so'm" if d.price > 0 else f"{d.name} — Bepul"
        kb.row(label)
    kb.row("🔙 Orqaga")
    return kb

def payment_kb(methods):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for m in methods:
        kb.row(m.name)
    kb.row("🔙 Orqaga")
    return kb

def confirm_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("✅ Tasdiqlash", "❌ Bekor qilish")
    return kb