from datetime import timedelta


def duration_str_to_seconds(duration_str):
    hours, minutes, seconds = map(float, duration_str.split(':'))
    duration_td = timedelta(hours=hours, minutes=minutes, seconds=seconds)
    return duration_td.total_seconds()


def normalize_preferences(preferences: dict) -> dict:
    total_seconds = sum(preferences.values())
    if total_seconds > 0:
        return {category: (seconds / total_seconds) * 100 for category, seconds in preferences.items()}
    return preferences
