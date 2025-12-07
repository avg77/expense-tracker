from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from io import BytesIO
import pandas as pd
from app import db
from .models import Expense, Category

main_bp = Blueprint("main", __name__)

# ====================== DASHBOARD ========================

@main_bp.route("/")
@login_required
def dashboard():
    total = db.session.query(func.coalesce(func.sum(Expense.amount), 0.0))\
        .filter_by(user_id=current_user.id).scalar()

    expenses = Expense.query.filter_by(user_id=current_user.id)\
        .order_by(Expense.date.desc()).limit(5).all()

    rows = (
        db.session.query(
            Category.name,
            func.coalesce(func.sum(Expense.amount), 0.0)
        )
        .outerjoin(Expense, Expense.category_id == Category.id)
        .filter(Category.user_id == current_user.id)
        .group_by(Category.name)
        .all()
    )

    labels = [r[0] for r in rows]
    values = [float(r[1]) for r in rows]

    return render_template("dashboard.html",
                           total=total,
                           expenses=expenses,
                           labels=labels,
                           values=values)


# ====================== ADD EXPENSE =======================

@main_bp.route("/add-expense", methods=["GET", "POST"])
@login_required
def add_expense():
    categories = Category.query.filter_by(user_id=current_user.id).all()

    if request.method == "POST":
        title = request.form.get("title")
        amount = request.form.get("amount")
        category_id = request.form.get("category")

        if not title or not amount or not category_id:
            flash("All fields are required.", "warning")
            return render_template("add_expense.html", categories=categories)

        e = Expense(title=title, amount=float(amount),
                    category_id=int(category_id), user_id=current_user.id)
        db.session.add(e)
        db.session.commit()

        flash("Expense added successfully!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("add_expense.html", categories=categories)


# ====================== VIEW EXPENSES ======================

@main_bp.route("/expenses")
@login_required
def view_expenses():
    # Query params
    search = (request.args.get("q") or "").strip()
    sort = request.args.get("sort", "date_desc")
    category_id = request.args.get("category", type=int)

    # Base query
    query = Expense.query.filter_by(user_id=current_user.id)

    # Search by title
    if search:
        query = query.filter(Expense.title.ilike(f"%{search}%"))

    # Filter by category
    if category_id:
        query = query.filter(Expense.category_id == category_id)

    # Sorting
    if sort == "amount_asc":
        query = query.order_by(Expense.amount.asc())
    elif sort == "amount_desc":
        query = query.order_by(Expense.amount.desc())
    elif sort == "date_asc":
        query = query.order_by(Expense.date.asc())
    else:  # default date_desc
        query = query.order_by(Expense.date.desc())

    expenses = query.all()
    categories = Category.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "view_expenses.html",
        expenses=expenses,
        categories=categories,
        search=search,
        sort=sort,
        selected_category_id=category_id,
    )


from flask import abort  # at top with other imports, if not already

@main_bp.route("/expense/<int:id>/delete", methods=["POST"])
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)

    # Ensure user owns this expense
    if expense.user_id != current_user.id:
        abort(403)

    db.session.delete(expense)
    db.session.commit()
    flash("Expense deleted.", "danger")
    return redirect(url_for("main.view_expenses"))


# ====================== EDIT EXPENSE =======================

@main_bp.route("/expense/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    categories = Category.query.filter_by(user_id=current_user.id).all()

    if request.method == "POST":
        expense.title = request.form.get("title")
        expense.amount = float(request.form.get("amount"))
        expense.category_id = int(request.form.get("category"))
        db.session.commit()

        flash("Expense updated!", "success")
        return redirect(url_for("main.view_expenses"))

    return render_template("edit_expense.html",
                           expense=expense,
                           categories=categories)


# ====================== CATEGORY PAGE (UPDATED) =============

@main_bp.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()

        if not name:
            flash("Category name is required!", "warning")

        else:
            # 🔥 Check for duplicate under SAME USER only
            existing = Category.query.filter_by(
                user_id=current_user.id,
                name=name
            ).first()

            if existing:
                flash("You already created this category.", "danger")
            else:
                db.session.add(Category(name=name, user_id=current_user.id))
                db.session.commit()
                flash("Category added successfully!", "success")

        return redirect(url_for("main.categories"))

    cats = Category.query.filter_by(user_id=current_user.id).all()
    return render_template("categories.html", categories=cats)


# ====================== DELETE CATEGORY =====================

@main_bp.route("/category/delete/<int:id>", methods=["POST"])
@login_required
def delete_category(id):
    cat = Category.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()
    flash("Category deleted.", "danger")
    return redirect(url_for("main.categories"))


# ====================== REPORTS =============================

@main_bp.route("/reports")
@login_required
def reports():
    return render_template("reports.html")


# ------------- Live Graph Data (Category based) --------------

@main_bp.route("/reports/live-data")
@login_required
def reports_live_data():
    rows = (
        db.session.query(
            Category.name,
            func.coalesce(func.sum(Expense.amount), 0.0)
        )
        .outerjoin(Expense, Expense.category_id == Category.id)
        .filter(Category.user_id == current_user.id)
        .group_by(Category.name)
        .order_by(Category.name)
        .all()
    )

    labels = [r[0] for r in rows]      
    values = [float(r[1]) for r in rows]  

    return jsonify({"labels": labels, "values": values})


# ====================== EXPORT CSV ===========================

@main_bp.route("/export/csv")
@login_required
def export_csv():
    expenses = Expense.query.filter_by(user_id=current_user.id).all()

    df = pd.DataFrame([
        {
            "Title": e.title,
            "Amount": e.amount,
            "Category": e.category.name if e.category else "",
            "Date": e.date,
        }
        for e in expenses
    ])

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    buffer = BytesIO(csv_bytes)
    buffer.seek(0)

    return send_file(buffer,
                     mimetype="text/csv",
                     download_name="expenses.csv",
                     as_attachment=True)
