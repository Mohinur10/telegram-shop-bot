import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from models import Session, Category, Product, DeliverySettings, PaymentMethod, Order, OrderItem, Cart, CartItem
from fsm import States, get_state, set_state, clear_state, set_data, get_data, clear_data
from keyboards import main_menu_kb, confirm_kb

def register_shop_handlers(bot: telebot.TeleBot):

    # ------------------------- START -------------------------
    @bot.message_handler(commands=["start"])
    def cmd_start(msg):
        uid = msg.from_user.id
        clear_state(uid)
        clear_data(uid)
        set_state(uid, States.MAIN_MENU)
        bot.send_message(uid, "🖐 Assalomu alaykum! Ishonch Market botiga xush kelibsiz.", reply_markup=main_menu_kb())

    # ----------------------- MAIN MENU -----------------------
    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.MAIN_MENU and m.text == "🛒 Xarid qilish")
    def shop_categories(msg):
        uid = msg.from_user.id
        session = Session()
        try:
            cats = session.query(Category).all()
            if not cats:
                bot.send_message(uid, "Hozircha hech qanday kategoriya mavjud emas.")
                return
            kb = InlineKeyboardMarkup()
            for cat in cats:
                kb.add(InlineKeyboardButton(cat.name, callback_data=f"cat_{cat.id}"))
            bot.send_message(uid, "Kategoriyani tanlang:", reply_markup=kb)
        finally:
            session.close()

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.MAIN_MENU and m.text == "🛍 Savatni ko'rish")
    def view_cart(msg):
        uid = msg.from_user.id
        session = Session()
        try:
            cart = session.query(Cart).filter_by(user_id=uid).first()
            if not cart or not cart.items:
                bot.send_message(uid, "🛒 Savatingiz bo'sh.", reply_markup=main_menu_kb())
                return
            items = []
            total = 0
            for ci in cart.items:
                prod = ci.product
                item_total = prod.price * ci.quantity
                total += item_total
                items.append(f"• {prod.name} x{ci.quantity} = {item_total:,.0f} so'm")
            text = "🛍 <b>Savat</b>\n" + "\n".join(items) + f"\n\n<b>Jami: {total:,.0f} so'm</b>"
            kb = InlineKeyboardMarkup()
            for ci in cart.items:
                kb.add(InlineKeyboardButton(f"❌ {ci.product.name}", callback_data=f"cart_remove_{ci.id}"),
                       InlineKeyboardButton("+", callback_data=f"cart_inc_{ci.id}"),
                       InlineKeyboardButton("-", callback_data=f"cart_dec_{ci.id}"))
            kb.add(InlineKeyboardButton("✅ Buyurtma berish", callback_data="cart_checkout"))
            kb.add(InlineKeyboardButton("🗑 Savatni tozalash", callback_data="cart_clear"))
            bot.send_message(uid, text, parse_mode="HTML", reply_markup=kb)
        finally:
            session.close()

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.MAIN_MENU and m.text == "📋 Buyurtmalarim")
    def my_orders(msg):
        uid = msg.from_user.id
        session = Session()
        try:
            orders = session.query(Order).filter_by(user_id=uid).order_by(Order.id.desc()).all()
            if not orders:
                bot.send_message(uid, "📭 Siz hali hech qanday buyurtma bermagansiz.")
                return
            text = "📋 <b>Sizning buyurtmalaringiz</b>\n\n"
            for o in orders:
                text += f"#{o.id} – {o.status} – {o.total:,.0f} so'm\n"
            bot.send_message(uid, text, parse_mode="HTML")
        finally:
            session.close()

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.MAIN_MENU and m.text == "📞 Bog'lanish")
    def contact_info(msg):
        uid = msg.from_user.id
        text = "📞 <b>Biz bilan bog'lanish:</b>\n\n📱 Telegram: @ishonch_support\n📞 Telefon: +998 90 123 45 67\n🌐 Website: ishonch.uz"
        bot.send_message(uid, text, parse_mode="HTML")

    # ------------------- CATEGORY & PRODUCT -------------------
    @bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
    def show_products(call):
        uid = call.from_user.id
        cat_id = int(call.data.split("_")[1])
        session = Session()
        try:
            products = session.query(Product).filter_by(category_id=cat_id).all()
            if not products:
                bot.answer_callback_query(call.id, "Bu kategoriyada mahsulot yo'q.")
                return
            kb = InlineKeyboardMarkup()
            for p in products:
                kb.add(InlineKeyboardButton(f"{p.name} — {p.price:,.0f} so'm", callback_data=f"prod_{p.id}"))
            kb.add(InlineKeyboardButton("🔙 Ortga", callback_data="back_to_categories"))
            bot.edit_message_text("Mahsulotni tanlang:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        finally:
            session.close()
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("prod_"))
    def product_detail(call):
        uid = call.from_user.id
        prod_id = int(call.data.split("_")[1])
        session = Session()
        try:
            prod = session.query(Product).filter_by(id=prod_id).first()
            if not prod:
                bot.answer_callback_query(call.id, "Mahsulot topilmadi.")
                return
            text = f"📦 <b>{prod.name}</b>\n💰 Narxi: {prod.price:,.0f} so'm\n📝 {prod.description or 'Tavsif mavjud emas'}"
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🛒 Savatga qo'shish", callback_data=f"add_to_cart_{prod.id}"))
            kb.add(InlineKeyboardButton("🔙 Ortga", callback_data="back_to_products"))
            if prod.image:
                bot.send_photo(uid, prod.image, caption=text, parse_mode="HTML", reply_markup=kb)
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            else:
                bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)
        finally:
            session.close()
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("add_to_cart_"))
    def add_to_cart(call):
        uid = call.from_user.id
        prod_id = int(call.data.split("_")[-1])
        session = Session()
        try:
            cart = session.query(Cart).filter_by(user_id=uid).first()
            if not cart:
                cart = Cart(user_id=uid)
                session.add(cart)
                session.commit()
                session.refresh(cart)
            item = session.query(CartItem).filter_by(cart_id=cart.id, product_id=prod_id).first()
            if item:
                item.quantity += 1
            else:
                item = CartItem(cart_id=cart.id, product_id=prod_id, quantity=1)
                session.add(item)
            session.commit()
            bot.answer_callback_query(call.id, "✅ Savatga qo'shildi!", show_alert=False)
        finally:
            session.close()

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_categories")
    def back_to_categories(call):
        uid = call.from_user.id
        session = Session()
        try:
            cats = session.query(Category).all()
            if not cats:
                bot.edit_message_text("Kategoriya mavjud emas.", chat_id=call.message.chat.id, message_id=call.message.message_id)
                return
            kb = InlineKeyboardMarkup()
            for cat in cats:
                kb.add(InlineKeyboardButton(cat.name, callback_data=f"cat_{cat.id}"))
            bot.edit_message_text("Kategoriyani tanlang:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        finally:
            session.close()
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_products")
    def back_to_products(call):
        back_to_categories(call)

    # ----------------------- CART (inline) -----------------------
    @bot.callback_query_handler(func=lambda call: call.data.startswith("cart_remove_"))
    def cart_remove_item(call):
        uid = call.from_user.id
        item_id = int(call.data.split("_")[-1])
        session = Session()
        try:
            item = session.query(CartItem).filter_by(id=item_id).first()
            if item and item.cart.user_id == uid:
                session.delete(item)
                session.commit()
            bot.answer_callback_query(call.id, "🗑 Mahsulot savatdan o'chirildi.")
            view_cart_from_callback(call, bot)
        finally:
            session.close()

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cart_inc_"))
    def cart_increment(call):
        uid = call.from_user.id
        item_id = int(call.data.split("_")[-1])
        session = Session()
        try:
            item = session.query(CartItem).filter_by(id=item_id).first()
            if item and item.cart.user_id == uid:
                item.quantity += 1
                session.commit()
            bot.answer_callback_query(call.id, "✅ Miqdor oshirildi.")
            view_cart_from_callback(call, bot)
        finally:
            session.close()

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cart_dec_"))
    def cart_decrement(call):
        uid = call.from_user.id
        item_id = int(call.data.split("_")[-1])
        session = Session()
        try:
            item = session.query(CartItem).filter_by(id=item_id).first()
            if item and item.cart.user_id == uid:
                if item.quantity > 1:
                    item.quantity -= 1
                    session.commit()
                else:
                    session.delete(item)
                    session.commit()
            bot.answer_callback_query(call.id, "✅ Miqdor kamaytirildi.")
            view_cart_from_callback(call, bot)
        finally:
            session.close()

    @bot.callback_query_handler(func=lambda call: call.data == "cart_clear")
    def cart_clear(call):
        uid = call.from_user.id
        session = Session()
        try:
            cart = session.query(Cart).filter_by(user_id=uid).first()
            if cart:
                session.query(CartItem).filter_by(cart_id=cart.id).delete()
                session.commit()
            bot.answer_callback_query(call.id, "🗑 Savat tozalandi.")
            bot.edit_message_text("🛒 Savatingiz bo'sh.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        finally:
            session.close()

    def view_cart_from_callback(call, bot):
        uid = call.from_user.id
        session = Session()
        try:
            cart = session.query(Cart).filter_by(user_id=uid).first()
            if not cart or not cart.items:
                bot.edit_message_text("🛒 Savatingiz bo'sh.", chat_id=call.message.chat.id, message_id=call.message.message_id)
                return
            items = []
            total = 0
            for ci in cart.items:
                prod = ci.product
                item_total = prod.price * ci.quantity
                total += item_total
                items.append(f"• {prod.name} x{ci.quantity} = {item_total:,.0f} so'm")
            text = "🛍 <b>Savat</b>\n" + "\n".join(items) + f"\n\n<b>Jami: {total:,.0f} so'm</b>"
            kb = InlineKeyboardMarkup()
            for ci in cart.items:
                kb.add(InlineKeyboardButton(f"❌ {ci.product.name}", callback_data=f"cart_remove_{ci.id}"),
                       InlineKeyboardButton("+", callback_data=f"cart_inc_{ci.id}"),
                       InlineKeyboardButton("-", callback_data=f"cart_dec_{ci.id}"))
            kb.add(InlineKeyboardButton("✅ Buyurtma berish", callback_data="cart_checkout"))
            kb.add(InlineKeyboardButton("🗑 Savatni tozalash", callback_data="cart_clear"))
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)
        finally:
            session.close()

    # ------------------------ CHECKOUT (ORDER) ------------------------
    @bot.callback_query_handler(func=lambda call: call.data == "cart_checkout")
    def checkout_start(call):
        uid = call.from_user.id
        session = Session()
        try:
            cart = session.query(Cart).filter_by(user_id=uid).first()
            if not cart or not cart.items:
                bot.answer_callback_query(call.id, "Savatingiz bo'sh.", show_alert=True)
                return
            deliveries = session.query(DeliverySettings).filter_by(is_active=True).all()
            if not deliveries:
                bot.send_message(uid, "⚠️ Hozircha yetkazib berish xizmati mavjud emas.")
                return
            set_state(uid, States.ORDER_DELIVERY)
            set_data(uid, "order_cart_id", cart.id)
            # Inline tugmalar bilan delivery
            kb = InlineKeyboardMarkup()
            for d in deliveries:
                label = f"{d.name} — {d.price:,.0f} so'm" if d.price > 0 else f"{d.name} — Bepul"
                kb.add(InlineKeyboardButton(label, callback_data=f"delivery_{d.id}"))
            kb.add(InlineKeyboardButton("🔙 Bosh menyu", callback_data="main_menu"))
            bot.send_message(uid, "🚚 Yetkazib berish turini tanlang:", reply_markup=kb)
        finally:
            session.close()
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delivery_"))
    def order_delivery(call):
        uid = call.from_user.id
        delivery_id = int(call.data.split("_")[1])
        session = Session()
        try:
            delivery = session.query(DeliverySettings).filter_by(id=delivery_id, is_active=True).first()
            if not delivery:
                bot.answer_callback_query(call.id, "Yetkazib berish topilmadi.", show_alert=True)
                return
            set_data(uid, "order_delivery_id", delivery.id)
            set_state(uid, States.ORDER_PHONE)

            # Telefon raqamini so'rash
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("📞 Telefon raqamini yuborish", request_contact=True))
            kb.add(KeyboardButton("🔙 Orqaga"))
            bot.send_message(uid, "📞 Telefon raqamingizni yuboring (yoki matn kiriting):", reply_markup=kb)
        finally:
            session.close()
        bot.answer_callback_query(call.id)

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ORDER_PHONE, content_types=['text', 'contact'])
    def order_phone(msg):
        uid = msg.from_user.id
        if msg.text == "🔙 Orqaga":
            # delivery tanlashga qaytish
            session = Session()
            try:
                deliveries = session.query(DeliverySettings).filter_by(is_active=True).all()
                kb = InlineKeyboardMarkup()
                for d in deliveries:
                    label = f"{d.name} — {d.price:,.0f} so'm" if d.price > 0 else f"{d.name} — Bepul"
                    kb.add(InlineKeyboardButton(label, callback_data=f"delivery_{d.id}"))
                kb.add(InlineKeyboardButton("🔙 Bosh menyu", callback_data="main_menu"))
                bot.send_message(uid, "🚚 Yetkazib berish turini qaytadan tanlang:", reply_markup=kb)
                set_state(uid, States.ORDER_DELIVERY)
            finally:
                session.close()
            return

        if msg.contact:
            phone = msg.contact.phone_number
        else:
            phone = msg.text.strip()

        set_data(uid, "order_phone", phone)
        set_state(uid, States.ORDER_ADDRESS)

        # Manzil so'rash (geolokatsiya yoki matn)
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("📍 Geolokatsiya yuborish", request_location=True))
        kb.add(KeyboardButton("🔙 Orqaga"))
        bot.send_message(uid, "📍 Manzilingizni matn shaklida kiriting yoki lokatsiya yuboring:", reply_markup=kb)

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ORDER_ADDRESS, content_types=['text', 'location'])
    def order_address(msg):
        uid = msg.from_user.id
        if msg.text == "🔙 Orqaga":
            set_state(uid, States.ORDER_PHONE)
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("📞 Telefon raqamini yuborish", request_contact=True))
            kb.add(KeyboardButton("🔙 Orqaga"))
            bot.send_message(uid, "📞 Telefon raqamingizni qayta kiriting:", reply_markup=kb)
            return

        if msg.location:
            address = f"Lat: {msg.location.latitude}, Lon: {msg.location.longitude}"
        else:
            address = msg.text.strip()

        set_data(uid, "order_address", address)
        set_state(uid, States.ORDER_PAYMENT)

        # To'lov usullarini ko'rsatish (inline)
        session = Session()
        try:
            payments = session.query(PaymentMethod).filter_by(is_active=True).all()
            if not payments:
                bot.send_message(uid, "⚠️ Hozircha to'lov usuli mavjud emas. Iltimos, admin bilan bog'laning.")
                return
            kb = InlineKeyboardMarkup()
            for p in payments:
                kb.add(InlineKeyboardButton(p.name, callback_data=f"payment_{p.id}"))
            kb.add(InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_address"))
            bot.send_message(uid, "💳 To'lov usulini tanlang:", reply_markup=kb)
        finally:
            session.close()

    @bot.callback_query_handler(func=lambda call: call.data.startswith("payment_"))
    def order_payment(call):
        uid = call.from_user.id
        payment_id = int(call.data.split("_")[1])
        session = Session()
        try:
            payment = session.query(PaymentMethod).filter_by(id=payment_id, is_active=True).first()
            if not payment:
                bot.answer_callback_query(call.id, "To'lov usuli topilmadi.")
                return
            set_data(uid, "order_payment_id", payment.id)

            # buyurtma ma'lumotlarini yig'ish va tasdiqlash
            cart_id = get_data(uid, "order_cart_id")
            delivery_id = get_data(uid, "order_delivery_id")
            phone = get_data(uid, "order_phone")
            address = get_data(uid, "order_address")

            cart = session.query(Cart).filter_by(id=cart_id).first()
            if not cart or not cart.items:
                bot.send_message(uid, "❌ Savat topilmadi yoki bo'sh.")
                clear_state(uid); clear_data(uid)
                return

            total = sum(ci.product.price * ci.quantity for ci in cart.items)
            delivery = session.query(DeliverySettings).filter_by(id=delivery_id).first()
            delivery_price = delivery.price if delivery else 0
            total += delivery_price

            items_text = "\n".join(f"• {ci.product.name} x{ci.quantity} = {ci.product.price * ci.quantity:,.0f} so'm" for ci in cart.items)
            confirm_text = (
                f"📝 <b>Buyurtma ma'lumotlari</b>\n\n"
                f"<b>Mahsulotlar:</b>\n{items_text}\n"
                f"🚚 Yetkazib berish: {delivery.name} + {delivery_price:,.0f} so'm\n"
                f"📞 Telefon: {phone}\n"
                f"📍 Manzil: {address}\n"
                f"💳 To'lov: {payment.name}\n\n"
                f"💰 <b>Jami: {total:,.0f} so'm</b>\n\n"
                f"Buyurtmani tasdiqlaysizmi?"
            )
            set_data(uid, "order_total", total)
            set_state(uid, States.ORDER_CONFIRM)
            bot.send_message(uid, confirm_text, parse_mode="HTML", reply_markup=confirm_kb())
        finally:
            session.close()
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_address")
    def back_to_address(call):
        uid = call.from_user.id
        set_state(uid, States.ORDER_ADDRESS)
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("📍 Geolokatsiya yuborish", request_location=True))
        kb.add(KeyboardButton("🔙 Orqaga"))
        bot.send_message(uid, "📍 Manzilingizni qayta kiriting:", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ORDER_CONFIRM)
    def order_confirm(msg):
        uid = msg.from_user.id
        if msg.text == "✅ Tasdiqlash":
            cart_id = get_data(uid, "order_cart_id")
            delivery_id = get_data(uid, "order_delivery_id")
            payment_id = get_data(uid, "order_payment_id")
            phone = get_data(uid, "order_phone")
            address = get_data(uid, "order_address")
            total = get_data(uid, "order_total")
            session = Session()
            try:
                cart = session.query(Cart).filter_by(id=cart_id).first()
                if not cart:
                    bot.send_message(uid, "❌ Xatolik yuz berdi.")
                    clear_state(uid); clear_data(uid)
                    return
                order = Order(
                    user_id=uid,
                    user_name=msg.from_user.first_name,
                    phone=phone,
                    address=address,
                    delivery_id=delivery_id,
                    payment_id=payment_id,
                    total=total,
                    status="pending"
                )
                session.add(order)
                session.flush()
                for ci in cart.items:
                    oi = OrderItem(
                        order_id=order.id,
                        product_id=ci.product_id,
                        product_name=ci.product.name,
                        quantity=ci.quantity,
                        price=ci.product.price
                    )
                    session.add(oi)
                session.query(CartItem).filter_by(cart_id=cart.id).delete()
                session.commit()
                # Foydalanuvchiga xabar
                bot.send_message(uid, f"✅ Buyurtmangiz #{order.id} qabul qilindi! Tez orada operator siz bilan bog'lanadi.\nRahmat tanlaganingiz uchun!", reply_markup=main_menu_kb())
            except Exception as e:
                session.rollback()
                bot.send_message(uid, f"❌ Xatolik: {str(e)}")
            finally:
                session.close()
                clear_state(uid)
                clear_data(uid)
        elif msg.text == "❌ Bekor qilish":
            clear_state(uid)
            clear_data(uid)
            bot.send_message(uid, "❌ Buyurtma bekor qilindi.", reply_markup=main_menu_kb())
        else:
            bot.send_message(uid, "Iltimos, tasdiqlash yoki bekor qilish tugmasini bosing.", reply_markup=confirm_kb())

    @bot.callback_query_handler(func=lambda call: call.data == "main_menu")
    def main_menu_callback(call):
        uid = call.from_user.id
        clear_state(uid)
        clear_data(uid)
        set_state(uid, States.MAIN_MENU)
        bot.send_message(uid, "Asosiy menyu:", reply_markup=main_menu_kb())
        bot.answer_callback_query(call.id)