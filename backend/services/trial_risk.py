"""Shared trial risk categorization logic.

Used by both the daily cron job and the admin dashboard endpoint.
"""


def categorize_trial_risk(searches: int, total_value: float, trial_day: int) -> str:
    """Categorize a trial user's risk level.

    Returns: 'critical', 'at_risk', or 'healthy'
    """
    if searches == 0 and trial_day >= 2:
        return "critical"
    if searches <= 3 and total_value < 100_000 and trial_day >= 5:
        return "at_risk"
    return "healthy"
