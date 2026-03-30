"""Portfolio construction helpers.

Assumptions:
- Inputs are dictionaries of single-asset OHLCV DataFrames keyed by ticker.
- Weights are normalized internally and initial portfolio NAV is 100.
- Buy-and-hold keeps inception units fixed.
- Rebalanced portfolios rebalance at the close of flagged rebalance dates.
- Portfolio ``High`` and ``Low`` are synthetic bar approximations.
- Portfolio ``Volume`` is a weighted dollar-volume proxy, not traded turnover.
"""

import pandas as pd
from collections.abc import Mapping
from typing import TypeAlias

AssetOhlcvMap: TypeAlias = Mapping[str, pd.DataFrame]
PortfolioWeights: TypeAlias = Mapping[str, float]


def construct_nav_buyhold(ohlcv_data: AssetOhlcvMap, weights: PortfolioWeights) -> pd.Series:
    """Return buy-and-hold portfolio NAV as the synthetic close series."""

    portfolio_ohlcv = construct_ohlcv_buyhold(ohlcv_data, weights)
    return portfolio_ohlcv['Close']


def construct_nav_rebalanced(
    ohlcv_data: AssetOhlcvMap,
    weights: PortfolioWeights,
    rebalance_freq: str = 'M',
) -> pd.Series:
    """Return rebalanced portfolio NAV as the synthetic close series."""

    portfolio_ohlcv = construct_ohlcv_rebalanced(ohlcv_data, weights, rebalance_freq=rebalance_freq)
    return portfolio_ohlcv['Close']


def construct_ohlcv_buyhold(ohlcv_data: AssetOhlcvMap, weights: PortfolioWeights) -> pd.DataFrame:
    """Return synthetic portfolio OHLCV for a buy-and-hold allocation."""

    weights_series, opens, highs, lows, closes, volumes = _prepare_inputs(ohlcv_data, weights)

    units = (weights_series * 100) / opens.iloc[0]
    records: list[dict[str, float | pd.Timestamp]] = []

    for date in opens.index:
        open_prices = opens.loc[date]
        high_prices = highs.loc[date]
        low_prices = lows.loc[date]
        close_prices = closes.loc[date]
        volume_values = volumes.loc[date]

        portfolio_open = (units * open_prices).sum()
        portfolio_high = (units * high_prices).sum()
        portfolio_low = (units * low_prices).sum()
        portfolio_close = (units * close_prices).sum()

        start_weights = (units * open_prices) / portfolio_open
        dollar_volume_proxy = (volume_values * close_prices * start_weights).sum()

        records.append({
            'date': date,
            'Open': portfolio_open,
            'High': portfolio_high,
            'Low': portfolio_low,
            'Close': portfolio_close,
            'Volume': dollar_volume_proxy,
        })

    return pd.DataFrame(records).set_index('date')


def construct_ohlcv_rebalanced(
    ohlcv_data: AssetOhlcvMap,
    weights: PortfolioWeights,
    rebalance_freq: str = 'M',
) -> pd.DataFrame:
    """Return synthetic portfolio OHLCV for a periodically rebalanced allocation."""

    weights_series, opens, highs, lows, closes, volumes = _prepare_inputs(ohlcv_data, weights)
    rebalance_flags = _get_rebalance_flags(opens.index, rebalance_freq)

    units = (weights_series * 100) / opens.iloc[0]
    records: list[dict[str, float | pd.Timestamp]] = []

    for date in opens.index:
        open_prices = opens.loc[date]
        high_prices = highs.loc[date]
        low_prices = lows.loc[date]
        close_prices = closes.loc[date]
        volume_values = volumes.loc[date]

        portfolio_open = (units * open_prices).sum()
        portfolio_high = (units * high_prices).sum()
        portfolio_low = (units * low_prices).sum()
        portfolio_close = (units * close_prices).sum()

        start_weights = (units * open_prices) / portfolio_open
        dollar_volume_proxy = (volume_values * close_prices * start_weights).sum()

        records.append({
            'date': date,
            'Open': portfolio_open,
            'High': portfolio_high,
            'Low': portfolio_low,
            'Close': portfolio_close,
            'Volume': dollar_volume_proxy,
        })

        if rebalance_flags.loc[date]:
            units = (weights_series * portfolio_close) / close_prices

    return pd.DataFrame(records).set_index('date')


def _prepare_inputs(
    ohlcv_data: AssetOhlcvMap,
    weights: PortfolioWeights,
) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Validate and align asset OHLCV inputs to a shared date index."""

    weights_series = pd.Series(weights, dtype=float)

    if weights_series.empty:
        raise ValueError('weights must not be empty')

    if (weights_series < 0).any():
        raise ValueError('weights must be non-negative')

    if weights_series.sum() != 1:
        raise ValueError('weights must sum to 1')

    missing_assets = set(weights_series.index) - set(ohlcv_data.keys())
    if missing_assets:
        missing = ', '.join(sorted(missing_assets))
        raise ValueError(f'Missing OHLCV data for assets: {missing}')

    weights_series = weights_series / weights_series.sum()

    opens = pd.DataFrame({ticker: ohlcv_data[ticker]['Open'] for ticker in weights_series.index})
    highs = pd.DataFrame({ticker: ohlcv_data[ticker]['High'] for ticker in weights_series.index})
    lows = pd.DataFrame({ticker: ohlcv_data[ticker]['Low'] for ticker in weights_series.index})
    closes = pd.DataFrame({ticker: ohlcv_data[ticker]['Close'] for ticker in weights_series.index})
    volumes = pd.DataFrame({ticker: ohlcv_data[ticker]['Volume'] for ticker in weights_series.index})

    aligned = pd.concat(
        {
            'Open': opens,
            'High': highs,
            'Low': lows,
            'Close': closes,
            'Volume': volumes,
        },
        axis=1,
    ).dropna()

    opens = aligned['Open']
    highs = aligned['High']
    lows = aligned['Low']
    closes = aligned['Close']
    volumes = aligned['Volume']

    if opens.empty:
        raise ValueError('No overlapping OHLCV history after alignment')

    return weights_series, opens, highs, lows, closes, volumes


def _get_rebalance_flags(index: pd.Index, freq: str) -> pd.Series:
    """Flag the last available row in each rebalance period."""

    index = pd.DatetimeIndex(index)

    if freq == 'D':
        return pd.Series(True, index=index)

    if freq == 'W':
        periods = index.to_period('W-FRI')
    elif freq == 'M':
        periods = index.to_period('M')
    elif freq == 'Q':
        periods = index.to_period('Q')
    elif freq == 'Y':
        periods = index.to_period('Y')
    else:
        raise ValueError(f'Unsupported rebalance frequency: {freq}')

    period_series = pd.Series(index, index=index)
    period_ends = period_series.groupby(periods).transform('max')

    return pd.Series(index == period_ends.to_numpy(), index=index)
