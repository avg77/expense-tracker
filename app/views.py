
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from io import BytesIO
import pandas as pd
from app import db
from .models import Expense, Category

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
@login_required
def dashboard():
    # Total expenses for current user
    total = db.session.query(func.coalesce(func.sum(Expense.amount), 0.0)) \
        .filter_by(user_id=current_user.id).scalar()

    # Last 5 expenses for current user
    expenses = Expense.query.filter_by(user_id=current_user.id) \
        .order_by(Expense.date.desc()).limit(5).all()

    # Category-wise expense summary for current user
    rows = (
        db.session.query(Category.name, func.coalesce(func.sum(Expense.amount), 0.0))
        .outerjoin(Expense, Expense.category_id == Category.id)
        .filter(Category.user_id == current_user.id)
        .filter((Expense.user_id == current_user.id) | (Expense.user_id.is_(None)))
        .group_by(Category.name)
        .all()
    )

    labels = [r[0] for r in rows]
    values = [float(r[1]) for r in rows]

    return render_template("dashboard.html", total=total, expenses=expenses, labels=labels, values=values)

@main_bp.route("/add-expense", methods=["GET", "POST"])
@login_required
def add_expense():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        amount = request.form.get("amount")
        category_id = request.form.get("category")

        if not title or not amount or not category_id:
            flash("All fields are required.", "warning")
            return render_template("add_expense.html", categories=categories)

        # Validate category belongs to current user
        category = Category.query.filter_by(id=int(category_id), user_id=current_user.id).first()
        if not category:
            flash("Invalid category selection.", "warning")
            return render_template("add_expense.html", categories=categories)

        e = Expense(title=title, amount=float(amount), category_id=category.id, user_id=current_user.id)
        db.session.add(e)
        db.session.commit()
        flash("Expense added.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("add_expense.html", categories=categories)

@main_bp.route("/expenses")
@login_required
def view_expenses():
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    return render_template("view_expenses.html", expenses=expenses)

@main_bp.route("/expense/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)

    # Ensure expense belongs to current user
    if expense.user_id != current_user.id:
        flash("You cannot edit this expense.", "warning")
        return redirect(url_for("main.view_expenses"))

    categories = Category.query.filter_by(user_id=current_user.id).all()

    if request.method == "POST":
        expense.title = (request.form.get("title") or "").strip()
        expense.amount = float(request.form.get("amount"))
        category_id = int(request.form.get("category"))

        # Validate category belongs to user
        category = Category.query.filter_by(id=category_id, user_id=current_user.id).first()
        if not category:
            flash("Invalid category selection.", "warning")
            return render_template("edit_expense.html", expense=expense, categories=categories)

        expense.category_id = category.id
        db.session.commit()
        flash("Expense updated.", "success")
        return redirect(url_for("main.view_expenses"))

    return render_template("edit_expense.html", expense=expense, categories=categories)

@main_bp.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if name:
            try:
                db.session.add(Category(name=name, user_id=current_user.id))
                db.session.commit()
                flash("Category added.", "success")
            except IntegrityError:
                db.session.rollback()
                flash("Category already exists for your account.", "warning")
        else:
            flash("Category name is required.", "warning")

    cats = Category.query.filter_by(user_id=current_user.id).all()
    return render_template("categories.html", categories=cats)

@main_bp.route("/reports")
@login_required
def reports():
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    return render_template("reports.html", expenses=expenses)

@main_bp.route("/export/csv")
@login_required
def export_csv():
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    df = pd.DataFrame([{
        "Title": e.title,
        "Amount": e.amount,
        "Category": e.category.name if e.category else "",
        "Date": e.date
    } for e in expenses])

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    buffer = BytesIO(csv_bytes)
    buffer.seek(0)
    return send_file(buffer, mimetype="text/csv", download_name="expenses.csv", as_attachment=True)
