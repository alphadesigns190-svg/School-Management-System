from flask import Blueprint, current_app, flash, redirect, render_template, request

from ..db import execute, fetch_all, fetch_one
from ..queries.loader import load_query_config, require_query

enrollments_bp = Blueprint("enrollments", __name__, url_prefix="/enrollments")


def _get_config():
    return load_query_config("enrollments")


def _fields_from_config(cfg):
    fields = cfg.get("fields", [])
    return [
        {
            "name": f.get("name", ""),
            "label": f.get("label", f.get("name", "")),
            "type": f.get("type", "text"),
            "required": bool(f.get("required", False)),
        }
        for f in fields
        if f.get("name")
    ]


def _students_options(cfg):
    q = require_query(cfg, "students_select")
    rows = fetch_all(current_app, q["sql"], q.get("params", []), request_source=request)
    return [{"id": r.get("id"), "name": r.get("name")} for r in rows]


def _courses_options(cfg):
    q = require_query(cfg, "courses_select")
    rows = fetch_all(current_app, q["sql"], q.get("params", []), request_source=request)
    return [{"id": r.get("id"), "course_name": r.get("course_name")} for r in rows]


@enrollments_bp.get("")
def list_enrollments():
    cfg = _get_config()
    q = require_query(cfg, "list")
    enrollments = fetch_all(current_app, q["sql"], q.get("params", []), request_source=request)
    return render_template(
        "enrollments/list.html", title="Enrollments", enrollments=enrollments
    )


@enrollments_bp.get("/new")
def new_enrollment():
    cfg = _get_config()
    fields = _fields_from_config(cfg)
    students = _students_options(cfg)
    courses = _courses_options(cfg)
    return render_template(
        "enrollments/form.html",
        title="Add enrollment",
        heading="Assign student to course",
        subheading="Select a student and a course.",
        fields=fields,
        enrollment=None,
        students=students,
        courses=courses,
        action="/enrollments",
        submit_label="Create",
    )


@enrollments_bp.post("")
def create_enrollment():
    cfg = _get_config()
    q = require_query(cfg, "insert")

    values = []
    for name in q.get("params", []):
        raw = request.form.get(name, "")
        if raw is None:
            values.append(None)
        else:
            cleaned = raw.strip() if isinstance(raw, str) else raw
            values.append(cleaned if cleaned != "" else None)

    execute(current_app, q["sql"], values, request_source=request)
    flash("Enrollment added.", "success")
    return redirect("/enrollments")


@enrollments_bp.get("/<int:enrollment_id>/edit")
def edit_enrollment(enrollment_id: int):
    cfg = _get_config()
    fields = _fields_from_config(cfg)
    students = _students_options(cfg)
    courses = _courses_options(cfg)

    q = require_query(cfg, "get")
    enrollment = fetch_one(current_app, q["sql"], [enrollment_id], request_source=request)
    if not enrollment:
        flash("Enrollment not found.", "error")
        return redirect("/enrollments")

    return render_template(
        "enrollments/form.html",
        title="Edit enrollment",
        heading="Edit enrollment",
        subheading="Update student/course or dates.",
        fields=fields,
        enrollment=enrollment,
        students=students,
        courses=courses,
        action=f"/enrollments/{enrollment_id}",
        submit_label="Save changes",
    )


@enrollments_bp.post("/<int:enrollment_id>")
def update_enrollment(enrollment_id: int):
    cfg = _get_config()
    q = require_query(cfg, "update")

    values = []
    for name in q.get("params", []):
        if name == "id":
            values.append(enrollment_id)
            continue

        raw = request.form.get(name, "")
        if raw is None:
            values.append(None)
        else:
            cleaned = raw.strip() if isinstance(raw, str) else raw
            values.append(cleaned if cleaned != "" else None)

    execute(current_app, q["sql"], values, request_source=request)
    flash("Enrollment updated.", "success")
    return redirect("/enrollments")


@enrollments_bp.post("/<int:enrollment_id>/delete")
def delete_enrollment(enrollment_id: int):
    cfg = _get_config()
    q = require_query(cfg, "delete")
    execute(current_app, q["sql"], [enrollment_id], request_source=request)
    flash("Enrollment deleted.", "success")
    return redirect("/enrollments")

