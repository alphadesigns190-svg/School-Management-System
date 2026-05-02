import os
import sqlite3
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

TABLE_ORDER = ["Students", "Teachers", "Courses", "Enrollments", "Payments", "Results"]

CREATE_TABLE_SQL = {
    "Students": """
        CREATE TABLE IF NOT EXISTS Students (
            id VARCHAR(10) PRIMARY KEY,
            name VARCHAR(50),
            father_name VARCHAR(50),
            phone VARCHAR(15),
            status VARCHAR(20)
        )
    """,
    "Teachers": """
        CREATE TABLE IF NOT EXISTS Teachers (
            id VARCHAR(10) PRIMARY KEY,
            name VARCHAR(50),
            subject VARCHAR(50),
            salary INT,
            shift VARCHAR(20)
        )
    """,
    "Courses": """
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
    "Enrollments": """
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
    "Payments": """
        CREATE TABLE IF NOT EXISTS Payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id VARCHAR(10),
            amount INT,
            payment_date DATE,
            FOREIGN KEY (student_id) REFERENCES Students(id)
        )
    """,
    "Results": """
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
}


def sqlite_path() -> str:
    raw = os.getenv("SQLITE_PATH", "data/learning_center.sqlite3")
    base = Path(__file__).resolve().parents[1]
    path = Path(raw)
    if not path.is_absolute():
        path = base / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def mysql_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "LearningCenter"),
    )


def create_sqlite_schema(conn: sqlite3.Connection):
    conn.execute("PRAGMA foreign_keys = ON")
    for table in TABLE_ORDER:
        conn.execute(CREATE_TABLE_SQL[table])
    conn.commit()


def migrate_table(mysql_cur, sqlite_conn: sqlite3.Connection, table: str):
    mysql_cur.execute(f"SELECT * FROM {table}")
    rows = mysql_cur.fetchall()
    cols = [c[0] for c in mysql_cur.description]

    sqlite_conn.execute(f"DELETE FROM {table}")
    if not rows:
        return 0

    placeholders = ", ".join(["?"] * len(cols))
    col_sql = ", ".join(cols)
    insert_sql = f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})"
    sqlite_conn.executemany(insert_sql, rows)
    return len(rows)


def main():
    load_dotenv()

    mysql_conn = mysql_connection()
    sqlite_conn = sqlite3.connect(sqlite_path())

    try:
        sqlite_conn.execute("PRAGMA foreign_keys = OFF")
        create_sqlite_schema(sqlite_conn)

        mysql_cur = mysql_conn.cursor()
        counts = {}
        for table in TABLE_ORDER:
            counts[table] = migrate_table(mysql_cur, sqlite_conn, table)

        sqlite_conn.execute("PRAGMA foreign_keys = ON")
        sqlite_conn.commit()

        print("Migration completed:")
        for table in TABLE_ORDER:
            print(f"- {table}: {counts[table]} rows")
        print(f"SQLite DB: {sqlite_path()}")
    finally:
        sqlite_conn.close()
        mysql_conn.close()


if __name__ == "__main__":
    main()
