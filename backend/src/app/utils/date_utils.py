from datetime import datetime, date, time

def parse_date(value: str) -> date:
    """Parse YYYY-MM-DD string -> date object."""
    return datetime.strptime(value, "%Y-%m-%d").date()

def parse_time(value: str) -> time:
    """Parse HH:MM string -> time object."""
    return datetime.strptime(value, "%H:%M").time()
