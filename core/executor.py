from typing import Dict, Any

import pandas as pd

from trading_core.live_signals import LiveSignalGenerator
from core.broker_mt5 import BrokerMT5
from core.utils.position_sizing import compute_position_size
import MetaTrader5 as mt5


class Executor:
    def __init__(self, broker: BrokerMT5, bot_cfg: dict):
        self.broker = broker
        self.bot_cfg = bot_cfg

    def _compute_sl_tp_atr(self, df, signal, strategy_cfg):
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

    def _compute_sl_tp(self, df, signal, strategy_cfg):
        """
        Zone-based SL/TP with ATR fallback.
        """

        price = signal["price"]
        zones = signal.get("zones", [])

        # Separate demand (support) and supply (resistance)
        demand = [z["level"] for z in zones if z["type"] == "demand"]
        supply = [z["level"] for z in zones if z["type"] == "supply"]

        sl = None
        tp = None

        # -----------------------------
        # ZONE-BASED SL/TP
        # -----------------------------
        if signal["direction"] == "long":
            # SL = nearest demand zone below price
            sl_candidates = [z for z in demand if z < price]
            if sl_candidates:
                sl = max(sl_candidates)

            # TP = nearest supply zone above price
            tp_candidates = [z for z in supply if z > price]
            if tp_candidates:
                tp = min(tp_candidates)

        elif signal["direction"] == "short":
            # SL = nearest supply zone above price
            sl_candidates = [z for z in supply if z > price]
            if sl_candidates:
                sl = min(sl_candidates)

            # TP = nearest demand zone below price
            tp_candidates = [z for z in demand if z < price]
            if tp_candidates:
                tp = max(tp_candidates)

        # -----------------------------
        # VALIDATION
        # -----------------------------
        if sl is not None and tp is not None:
            # Optional: enforce minimum distances
            min_dist = strategy_cfg.get("min_sl_tp_distance", 0)
            if abs(price - sl) >= min_dist and abs(tp - price) >= min_dist:
                print(f"{signal['symbol']} → Using ZONE-based SL/TP")
                return sl, tp

        # -----------------------------
        # FALLBACK TO ATR
        # -----------------------------
        print(f"{signal['symbol']} → No valid zone SL/TP → using ATR fallback")
        return self._compute_sl_tp_atr(df, signal, strategy_cfg)

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


        # --- SAFETY CHECK 1: Max open positions per symbol ---
        max_pos = self.bot_cfg.get("max_open_positions", 5)
        positions = mt5.positions_get(symbol=symbol)

        if positions and len(positions) >= max_pos:
            print(f"{symbol} → max open positions reached ({max_pos}), skipping")
            return

        # --- SAFETY CHECK 2: Margin usage limit ---
        account = mt5.account_info()
        if account is None:
            print("Cannot get account info, skipping trade")
            return

        margin_used_pct = account.margin / account.equity if account.equity > 0 else 1

        max_margin_used = self.bot_cfg.get("max_margin_used", 0.7)
        if margin_used_pct > max_margin_used:
            print(f"{symbol} → margin usage {margin_used_pct:.2f} exceeds limit {max_margin_used}, skipping")
            return

        # --- SAFETY CHECK 3: Free margin check for this trade ---
        order_type = mt5.ORDER_TYPE_BUY if signal["direction"] == "long" else mt5.ORDER_TYPE_SELL

        margin_required = mt5.order_calc_margin(
            order_type,
            symbol,
            volume,
            signal["price"]
        )

        if margin_required is None:
            print(f"{symbol} → cannot calculate margin, skipping")
            return

        if margin_required > account.margin_free:
            print(f"{symbol} → not enough free margin ({account.margin_free}), required {margin_required}, skipping")
            return

        print(f"{symbol} {timeframe} → {signal['direction']} | score={signal['total_score']} conf={signal['confidence']:.2f}")
        print(f"SL={sl}, TP={tp}")
        comment = f"{signal['direction']}|S:{signal['total_score']}|C:{signal['confidence']:.2f}"

        info = mt5.symbol_info(symbol)

        print("\n--- Position Sizing Debug ---")
        print(f"Symbol: {symbol}")
        print(f"Contract size: {info.trade_contract_size}")
        print(f"Point size: {info.point}")
        print(f"Tick value: {info.trade_tick_value}")
        print(f"Tick size: {info.trade_tick_size}")
        print(f"SL distance (points): {abs(signal['price'] - sl) / info.point}")
        print(f"Risk amount: {account.equity * risk_pct}")
        print(f"Computed lot size: {volume}")
        print("-----------------------------\n")

        result = self.broker.send_market_order(
            symbol=symbol,
            direction=signal["direction"],
            volume=volume,
            sl=sl,
            tp=tp,
            comment=comment
        )

        if result.success:
            print(f"Order sent, ticket={result.ticket}")
        else:
            print(f"Order failed: {result.error}")
