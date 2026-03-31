# core/utils/time_utils.py

from datetime import datetime, timedelta, timezone


def tf_to_minutes(tf: str) -> int:
    return int(tf.replace("M", ""))


def next_candle_close(tf_minutes: int) -> datetime:
    now = datetime.now(timezone.utc)
    minute = (now.minute // tf_minutes) * tf_minutes
    last_close = now.replace(minute=minute, second=0, microsecond=0)
    return last_close + timedelta(minutes=tf_minutes)
