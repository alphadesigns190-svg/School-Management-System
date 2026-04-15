import hmac

from flask import Blueprint, current_app, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from ..services.admin_settings import load_admin_settings, save_admin_settings

auth_bp = Blueprint("auth", __name__)


def _admin_password_hash():
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

    settings = load_admin_settings(current_app)
    admin_user = settings["username"]
    admin_hash = settings["password_hash"] or _admin_password_hash()

    if not hmac.compare_digest(username, admin_user):
        flash("Invalid username or password.", "error")
        return redirect(f"/login?next={next_url}")

    if not check_password_hash(admin_hash, password):
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


@auth_bp.get("/account")
def account_settings():
    settings = load_admin_settings(current_app)
    return render_template(
        "auth/account.html",
        title="Account Settings",
        admin_username=settings["username"],
        school_name=settings["school_name"],
    )


@auth_bp.post("/account")
def update_account_settings():
    current_password = request.form.get("current_password") or ""
    new_username = (request.form.get("username") or "").strip()
    new_school_name = (request.form.get("school_name") or "").strip()
    new_password = request.form.get("new_password") or ""
    confirm_password = request.form.get("confirm_password") or ""

    settings = load_admin_settings(current_app)
    admin_hash = settings["password_hash"] or _admin_password_hash()

    if not check_password_hash(admin_hash, current_password):
        flash("Current password is incorrect.", "error")
        return redirect("/account")

    if not new_username:
        flash("Username is required.", "error")
        return redirect("/account")
    if len(new_username) < 3 or len(new_username) > 50:
        flash("Username must be between 3 and 50 characters.", "error")
        return redirect("/account")

    if not new_school_name:
        flash("School name is required.", "error")
        return redirect("/account")
    if len(new_school_name) > 100:
        flash("School name must be 100 characters or less.", "error")
        return redirect("/account")

    next_hash = admin_hash
    if new_password:
        if len(new_password) < 6:
            flash("New password must be at least 6 characters.", "error")
            return redirect("/account")
        if new_password != confirm_password:
            flash("New password and confirm password do not match.", "error")
            return redirect("/account")
        next_hash = generate_password_hash(new_password)

    save_admin_settings(
        current_app,
        username=new_username,
        password_hash=next_hash,
        school_name=new_school_name,
    )
    session["user"] = {"username": new_username}
    flash("Account settings updated.", "success")
    return redirect("/account")
