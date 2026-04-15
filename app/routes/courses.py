from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request

from ..db import execute, fetch_all, fetch_one
from ..queries.loader import load_query_config, require_query
from ..services.id_generator import mysql_named_lock, next_formatted_id
from ..services.validators import clean_text, is_valid_module_id, parse_non_negative_int

courses_bp = Blueprint("courses", __name__, url_prefix="/courses")


def _get_config():
    return load_query_config("courses")


def _fields_from_config(cfg):
    fields = cfg.get("fields", [])
    return [
        {
            "name": f.get("name", ""),
            "label": f.get("label", f.get("name", "")),
            "type": f.get("type", "text"),
            "required": bool(f.get("required", False)),
            "options": f.get("options"),
        }
        for f in fields
        if f.get("name")
    ]


def _create_fields(cfg):
    fields = _fields_from_config(cfg)
    return [f for f in fields if f.get("name") != "id"]


def _teacher_options(cfg):
    q = require_query(cfg, "teachers_select")
    rows = fetch_all(current_app, q["sql"], q.get("params", []), request_source=request)
    return [{"id": r.get("id"), "name": r.get("name")} for r in rows]


def _search_courses(search: str):
    like = f"%{search}%"
    sql = (
        "SELECT c.id, c.course_name, c.fee, c.duration, c.shift, c.teacher_id, "
        "t.name AS teacher_name, COALESCE(COUNT(DISTINCT e.student_id), 0) AS student_count "
        "FROM Courses c "
        "LEFT JOIN Teachers t ON t.id = c.teacher_id "
        "LEFT JOIN Enrollments e ON e.course_id = c.id "
        "WHERE c.id LIKE %s OR c.course_name LIKE %s "
        "GROUP BY c.id, c.course_name, c.fee, c.duration, c.shift, c.teacher_id, t.name "
        "ORDER BY c.id"
    )
    return fetch_all(current_app, sql, [like, like], request_source=request)


@courses_bp.get("")
def list_courses():
    cfg = _get_config()
    search = (request.args.get("q") or "").strip()
    base_sql = (
        "SELECT c.id, c.course_name, c.fee, c.duration, c.shift, c.teacher_id, "
        "t.name AS teacher_name, COALESCE(COUNT(DISTINCT e.student_id), 0) AS student_count "
        "FROM Courses c "
        "LEFT JOIN Teachers t ON t.id = c.teacher_id "
        "LEFT JOIN Enrollments e ON e.course_id = c.id "
    )

    if search:
        courses = _search_courses(search)
    else:
        courses = fetch_all(
            current_app,
            base_sql
            + "GROUP BY c.id, c.course_name, c.fee, c.duration, c.shift, c.teacher_id, t.name "
            + "ORDER BY c.id",
            [],
            request_source=request,
        )

    return render_template("courses/list.html", title="Courses", courses=courses, search=search)


@courses_bp.get("/_data")
def courses_data():
    search = (request.args.get("q") or "").strip()
    if not search:
        return jsonify({"courses": []})
    return jsonify({"courses": _search_courses(search)})


@courses_bp.get("/new")
def new_course():
    cfg = _get_config()
    fields = _create_fields(cfg)
    teachers = _teacher_options(cfg)
    return render_template(
        "courses/form.html",
        title="Add course",
        heading="Add course",
        subheading="Course ID will be generated automatically (CS-001, CS-002...).",
        fields=fields,
        course=None,
        teachers=teachers,
        action="/courses",
        submit_label="Create",
    )


@courses_bp.post("")
def create_course():
    cfg = _get_config()
    q = require_query(cfg, "insert")
    course_name = clean_text(request.form.get("course_name"), 50)
    fee = parse_non_negative_int(request.form.get("fee"))
    duration = clean_text(request.form.get("duration"), 20)
    shift = clean_text(request.form.get("shift"), 20)
    teacher_id = clean_text(request.form.get("teacher_id"), 10)

    if not course_name:
        flash("Course name is required.", "error")
        return redirect("/courses/new")
    if request.form.get("fee", "").strip() and fee is None:
        flash("Fee must be a valid non-negative number.", "error")
        return redirect("/courses/new")
    if teacher_id and not is_valid_module_id(teacher_id, "TE"):
        flash("Teacher ID format is invalid.", "error")
        return redirect("/courses/new")

    from ..db import get_connection

    conn = get_connection(current_app)
    new_id = None
    try:
        conn.start_transaction()
        with mysql_named_lock(conn, "lcms:courses:id", timeout_seconds=5):
            new_id = next_formatted_id(conn, table="Courses", id_column="id", prefix="CS", width=3)

            values = []
            for param_name in q.get("params", []):
                if param_name == "id":
                    values.append(new_id)
                    continue

                if param_name == "course_name":
                    values.append(course_name)
                elif param_name == "fee":
                    values.append(fee)
                elif param_name == "duration":
                    values.append(duration)
                elif param_name == "shift":
                    values.append(shift)
                elif param_name == "teacher_id":
                    values.append(teacher_id)
                else:
                    raw = request.form.get(param_name, "")
                    cleaned = raw.strip() if isinstance(raw, str) else raw
                    values.append(cleaned if cleaned != "" else None)

            cur = conn.cursor(dictionary=True, buffered=True)
            cur.execute(q["sql"], values)
        conn.commit()
    finally:
        conn.close()

    flash(f"Course added. ID: {new_id}", "success")
    return redirect("/courses")


@courses_bp.get("/<course_id>/edit")
def edit_course(course_id: str):
    cfg = _get_config()
    fields = _fields_from_config(cfg)
    teachers = _teacher_options(cfg)

    q = require_query(cfg, "get")
    course = fetch_one(current_app, q["sql"], [course_id], request_source=request)
    if not course:
        flash("Course not found.", "error")
        return redirect("/courses")

    return render_template(
        "courses/form.html",
        title="Edit course",
        heading="Edit course",
        subheading="Update the course details and assigned teacher.",
        fields=fields,
        course=course,
        teachers=teachers,
        action=f"/courses/{course_id}",
        submit_label="Save changes",
    )


@courses_bp.post("/<course_id>")
def update_course(course_id: str):
    cfg = _get_config()
    q = require_query(cfg, "update")
    course_name = clean_text(request.form.get("course_name"), 50)
    fee = parse_non_negative_int(request.form.get("fee"))
    duration = clean_text(request.form.get("duration"), 20)
    shift = clean_text(request.form.get("shift"), 20)
    teacher_id = clean_text(request.form.get("teacher_id"), 10)

    if not course_name:
        flash("Course name is required.", "error")
        return redirect(f"/courses/{course_id}/edit")
    if request.form.get("fee", "").strip() and fee is None:
        flash("Fee must be a valid non-negative number.", "error")
        return redirect(f"/courses/{course_id}/edit")
    if teacher_id and not is_valid_module_id(teacher_id, "TE"):
        flash("Teacher ID format is invalid.", "error")
        return redirect(f"/courses/{course_id}/edit")

    values = []
    for param_name in q.get("params", []):
        if param_name == "id":
            values.append(course_id)
            continue

        if param_name == "course_name":
            values.append(course_name)
        elif param_name == "fee":
            values.append(fee)
        elif param_name == "duration":
            values.append(duration)
        elif param_name == "shift":
            values.append(shift)
        elif param_name == "teacher_id":
            values.append(teacher_id)
        else:
            raw = request.form.get(param_name, "")
            values.append(raw.strip() if isinstance(raw, str) else raw)

    execute(current_app, q["sql"], values, request_source=request)
    flash("Course updated.", "success")
    return redirect("/courses")


@courses_bp.post("/<course_id>/delete")
def delete_course(course_id: str):
    cfg = _get_config()
    q = require_query(cfg, "delete")
    execute(current_app, q["sql"], [course_id], request_source=request)
    flash("Course deleted.", "success")
    return redirect("/courses")
