from datetime import datetime

from flask import Blueprint, current_app, render_template, request

from ..db import fetch_all, fetch_one
from ..queries.loader import load_query_config, require_query

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def _get_config():
    return load_query_config("reports")


@reports_bp.get("/student/<student_id>")
def student_report(student_id: str):
    cfg = _get_config()

    student = fetch_one(
        current_app,
        require_query(cfg, "student")["sql"],
        [student_id],
        request_source=request,
    )
    if not student:
        return render_template(
            "error.html", title="Not found", message=f"Student not found: {student_id}"
        ), 404

    enrollments = fetch_all(
        current_app,
        require_query(cfg, "enrollments")["sql"],
        [student_id],
        request_source=request,
    )
    payments = fetch_all(
        current_app,
        require_query(cfg, "payments")["sql"],
        [student_id],
        request_source=request,
    )
    results = fetch_all(
        current_app,
        require_query(cfg, "results")["sql"],
        [student_id],
        request_source=request,
    )

    total_fee = fetch_one(
        current_app,
        require_query(cfg, "total_fee")["sql"],
        [student_id],
        request_source=request,
    )["total_fee"]
    total_paid = fetch_one(
        current_app,
        require_query(cfg, "total_paid")["sql"],
        [student_id],
        request_source=request,
    )["total_paid"]
    remaining = (total_fee or 0) - (total_paid or 0)

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    return render_template(
        "reports/student.html",
        title="Student Report",
        student=student,
        enrollments=enrollments,
        payments=payments,
        results=results,
        total_fee=total_fee,
        total_paid=total_paid,
        remaining=remaining,
        generated_at=generated_at,
    )

