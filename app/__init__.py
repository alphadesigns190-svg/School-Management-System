from flask import Flask, redirect, render_template, request, session
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


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config())
    app.config["ADMIN_PASSWORD_HASH"] = generate_password_hash(app.config.get("ADMIN_PASSWORD", ""))

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

    @app.get("/")
    def home():
        return redirect("/dashboard")

    return app
