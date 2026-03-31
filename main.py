from bots.candle_bot import CandleBot
from core.config_loader import LiveConfigLoader
# from core.market_data import MarketDataMT5
# from core.broker_mt5 import BrokerMT5
# from core.executor import Executor
# from datetime import datetime, timedelta, timezone


# def drop_forming_candle(df, timeframe_minutes: int):
#     last_ts = df.index[-1]
#
#     # Normalize last_ts to timezone-aware UTC
#     if getattr(last_ts, "tzinfo", None) is None:
#         last_ts_utc = last_ts.replace(tzinfo=timezone.utc)
#     else:
#         last_ts_utc = last_ts.tz_convert(timezone.utc)
#
#     now_utc = datetime.now(timezone.utc)
#     candle_close = last_ts_utc + timedelta(minutes=timeframe_minutes)
#
#     # If candle is still forming → drop it
#     if now_utc < candle_close:
#         return df.iloc[:-1]
#
#     return df


# def run_once():
#     cfg = LiveConfigLoader().load()
#     symbols_cfg = cfg["symbols"]
#
#     md = MarketDataMT5(bars=500)
#     broker = BrokerMT5()
#     executor = Executor(broker)
#
#     for symbol, scfg in symbols_cfg.items():
#         timeframe = scfg["timeframe"]
#         print(f"\n=== {symbol} {timeframe} ===")
#
#         df = md.get_candles(symbol, timeframe)
#
#         # Convert timeframe string to minutes
#         tf_minutes = int(timeframe.replace("M", ""))
#
#         df = drop_forming_candle(df, tf_minutes)
#
#         # --- DEBUG: Print last candle timestamp ---
#         last_ts = df.index[-1]
#         last_row = df.iloc[-1]
#
#         print(f"Last candle for {symbol} {timeframe}:")
#         print(f"  Timestamp: {last_ts}  (UTC)")
#         print(f"  OHLC: {last_row['open']}, {last_row['high']}, {last_row['low']}, {last_row['close']}")
#         print(f"  Local time now: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
#         print("-" * 50)
#
#         executor.process_symbol(symbol, timeframe, df, scfg)


if __name__ == "__main__":
    strategy_cfg = LiveConfigLoader("config/live_settings.yaml").load()
    bot_cfg = LiveConfigLoader("config/bot_configs/candle_bot.yaml").load()

    bot = CandleBot(strategy_cfg, bot_cfg)
    bot.run()
