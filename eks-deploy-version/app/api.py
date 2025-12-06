from flask import Blueprint, jsonify
from flask_restful import Resource, Api
from flask_login import current_user, login_required
from .models import Expense

api_bp = Blueprint("api", __name__)
api = Api(api_bp)

class ExpenseAPI(Resource):
    method_decorators = [login_required]

    def get(self):
        expenses = Expense.query.filter_by(user_id=current_user.id).all()
        return jsonify([{
            "id": e.id,
            "title": e.title,
            "amount": e.amount,
            "date": e.date.isoformat(),
            "category": e.category.name if e.category else None
        } for e in expenses])

api.add_resource(ExpenseAPI, "/expenses")
