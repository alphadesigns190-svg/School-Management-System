from flask import Blueprint, current_app, jsonify

from ..db import get_connection

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@health_bp.get("/db/ping")
def db_ping():
    conn = get_connection(current_app)
    try:
        conn.execute("SELECT 1")
        return jsonify({"db": "ok"})
    finally:
        conn.close()
