"""CRT robot: data layer, look-ahead-safe multi-timeframe view, ICT/CRT
primitives and a validated event-driven backtester.

All trading logic works in New York time. Candles are built on the MT5
broker clock (New York time + 7 hours, i.e. GMT+2 winter / GMT+3 summer).
"""

__version__ = "0.1.0"
