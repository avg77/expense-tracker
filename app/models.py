
from flask_login import UserMixin
from datetime import datetime
from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    expenses = db.relationship("Expense", backref="user", lazy=True)
    categories = db.relationship("Category", backref="user", lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)  # Removed global unique
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    expenses = db.relationship("Expense", backref="category", lazy=True)

    __table_args__ = (
        db.UniqueConstraint('name', 'user_id', name='unique_category_per_user'),
    )

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
