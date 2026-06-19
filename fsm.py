import json
from models import Session, UserState

def get_state(user_id: int) -> str | None:
    session = Session()
    try:
        us = session.query(UserState).filter_by(user_id=user_id).first()
        return us.state if us else None
    except Exception as e:
        print(f"[FSM Error] get_state: {e}")
        return None
    finally:
        session.close()

def set_state(user_id: int, state: str):
    session = Session()
    try:
        us = session.query(UserState).filter_by(user_id=user_id).first()
        if not us:
            us = UserState(user_id=user_id, state=state, data_json="{}")
            session.add(us)
        else:
            us.state = state
        session.commit()
    except Exception as e:
        print(f"[FSM Error] set_state: {e}")
        session.rollback()
    finally:
        session.close()

def clear_state(user_id: int):
    session = Session()
    try:
        us = session.query(UserState).filter_by(user_id=user_id).first()
        if us:
            session.delete(us)
            session.commit()
    except Exception as e:
        print(f"[FSM Error] clear_state: {e}")
        session.rollback()
    finally:
        session.close()

def set_data(user_id: int, key: str, value):
    session = Session()
    try:
        us = session.query(UserState).filter_by(user_id=user_id).first()
        if not us:
            us = UserState(user_id=user_id, state=None, data_json="{}")
            session.add(us)
        
        data = json.loads(us.data_json or "{}")
        data[key] = value
        us.data_json = json.dumps(data)
        session.commit()
    except Exception as e:
        print(f"[FSM Error] set_data: {e}")
        session.rollback()
    finally:
        session.close()

def get_data(user_id: int, key: str, default=None):
    session = Session()
    try:
        us = session.query(UserState).filter_by(user_id=user_id).first()
        if us and us.data_json:
            data = json.loads(us.data_json)
            return data.get(key, default)
        return default
    except Exception as e:
        print(f"[FSM Error] get_data: {e}")
        return default
    finally:
        session.close()

def clear_data(user_id: int):
    session = Session()
    try:
        us = session.query(UserState).filter_by(user_id=user_id).first()
        if us:
            us.data_json = "{}"
            session.commit()
    except Exception as e:
        print(f"[FSM Error] clear_data: {e}")
        session.rollback()
    finally:
        session.close()

class States:
    ADMIN_WAIT_USERNAME = "admin_wait_username"
    ADMIN_WAIT_PASSWORD = "admin_wait_password"
    ADMIN_PANEL = "admin_panel"
    ADMIN_CRUD_MENU = "admin_crud_menu"
    ADMIN_ADD_CAT_NAME = "admin_add_cat_name"
    ADMIN_ADD_CAT_PARENT = "admin_add_cat_parent"
    ADMIN_EDIT_CAT_NAME = "admin_edit_cat_name"
    ADMIN_ADD_PROD_NAME = "admin_add_prod_name"
    ADMIN_ADD_PROD_DESC = "admin_add_prod_desc"
    ADMIN_ADD_PROD_PRICE = "admin_add_prod_price"
    ADMIN_ADD_PROD_IMAGE = "admin_add_prod_image"
    ADMIN_ADD_PROD_CAT = "admin_add_prod_cat"
    ADMIN_EDIT_PROD_NAME = "admin_edit_prod_name"
    ADMIN_ADD_DELIVERY_NAME = "admin_add_delivery_name"
    ADMIN_ADD_DELIVERY_PRICE = "admin_add_delivery_price"
    ADMIN_EDIT_DELIVERY_NAME = "admin_edit_delivery_name"
    ADMIN_ADD_PAY_NAME = "admin_add_pay_name"
    ADMIN_ADD_PAY_DETAILS = "admin_add_pay_details"
    ADMIN_EDIT_PAY_NAME = "admin_edit_pay_name"
    ADMIN_CHANGE_PW_OLD = "admin_change_pw_old"
    ADMIN_CHANGE_PW_NEW = "admin_change_pw_new"
    ADMIN_CHANGE_PW_CONF = "admin_change_pw_conf"

    NEWS_MENU = "news_menu"
    NEWS_ADD_TEXT = "news_add_text"
    NEWS_ADD_PHOTO = "news_add_photo"
    NEWS_EDIT_SELECT = "news_edit_select"
    NEWS_EDIT_TEXT = "news_edit_text"
    NEWS_EDIT_PHOTO = "news_edit_photo"
    NEWS_DELETE_SELECT = "news_delete_select"

    MAIN_MENU = "main_menu"
    ORDER_DELIVERY = "order_delivery"
    ORDER_PAYMENT = "order_payment"
    ORDER_PHONE = "order_phone"
    ORDER_ADDRESS = "order_address"
    ORDER_CONFIRM = "order_confirm"