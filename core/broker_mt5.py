from dataclasses import dataclass
from typing import Optional

import MetaTrader5 as mt5


@dataclass
class OrderResult:
    success: bool
    ticket: Optional[int]
    error: Optional[str]


class BrokerMT5:
    def __init__(self):
        if not mt5.initialize():
            raise RuntimeError(f"MT5 initialize() failed, error: {mt5.last_error()}")

    def _symbol_info(self, symbol: str):
        info = mt5.symbol_info(symbol)
        if info is None:
            raise RuntimeError(f"Symbol {symbol} not found")
        if not info.visible:
            mt5.symbol_select(symbol, True)
        return info

    def send_market_order(
        self,
        symbol: str,
        direction: str,  # "long" or "short"
        volume: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
    ) -> OrderResult:
        self._symbol_info(symbol)

        if direction == "long":
            order_type = mt5.ORDER_TYPE_BUY
        elif direction == "short":
            order_type = mt5.ORDER_TYPE_SELL
        else:
            return OrderResult(False, None, f"Invalid direction: {direction}")

        price = mt5.symbol_info_tick(symbol).ask if direction == "long" else mt5.symbol_info_tick(symbol).bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl or 0.0,
            "tp": tp or 0.0,
            "deviation": 20,
            "magic": 123456,
            "comment": "LiveBot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        result = mt5.order_send(request)
        if result is None:
            return OrderResult(False, None, f"order_send() failed: {mt5.last_error()}")

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return OrderResult(False, None, f"retcode={result.retcode}, comment={result.comment}")

        return OrderResult(True, result.order, None)
