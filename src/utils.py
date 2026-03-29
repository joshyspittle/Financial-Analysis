"""General utility functions for returns and rolling calculations.

Most helpers in this module are deliberately generic and operate on pandas
Series or DataFrames without any project-specific state.
"""

from collections.abc import Callable
from typing import TypeAlias

import numpy as np
import pandas as pd

PriceData: TypeAlias = pd.Series | pd.DataFrame


def get_returns(
    price_data: PriceData,
    return_type: str = 'log',
) -> PriceData:
    """Return log, simple, or arithmetic returns for a price series."""

    if return_type == 'log':
        return np.log(price_data / price_data.shift(1))
    if return_type == 'simple':
        return price_data.pct_change()
    if return_type == 'arithmetic':
        return price_data.diff()

    raise ValueError(f"Unsupported return type: {return_type}")


def mean_returns(
    close_data: pd.DataFrame,
    asset_id: str,
    interval: str,
    start_date: str | pd.Timestamp | None = None,
    end_date: str | pd.Timestamp | None = None,
) -> float:
    """Return annualised mean simple return for one column in a panel."""

    returns = get_returns(close_data[asset_id], return_type='simple')
    mean_return = returns.mean() * 365.25

    return float(mean_return)


def rolling_average(
    parameter_func: Callable[[pd.DataFrame, str, str], float],
    window_size: int,
    close_data: pd.DataFrame,
    asset_id: str,
    interval: str,
    start_date: str | pd.Timestamp | None = None,
    end_date: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Apply a parameter function over rolling windows and return the result."""

    results: list[dict[str, float | pd.Timestamp]] = []

    for i in range(window_size, len(close_data) + 1):
        window_slice = close_data.iloc[i - window_size:i]
        current_date = window_slice.index[-1]

        val = parameter_func(window_slice, asset_id, interval)
        results.append({'Date:': current_date, 'Value': val})

    return pd.DataFrame(results).set_index('Date:')
