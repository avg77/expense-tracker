from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import UniqueConstraint
from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    expenses = db.relationship("Expense", backref="user", lazy=True)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)     # ⬅ removed unique=True
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    # 🔥 category name must be unique per user (NOT global)
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="unique_user_category"),
    )


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    category = db.relationship("Category")
