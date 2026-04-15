import re
from datetime import date


PHONE_ALLOWED_RE = re.compile(r"^\+?[0-9\s\-()]+$")
ID_RE = re.compile(r"^[A-Z]{2}-[0-9]{3,}$")


def clean_text(value: str | None, max_length: int | None = None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if cleaned == "":
        return None
    if max_length and len(cleaned) > max_length:
        return cleaned[:max_length]
    return cleaned


def normalize_phone(value: str | None) -> str | None:
    cleaned = clean_text(value)
    if not cleaned:
        return None
    if not PHONE_ALLOWED_RE.match(cleaned):
        return None

    if cleaned.startswith("+"):
        digits = re.sub(r"\D", "", cleaned[1:])
        normalized = f"+{digits}" if digits else ""
    else:
        digits = re.sub(r"\D", "", cleaned)
        normalized = digits
    return normalized or None


def is_valid_phone(value: str | None) -> bool:
    normalized = normalize_phone(value)
    if not normalized:
        return False
    digit_count = len(re.sub(r"\D", "", normalized))
    return 9 <= digit_count <= 15


def parse_non_negative_int(value: str | None):
    cleaned = clean_text(value)
    if cleaned is None:
        return None
    if not cleaned.isdigit():
        return None
    return int(cleaned)


def parse_iso_date(value: str | None):
    cleaned = clean_text(value)
    if not cleaned:
        return None
    try:
        return date.fromisoformat(cleaned)
    except ValueError:
        return None


def is_valid_module_id(value: str | None, prefix: str) -> bool:
    cleaned = clean_text(value)
    if not cleaned:
        return False
    return bool(ID_RE.match(cleaned.upper()) and cleaned.upper().startswith(f"{prefix.upper()}-"))
