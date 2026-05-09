# bots/candle_bot.py

import time
from datetime import datetime, timezone

from bots.base_bot import BaseBot
from core.market_data import MarketDataMT5
from core.broker_mt5 import BrokerMT5
from core.executor import Executor
from core.utils.time_utils import tf_to_minutes, next_candle_close
from core.utils.candle_utils import drop_forming_candle
from trading_core.candles import CandleMetrics


class CandleBot(BaseBot):
    def __init__(self, strategy_cfg, bot_cfg):
        super().__init__(strategy_cfg)
        self.bot_cfg = bot_cfg["bot"]

    def run(self):
        symbols_cfg = self.config["symbols"]

        # Determine lowest timeframe
        tf_minutes_list = [tf_to_minutes(scfg["timeframe"]) for scfg in symbols_cfg.values()]
        base_tf = min(tf_minutes_list)

        print(f"CandleBot running on base timeframe: {base_tf} minutes")

        md = MarketDataMT5(bars=500)
        broker = BrokerMT5()
        executor = Executor(broker, self.bot_cfg)

        while True:
            wake_time = next_candle_close(base_tf)
            now = datetime.now(timezone.utc)

            sleep_seconds = (wake_time - now).total_seconds()
            if sleep_seconds > 0:
                print(f"Sleeping {sleep_seconds:.1f}s until next candle close ({wake_time})")
                time.sleep(sleep_seconds + 1)

            print("\n=== New Candle Closed ===")

            for symbol, scfg in symbols_cfg.items():
                timeframe = scfg["timeframe"]
                print(f"\n--- Processing {symbol} {timeframe} ---")

                df = md.get_candles(symbol, timeframe)

                tf_minutes = tf_to_minutes(timeframe)
                df = drop_forming_candle(df, tf_minutes)
                # Add ATR using research settings
                atr_period = scfg["volatility"]["atr_period"]
                df = CandleMetrics.add_atr(df, period=atr_period)

                executor.process_symbol(symbol, timeframe, df, scfg)

            print("\nWaiting for next candle...\n")
