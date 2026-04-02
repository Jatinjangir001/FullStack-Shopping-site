from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.name = user_data.get("name")
        self.email = user_data.get("email")
        self.mobile = user_data.get("mobile")
        self.password_hash = user_data.get("password_hash")
        self.is_admin = user_data.get("is_admin", False)
