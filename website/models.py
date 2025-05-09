from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(12), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    attribute = db.Column(db.String(12), nullable=False)
    
    def __repr__(self):
        return f'<User {self.username}>'