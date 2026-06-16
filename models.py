import os
import bcrypt
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()
engine = create_engine(
    os.getenv("DATABASE_URL"),
    echo=False,
    implicit_returning=False,
    pool_pre_ping=True,
    pool_recycle=300
)
Session = sessionmaker(bind=engine)


class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    def set_password(self, password: str):
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, password: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode(), self.password_hash.encode())
        except ValueError:
            return False


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    first_name = Column(String(200), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    image_file_id = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=True)

    parent = relationship("Category", remote_side=[id], back_populates="subcategories")
    subcategories = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = {'implicit_returning': False}
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    image = Column(String, nullable=True)
    image_file_id = Column(String, nullable=True)  # New column for Telegram file_id
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    category = relationship("Category", back_populates="products")


class Cart(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=1)
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")


class DeliverySettings(Base):
    __tablename__ = "delivery_settings"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    price = Column(Float, nullable=False, default=0.0)
    delivery_time = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)


class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    details = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    user_name = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    delivery_id = Column(Integer, ForeignKey("delivery_settings.id", ondelete="SET NULL"), nullable=True)
    payment_id = Column(Integer, ForeignKey("payment_methods.id", ondelete="SET NULL"), nullable=True)
    total = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, server_default=func.now())
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    delivery = relationship("DeliverySettings")
    payment = relationship("PaymentMethod")


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    product_name = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price = Column(Float, nullable=False)
    order = relationship("Order", back_populates="items")
    product = relationship("Product")


def init_db():
    # Recreate tables according to current models

    # Recreate tables according to current models
    Base.metadata.create_all(engine)
    session = Session()
    try:
        # Ensure at least one delivery option exists
        delivery = session.query(DeliverySettings).first()
        if delivery is None:
            default_delivery = DeliverySettings(name='Standard', price=0.0, is_active=True)
            session.add(default_delivery)
            session.commit()
            print(f"[DB] Default delivery created: {default_delivery.name}")

        # Ensure at least one payment method exists
        payment = session.query(PaymentMethod).first()
        if payment is None:
            default_payment = PaymentMethod(name='Cash', details='Pay on delivery', is_active=True)
            session.add(default_payment)
            session.commit()
            print(f"[DB] Default payment method created: {default_payment.name}")

        admin = session.query(Admin).first()
        if admin is None:
            admin = Admin(username=os.getenv("ADMIN_USERNAME", "admin"))
            admin.set_password(os.getenv("ADMIN_PASSWORD", "admin123"))
            session.add(admin)
            session.commit()
            print(f"[DB] Admin created: {admin.username}")
        else:
            admin.set_password(os.getenv("ADMIN_PASSWORD", "admin123"))
            session.commit()
            print(f"[DB] Admin password updated")
    except Exception as e:
        print(f"[DB] Error: {e}")
        session.rollback()
    finally:
        session.close()