from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request

from ..db import execute, fetch_all, fetch_one
from ..queries.loader import load_query_config, require_query
from ..services.id_generator import mysql_named_lock, next_formatted_id

students_bp = Blueprint("students", __name__, url_prefix="/students")


def _get_config():
    return load_query_config("students")


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


def _search_students(search: str):
    like = f"%{search}%"
    sql = (
        "SELECT id, name, father_name, phone, status "
        "FROM Students "
        "WHERE id LIKE %s OR name LIKE %s OR father_name LIKE %s "
        "ORDER BY id"
    )
    return fetch_all(current_app, sql, [like, like, like], request_source=request)


@students_bp.get("")
def list_students():
    cfg = _get_config()
    fields = _fields_from_config(cfg)
    id_field = cfg.get("id_field", "id")

    search = (request.args.get("q") or "").strip()
    if search:
        students = _search_students(search)
    else:
        q = require_query(cfg, "list")
        students = fetch_all(current_app, q["sql"], q.get("params", []), request_source=request)

    return render_template(
        "students/list.html",
        title="Students",
        students=students,
        fields=fields,
        id_field=id_field,
        search=search,
    )


@students_bp.get("/_data")
def students_data():
    search = (request.args.get("q") or "").strip()
    if not search:
        return jsonify({"students": []})
    return jsonify({"students": _search_students(search)})


@students_bp.get("/new")
def new_student():
    cfg = _get_config()
    fields = _create_fields(cfg)
    return render_template(
        "students/form.html",
        title="Add student",
        heading="Add student",
        subheading="Student ID will be generated automatically (ST-001, ST-002...).",
        fields=fields,
        student=None,
        action="/students",
        submit_label="Create",
    )


@students_bp.post("")
def create_student():
    cfg = _get_config()
    q = require_query(cfg, "insert")

    from ..db import get_connection

    conn = get_connection(current_app)
    new_id = None
    try:
        conn.start_transaction()
        with mysql_named_lock(conn, "lcms:students:id", timeout_seconds=5):
            new_id = next_formatted_id(
                conn, table="Students", id_column=cfg.get("id_field", "id"), prefix="ST", width=3
            )

            values = []
            for name in q.get("params", []):
                if name == "id":
                    values.append(new_id)
                else:
                    raw = request.form.get(name, "")
                    cleaned = raw.strip() if isinstance(raw, str) else raw
                    values.append(cleaned if cleaned != "" else None)

            cur = conn.cursor(dictionary=True, buffered=True)
            cur.execute(q["sql"], values)
        conn.commit()

    finally:
        conn.close()

    flash(f"Student added. ID: {new_id}", "success")
    return redirect("/students")


@students_bp.get("/<student_id>/edit")
def edit_student(student_id: str):
    cfg = _get_config()
    fields = _fields_from_config(cfg)

    q = require_query(cfg, "get")
    params = []
    for name in q.get("params", []):
        params.append(student_id if name == "id" else request.args.get(name))

    student = fetch_one(current_app, q["sql"], params, request_source=request)
    if not student:
        flash("Student not found.", "error")
        return redirect("/students")

    return render_template(
        "students/form.html",
        title="Edit student",
        heading="Edit student",
        subheading="Update the student information.",
        fields=fields,
        student=student,
        action=f"/students/{student_id}",
        submit_label="Save changes",
    )


@students_bp.post("/<student_id>")
def update_student(student_id: str):
    cfg = _get_config()
    q = require_query(cfg, "update")

    values = []
    for name in q.get("params", []):
        if name == "id":
            values.append(student_id)
        else:
            values.append(request.form.get(name, "").strip())

    execute(current_app, q["sql"], values, request_source=request)
    flash("Student updated.", "success")
    return redirect("/students")


@students_bp.post("/<student_id>/delete")
def delete_student(student_id: str):
    cfg = _get_config()
    q = require_query(cfg, "delete")

    values = []
    for name in q.get("params", []):
        values.append(student_id if name == "id" else request.form.get(name))

    execute(current_app, q["sql"], values, request_source=request)
    flash("Student deleted.", "success")
    return redirect("/students")
