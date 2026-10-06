def percentage(part, total):
    """Return part as a percentage of total, including a safe zero case."""
    if total == 0:
        return 0
    return part / total * 100
