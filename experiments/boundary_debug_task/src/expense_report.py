def clamp_score(score, low=0, high=100):
    """Clamp an integer score to the inclusive range [low, high]."""
    return min(max(score, low), high)
