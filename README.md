# 🛒 Telegram Shop Bot

Uzbek-language Telegram shop bot with admin panel and customer shopping flow.

---

## 📁 Project Structure

```
shopbot/
├── bot.py              # Entry point
├── models.py           # SQLAlchemy models + DB init
├── fsm.py              # In-memory FSM state manager
├── keyboards.py        # All keyboard builders
├── admin_handlers.py   # Admin auth + CRUD handlers
├── shop_handlers.py    # Customer shopping flow
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create PostgreSQL database
```sql
CREATE DATABASE shopbot;
```

### 3. Configure environment
```bash
cp .env.example .env
```

Edit `.env`:
```
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://postgres:password@localhost:5432/shopbot
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
```

### 4. Run
```bash
python bot.py
```

On first run, the default admin is created automatically from `.env` values.

---

## 👤 Customer Flow

```
/start → Main Menu → 🛒 Xarid qilish → Categories → Products → Cart → Checkout → Order
```

- No login required for customers
- Cart is session-based (in memory)
- Checkout: phone → address → delivery → payment → confirm

---

## 🔐 Admin Flow

```
/admin → Enter Username → Enter Password → Admin Panel
```

### Admin Panel Features:
| Menu | Description |
|------|-------------|
| 📂 Kategoriyalar | Add / Edit / Delete categories |
| 📦 Mahsulotlar | Add / Edit / Delete products (with category, price, description) |
| 🚚 Yetkazib berish | Manage delivery options and prices |
| 💳 To'lov usullari | Manage payment methods |
| 📋 Buyurtmalar | View orders, update order status |
| 🔑 Parolni o'zgartirish | Change admin password (bcrypt hashed) |
| 🚪 Chiqish | Logout |

---

## 🔒 Security

- Passwords hashed with **bcrypt**
- Admin credentials stored in PostgreSQL
- FSM state required to access any admin operation
- Unauthorized users are silently blocked from admin callbacks

---

## 🗄️ Database Tables

- `admins` — admin credentials
- `categories` — product categories
- `products` — products with price, description, category
- `delivery_settings` — delivery options with price
- `payment_methods` — payment methods with details
- `orders` — customer orders
- `order_items` — line items for each order
