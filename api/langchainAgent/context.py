# context.py
_current_user_info = {}

def set_user_info(user_id: str, token: str):
    _current_user_info["user_id"] = user_id
    _current_user_info["auth_token"] = token

def get_current_user_info():
    return _current_user_info.get("user_id"), _current_user_info.get("auth_token")
