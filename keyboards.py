import telebot.types as types

def admin_main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton(text="📂 Kategoriyalar"),
        types.KeyboardButton(text="📦 Mahsulotlar"),
        types.KeyboardButton(text="🚚 Yetkazib berish"),
        types.KeyboardButton(text="💳 To'lov usullari"),
        types.KeyboardButton(text="📋 Buyurtmalar"),
        types.KeyboardButton(text="📊 Bir kunlik statistika"),
        types.KeyboardButton(text="🔑 Parolni o'zgartirish"),
        types.KeyboardButton(text="🚪 Chiqish")
    )
    return kb

def admin_crud_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton(text="➕ Qo'shish"),
        types.KeyboardButton(text="✏️ Tahrirlash"),
        types.KeyboardButton(text="🗑 O'chirish"),
        types.KeyboardButton(text="📋 Ko'rish"),
        types.KeyboardButton(text="🔙 Ortga")
    )
    return kb

def admin_orders_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton(text="✅ Qabul qilingan"),
        types.KeyboardButton(text="⏳ Tayyorlanmoqda"),
        types.KeyboardButton(text="🚚 Yetkazilmoqda"),
        types.KeyboardButton(text="📦 Yetkazildi"),
        types.KeyboardButton(text="🔙 Ortga")
    )
    return kb

def order_status_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    kb.add(
        types.KeyboardButton(text="✅ Qabul qilingan"),
        types.KeyboardButton(text="⏳ Tayyorlanmoqda"),
        types.KeyboardButton(text="🚚 Yetkazilmoqda"),
        types.KeyboardButton(text="📦 Yetkazildi"),
        types.KeyboardButton(text="🔙 Ortga")
    )
    return kb

def main_menu_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton(text="🛒 Xarid qilish"),
        types.KeyboardButton(text="🛍 Savatni ko'rish"),
        types.KeyboardButton(text="📋 Buyurtmalarim"),
        types.KeyboardButton(text="📞 Bog'lanish")
    )
    return kb

def back_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton(text="🔙 Orqaga"))
    return kb

def cart_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton(text="✅ Buyurtma berish"),
        types.KeyboardButton(text="🗑 Savatni tozalash"),
        types.KeyboardButton(text="🔙 Orqaga")
    )
    return kb

def delivery_kb(deliveries):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    for d in deliveries:
        label = f"{d.name} — {d.price:,.0f} so'm" if d.price > 0 else f"{d.name} — Bepul"
        kb.add(types.KeyboardButton(text=label))
    kb.add(types.KeyboardButton(text="🔙 Orqaga"))
    return kb

def payment_kb(methods):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    for m in methods:
        kb.add(types.KeyboardButton(text=m.name))
    kb.add(types.KeyboardButton(text="🔙 Orqaga"))
    return kb

def confirm_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton(text="✅ Tasdiqlash"),
        types.KeyboardButton(text="❌ Bekor qilish")
    )
    return kb