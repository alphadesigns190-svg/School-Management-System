from flask import Blueprint, current_app, render_template, request

from ..db import fetch_all, fetch_one
from ..queries.loader import load_query_config, require_query

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def _get_config():
    return load_query_config("dashboard")


@dashboard_bp.get("")
def dashboard():
    cfg = _get_config()

    total_students = fetch_one(
        current_app,
        require_query(cfg, "total_students")["sql"],
        [],
        request_source=request,
    )["total_students"]

    total_income = fetch_one(
        current_app,
        require_query(cfg, "total_income")["sql"],
        [],
        request_source=request,
    )["total_income"]

    unpaid_count = fetch_one(
        current_app,
        require_query(cfg, "unpaid_count")["sql"],
        [],
        request_source=request,
    )["unpaid_count"]

    unpaid_top = fetch_all(
        current_app,
        require_query(cfg, "unpaid_top")["sql"],
        [],
        request_source=request,
    )

    return render_template(
        "dashboard/index.html",
        title="Dashboard",
        total_students=total_students,
        total_income=total_income,
        unpaid_count=unpaid_count,
        unpaid_top=unpaid_top,
    )

