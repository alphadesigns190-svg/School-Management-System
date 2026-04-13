import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool


_pool = None


def init_pool(app):
    global _pool
    if _pool is not None:
        return

    _pool = MySQLConnectionPool(
        pool_name="lcms_pool",
        pool_size=5,
        host=app.config["MYSQL_HOST"],
        port=app.config["MYSQL_PORT"],
        user=app.config["MYSQL_USER"],
        password=app.config["MYSQL_PASSWORD"],
        database=app.config["MYSQL_DATABASE"],
    )


def get_connection(app):
    if _pool is None:
        init_pool(app)
    return _pool.get_connection()


def get_cursor(conn):
    return conn.cursor(dictionary=True, buffered=True)


def fetch_all(app, sql: str, params=None, request_source=None):
    conn = get_connection(app)
    try:
        cur = get_cursor(conn)
        cur.execute(sql, params or [])
        return cur.fetchall()
    finally:
        conn.close()


def fetch_one(app, sql: str, params=None, request_source=None):
    conn = get_connection(app)
    try:
        cur = get_cursor(conn)
        cur.execute(sql, params or [])
        return cur.fetchone()
    finally:
        conn.close()


def execute(app, sql: str, params=None, request_source=None):
    conn = get_connection(app)
    try:
        cur = get_cursor(conn)
        cur.execute(sql, params or [])
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()
