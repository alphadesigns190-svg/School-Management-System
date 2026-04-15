import json
import os


def _settings_path(app) -> str:
    return os.path.join(app.root_path, "data", "admin_settings.json")


def _legacy_path(app) -> str:
    return os.path.join(app.root_path, "data", "admin_account.json")


def load_admin_settings(app) -> dict:
    defaults = {
        "username": app.config.get("ADMIN_USERNAME", "admin"),
        "password_hash": app.config.get("ADMIN_PASSWORD_HASH", ""),
        "school_name": app.config.get("SCHOOL_NAME", "Learning Center"),
    }

    payload = None
    path = _settings_path(app)

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except (OSError, json.JSONDecodeError):
            payload = None
    else:
        legacy = _legacy_path(app)
        if os.path.exists(legacy):
            try:
                with open(legacy, "r", encoding="utf-8") as f:
                    payload = json.load(f)
            except (OSError, json.JSONDecodeError):
                payload = None

    if not isinstance(payload, dict):
        return defaults

    username = str(payload.get("username") or "").strip() or defaults["username"]
    password_hash = str(payload.get("password_hash") or "").strip() or defaults["password_hash"]
    school_name = str(payload.get("school_name") or "").strip() or defaults["school_name"]
    return {
        "username": username,
        "password_hash": password_hash,
        "school_name": school_name,
    }


def save_admin_settings(app, username: str, password_hash: str, school_name: str) -> dict:
    payload = {
        "username": (username or "").strip() or app.config.get("ADMIN_USERNAME", "admin"),
        "password_hash": (password_hash or "").strip() or app.config.get("ADMIN_PASSWORD_HASH", ""),
        "school_name": (school_name or "").strip() or app.config.get("SCHOOL_NAME", "Learning Center"),
    }

    path = _settings_path(app)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    app.config["ADMIN_USERNAME"] = payload["username"]
    app.config["ADMIN_PASSWORD_HASH"] = payload["password_hash"]
    app.config["SCHOOL_NAME"] = payload["school_name"]
    return payload
