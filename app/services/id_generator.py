from contextlib import contextmanager


class IdGenerationError(RuntimeError):
    pass


@contextmanager
def mysql_named_lock(conn, name: str, timeout_seconds: int = 5):
    cur = conn.cursor(dictionary=True, buffered=True)
    acquired = False
    try:
        cur.execute("SELECT GET_LOCK(%s, %s) AS got", [name, timeout_seconds])
        row = cur.fetchone() or {}
        if row.get("got") != 1:
            raise IdGenerationError(f"Could not acquire ID lock: {name}")
        acquired = True
        yield
    finally:
        if acquired:
            cur.execute("SELECT RELEASE_LOCK(%s) AS released", [name])
            cur.fetchone()
        cur.close()


def next_formatted_id(conn, *, table: str, id_column: str, prefix: str, width: int = 3) -> str:
    """
    Generates the next ID based on the maximum numeric suffix in the table.
    Example: prefix='ST' => ST-001, ST-002, ...

    Important: To avoid duplicates under concurrent requests, call this inside
    a MySQL named lock (GET_LOCK) and insert in the same transaction/connection.
    """
    code_prefix = f"{prefix}-"
    start_pos = len(code_prefix) + 1  # MySQL SUBSTRING is 1-based
    regex = f"^{prefix}-[0-9]+$"

    cur = conn.cursor(dictionary=True, buffered=True)
    sql = (
        f"SELECT COALESCE(MAX(CAST(SUBSTRING({id_column}, {start_pos}) AS UNSIGNED)), 0) AS max_num "
        f"FROM {table} WHERE {id_column} REGEXP %s"
    )
    try:
        cur.execute(sql, [regex])
        row = cur.fetchone() or {}
    finally:
        cur.close()
    max_num = int(row.get("max_num") or 0)
    next_num = max_num + 1
    return f"{code_prefix}{str(next_num).zfill(width)}"
