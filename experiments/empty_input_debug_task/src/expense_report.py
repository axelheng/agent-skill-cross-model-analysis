def average(values):
    """Return the arithmetic mean, or None when there are no values."""
    if not values:
        return None
    return sum(values) / len(values)
