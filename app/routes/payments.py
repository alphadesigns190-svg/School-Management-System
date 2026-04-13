from datetime import date

from flask import Blueprint, current_app, flash, redirect, render_template, request

from ..db import execute, fetch_all, fetch_one
from ..queries.loader import load_query_config, require_query

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


def _get_config():
    return load_query_config("payments")


def _students_options(cfg):
    q = require_query(cfg, "students_select")
    rows = fetch_all(current_app, q["sql"], q.get("params", []), request_source=request)
    return [{"id": r.get("id"), "name": r.get("name")} for r in rows]


@payments_bp.get("")
def list_payments():
    cfg = _get_config()
    q = require_query(cfg, "list")
    payments = fetch_all(current_app, q["sql"], q.get("params", []), request_source=request)
    return render_template("payments/list.html", title="Payments", payments=payments)


@payments_bp.get("/balances")
def balances():
    cfg = _get_config()
    q = require_query(cfg, "balances")
    rows = fetch_all(current_app, q["sql"], q.get("params", []), request_source=request)
    return render_template("payments/balances.html", title="Fee Balances", rows=rows)


@payments_bp.get("/unpaid")
def unpaid():
    cfg = _get_config()
    q = require_query(cfg, "unpaid")
    rows = fetch_all(current_app, q["sql"], q.get("params", []), request_source=request)
    return render_template("payments/unpaid.html", title="Unpaid Students", rows=rows)


@payments_bp.get("/new")
def new_payment():
    cfg = _get_config()
    students = _students_options(cfg)
    default_date = date.today().isoformat()
    return render_template(
        "payments/form.html",
        title="Record payment",
        heading="Record payment",
        subheading="Record a payment for a student. Multiple payments are allowed.",
        payment=None,
        students=students,
        default_date=default_date,
        action="/payments",
        submit_label="Save payment",
    )


@payments_bp.post("")
def create_payment():
    cfg = _get_config()
    q = require_query(cfg, "insert")

    student_id = request.form.get("student_id", "").strip()
    amount = request.form.get("amount", "").strip()
    payment_date = request.form.get("payment_date", "").strip() or None

    if not student_id:
        flash("Student is required.", "error")
        return redirect("/payments/new")
    if not amount:
        flash("Amount is required.", "error")
        return redirect("/payments/new")

    execute(current_app, q["sql"], [student_id, amount, payment_date], request_source=request)
    flash("Payment recorded.", "success")
    return redirect("/payments")


@payments_bp.post("/new")
def create_payment_from_new():
    return create_payment()


@payments_bp.get("/<int:payment_id>/edit")
def edit_payment(payment_id: int):
    cfg = _get_config()
    students = _students_options(cfg)

    q = require_query(cfg, "get")
    payment = fetch_one(current_app, q["sql"], [payment_id], request_source=request)
    if not payment:
        flash("Payment not found.", "error")
        return redirect("/payments")

    default_date = date.today().isoformat()
    return render_template(
        "payments/form.html",
        title="Edit payment",
        heading="Edit payment",
        subheading="Update the payment information.",
        payment=payment,
        students=students,
        default_date=default_date,
        action=f"/payments/{payment_id}",
        submit_label="Save changes",
    )


@payments_bp.post("/<int:payment_id>")
def update_payment(payment_id: int):
    cfg = _get_config()
    q = require_query(cfg, "update")

    student_id = request.form.get("student_id", "").strip()
    amount = request.form.get("amount", "").strip()
    payment_date = request.form.get("payment_date", "").strip() or None

    if not student_id:
        flash("Student is required.", "error")
        return redirect(f"/payments/{payment_id}/edit")
    if not amount:
        flash("Amount is required.", "error")
        return redirect(f"/payments/{payment_id}/edit")

    execute(
        current_app,
        q["sql"],
        [student_id, amount, payment_date, payment_id],
        request_source=request,
    )
    flash("Payment updated.", "success")
    return redirect("/payments")


@payments_bp.post("/<int:payment_id>/delete")
def delete_payment(payment_id: int):
    cfg = _get_config()
    q = require_query(cfg, "delete")
    execute(current_app, q["sql"], [payment_id], request_source=request)
    flash("Payment deleted.", "success")
    return redirect("/payments")
