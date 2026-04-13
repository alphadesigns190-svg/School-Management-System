import hmac

from flask import Blueprint, current_app, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint("auth", __name__)


def _admin_password_hash():
    # Hash once per process; store on app config.
    hashed = current_app.config.get("ADMIN_PASSWORD_HASH")
    if hashed:
        return hashed
    plain = current_app.config.get("ADMIN_PASSWORD", "")
    hashed = generate_password_hash(plain)
    current_app.config["ADMIN_PASSWORD_HASH"] = hashed
    return hashed


@auth_bp.get("/login")
def login_form():
    next_url = request.args.get("next") or "/dashboard"
    return render_template("auth/login.html", title="Login", next_url=next_url)


@auth_bp.post("/login")
def login_submit():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    next_url = request.form.get("next") or "/dashboard"

    admin_user = current_app.config.get("ADMIN_USERNAME", "admin")
    if not hmac.compare_digest(username, admin_user):
        flash("Invalid username or password.", "error")
        return redirect(f"/login?next={next_url}")

    if not check_password_hash(_admin_password_hash(), password):
        flash("Invalid username or password.", "error")
        return redirect(f"/login?next={next_url}")

    session["user"] = {"username": admin_user}
    flash("Welcome back.", "success")
    return redirect(next_url)


@auth_bp.post("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out.", "success")
    return redirect("/login")

