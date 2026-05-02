import re
from contextlib import contextmanager


class IdGenerationError(RuntimeError):
    pass


def _safe_identifier(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name or ""):
        raise IdGenerationError(f"Unsafe identifier: {name}")
    return name


@contextmanager
def mysql_named_lock(conn, name: str, timeout_seconds: int = 5):
    started = False
    try:
        if not conn.in_transaction:
            conn.execute("BEGIN IMMEDIATE")
            started = True
        yield
    except Exception:
        if started and conn.in_transaction:
            conn.rollback()
        raise


def next_formatted_id(conn, *, table: str, id_column: str, prefix: str, width: int = 3) -> str:
    table_name = _safe_identifier(table)
    id_col = _safe_identifier(id_column)
    code_prefix = f"{prefix}-"

    cur = conn.cursor()
    try:
        cur.execute(
            f"SELECT {id_col} FROM {table_name} WHERE {id_col} LIKE ?",
            [f"{code_prefix}%"],
        )
        rows = cur.fetchall()
    finally:
        cur.close()

    max_num = 0
    for row in rows:
        value = row[0] if isinstance(row, (tuple, list)) else row[id_col]
        text = str(value or "")
        if not text.startswith(code_prefix):
            continue
        suffix = text[len(code_prefix):]
        if not suffix.isdigit():
            continue
        max_num = max(max_num, int(suffix))

    next_num = max_num + 1
    return f"{code_prefix}{str(next_num).zfill(width)}"
