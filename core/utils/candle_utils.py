# core/utils/candle_utils.py

from datetime import datetime, timedelta, timezone


def drop_forming_candle(df, timeframe_minutes: int):
    last_ts = df.index[-1]

    # Normalize to timezone-aware UTC
    if last_ts.tzinfo is None:
        last_ts_utc = last_ts.replace(tzinfo=timezone.utc)
    else:
        last_ts_utc = last_ts.tz_convert(timezone.utc)

    now_utc = datetime.now(timezone.utc)
    candle_close = last_ts_utc + timedelta(minutes=timeframe_minutes)

    # If candle is still forming → drop it
    if now_utc < candle_close:
        return df.iloc[:-1]

    return df
