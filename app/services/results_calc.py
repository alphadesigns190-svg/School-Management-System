def _to_int(value) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if text == "":
        return 0
    try:
        return int(text)
    except ValueError:
        return 0


def calculate_total_and_grade(payload: dict) -> tuple[int, str]:
    quiz1 = _to_int(payload.get("quiz1"))
    quiz2 = _to_int(payload.get("quiz2"))
    quiz3 = _to_int(payload.get("quiz3"))
    quiz4 = _to_int(payload.get("quiz4"))
    exam20 = _to_int(payload.get("exam20"))
    exam30 = _to_int(payload.get("exam30"))
    interview = _to_int(payload.get("interview"))

    total = quiz1 + quiz2 + quiz3 + quiz4 + exam20 + exam30 + interview
    grade = grade_from_total(total)
    return total, grade


def grade_from_total(total: int) -> str:
    if total >= 90:
        return "A"
    if total >= 80:
        return "B"
    if total >= 70:
        return "C"
    if total >= 60:
        return "D"
    return "F"

