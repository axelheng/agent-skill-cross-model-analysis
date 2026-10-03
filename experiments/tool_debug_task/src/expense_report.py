"""Helpers for filtering and aggregating a small expense report."""


def summarize_by_category(rows, category=None):
    """Return total amounts grouped by category.

    Categories are case-insensitive and surrounding whitespace is ignored.
    Amounts are integer cents so the function does not introduce float error.
    """
    totals = {}
    for row in rows:
        row_category = row["category"].strip().lower()
        if category is not None and row_category != category:
            continue
        totals[row_category] = totals.get(row_category, 0) + row["cents"]
    return dict(sorted(totals.items()))
