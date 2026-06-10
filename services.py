import logging
from typing import List, Tuple, Optional

from models import Session, Cart, CartItem, Product

logger = logging.getLogger(__name__)


def get_cart(user_id: int) -> Optional[Cart]:
    """Return the Cart object for a user, or ``None`` if not existent."""
    session = Session()
    try:
        return session.query(Cart).filter_by(user_id=user_id).first()
    finally:
        session.close()


def create_cart(session, user_id: int) -> Cart:
    cart = Cart(user_id=user_id)
    session.add(cart)
    session.commit()
    session.refresh(cart)
    return cart


def add_to_cart(user_id: int, product_id: int) -> bool:
    """Add a product to the user's cart (or increment quantity).
    Returns ``True`` on success, ``False`` on DB error.
    """
    session = Session()
    try:
        cart = session.query(Cart).filter_by(user_id=user_id).first()
        if not cart:
            cart = create_cart(session, user_id)
        item = session.query(CartItem).filter_by(cart_id=cart.id, product_id=product_id).first()
        if item:
            item.quantity += 1
        else:
            item = CartItem(cart_id=cart.id, product_id=product_id, quantity=1)
            session.add(item)
        session.commit()
        return True
    except Exception as e:
        logger.error(f"add_to_cart failed: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def remove_cart_item(user_id: int, item_id: int) -> bool:
    session = Session()
    try:
        item = session.query(CartItem).filter_by(id=item_id).first()
        if item and item.cart.user_id == user_id:
            session.delete(item)
            session.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"remove_cart_item failed: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def change_quantity(user_id: int, item_id: int, delta: int) -> bool:
    """Increase (delta>0) or decrease (delta<0) quantity.
    If quantity would drop below 1, the item is removed.
    """
    session = Session()
    try:
        item = session.query(CartItem).filter_by(id=item_id).first()
        if not item or item.cart.user_id != user_id:
            return False
        if delta > 0:
            item.quantity += delta
        else:
            if item.quantity + delta > 0:
                item.quantity += delta
            else:
                session.delete(item)
        session.commit()
        return True
    except Exception as e:
        logger.error(f"change_quantity failed: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def clear_cart(user_id: int) -> bool:
    session = Session()
    try:
        cart = session.query(Cart).filter_by(user_id=user_id).first()
        if cart:
            session.query(CartItem).filter_by(cart_id=cart.id).delete()
            session.commit()
        return True
    except Exception as e:
        logger.error(f"clear_cart failed: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def cart_summary(user_id: int) -> Tuple[List[str], float]:
    """Return a list of formatted item strings and the total price."""
    session = Session()
    try:
        cart = session.query(Cart).filter_by(user_id=user_id).first()
        if not cart or not cart.items:
            return [], 0.0
        lines = []
        total = 0.0
        for ci in cart.items:
            prod = ci.product
            item_total = prod.price * ci.quantity
            total += item_total
            lines.append(f"• {prod.name} x{ci.quantity} = {item_total:,.0f} so'm")
        return lines, total
    finally:
        session.close()
