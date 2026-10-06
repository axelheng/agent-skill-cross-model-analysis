def parse_amount(text):
    """Parse a decimal amount such as '$12.50' into integer cents."""
    return int(float(text.split()[0].replace("$", "")) * 100)
