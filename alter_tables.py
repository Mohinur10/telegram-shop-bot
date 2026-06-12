from models import engine
from sqlalchemy import text

with engine.connect() as conn:
    # cart_items.product_id -> ON DELETE CASCADE
    try:
        conn.execute(text("ALTER TABLE cart_items DROP CONSTRAINT cart_items_product_id_fkey;"))
        conn.execute(text("ALTER TABLE cart_items ADD CONSTRAINT cart_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;"))
    except Exception as e:
        print("cart_items product_id", e)

    # cart_items.cart_id -> ON DELETE CASCADE
    try:
        conn.execute(text("ALTER TABLE cart_items DROP CONSTRAINT cart_items_cart_id_fkey;"))
        conn.execute(text("ALTER TABLE cart_items ADD CONSTRAINT cart_items_cart_id_fkey FOREIGN KEY (cart_id) REFERENCES carts(id) ON DELETE CASCADE;"))
    except Exception as e:
        print("cart_items cart_id", e)

    # products.category_id -> ON DELETE CASCADE
    try:
        conn.execute(text("ALTER TABLE products DROP CONSTRAINT products_category_id_fkey;"))
        conn.execute(text("ALTER TABLE products ADD CONSTRAINT products_category_id_fkey FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE;"))
    except Exception as e:
        print("products category_id", e)

    # order_items.order_id -> ON DELETE CASCADE
    try:
        conn.execute(text("ALTER TABLE order_items DROP CONSTRAINT order_items_order_id_fkey;"))
        conn.execute(text("ALTER TABLE order_items ADD CONSTRAINT order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;"))
    except Exception as e:
        print("order_items order_id", e)

    # order_items.product_id -> SET NULL
    try:
        conn.execute(text("ALTER TABLE order_items ALTER COLUMN product_id DROP NOT NULL;"))
        conn.execute(text("ALTER TABLE order_items DROP CONSTRAINT order_items_product_id_fkey;"))
        conn.execute(text("ALTER TABLE order_items ADD CONSTRAINT order_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL;"))
    except Exception as e:
        print("order_items product_id", e)

    # orders.delivery_id -> SET NULL
    try:
        conn.execute(text("ALTER TABLE orders DROP CONSTRAINT orders_delivery_id_fkey;"))
        conn.execute(text("ALTER TABLE orders ADD CONSTRAINT orders_delivery_id_fkey FOREIGN KEY (delivery_id) REFERENCES delivery_settings(id) ON DELETE SET NULL;"))
    except Exception as e:
        print("orders delivery_id", e)

    # orders.payment_id -> SET NULL
    try:
        conn.execute(text("ALTER TABLE orders DROP CONSTRAINT orders_payment_id_fkey;"))
        conn.execute(text("ALTER TABLE orders ADD CONSTRAINT orders_payment_id_fkey FOREIGN KEY (payment_id) REFERENCES payment_methods(id) ON DELETE SET NULL;"))
    except Exception as e:
        print("orders payment_id", e)

    conn.commit()
    print("Database constraints updated successfully.")
