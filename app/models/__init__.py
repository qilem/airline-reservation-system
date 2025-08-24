from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin):
    """Base user model with common authentication methods"""
    def get_id(self):
        # 对于AirlineStaff,使用username
        if hasattr(self, 'username'):
            return self.username
        # 对于Customer和BookingAgent,使用email
        return self.email