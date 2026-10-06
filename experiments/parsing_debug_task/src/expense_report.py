def parse_amount(text):
    """Parse a decimal amount such as '$12.50' into integer cents."""
    if not text.startswith("$"):
        raise ValueError(f"Invalid currency format: {text}")
    return int(float(text.split()[0].replace("$", "")) * 100)
