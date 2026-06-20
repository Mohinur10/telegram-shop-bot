import telebot
from models import Session, Admin, Category, Product, DeliverySettings, PaymentMethod, Order, OrderItem, News, User
from fsm import States, get_state, set_state, clear_state, set_data, get_data, clear_data
from keyboards import admin_main_kb, admin_crud_kb, admin_orders_kb, order_status_kb, back_kb
from utils import upload_to_telegraph

def register_admin_handlers(bot: telebot.TeleBot):
    def is_admin(uid):
        state = get_state(uid)
        return state == States.ADMIN_PANEL or (state or "").startswith("admin_") or (state or "").startswith("news_")

    @bot.message_handler(func=lambda m: m.text in ["🔙 Orqaga", "🔙 Ortga"] and is_admin(m.from_user.id) and not (m.text or "").startswith("/"))
    def admin_global_back(msg):
        uid = msg.from_user.id
        clear_data(uid)
        set_state(uid, States.ADMIN_PANEL)
        bot.send_message(uid, "🔙 Bekor qilindi. Bosh menyuga qaytdingiz.", reply_markup=admin_main_kb())

    @bot.message_handler(commands=["admin"])
    def cmd_admin(msg):
        uid = msg.from_user.id
        if get_state(uid) == States.ADMIN_PANEL:
            bot.send_message(uid, "✅ Siz allaqachon admin paneldasiz.", reply_markup=admin_main_kb())
            return
        clear_state(uid)
        set_state(uid, States.ADMIN_WAIT_USERNAME)
        bot.send_message(uid, "👤 Admin username kiriting:")

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_WAIT_USERNAME)
    def admin_username(msg):
        uid = msg.from_user.id
        set_data(uid, "admin_username", msg.text.strip())
        set_state(uid, States.ADMIN_WAIT_PASSWORD)
        bot.send_message(uid, "🔑 Parolni kiriting:")

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_WAIT_PASSWORD)
    def admin_password(msg):
        uid = msg.from_user.id
        username = get_data(uid, "admin_username")
        password = msg.text.strip()
        session = Session()
        try:
            admin = session.query(Admin).filter_by(username=username).first()
            ok = admin and admin.check_password(password)
            admin_id = admin.id if ok else None
        finally:
            session.close()
        if ok:
            set_data(uid, "admin_id", admin_id)
            set_data(uid, "admin_username_confirmed", username)
            set_state(uid, States.ADMIN_PANEL)
            bot.send_message(uid, f"✅ Xush kelibsiz, {username}!", reply_markup=admin_main_kb())
        else:
            clear_state(uid)
            bot.send_message(uid, "❌ Noto'g'ri username yoki parol.")

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_PANEL and m.text == "🚪 Chiqish")
    def admin_logout(msg):
        uid = msg.from_user.id
        clear_state(uid)
        # Reset daily‑stats flag so future requests work again
        set_data(uid, "daily_stats_sent", False)
        bot.send_message(uid, "👋 Chiqdingiz.", reply_markup=telebot.types.ReplyKeyboardRemove())

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_PANEL and m.text == "📂 Kategoriyalar")
    def admin_categories(msg):
        uid = msg.from_user.id
        set_data(uid, "current_section", "category")
        set_state(uid, States.ADMIN_CRUD_MENU)
        session = Session()
        try:
            cats = session.query(Category).all()
            out = "📂 <b>Kategoriyalar</b>:\n\n"
            for i, c in enumerate(cats, 1):
                parent_info = f" (Ichida: {c.parent.name})" if c.parent else ""
                out += f"{i}. {c.name}{parent_info}\n"
            if not cats:
                out += "Bo'sh."
            bot.send_message(uid, out, parse_mode="HTML", reply_markup=admin_crud_kb())
        finally:
            session.close()

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_ADD_CAT_NAME)
    def admin_cat_add_save(msg):
        uid = msg.from_user.id
        name = msg.text.strip()
        set_data(uid, "new_cat_name", name)
        set_state(uid, States.ADMIN_ADD_CAT_PARENT)
        
        session = Session()
        try:
            cats = session.query(Category).all()
            cat_names = [c.name for c in cats]
        finally:
            session.close()
            
        kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row("Asosiy kategoriya")
        for cname in cat_names:
            kb.row(cname)
            
        bot.send_message(uid, "📂 Bu kategoriya qaysi kategoriyaga tegishli? (Asosiy kategoriya uchun 'Asosiy kategoriya' ni tanlang)", reply_markup=kb)

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_ADD_CAT_PARENT)
    def admin_cat_add_parent(msg):
        uid = msg.from_user.id
        parent_name = msg.text.strip()
        name = get_data(uid, "new_cat_name")

        if not name:
            bot.send_message(uid, "❌ Kategoriya nomi topilmadi. Qaytadan boshlang:", reply_markup=admin_main_kb())
            set_state(uid, States.ADMIN_PANEL)
            return

        # 1. Agar ota-kategoriya tanlangan bo'lsa, uni bazadan olamiz
        parent_id = None
        if parent_name != "Asosiy kategoriya":
            s1 = Session()
            try:
                parent_cat = s1.query(Category).filter_by(name=parent_name).first()
                if parent_cat:
                    parent_id = parent_cat.id
            finally:
                s1.close()

            if parent_id is None:
                # Topilmadi — keyboard bilan xato xabar qaytaramiz
                s2 = Session()
                try:
                    cats = s2.query(Category).all()
                    cat_names = [c.name for c in cats]
                finally:
                    s2.close()
                kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
                kb.row("Asosiy kategoriya")
                for cname in cat_names:
                    kb.row(cname)
                bot.send_message(uid, "❌ Kategoriya topilmadi. Qaytadan tanlang:", reply_markup=kb)
                return

        # 2. Yangi kategoriyani saqlaymiz
        added_name = None
        s3 = Session()
        try:
            cat = Category(name=name, parent_id=parent_id)
            s3.add(cat)
            s3.commit()
            added_name = cat.name
        except Exception as e:
            s3.rollback()
            bot.send_message(uid, f"❌ Kategoriya qo'shishda xatolik: {e}")
            return
        finally:
            s3.close()

        clear_data(uid)
        set_state(uid, States.ADMIN_CRUD_MENU)
        bot.send_message(uid, f"✅ Kategoriya qo'shildi: {added_name}")
        admin_categories(msg)

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_EDIT_CAT_NAME)
    def admin_cat_edit_save(msg):
        uid = msg.from_user.id
        item_id = get_data(uid, "edit_id")
        new_name = msg.text.strip()
        session = Session()
        try:
            cat = session.query(Category).filter_by(id=item_id).first()
            if cat:
                cat.name = new_name
                session.commit()
        finally:
            session.close()
        set_state(uid, States.ADMIN_PANEL)
        bot.send_message(uid, f"✅ Yangilandi: {new_name}", reply_markup=admin_main_kb())

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_PANEL and m.text == "📦 Mahsulotlar")
    def admin_products(msg):
        uid = msg.from_user.id
        set_data(uid, "current_section", "product")
        set_state(uid, States.ADMIN_CRUD_MENU)
        session = Session()
        try:
            prods = session.query(Product).all()
            out = "📦 <b>Mahsulotlar</b>:\n\n"
            for i, p in enumerate(prods, 1):
                out += f"{i}. {p.name} - {p.price:,.0f} so'm\n"
            if not prods:
                out += "Bo'sh."
            bot.send_message(uid, out, parse_mode="HTML", reply_markup=admin_crud_kb())
        finally:
            session.close()

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_ADD_PROD_NAME)
    def admin_prod_add_name(msg):
        uid = msg.from_user.id
        set_data(uid, "new_prod_name", msg.text.strip())
        set_state(uid, States.ADMIN_ADD_PROD_DESC)
        bot.send_message(uid, "📝 Tavsif kiriting (o'tkazib yuborish uchun: skip):")

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_ADD_PROD_DESC)
    def admin_prod_add_desc(msg):
        uid = msg.from_user.id
        desc = None if msg.text.strip().lower() == "skip" else msg.text.strip()
        set_data(uid, "new_prod_desc", desc)
        set_state(uid, States.ADMIN_ADD_PROD_PRICE)
        bot.send_message(uid, "💰 Narxni kiriting (so'mda):")

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_ADD_PROD_PRICE)
    def admin_prod_add_price(msg):
        uid = msg.from_user.id
        try:
            price = float(msg.text.strip().replace(",", "").replace(" ", ""))
        except ValueError:
            bot.send_message(uid, "❌ Noto'g'ri format. Raqam kiriting:")
            return
        set_data(uid, "new_prod_price", price)
        set_state(uid, States.ADMIN_ADD_PROD_IMAGE)
        bot.send_message(uid, "🖼 Endi mahsulot RASMINI yuboring (foto sifatida):")

    @bot.message_handler(content_types=['photo'], func=lambda m: get_state(m.from_user.id) == States.ADMIN_ADD_PROD_IMAGE)
    def admin_prod_add_image(msg):
        uid = msg.from_user.id
        file_id = msg.photo[-1].file_id
        bot.send_message(uid, "⏳ Rasm yuklanmoqda...")
        url = upload_to_telegraph(file_id, bot)
        if not url:
            bot.send_message(uid, "❌ Rasmni yuklashda xatolik yuz berdi. Iltimos qaytadan yuboring:")
            return
        set_data(uid, "new_prod_image", url)
        set_state(uid, States.ADMIN_ADD_PROD_CAT)
        session = Session()
        try:
            cats = session.query(Category).all()
            cat_names = [c.name for c in cats]
        finally:
            session.close()
        if not cat_names:
            bot.send_message(uid, "❌ Avval kategoriya yarating.", reply_markup=admin_main_kb())
            set_state(uid, States.ADMIN_PANEL)
            return
        kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        for name in cat_names:
            kb.row(name)
        bot.send_message(uid, "📂 Kategoriyani tanlang:", reply_markup=kb)

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_ADD_PROD_IMAGE and not m.photo)
    def admin_prod_image_invalid(msg):
        bot.send_message(msg.from_user.id, "❌ Iltimos, faqat rasm (foto) yuboring. Qaytadan urinib ko'ring:")

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_ADD_PROD_CAT)
    def admin_prod_add_cat(msg):
        uid = msg.from_user.id
        session = Session()
        try:
            cat = session.query(Category).filter_by(name=msg.text.strip()).first()
            if not cat:
                bot.send_message(uid, "❌ Kategoriya topilmadi. Qaytadan tanlang:")
                return
            prod = Product(
                name=get_data(uid, "new_prod_name"),
                description=get_data(uid, "new_prod_desc"),
                price=get_data(uid, "new_prod_price"),
                image=None,  # Preserve old column for backward compatibility
                image_file_id=get_data(uid, "new_prod_image"),
                category_id=cat.id,
            )
            session.add(prod)
            session.commit()
            prod_name = prod.name
        finally:
            session.close()
        clear_data(uid)
        set_data(uid, "current_section", "product")
        set_state(uid, States.ADMIN_CRUD_MENU)
        bot.send_message(uid, f"✅ Mahsulot qo'shildi: {prod_name} (rasm bilan)")
        admin_products(msg)

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_EDIT_PROD_NAME)
    def admin_prod_edit_name(msg):
        uid = msg.from_user.id
        item_id = get_data(uid, "edit_id")
        new_name = msg.text.strip()
        session = Session()
        try:
            p = session.query(Product).filter_by(id=item_id).first()
            if p:
                p.name = new_name
                session.commit()
        finally:
            session.close()
        set_state(uid, States.ADMIN_PANEL)
        bot.send_message(uid, f"✅ Yangilandi: {new_name}", reply_markup=admin_main_kb())

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_PANEL and m.text == "🚚 Yetkazib berish")
    def admin_delivery(msg):
        uid = msg.from_user.id
        set_data(uid, "current_section", "delivery")
        set_state(uid, States.ADMIN_CRUD_MENU)
        session = Session()
        try:
            dels = session.query(DeliverySettings).all()
            out = "🚚 <b>Yetkazib berish</b>:\n\n"
            for i, d in enumerate(dels, 1):
                st = "Faol" if d.is_active else "Nofaol"
                out += f"{i}. {d.name} ({d.price:,.0f} so'm) - {st}\n"
            if not dels:
                out += "Bo'sh."
            bot.send_message(uid, out, parse_mode="HTML", reply_markup=admin_crud_kb())
        finally:
            session.close()

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_ADD_DELIVERY_NAME)
    def admin_delivery_add_name(msg):
        uid = msg.from_user.id
        set_data(uid, "new_del_name", msg.text.strip())
        set_state(uid, States.ADMIN_ADD_DELIVERY_PRICE)
        bot.send_message(uid, "💰 Narxini kiriting (bepul uchun 0):")

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_ADD_DELIVERY_PRICE)
    def admin_delivery_add_price(msg):
        uid = msg.from_user.id
        try:
            price = float(msg.text.strip().replace(",", "").replace(" ", ""))
        except ValueError:
            bot.send_message(uid, "❌ Raqam kiriting:")
            return
        name = get_data(uid, "new_del_name")
        session = Session()
        try:
            d = DeliverySettings(name=name, price=price)
            session.add(d)
            session.commit()
        finally:
            session.close()
        clear_data(uid)
        set_data(uid, "current_section", "delivery")
        set_state(uid, States.ADMIN_CRUD_MENU)
        bot.send_message(uid, f"✅ Qo'shildi: {name}")
        admin_delivery(msg)

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_EDIT_DELIVERY_NAME)
    def admin_delivery_edit_name(msg):
        uid = msg.from_user.id
        item_id = get_data(uid, "edit_id")
        new_name = msg.text.strip()
        session = Session()
        try:
            d = session.query(DeliverySettings).filter_by(id=item_id).first()
            if d:
                d.name = new_name
                session.commit()
        finally:
            session.close()
        set_state(uid, States.ADMIN_PANEL)
        bot.send_message(uid, f"✅ Yangilandi: {new_name}", reply_markup=admin_main_kb())

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_PANEL and m.text == "💳 To'lov usullari")
    def admin_payments(msg):
        uid = msg.from_user.id
        set_data(uid, "current_section", "payment")
        session = Session()
        try:
            items = session.query(PaymentMethod).all()
            item_list = [{"id": p.id, "name": p.name, "details": p.details, "active": p.is_active} for p in items]
        finally:
            session.close()
        kb = telebot.types.InlineKeyboardMarkup()
        for p in item_list:
            state = "✅" if p["active"] else "❌"
            kb.add(
                telebot.types.InlineKeyboardButton(f"✏️ {state} {p['name']}", callback_data=f"edit_{p['id']}"),
                telebot.types.InlineKeyboardButton("🗑", callback_data=f"delete_{p['id']}"),
            )
        kb.add(telebot.types.InlineKeyboardButton("➕ Yangi qo'shish", callback_data="add_new"))
        bot.send_message(uid, "💳 <b>To'lov usullari</b>:", parse_mode="HTML", reply_markup=kb)

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_ADD_PAY_NAME)
    def admin_pay_add_name(msg):
        uid = msg.from_user.id
        set_data(uid, "new_pay_name", msg.text.strip())
        set_state(uid, States.ADMIN_ADD_PAY_DETAILS)
        bot.send_message(uid, "ℹ️ Tafsilotlar kiriting (o'tkazish uchun: skip):")

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_ADD_PAY_DETAILS)
    def admin_pay_add_details(msg):
        uid = msg.from_user.id
        details = None if msg.text.strip().lower() == "skip" else msg.text.strip()
        name = get_data(uid, "new_pay_name")
        session = Session()
        try:
            p = PaymentMethod(name=name, details=details)
            session.add(p)
            session.commit()
        finally:
            session.close()
        clear_data(uid)
        set_state(uid, States.ADMIN_PANEL)
        bot.send_message(uid, f"✅ Qo'shildi: {name}", reply_markup=admin_main_kb())

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_EDIT_PAY_NAME)
    def admin_pay_edit_name(msg):
        uid = msg.from_user.id
        item_id = get_data(uid, "edit_id")
        new_name = msg.text.strip()
        session = Session()
        try:
            p = session.query(PaymentMethod).filter_by(id=item_id).first()
            if p:
                p.name = new_name
                session.commit()
        finally:
            session.close()
        set_state(uid, States.ADMIN_PANEL)
        bot.send_message(uid, f"✅ Yangilandi: {new_name}", reply_markup=admin_main_kb())

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_PANEL and m.text == "📋 Buyurtmalar")
    def admin_orders(msg):
        uid = msg.from_user.id
        session = Session()
        try:
            orders = session.query(Order).order_by(Order.id.desc()).limit(20).all()
            order_list = [
                {"id": o.id, "status": o.status, "total": o.total,
                 "user_name": o.user_name or "—", "created_at": o.created_at}
                for o in orders
            ]
        finally:
            session.close()
        if not order_list:
            bot.send_message(uid, "📋 Buyurtmalar yo'q.", reply_markup=admin_main_kb())
            return
        kb = telebot.types.InlineKeyboardMarkup()
        for o in order_list:
            date_str = o["created_at"].strftime("%d.%m") if o["created_at"] else ""
            kb.add(telebot.types.InlineKeyboardButton(
                f"#{o['id']} {o['user_name']} — {o['total']:,.0f} so'm — {o['status']} {date_str}",
                callback_data=f"order_{o['id']}"
            ))
        bot.send_message(uid, "📋 <b>Buyurtmalar (oxirgi 20):</b>", parse_mode="HTML", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("order_"))
    def admin_order_detail(call):
        uid = call.from_user.id
        if not is_admin(uid):
            bot.answer_callback_query(call.id, "❌ Ruxsat yo'q.")
            return
        order_id = int(call.data.split("_")[1])
        bot.answer_callback_query(call.id)
        session = Session()
        try:
            order = session.query(Order).filter_by(id=order_id).first()
            if not order:
                bot.send_message(uid, "Topilmadi.")
                return
            items = session.query(OrderItem).filter_by(order_id=order_id).all()
            items_text = "\n".join(f"  • {i.product_name} x{i.quantity} = {i.price * i.quantity:,.0f} so'm" for i in items)
            delivery_name = "—"
            if order.delivery_id:
                d = session.query(DeliverySettings).filter_by(id=order.delivery_id).first()
                if d: delivery_name = d.name
            payment_name = "—"
            if order.payment_id:
                p = session.query(PaymentMethod).filter_by(id=order.payment_id).first()
                if p: payment_name = p.name
            text = (
                f"📦 <b>Buyurtma #{order.id}</b>\n"
                f"👤 {order.user_name or '—'}\n"
                f"📞 {order.phone or '—'}\n"
                f"📍 {order.address or '—'}\n"
                f"🚚 {delivery_name}\n"
                f"💳 {payment_name}\n\n"
                f"<b>Mahsulotlar:</b>\n{items_text}\n\n"
                f"💰 Jami: <b>{order.total:,.0f} so'm</b>\n"
                f"📌 Holat: <b>{order.status}</b>\n"
                f"🕐 {order.created_at.strftime('%d.%m.%Y %H:%M') if order.created_at else '—'}"
            )
        finally:
            session.close()
        kb = telebot.types.InlineKeyboardMarkup()
        for label, status in [("⏳ Kutilmoqda", "pending"), ("🔄 Jarayonda", "processing"),
                               ("✅ Bajarildi", "completed"), ("❌ Bekor", "cancelled")]:
            kb.add(telebot.types.InlineKeyboardButton(label, callback_data=f"setstatus_{order_id}_{status}"))
        bot.send_message(uid, text, parse_mode="HTML", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("setstatus_"))
    def admin_set_order_status(call):
        uid = call.from_user.id
        if not is_admin(uid):
            bot.answer_callback_query(call.id, "❌ Ruxsat yo'q.")
            return
        parts = call.data.split("_", 2)
        order_id = int(parts[1])
        status = parts[2]
        session = Session()
        try:
            order = session.query(Order).filter_by(id=order_id).first()
            if order:
                order.status = status
                session.commit()
        finally:
            session.close()
        bot.answer_callback_query(call.id, f"✅ Holat: {status}")
        bot.send_message(uid, f"✅ Buyurtma #{order_id} holati: <b>{status}</b>", parse_mode="HTML", reply_markup=admin_main_kb())

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_PANEL and m.text == "📊 Bir kunlik statistika")
    def admin_daily_stats(msg):
        uid = msg.from_user.id
        # Prevent sending duplicate stats in the same session
        if get_data(uid, "daily_stats_sent", False):
            bot.send_message(uid, "⚠️ Statistikani avval ham yuborilgan.", reply_markup=admin_main_kb())
            return

        from datetime import datetime
        from collections import Counter
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        session = Session()
        try:
            orders = session.query(Order).filter(Order.created_at >= today_start).all()
            total_orders = len(orders)
            total_amount = sum(o.total for o in orders if o.total)
            order_ids = [o.id for o in orders]
            items = session.query(OrderItem).filter(OrderItem.order_id.in_(order_ids)).all() if order_ids else []
            total_items_sold = sum(i.quantity for i in items)
            product_counter = Counter()
            for it in items:
                product_counter[it.product_name] += it.quantity
            top_products = product_counter.most_common(5)
            lines = [
                "📊 <b>Bugungi statistika (00:00 dan hozirgacha)</b>",
                f"📅 Sana: {datetime.now().strftime('%d.%m.%Y')}",
                f"📦 Jami buyurtmalar: <b>{total_orders}</b>",
                f"🛒 Sotilgan tovarlar soni: <b>{total_items_sold}</b>",
                f"💰 Umumiy tushum: <b>{total_amount:,.0f} so'm</b>",
                "",
                "🏆 <b>Eng ko'p sotilgan tovarlar:</b>"
            ]
            if top_products:
                for name, count in top_products:
                    lines.append(f"• {name} — {count} dona")
            else:
                lines.append("• Hech qanday tovar sotilmagan.")
            text = "\n".join(lines)
        finally:
            session.close()
        # Mark that stats have been sent for this admin session
        set_data(uid, "daily_stats_sent", True)
        bot.send_message(uid, text, parse_mode="HTML", reply_markup=admin_main_kb())

    @bot.callback_query_handler(func=lambda c: c.data == "add_new")
    def admin_add_new(call):
        uid = call.from_user.id
        if not is_admin(uid):
            bot.answer_callback_query(call.id, "❌ Ruxsat yo'q.")
            return
        bot.answer_callback_query(call.id)
        context = get_data(uid, "current_section", "category")
        if context not in ["category", "product", "delivery", "payment", "news"]:
            bot.send_message(uid, "⚠️ Iltimos, avval kerakli bo'limni tanlang (masalan, 📦 Mahsulotlar).", reply_markup=admin_main_kb())
            return
        dispatch = {
            "category": (States.ADMIN_ADD_CAT_NAME, "📂 Yangi kategoriya nomini kiriting:"),
            "product":  (States.ADMIN_ADD_PROD_NAME, "📦 Yangi mahsulot nomini kiriting:"),
            "delivery": (States.ADMIN_ADD_DELIVERY_NAME, "🚚 Yetkazib berish turi nomini kiriting:"),
            "payment":  (States.ADMIN_ADD_PAY_NAME, "💳 To'lov usuli nomini kiriting:"),
            "news":     (States.NEWS_ADD_TEXT, "📝 Yangilik matnini kiriting:"),
        }
        state, prompt = dispatch[context]
        set_state(uid, state)
        bot.send_message(uid, prompt, reply_markup=back_kb())

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_CRUD_MENU and not (m.text or "").startswith("/"))
    def admin_crud_actions(msg):
        uid = msg.from_user.id
        text = msg.text
        section = get_data(uid, "current_section")
        
        if text == "🔙 Ortga":
            clear_data(uid)
            set_state(uid, States.ADMIN_PANEL)
            bot.send_message(uid, "🔙 Bosh menyuga qaytdingiz.", reply_markup=admin_main_kb())
            return
            
        if text == "➕ Qo'shish":
            dispatch = {
                "category": (States.ADMIN_ADD_CAT_NAME, "📂 Yangi kategoriya nomini kiriting:"),
                "product":  (States.ADMIN_ADD_PROD_NAME, "📦 Yangi mahsulot nomini kiriting:"),
                "delivery": (States.ADMIN_ADD_DELIVERY_NAME, "🚚 Yetkazib berish turi nomini kiriting:"),
                "payment":  (States.ADMIN_ADD_PAY_NAME, "💳 To'lov usuli nomini kiriting:"),
                "news":     (States.NEWS_ADD_TEXT, "📝 Yangilik matnini kiriting:"),
            }
            if section in dispatch:
                state, prompt = dispatch[section]
                set_state(uid, state)
                bot.send_message(uid, prompt, reply_markup=back_kb())
            return
            
        if text == "📋 Ko'rish":
            if section == "category": admin_categories(msg)
            elif section == "product": admin_products(msg)
            elif section == "delivery": admin_delivery(msg)
            elif section == "payment": admin_payments(msg)
            elif section == "news": admin_news(msg)
            return
            
        if text in ["✏️ Tahrirlash", "🗑 O'chirish"]:
            action_prefix = "edit" if text == "✏️ Tahrirlash" else "delete"
            kb = telebot.types.InlineKeyboardMarkup()
            items = []
            session = Session()
            try:
                if section == "category":
                    items = session.query(Category).all()
                    for c in items:
                        kb.add(telebot.types.InlineKeyboardButton(c.name, callback_data=f"{action_prefix}_{c.id}"))
                elif section == "product":
                    items = session.query(Product).all()
                    for p in items:
                        kb.add(telebot.types.InlineKeyboardButton(p.name, callback_data=f"{action_prefix}_{p.id}"))
                elif section == "delivery":
                    items = session.query(DeliverySettings).all()
                    for d in items:
                        kb.add(telebot.types.InlineKeyboardButton(d.name, callback_data=f"{action_prefix}_{d.id}"))
                elif section == "payment":
                    items = session.query(PaymentMethod).all()
                    for p in items:
                        kb.add(telebot.types.InlineKeyboardButton(p.name, callback_data=f"{action_prefix}_{p.id}"))
                elif section == "news":
                    items = session.query(News).order_by(News.id.desc()).limit(10).all()
                    for n in items:
                        kb.add(telebot.types.InlineKeyboardButton(f"{n.text[:20]}...", callback_data=f"{action_prefix}_{n.id}"))
                items_count = len(items)
            finally:
                session.close()

            if items_count == 0:
                bot.send_message(uid, "Hech narsa yo'q.")
            else:
                action_word = "tahrirlash" if text == "✏️ Tahrirlash" else "o'chirish"
                bot.send_message(uid, f"Qaysi birini {action_word} xohlaysiz? Tanlang:", reply_markup=kb)
            return
            
        bot.send_message(uid, "Iltimos, pastdagi tugmalardan birini tanlang.")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("edit_"))
    def admin_edit_dispatch(call):
        uid = call.from_user.id
        if not is_admin(uid):
            bot.answer_callback_query(call.id, "❌ Ruxsat yo'q.")
            return
        bot.answer_callback_query(call.id)
        item_id = int(call.data.split("_")[1])
        set_data(uid, "edit_id", item_id)
        context = get_data(uid, "current_section", "category")
        dispatch = {
            "category": (States.ADMIN_EDIT_CAT_NAME, "✏️ Yangi kategoriya nomini kiriting:"),
            "product":  (States.ADMIN_EDIT_PROD_NAME, "✏️ Yangi mahsulot nomini kiriting:"),
            "delivery": (States.ADMIN_EDIT_DELIVERY_NAME, "✏️ Yangi nom kiriting:"),
            "payment":  (States.ADMIN_EDIT_PAY_NAME, "✏️ Yangi nom kiriting:"),
            "news":     (States.NEWS_EDIT_TEXT, "📝 Yangilikning yangi matnini kiriting:"),
        }
        state, prompt = dispatch.get(context, (States.ADMIN_EDIT_CAT_NAME, "Yangi nom:"))
        set_state(uid, state)
        bot.send_message(uid, prompt, reply_markup=back_kb())

    @bot.callback_query_handler(func=lambda c: c.data.startswith("delete_"))
    def admin_delete_dispatch(call):
        uid = call.from_user.id
        if not is_admin(uid):
            bot.answer_callback_query(call.id, "❌ Ruxsat yo'q.")
            return
        bot.answer_callback_query(call.id)
        item_id = int(call.data.split("_")[1])
        context = get_data(uid, "current_section", "category")
        model_map = {
            "category": Category,
            "product":  Product,
            "delivery": DeliverySettings,
            "payment":  PaymentMethod,
            "news":     News,
        }
        model = model_map.get(context)
        deleted_name = "?"
        session = Session()
        try:
            if model:
                obj = session.query(model).filter_by(id=item_id).first()
                if obj:
                    deleted_name = getattr(obj, "name", None) or (obj.text[:20] + "..." if hasattr(obj, "text") else "?")
                    session.delete(obj)
                    session.commit()
        except Exception as e:
            session.rollback()
            bot.send_message(uid, "❌ O'chirishda xatolik: Ushbu ma'lumot boshqa joyda (masalan, savatcha yoki buyurtmalarda) ishlatilayotgan bo'lishi mumkin.")
            return
        finally:
            session.close()
        set_state(uid, States.ADMIN_CRUD_MENU)
        bot.send_message(uid, f"🗑 O'chirildi: {deleted_name}", reply_markup=admin_crud_kb())
        # Call admin_crud_actions to re-render the list
        mock_msg = type('MockMsg', (object,), {'from_user': call.from_user, 'text': "📋 Ko'rish", 'message_id': call.message.message_id})
        admin_crud_actions(mock_msg)

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_PANEL and m.text == "🔑 Parolni o'zgartirish")
    def admin_change_pw_start(msg):
        uid = msg.from_user.id
        set_state(uid, States.ADMIN_CHANGE_PW_OLD)
        bot.send_message(uid, "🔑 Joriy parolni kiriting:")

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_CHANGE_PW_OLD)
    def admin_change_pw_old(msg):
        uid = msg.from_user.id
        admin_id = get_data(uid, "admin_id")
        session = Session()
        try:
            admin = session.query(Admin).filter_by(id=admin_id).first()
            ok = admin and admin.check_password(msg.text.strip())
        finally:
            session.close()
        if not ok:
            set_state(uid, States.ADMIN_PANEL)
            bot.send_message(uid, "❌ Noto'g'ri parol.", reply_markup=admin_main_kb())
            return
        set_state(uid, States.ADMIN_CHANGE_PW_NEW)
        bot.send_message(uid, "🔏 Yangi parolni kiriting (kamida 6 belgi):")

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_CHANGE_PW_NEW)
    def admin_change_pw_new(msg):
        uid = msg.from_user.id
        if len(msg.text.strip()) < 6:
            bot.send_message(uid, "❌ Kamida 6 ta belgi bo'lishi kerak:")
            return
        set_data(uid, "new_password", msg.text.strip())
        set_state(uid, States.ADMIN_CHANGE_PW_CONF)
        bot.send_message(uid, "🔏 Yangi parolni tasdiqlang:")

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_CHANGE_PW_CONF)
    def admin_change_pw_confirm(msg):
        uid = msg.from_user.id
        new_pw = get_data(uid, "new_password")
        if msg.text.strip() != new_pw:
            set_state(uid, States.ADMIN_CHANGE_PW_NEW)
            bot.send_message(uid, "❌ Parollar mos kelmadi. Qaytadan yangi parol kiriting:")
            return
        admin_id = get_data(uid, "admin_id")
        session = Session()
        try:
            admin = session.query(Admin).filter_by(id=admin_id).first()
            if admin:
                admin.set_password(new_pw)
                session.commit()
        finally:
            session.close()
        clear_data(uid)
        set_state(uid, States.ADMIN_PANEL)
        bot.send_message(uid, "✅ Parol muvaffaqiyatli o'zgartirildi.", reply_markup=admin_main_kb())

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.ADMIN_PANEL and m.text == "📢 Yangiliklar")
    def admin_news(msg):
        uid = msg.from_user.id
        set_data(uid, "current_section", "news")
        set_state(uid, States.ADMIN_CRUD_MENU)
        session = Session()
        try:
            news_items = session.query(News).order_by(News.id.desc()).limit(10).all()
            out = "📢 <b>Yangiliklar (oxirgi 10 ta)</b>:\n\n"
            for i, n in enumerate(news_items, 1):
                short = n.text[:30].replace('\n', ' ')
                out += f"{i}. {short}...\n"
            if not news_items:
                out += "Bo'sh."
            bot.send_message(uid, out, parse_mode="HTML", reply_markup=admin_crud_kb())
        finally:
            session.close()

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.NEWS_ADD_TEXT)
    def admin_news_add_text(msg):
        uid = msg.from_user.id
        set_data(uid, "new_news_text", msg.text.strip())
        set_state(uid, States.NEWS_ADD_PHOTO)
        bot.send_message(uid, "📷 Yangilik rasmini yuboring (yoki rasm kerak bo'lmasa 'skip' deb yozing):")

    @bot.message_handler(content_types=['photo', 'text'], func=lambda m: get_state(m.from_user.id) == States.NEWS_ADD_PHOTO)
    def admin_news_add_photo(msg):
        uid = msg.from_user.id
        file_id = None
        if msg.photo:
            raw_file_id = msg.photo[-1].file_id
            bot.send_message(uid, "⏳ Rasm yuklanmoqda...")
            file_id = upload_to_telegraph(raw_file_id, bot)
            if not file_id:
                bot.send_message(uid, "❌ Rasmni yuklashda xatolik yuz berdi. Iltimos qaytadan yuboring (yoki matn bo'lsa 'skip' yozing):")
                return

        text = get_data(uid, "new_news_text")
        session = Session()
        try:
            news = News(text=text, image_file_id=file_id)
            session.add(news)
            session.commit()
            
            # Broadcast to all users
            users = session.query(User).all()
            for u in users:
                try:
                    if file_id:
                        bot.send_photo(u.user_id, file_id, caption=text, parse_mode="HTML")
                    else:
                        bot.send_message(u.user_id, text, parse_mode="HTML")
                except Exception:
                    pass
        finally:
            session.close()
        clear_data(uid)
        set_state(uid, States.ADMIN_PANEL)
        bot.send_message(uid, "✅ Yangilik qo'shildi va hammaga yuborildi.", reply_markup=admin_main_kb())

    @bot.message_handler(func=lambda m: get_state(m.from_user.id) == States.NEWS_EDIT_TEXT)
    def admin_news_edit_save(msg):
        uid = msg.from_user.id
        item_id = get_data(uid, "edit_id")
        new_text = msg.text.strip()
        session = Session()
        try:
            n = session.query(News).filter_by(id=item_id).first()
            if n:
                n.text = new_text
                session.commit()
        finally:
            session.close()
        set_state(uid, States.ADMIN_PANEL)
        bot.send_message(uid, f"✅ Yangilik yangilandi", reply_markup=admin_main_kb())