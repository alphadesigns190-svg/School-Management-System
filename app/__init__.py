from flask import Flask, flash, jsonify, redirect, render_template, request, session
from mysql.connector.errors import DatabaseError, IntegrityError
from werkzeug.security import generate_password_hash

from .config import Config
from .routes.health import health_bp
from .routes.auth import auth_bp
from .routes.dashboard import dashboard_bp
from .routes.students import students_bp
from .routes.teachers import teachers_bp
from .routes.courses import courses_bp
from .routes.enrollments import enrollments_bp
from .routes.payments import payments_bp
from .routes.results import results_bp
from .routes.reports import reports_bp
from .services.admin_settings import load_admin_settings


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config())
    app.config["ADMIN_PASSWORD_HASH"] = generate_password_hash(app.config.get("ADMIN_PASSWORD", ""))

    persisted = load_admin_settings(app)
    app.config["ADMIN_USERNAME"] = persisted["username"]
    app.config["ADMIN_PASSWORD_HASH"] = persisted["password_hash"]
    app.config["SCHOOL_NAME"] = persisted["school_name"]

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(teachers_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(enrollments_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(results_bp)
    app.register_blueprint(reports_bp)

    @app.context_processor
    def inject_branding():
        return {"school_name": app.config.get("SCHOOL_NAME", "Learning Center")}

    @app.template_filter("afn")
    def afn(value):
        if value is None or value == "":
            return "؋\u00a0\u00a00"
        try:
            amount = int(value)
            return f"؋\u00a0\u00a0{amount:,}"
        except (TypeError, ValueError):
            return f"؋\u00a0\u00a0{value}"

    @app.before_request
    def require_login():
        path = request.path or ""
        if path.startswith("/static/"):
            return None
        if path in ("/login", "/health", "/db/ping"):
            return None

        if not session.get("user"):
            next_url = request.full_path if request.query_string else request.path
            return redirect(f"/login?next={next_url}")
        return None

    @app.errorhandler(RuntimeError)
    def handle_runtime_error(err):
        return render_template("error.html", title="Configuration needed", message=str(err)), 500

    def _wants_json():
        path = request.path or ""
        if path.endswith("/_data") or "/student-info/" in path:
            return True
        best = request.accept_mimetypes.best_match(["application/json", "text/html"])
        return best == "application/json"

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(err):
        errno = getattr(err, "errno", None)
        if errno == 1451:
            message = "You cannot delete or update this entry because it is used elsewhere."
        elif errno == 1452:
            message = "This action references missing related data. Please check linked records."
        elif errno == 1062:
            message = "This value already exists. Please use a unique value."
        else:
            message = "Database integrity error. Please check related data and try again."

        if _wants_json():
            return jsonify({"ok": False, "error": message}), 400

        flash(message, "error")
        return redirect(request.referrer or "/dashboard")

    @app.errorhandler(DatabaseError)
    def handle_database_error(err):
        message = "A database error occurred. Please try again."
        if _wants_json():
            return jsonify({"ok": False, "error": message}), 500
        flash(message, "error")
        return redirect(request.referrer or "/dashboard")

    @app.get("/")
    def home():
        return redirect("/dashboard")

    return app
