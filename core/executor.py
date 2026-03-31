from typing import Dict, Any

import pandas as pd

from trading_core.live_signals import LiveSignalGenerator
from core.broker_mt5 import BrokerMT5
from core.utils.position_sizing import compute_position_size


class Executor:
    def __init__(self, broker: BrokerMT5, bot_cfg: dict):
        self.broker = broker
        self.bot_cfg = bot_cfg

    def _compute_sl_tp(
        self,
        df: pd.DataFrame,
        signal: Dict[str, Any],
        strategy_cfg: Dict[str, Any],
    ):
        # assumes ATR already in df["atr"] from volatility module
        last = df.iloc[-1]
        atr = last.get("atr", None)
        if atr is None:
            return None, None

        price = signal["price"]
        sl_mult = strategy_cfg["sl_atr_multiplier"]
        tp_mult = strategy_cfg["tp_atr_multiplier"]

        if signal["direction"] == "long":
            sl = price - sl_mult * atr
            tp = price + tp_mult * atr
        elif signal["direction"] == "short":
            sl = price + sl_mult * atr
            tp = price - tp_mult * atr
        else:
            return None, None

        return sl, tp

    def process_symbol(
        self,
        symbol: str,
        timeframe: str,
        df: pd.DataFrame,
        symbol_cfg: Dict[str, Any],
    ):
        lsg = LiveSignalGenerator(symbol_cfg)
        signal = lsg.generate(df, symbol, timeframe)

        print("Raw signal:", signal)

        strat = symbol_cfg["strategy"]

        # basic filters
        if signal["direction"] == "neutral":
            print(symbol, timeframe, "→ neutral, no trade")
            return

        if abs(signal["total_score"]) < strat["min_score"]:
            print(symbol, timeframe, "→ score too low")
            return

        if signal["confidence"] < strat["min_confidence"]:
            print(symbol, timeframe, "→ confidence too low")
            return

        if strat["require_trend_alignment"] and signal["trend_score"] * signal["total_score"] <= 0:
            print(symbol, timeframe, "→ trend misaligned")
            return

        sl, tp = self._compute_sl_tp(df, signal, strat)
        if sl is None or tp is None:
            print(symbol, timeframe, "→ cannot compute SL/TP")
            return

        risk_pct = self.bot_cfg.get("risk_per_trade", 0.01)

        volume = compute_position_size(
            symbol=symbol,
            sl_price=sl,
            entry_price=signal["price"],
            risk_pct=risk_pct,
        )

        print(f"Position size: {volume} lots")

        print(f"{symbol} {timeframe} → {signal['direction']} | score={signal['total_score']} conf={signal['confidence']:.2f}")
        print(f"SL={sl}, TP={tp}")

        result = self.broker.send_market_order(
            symbol=symbol,
            direction=signal["direction"],
            volume=volume,
            sl=sl,
            tp=tp,
        )

        if result.success:
            print(f"Order sent, ticket={result.ticket}")
        else:
            print(f"Order failed: {result.error}")
