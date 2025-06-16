from datetime import datetime, timedelta

def seconds_until_next_hour():
    now = datetime.now()
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    return (next_hour - now).total_seconds()

def seconds_until_next_quarter():
    now = datetime.now()
    # round to next 15 min mark
    next_minute = (now.minute // 15 + 1) * 15
    if next_minute == 60:
        next_time = now.replace(hour=(now.hour + 1) % 24, minute=0, second=0, microsecond=0)
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)
    return (next_time - now).total_seconds()

def seconds_until_next_half_hour():
    now = datetime.now()
    if now.minute < 30:
        next_time = now.replace(minute=30, second=0, microsecond=0)
    else:
        next_time = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    return (next_time - now).total_seconds()