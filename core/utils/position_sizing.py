# core/utils/position_sizing.py

import MetaTrader5 as mt5


def compute_position_size(symbol: str, sl_price: float, entry_price: float, risk_pct: float):
    """
    Risk-based position sizing.
    Supports hedging accounts.
    """

    account = mt5.account_info()
    if account is None:
        raise RuntimeError("Cannot get MT5 account info")

    equity = account.equity
    risk_amount = equity * risk_pct

    sl_distance = abs(entry_price - sl_price)
    if sl_distance <= 0:
        return 0.0

    info = mt5.symbol_info(symbol)
    if info is None:
        raise RuntimeError(f"Symbol {symbol} not found")

    tick_value = info.trade_tick_value
    tick_size = info.trade_tick_size

    value_per_price_unit = tick_value / tick_size

    lots = risk_amount / (sl_distance * value_per_price_unit)

    # Respect broker limits
    lots = max(lots, info.volume_min)
    lots = min(lots, info.volume_max)

    # Round to step
    step = info.volume_step
    lots = round(lots / step) * step

    return lots
