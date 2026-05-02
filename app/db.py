import os
import sqlite3

from .services.runtime_paths import resolve_data_path

_SCHEMA_READY = False

SCHEMA_SQL = [
    """
    CREATE TABLE IF NOT EXISTS Students (
        id VARCHAR(10) PRIMARY KEY,
        name VARCHAR(50),
        father_name VARCHAR(50),
        phone VARCHAR(15),
        status VARCHAR(20)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Teachers (
        id VARCHAR(10) PRIMARY KEY,
        name VARCHAR(50),
        subject VARCHAR(50),
        salary INT,
        shift VARCHAR(20)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Courses (
        id VARCHAR(10) PRIMARY KEY,
        course_name VARCHAR(50),
        fee INT,
        duration VARCHAR(20),
        shift VARCHAR(20),
        teacher_id VARCHAR(10),
        FOREIGN KEY (teacher_id) REFERENCES Teachers(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id VARCHAR(10),
        course_id VARCHAR(10),
        start_date DATE,
        end_date DATE,
        FOREIGN KEY (student_id) REFERENCES Students(id),
        FOREIGN KEY (course_id) REFERENCES Courses(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id VARCHAR(10),
        amount INT,
        payment_date DATE,
        FOREIGN KEY (student_id) REFERENCES Students(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id VARCHAR(10),
        month VARCHAR(20),
        quiz1 INT,
        quiz2 INT,
        quiz3 INT,
        quiz4 INT,
        exam20 INT,
        exam30 INT,
        interview INT,
        total_marks INT,
        grade VARCHAR(5),
        FOREIGN KEY (student_id) REFERENCES Students(id)
    )
    """,
]


def _sqlite_path(app):
    raw = app.config.get("SQLITE_PATH") or "data/learning_center.sqlite3"
    if os.path.isabs(raw):
        return raw
    return str(resolve_data_path(raw))


def adapt_sql(sql: str) -> str:
    return sql.replace("%s", "?")


def init_sqlite_schema(app):
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return

    db_path = _sqlite_path(app)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        for statement in SCHEMA_SQL:
            conn.execute(statement)
        conn.commit()
        _SCHEMA_READY = True
    finally:
        conn.close()


def get_connection(app):
    init_sqlite_schema(app)
    conn = sqlite3.connect(_sqlite_path(app), timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _to_dict(row):
    if row is None:
        return None
    if isinstance(row, sqlite3.Row):
        return dict(row)
    return row


def fetch_all(app, sql: str, params=None, request_source=None):
    conn = get_connection(app)
    try:
        cur = conn.cursor()
        cur.execute(adapt_sql(sql), params or [])
        rows = cur.fetchall()
        return [_to_dict(r) for r in rows]
    finally:
        conn.close()


def fetch_one(app, sql: str, params=None, request_source=None):
    conn = get_connection(app)
    try:
        cur = conn.cursor()
        cur.execute(adapt_sql(sql), params or [])
        row = cur.fetchone()
        return _to_dict(row)
    finally:
        conn.close()


def execute(app, sql: str, params=None, request_source=None):
    conn = get_connection(app)
    try:
        cur = conn.cursor()
        cur.execute(adapt_sql(sql), params or [])
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()
