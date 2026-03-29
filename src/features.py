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
