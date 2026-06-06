_store = {}

def get_state(user_id: int) -> str | None:
    return _store.get(user_id, {}).get("state")

def set_state(user_id: int, state: str):
    if user_id not in _store:
        _store[user_id] = {"state": state, "data": {}}
    else:
        _store[user_id]["state"] = state

def clear_state(user_id: int):
    _store.pop(user_id, None)

def set_data(user_id: int, key: str, value):
    if user_id not in _store:
        _store[user_id] = {"state": None, "data": {}}
    _store[user_id]["data"][key] = value

def get_data(user_id: int, key: str, default=None):
    return _store.get(user_id, {}).get("data", {}).get(key, default)

def clear_data(user_id: int):
    if user_id in _store:
        _store[user_id]["data"] = {}

class States:
    ADMIN_WAIT_USERNAME = "admin_wait_username"
    ADMIN_WAIT_PASSWORD = "admin_wait_password"
    ADMIN_PANEL = "admin_panel"
    ADMIN_ADD_CAT_NAME = "admin_add_cat_name"
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

    MAIN_MENU = "main_menu"
    ORDER_DELIVERY = "order_delivery"
    ORDER_PAYMENT = "order_payment"
    ORDER_PHONE = "order_phone"
    ORDER_ADDRESS = "order_address"
    ORDER_CONFIRM = "order_confirm"