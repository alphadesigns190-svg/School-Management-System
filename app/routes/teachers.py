from flask import Blueprint, current_app, flash, redirect, render_template, request
from flask import jsonify

from ..db import execute, fetch_all, fetch_one
from ..queries.loader import load_query_config, require_query
from ..services.id_generator import mysql_named_lock, next_formatted_id

teachers_bp = Blueprint("teachers", __name__, url_prefix="/teachers")


def _get_config():
    return load_query_config("teachers")


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


def _search_teachers(search: str):
    like = f"%{search}%"
    sql = (
        "SELECT id, name, subject, salary, shift "
        "FROM Teachers "
        "WHERE id LIKE %s OR name LIKE %s "
        "ORDER BY id"
    )
    return fetch_all(current_app, sql, [like, like], request_source=request)


@teachers_bp.get("")
def list_teachers():
    cfg = _get_config()
    fields = _fields_from_config(cfg)
    search = (request.args.get("q") or "").strip()
    if search:
        teachers = _search_teachers(search)
    else:
        q = require_query(cfg, "list")
        teachers = fetch_all(current_app, q["sql"], q.get("params", []), request_source=request)

    return render_template(
        "teachers/list.html",
        title="Teachers",
        teachers=teachers,
        fields=fields,
        search=search,
    )


@teachers_bp.get("/_data")
def teachers_data():
    search = (request.args.get("q") or "").strip()
    if not search:
        return jsonify({"teachers": []})
    return jsonify({"teachers": _search_teachers(search)})


@teachers_bp.get("/new")
def new_teacher():
    cfg = _get_config()
    fields = _create_fields(cfg)
    return render_template(
        "teachers/form.html",
        title="Add teacher",
        heading="Add teacher",
        subheading="Teacher ID will be generated automatically (TE-001, TE-002...).",
        fields=fields,
        teacher=None,
        action="/teachers",
        submit_label="Create",
    )


@teachers_bp.post("")
def create_teacher():
    cfg = _get_config()
    q = require_query(cfg, "insert")

    from ..db import get_connection

    conn = get_connection(current_app)
    new_id = None
    try:
        conn.start_transaction()
        with mysql_named_lock(conn, "lcms:teachers:id", timeout_seconds=5):
            new_id = next_formatted_id(conn, table="Teachers", id_column="id", prefix="TE", width=3)

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

    flash(f"Teacher added. ID: {new_id}", "success")
    return redirect("/teachers")


@teachers_bp.get("/<teacher_id>/edit")
def edit_teacher(teacher_id: str):
    cfg = _get_config()
    fields = _fields_from_config(cfg)

    q = require_query(cfg, "get")
    teacher = fetch_one(current_app, q["sql"], [teacher_id], request_source=request)
    if not teacher:
        flash("Teacher not found.", "error")
        return redirect("/teachers")

    return render_template(
        "teachers/form.html",
        title="Edit teacher",
        heading="Edit teacher",
        subheading="Update the teacher information.",
        fields=fields,
        teacher=teacher,
        action=f"/teachers/{teacher_id}",
        submit_label="Save changes",
    )


@teachers_bp.post("/<teacher_id>")
def update_teacher(teacher_id: str):
    cfg = _get_config()
    q = require_query(cfg, "update")

    values = []
    for name in q.get("params", []):
        if name == "id":
            values.append(teacher_id)
        else:
            raw = request.form.get(name, "")
            values.append(raw.strip() if isinstance(raw, str) else raw)

    execute(current_app, q["sql"], values, request_source=request)
    flash("Teacher updated.", "success")
    return redirect("/teachers")


@teachers_bp.post("/<teacher_id>/delete")
def delete_teacher(teacher_id: str):
    cfg = _get_config()
    q = require_query(cfg, "delete")

    execute(current_app, q["sql"], [teacher_id], request_source=request)
    flash("Teacher deleted.", "success")
    return redirect("/teachers")
