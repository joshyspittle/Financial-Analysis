"""Technical indicator helpers.

The functions in this module are intentionally simple and mostly stateless.
They accept a close-price Series or DataFrame and return a transformed object
with the same index.
"""

import pandas as pd


def sma(close_data: pd.Series | pd.DataFrame, window: int = 21) -> pd.Series | pd.DataFrame:
    """Return the simple moving average over ``window`` periods."""

    return close_data.rolling(window).mean()


def ema(close_data: pd.Series | pd.DataFrame, window: int = 21) -> pd.Series | pd.DataFrame:
    """Return the exponential moving average over ``window`` periods."""

    return close_data.ewm(span=window, adjust=False).mean()


def rsi(close_data: pd.Series | pd.DataFrame, window: int = 14) -> pd.Series | pd.DataFrame:
    """Return the relative strength index over ''window'' periods."""

    delta = close_data.diff()
    gains = delta.clip(lower=0)
    losses = delta.clip(upper=0).abs()

    avg_gain = gains.ewm(alpha=1/window, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1/window, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.dropna()


def macd(close_data: pd.Series | pd.DataFrame, fast_window: int = 12, slow_window: int = 26, signal_window: int = 9) -> pd.DataFrame:
    """Return the moving average convergence divergence (MACD) and signal line."""
    
    ema_fast = ema(close_data, window=fast_window)
    ema_slow = ema(close_data, window=slow_window)

    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, window=signal_window)
    histogram = macd_line - signal_line

    return pd.DataFrame({
        'MACD': macd_line,
        'Signal': signal_line,
        'Histogram': histogram,
    })