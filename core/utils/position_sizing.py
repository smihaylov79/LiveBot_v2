# core/utils/position_sizing.py

import MetaTrader5 as mt5


def compute_position_size(symbol: str, sl_price: float, entry_price: float, risk_pct: float, info=None):
    """
    Universal position sizing formula.
    Works for Forex, indices, metals, crypto, synthetic symbols.
    """

    account = mt5.account_info()
    if account is None:
        raise RuntimeError("Cannot get MT5 account info")

    equity = account.equity
    risk_amount = equity * risk_pct

    # Use cached symbol info if provided
    if info is None:
        info = mt5.symbol_info(symbol)
        if info is None:
            raise RuntimeError(f"Symbol {symbol} not found")

    point = info.point
    tick_value = info.trade_tick_value
    tick_size = info.trade_tick_size

    # -----------------------------
    # SL DISTANCE IN POINTS
    # -----------------------------
    sl_distance_points = abs(entry_price - sl_price) / point
    if sl_distance_points <= 0:
        return 0.0

    # -----------------------------
    # VALUE PER POINT PER 1 LOT
    # -----------------------------
    value_per_point_per_lot = tick_value / tick_size

    # -----------------------------
    # POSITION SIZE
    # -----------------------------
    lots = risk_amount / (sl_distance_points * value_per_point_per_lot)

    # -----------------------------
    # BROKER LIMITS
    # -----------------------------
    lots = max(lots, info.volume_min)
    lots = min(lots, info.volume_max)

    # Round to step
    step = info.volume_step
    lots = round(lots / step) * step

    return lots


