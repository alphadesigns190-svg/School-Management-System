from flask import Blueprint, current_app, flash, redirect, render_template, request

from ..db import execute, fetch_all, fetch_one
from ..queries.loader import load_query_config, require_query
from ..services.results_calc import calculate_total_and_grade
from ..services.validators import clean_text, is_valid_module_id, parse_non_negative_int

results_bp = Blueprint("results", __name__, url_prefix="/results")


def _get_config():
    return load_query_config("results")


def _students_options(cfg):
    q = require_query(cfg, "students_select")
    rows = fetch_all(current_app, q["sql"], q.get("params", []), request_source=request)
    return [{"id": r.get("id"), "name": r.get("name")} for r in rows]


def _validate_marks(payload: dict) -> str | None:
    fields = ["quiz1", "quiz2", "quiz3", "quiz4", "exam20", "exam30", "interview"]
    for field in fields:
        raw = (payload.get(field) or "").strip()
        if raw == "":
            continue
        parsed = parse_non_negative_int(raw)
        if parsed is None:
            return f"{field} must be a valid non-negative number."
        if parsed > 100:
            return f"{field} cannot be greater than 100."
    return None


@results_bp.get("")
def list_results():
    cfg = _get_config()
    q = require_query(cfg, "list")
    rows = fetch_all(current_app, q["sql"], q.get("params", []), request_source=request)
    return render_template("results/list.html", title="Results", rows=rows)


@results_bp.get("/new")
def new_result():
    cfg = _get_config()
    students = _students_options(cfg)
    return render_template(
        "results/form.html",
        title="Add result",
        heading="Add result",
        subheading="Enter marks; total and grade are calculated automatically.",
        result=None,
        students=students,
        action="/results",
        submit_label="Create",
    )


@results_bp.post("")
def create_result():
    cfg = _get_config()
    q = require_query(cfg, "insert")

    payload = dict(request.form)
    student_id = clean_text(payload.get("student_id"), 10)
    month = clean_text(payload.get("month"), 20)
    if not student_id:
        flash("Student is required.", "error")
        return redirect("/results/new")
    if not is_valid_module_id(student_id, "ST"):
        flash("Student ID format is invalid.", "error")
        return redirect("/results/new")
    if not month:
        flash("Month is required.", "error")
        return redirect("/results/new")
    marks_error = _validate_marks(payload)
    if marks_error:
        flash(marks_error, "error")
        return redirect("/results/new")

    total, grade = calculate_total_and_grade(payload)

    values = []
    for name in q.get("params", []):
        if name == "total_marks":
            values.append(total)
        elif name == "grade":
            values.append(grade)
        else:
            raw = payload.get(name, "")
            cleaned = raw.strip() if isinstance(raw, str) else raw
            values.append(cleaned if cleaned != "" else None)

    execute(current_app, q["sql"], values, request_source=request)
    flash("Result added.", "success")
    return redirect("/results")


@results_bp.get("/<int:result_id>/edit")
def edit_result(result_id: int):
    cfg = _get_config()
    students = _students_options(cfg)

    q = require_query(cfg, "get")
    result = fetch_one(current_app, q["sql"], [result_id], request_source=request)
    if not result:
        flash("Result not found.", "error")
        return redirect("/results")

    return render_template(
        "results/form.html",
        title="Edit result",
        heading="Edit result",
        subheading="Update marks; total and grade are recalculated automatically.",
        result=result,
        students=students,
        action=f"/results/{result_id}",
        submit_label="Save changes",
    )


@results_bp.post("/<int:result_id>")
def update_result(result_id: int):
    cfg = _get_config()
    q = require_query(cfg, "update")

    payload = dict(request.form)
    student_id = clean_text(payload.get("student_id"), 10)
    month = clean_text(payload.get("month"), 20)
    if not student_id:
        flash("Student is required.", "error")
        return redirect(f"/results/{result_id}/edit")
    if not is_valid_module_id(student_id, "ST"):
        flash("Student ID format is invalid.", "error")
        return redirect(f"/results/{result_id}/edit")
    if not month:
        flash("Month is required.", "error")
        return redirect(f"/results/{result_id}/edit")
    marks_error = _validate_marks(payload)
    if marks_error:
        flash(marks_error, "error")
        return redirect(f"/results/{result_id}/edit")

    total, grade = calculate_total_and_grade(payload)

    values = []
    for name in q.get("params", []):
        if name == "id":
            values.append(result_id)
        elif name == "total_marks":
            values.append(total)
        elif name == "grade":
            values.append(grade)
        else:
            raw = payload.get(name, "")
            cleaned = raw.strip() if isinstance(raw, str) else raw
            values.append(cleaned if cleaned != "" else None)

    execute(current_app, q["sql"], values, request_source=request)
    flash("Result updated.", "success")
    return redirect("/results")


@results_bp.post("/<int:result_id>/delete")
def delete_result(result_id: int):
    cfg = _get_config()
    q = require_query(cfg, "delete")
    execute(current_app, q["sql"], [result_id], request_source=request)
    flash("Result deleted.", "success")
    return redirect("/results")
