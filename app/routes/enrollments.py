from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request

from ..db import execute, fetch_all, fetch_one
from ..queries.loader import load_query_config, require_query
from ..services.validators import is_valid_module_id, parse_iso_date

enrollments_bp = Blueprint("enrollments", __name__, url_prefix="/enrollments")


def _get_config():
    return load_query_config("enrollments")


def _enrollment_code(enrollment_id: int) -> str:
    return f"EN-{str(enrollment_id).zfill(3)}"


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


def _student_lookup(cfg, student_id: str):
    q = require_query(cfg, "student_lookup")
    normalized = _normalize_student_id(student_id)
    return fetch_one(current_app, q["sql"], [normalized], request_source=request)


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
    courses = _courses_options(cfg)
    return render_template(
        "enrollments/form.html",
        title="Add enrollment",
        heading="Assign student to course",
        subheading="Enter student number and select a course.",
        fields=fields,
        enrollment=None,
        student_number="",
        courses=courses,
        action="/enrollments",
        submit_label="Create",
    )


@enrollments_bp.get("/student-info/<student_id>")
def student_info(student_id: str):
    cfg = _get_config()
    student = _student_lookup(cfg, student_id.strip())
    if not student:
        return jsonify({"found": False, "student": None})
    return jsonify(
        {
            "found": True,
            "student": {
                "id": student.get("id"),
                "name": student.get("name"),
                "father_name": student.get("father_name"),
                "phone": student.get("phone"),
                "status": student.get("status"),
                "course_id": student.get("course_id"),
                "course_name": student.get("course_name"),
            },
        }
    )


@enrollments_bp.post("")
def create_enrollment():
    cfg = _get_config()
    q = require_query(cfg, "insert")

    values = []
    for name in q.get("params", []):
        if name == "student_id":
            raw = _normalize_student_id(
                request.form.get("student_id", "") or request.form.get("student_number", "")
            )
        else:
            raw = request.form.get(name, "")
        if raw is None:
            values.append(None)
        else:
            cleaned = raw.strip() if isinstance(raw, str) else raw
            values.append(cleaned if cleaned != "" else None)

    if not values[0]:
        flash("Student ID is required.", "error")
        return redirect("/enrollments/new")
    if not is_valid_module_id(values[0], "ST"):
        flash("Student ID format is invalid.", "error")
        return redirect("/enrollments/new")
    if not values[1]:
        flash("Course is required.", "error")
        return redirect("/enrollments/new")
    if not is_valid_module_id(values[1], "CS"):
        flash("Course ID format is invalid.", "error")
        return redirect("/enrollments/new")
    start_date = parse_iso_date(values[2])
    end_date = parse_iso_date(values[3])
    if values[2] and start_date is None:
        flash("Start date is invalid.", "error")
        return redirect("/enrollments/new")
    if values[3] and end_date is None:
        flash("End date is invalid.", "error")
        return redirect("/enrollments/new")
    if start_date and end_date and end_date < start_date:
        flash("End date cannot be before start date.", "error")
        return redirect("/enrollments/new")
    if not _student_lookup(cfg, values[0]):
        flash("Student ID not found.", "error")
        return redirect("/enrollments/new")

    execute(current_app, q["sql"], values, request_source=request)
    flash("Enrollment added.", "success")
    return redirect("/enrollments")


@enrollments_bp.post("/new")
def create_enrollment_from_new():
    return create_enrollment()


@enrollments_bp.get("/<int:enrollment_id>/edit")
def edit_enrollment(enrollment_id: int):
    cfg = _get_config()
    fields = _fields_from_config(cfg)
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
        enrollment_code=_enrollment_code(enrollment_id),
        student_number=_student_number_from_id(enrollment.get("student_id", "")),
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

        if name == "student_id":
            raw = _normalize_student_id(
                request.form.get("student_id", "") or request.form.get("student_number", "")
            )
        else:
            raw = request.form.get(name, "")
        if raw is None:
            values.append(None)
        else:
            cleaned = raw.strip() if isinstance(raw, str) else raw
            values.append(cleaned if cleaned != "" else None)

    if not values[0]:
        flash("Student ID is required.", "error")
        return redirect(f"/enrollments/{enrollment_id}/edit")
    if not is_valid_module_id(values[0], "ST"):
        flash("Student ID format is invalid.", "error")
        return redirect(f"/enrollments/{enrollment_id}/edit")
    if not values[1]:
        flash("Course is required.", "error")
        return redirect(f"/enrollments/{enrollment_id}/edit")
    if not is_valid_module_id(values[1], "CS"):
        flash("Course ID format is invalid.", "error")
        return redirect(f"/enrollments/{enrollment_id}/edit")
    start_date = parse_iso_date(values[2])
    end_date = parse_iso_date(values[3])
    if values[2] and start_date is None:
        flash("Start date is invalid.", "error")
        return redirect(f"/enrollments/{enrollment_id}/edit")
    if values[3] and end_date is None:
        flash("End date is invalid.", "error")
        return redirect(f"/enrollments/{enrollment_id}/edit")
    if start_date and end_date and end_date < start_date:
        flash("End date cannot be before start date.", "error")
        return redirect(f"/enrollments/{enrollment_id}/edit")
    if not _student_lookup(cfg, values[0]):
        flash("Student ID not found.", "error")
        return redirect(f"/enrollments/{enrollment_id}/edit")

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
