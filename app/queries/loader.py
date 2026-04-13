import json
from pathlib import Path


_cache = {}


def load_query_config(name: str) -> dict:
    if name in _cache:
        return _cache[name]

    base_dir = Path(__file__).resolve().parent
    path = base_dir / f"{name}.json"
    if not path.exists():
        raise RuntimeError(
            f"Missing query config: {path}. Create it (see app/queries/students.json)."
        )

    cfg = json.loads(path.read_text(encoding="utf-8"))
    _cache[name] = cfg
    return cfg


def require_query(cfg: dict, key: str) -> dict:
    q = (cfg.get("queries") or {}).get(key) or {}
    sql = (q.get("sql") or "").strip()
    if not sql:
        raise RuntimeError(
            f"SQL for '{key}' is empty. Fill it in app/queries/students.json (queries.{key}.sql)."
        )
    return q

