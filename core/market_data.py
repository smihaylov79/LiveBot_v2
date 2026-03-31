from datetime import datetime, timedelta
from typing import Literal

import MetaTrader5 as mt5
import pandas as pd


TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
}


class MarketDataMT5:
    def __init__(self, bars: int = 500):
        self.bars = bars

    def _ensure_initialized(self):
        if not mt5.initialize():
            raise RuntimeError(f"MT5 initialize() failed, error: {mt5.last_error()}")

    def get_candles(self, symbol: str, timeframe: str) -> pd.DataFrame:
        self._ensure_initialized()

        tf = TIMEFRAME_MAP[timeframe]
        utc_to = datetime.utcnow()
        utc_from = utc_to - timedelta(days=10)  # enough history for 500 bars

        # rates = mt5.copy_rates_from(symbol, tf, utc_to, self.bars)
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, self.bars)

        if rates is None or len(rates) == 0:
            raise RuntimeError(f"No rates for {symbol} {timeframe}")

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.set_index("time", inplace=True)
        df.rename(columns={"real_volume": "volume"}, inplace=True)

        # debug

        # # --- DEBUG: MT5 status ---
        # info = mt5.symbol_info(symbol)
        # tick = mt5.symbol_info_tick(symbol)
        #
        # server_dt = None
        # if tick and tick.time:
        #     server_dt = datetime.utcfromtimestamp(tick.time)
        #
        # print(f"\n=== DEBUG {symbol} {timeframe} ===")
        # print(f"Bars returned: {len(df)}")
        #
        # print(f"Last candle timestamp (UTC): {df.index[-1]}")
        # print(f"Local time now: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        # print(f"MT5 server time (UTC): {server_dt}")
        #
        # if tick:
        #     print(f"Last tick time (UTC): {datetime.utcfromtimestamp(tick.time)}")
        #     print(f"Last tick bid/ask: {tick.bid} / {tick.ask}")
        # else:
        #     print("No tick data received!")
        #
        # print(f"Symbol visible: {info.visible if info else 'N/A'}")
        # print(f"Symbol info: {info}")
        # print("-" * 60)

        return df[["open", "high", "low", "close", "tick_volume"]].rename(
            columns={"tick_volume": "volume"}
        )
