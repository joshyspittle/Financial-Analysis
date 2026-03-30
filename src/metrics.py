"""Performance and risk metrics.

Assumptions:
- Inputs are close-price Series indexed by datetime unless stated otherwise.
- Annualisation is daily-based using ``365.25``.
- The risk-free proxy is sourced from ``US01Y`` in the macro dataset.
- Macro data is aligned to asset dates by forward filling where needed.
"""

import numpy as np
import pandas as pd

import src.paths as paths
import src.utils as utils

from typing import Literal


def calculate_cagr(close_series: pd.Series) -> float:
    """Return compound annual growth rate over the supplied window."""

    initial_price = close_series.iloc[0]
    final_price = close_series.iloc[-1]

    duration_days = (close_series.index[-1] - close_series.index[0]).days
    duration_years = duration_days / 365.25

    cagr = (final_price / initial_price) ** (1 / duration_years) - 1
    return float(cagr)


def calculate_sharpe_ratio(
    close_series: pd.Series,
    start_date: str | pd.Timestamp | None = None,
    end_date: str | pd.Timestamp | None = None,
) -> float:
    """Return the annualised Sharpe ratio using ``US01Y`` as the risk-free proxy."""

    df_macro = pd.read_csv(paths.MACRO_DATA_PARQUET, index_col=0, parse_dates=True).loc[start_date:end_date]
    returns = utils.get_returns(close_series, return_type='simple')
    risk_free_return = (df_macro['US01Y'] / (100 * 365.25)).reindex(close_series.index).ffill()

    excess_returns = returns - risk_free_return
    volatility = np.std(excess_returns, ddof=1)

    sharpe_ratio = excess_returns.mean() / volatility * np.sqrt(365.25)
    return float(sharpe_ratio)


def calculate_sortino_ratio(
    close_series: pd.Series,
    start_date: str | pd.Timestamp | None = None,
    end_date: str | pd.Timestamp | None = None,
) -> float:
    """Return the annualised Sortino ratio using downside volatility only."""

    df = pd.read_csv(paths.MACRO_DATA_PARQUET, index_col=0, parse_dates=True).loc[start_date:end_date]
    risk_free_return = df['US01Y'].mean() / 100
    risk_free_daily_return = risk_free_return / 365.25

    returns = utils.get_returns(close_series, return_type='simple')
    mean_return = returns.mean() * 365.25
    downside_returns = returns[returns < risk_free_daily_return]
    print('risk free daily', risk_free_daily_return)
    downside_volatility = downside_returns.std(ddof=1) * np.sqrt(365.25)

    sortino_ratio = (mean_return - risk_free_return) / downside_volatility
    return float(sortino_ratio)


def max_drawdown(
    ohlcv_data: pd.DataFrame,
    start_date: str | pd.Timestamp | None = None,
    end_date: str | pd.Timestamp | None = None,
    return_type: Literal['close-to-close', 'high-to-low'] = 'close-to-close',
) -> tuple[float, pd.Timestamp, pd.Timestamp]:
    """Placeholder for max drawdown logic."""

    ohlc_cols = {'Open', 'High', 'Low', 'Close'}
    is_ohlcv = ohlc_cols.issubset(ohlcv_data.columns)

    if return_type == 'high-to-low' and not is_ohlcv:
        raise ValueError("return_type: 'high-to-low' requires full OHLCV data")
    
    if return_type == 'high-to-low':
        peak_series = ohlcv_data['High']
        trough_series = ohlcv_data['Low']
    else:
        if is_ohlcv:
            peak_series = ohlcv_data['Close']
        else:
            peak_series = ohlcv_data
        trough_series = peak_series

    rolling_max = peak_series.cummax()
    drawdown = (trough_series - rolling_max) / rolling_max

    max_dd = drawdown.min()
    trough = drawdown.idxmin()
    peak = peak_series[:trough].idxmax()

    return max_dd, peak, trough

