from datetime import date, timedelta

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request

from ..db import execute, fetch_all, fetch_one
from ..queries.loader import load_query_config, require_query
from ..services.validators import is_valid_module_id, parse_iso_date, parse_non_negative_int

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


def _get_config():
    return load_query_config("payments")


def _normalize_student_id(raw_student_id: str) -> str:
    cleaned = (raw_student_id or "").strip()
    if not cleaned:
        return ""
    if cleaned.upper().startswith("ST-"):
        return f"ST-{cleaned.split('-', 1)[1].strip()}"
    if cleaned.isdigit():
        return f"ST-{cleaned.zfill(3)}"
    return cleaned


def _student_number_from_id(student_id: str) -> str:
    cleaned = (student_id or "").strip()
    if cleaned.upper().startswith("ST-"):
        return cleaned.split("-", 1)[1]
    return cleaned


def _students_options(cfg):
    q = require_query(cfg, "students_select")
    rows = fetch_all(current_app, q["sql"], q.get("params", []), request_source=request)
    return [{"id": r.get("id"), "name": r.get("name")} for r in rows]


def _student_lookup(cfg, student_id: str):
    q = require_query(cfg, "student_lookup")
    normalized = _normalize_student_id(student_id)
    return fetch_one(current_app, q["sql"], [normalized], request_source=request)


def _report_range(mode: str):
    today = date.today()
    if mode == "weekly":
        start = today - timedelta(days=6)
        label = "Weekly Report"
        span = "Last 7 days"
    elif mode == "monthly":
        start = today - timedelta(days=29)
        label = "Monthly Report"
        span = "Last 30 days"
    elif mode == "3months":
        start = today - timedelta(days=89)
        label = "3 Months Report"
        span = "Last 90 days"
    else:
        start = today - timedelta(days=6)
        label = "Weekly Report"
        span = "Last 7 days"
        mode = "weekly"
    return mode, label, span, start, today


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


@payments_bp.get("/report/<mode>")
def payment_report(mode: str):
    mode, label, span, start_date, end_date = _report_range(mode)

    sql = (
        "SELECT p.id, p.student_id, s.name AS student_name, p.amount, p.payment_date "
        "FROM Payments p "
        "LEFT JOIN Students s ON s.id = p.student_id "
        "WHERE p.payment_date BETWEEN %s AND %s "
        "ORDER BY p.payment_date DESC, p.id DESC"
    )
    payments = fetch_all(
        current_app,
        sql,
        [start_date.isoformat(), end_date.isoformat()],
        request_source=request,
    )

    total_amount = sum(int(p.get("amount") or 0) for p in payments)
    payment_count = len(payments)

    return render_template(
        "payments/report.html",
        title=label,
        label=label,
        span=span,
        mode=mode,
        start_date=start_date,
        end_date=end_date,
        payments=payments,
        total_amount=total_amount,
        payment_count=payment_count,
    )


@payments_bp.get("/new")
def new_payment():
    cfg = _get_config()
    default_date = date.today().isoformat()
    return render_template(
        "payments/form.html",
        title="Record payment",
        heading="Record payment",
        subheading="Enter the student ID. The system will show the student name and current course.",
        payment=None,
        student_number="",
        default_date=default_date,
        action="/payments",
        submit_label="Save payment",
    )


@payments_bp.get("/student-info/<student_id>")
def student_info(student_id: str):
    cfg = _get_config()
    student = _student_lookup(cfg, student_id.strip())
    if not student:
        return jsonify({"found": False, "student": None})
    return jsonify({
        "found": True,
        "student": {
            "id": student.get("id"),
            "name": student.get("name"),
            "father_name": student.get("father_name"),
            "status": student.get("status"),
            "course_id": student.get("course_id"),
            "course_name": student.get("course_name"),
            "shift": student.get("shift"),
            "start_date": student.get("start_date"),
            "end_date": student.get("end_date"),
            "total_fee": student.get("total_fee"),
            "total_paid": student.get("total_paid"),
            "remaining_balance": student.get("remaining_balance"),
        },
    })


@payments_bp.post("")
def create_payment():
    cfg = _get_config()
    q = require_query(cfg, "insert")

    student_id = _normalize_student_id(request.form.get("student_id", "") or request.form.get("student_number", ""))
    amount_text = request.form.get("amount", "").strip()
    payment_date = request.form.get("payment_date", "").strip() or None
    amount = parse_non_negative_int(amount_text)

    if not student_id:
        flash("Student is required.", "error")
        return redirect("/payments/new")
    if not is_valid_module_id(student_id, "ST"):
        flash("Student ID format is invalid.", "error")
        return redirect("/payments/new")
    if not _student_lookup(cfg, student_id):
        flash("Student ID not found.", "error")
        return redirect("/payments/new")
    if amount is None:
        flash("Amount must be a valid non-negative number.", "error")
        return redirect("/payments/new")
    if amount <= 0:
        flash("Amount must be greater than zero.", "error")
        return redirect("/payments/new")
    parsed_payment_date = parse_iso_date(payment_date)
    if payment_date and parsed_payment_date is None:
        flash("Payment date is invalid.", "error")
        return redirect("/payments/new")
    if parsed_payment_date and parsed_payment_date > date.today():
        flash("Payment date cannot be in the future.", "error")
        return redirect("/payments/new")

    execute(current_app, q["sql"], [student_id, amount, payment_date], request_source=request)
    flash("Payment recorded.", "success")
    return redirect("/payments")


@payments_bp.post("/new")
def create_payment_from_new():
    return create_payment()


@payments_bp.get("/<int:payment_id>/edit")
def edit_payment(payment_id: int):
    flash("Editing payments is disabled. Please delete and record a new payment if needed.", "error")
    return redirect("/payments")


@payments_bp.post("/<int:payment_id>")
def update_payment(payment_id: int):
    flash("Editing payments is disabled. Please delete and record a new payment if needed.", "error")
    return redirect("/payments")


@payments_bp.post("/<int:payment_id>/delete")
def delete_payment(payment_id: int):
    cfg = _get_config()
    q = require_query(cfg, "delete")
    execute(current_app, q["sql"], [payment_id], request_source=request)
    flash("Payment deleted.", "success")
    return redirect("/payments")
