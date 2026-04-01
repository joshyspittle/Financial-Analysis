"""Portfolio construction helpers.

Assumptions:
- Inputs are dictionaries of single-asset OHLCV DataFrames keyed by ticker.
- Weights are normalized internally and initial portfolio NAV is 100.
- Buy-and-hold keeps inception units fixed.
- Rebalanced portfolios rebalance at the open of flagged rebalance dates.
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

    portfolio_ohlcv, _ = construct_ohlcv_buyhold(ohlcv_data, weights)
    return portfolio_ohlcv['Close']


def construct_nav_rebalanced(
    ohlcv_data: AssetOhlcvMap,
    weights: PortfolioWeights,
    rebalance_freq: str = 'M',
) -> pd.Series:
    """Return rebalanced portfolio NAV as the synthetic close series."""

    portfolio_ohlcv, _ = construct_ohlcv_rebalanced(ohlcv_data, weights, rebalance_freq=rebalance_freq)
    return portfolio_ohlcv['Close']


def construct_ohlcv_buyhold(
    ohlcv_data: AssetOhlcvMap,
    weights: PortfolioWeights,
    contribution_amount: float = 100,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return synthetic portfolio OHLCV for a buy-and-hold allocation."""

    weights_series, opens, highs, lows, closes, volumes = _prepare_inputs(ohlcv_data, weights)

    units = (weights_series * contribution_amount) / opens.iloc[0]
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
            'TotalInvested': contribution_amount,
            'ReturnOnCost': (portfolio_close - contribution_amount) / contribution_amount,
        })

    result = pd.DataFrame(records).set_index('date')
    return _split_ohlcv_and_stats(result)


def construct_ohlcv_rebalanced(
    ohlcv_data: AssetOhlcvMap,
    weights: PortfolioWeights,
    contribution_amount: float = 100,
    rebalance_freq: str = 'M',
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return synthetic portfolio OHLCV for a periodically rebalanced allocation."""

    weights_series, opens, highs, lows, closes, volumes = _prepare_inputs(ohlcv_data, weights)
    rebalance_flags = _get_rebalance_flags(opens.index, rebalance_freq)

    units = (weights_series * contribution_amount) / opens.iloc[0]
    records: list[dict[str, float | pd.Timestamp]] = []

    for date in opens.index:
        open_prices = opens.loc[date]
        high_prices = highs.loc[date]
        low_prices = lows.loc[date]
        close_prices = closes.loc[date]
        volume_values = volumes.loc[date]

        if rebalance_flags.loc[date]:
            portfolio_open = (units * open_prices).sum()
            units = (weights_series * portfolio_open) / open_prices

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
            'TotalInvested': contribution_amount,
            'ReturnOnCost': (portfolio_close - contribution_amount) / contribution_amount,
        })

    result = pd.DataFrame(records).set_index('date')
    return _split_ohlcv_and_stats(result)


def dca(
    ohlcv_data: AssetOhlcvMap,
    weights: PortfolioWeights,
    contribution_freq: str = 'M',
    contribution_amount: float = 100,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return synthetic portfolio OHLCV for a dollar-cost average strategy."""

    weights_series, opens, _, _, _, _ = _prepare_inputs(ohlcv_data, weights)
    contribution_flags = _get_period_start_flags(opens.index, contribution_freq)
    contribution_dates = opens.index[contribution_flags]

    return _construct_dca_from_slices(
        ohlcv_data,
        weights,
        contribution_dates=contribution_dates,
        contribution_flags=contribution_flags,
        contribution_amount=contribution_amount,
        constructor=construct_ohlcv_buyhold,
    )


def dca_rebalanced(
    ohlcv_data: AssetOhlcvMap,
    weights: PortfolioWeights,
    contribution_freq: str = 'M',
    rebalance_freq: str = 'M',
    contribution_amount: float = 100,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return synthetic portfolio OHLCV for a DCA strategy with periodic rebalancing."""

    weights_series, opens, _, _, _, _ = _prepare_inputs(ohlcv_data, weights)
    contribution_flags = _get_period_start_flags(opens.index, contribution_freq)
    contribution_dates = opens.index[contribution_flags]

    return _construct_dca_from_slices(
        ohlcv_data,
        weights,
        contribution_dates=contribution_dates,
        contribution_flags=contribution_flags,
        contribution_amount=contribution_amount,
        constructor=construct_ohlcv_rebalanced,
        rebalance_freq=rebalance_freq,
    )


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


def _construct_dca_from_slices(
    ohlcv_data: AssetOhlcvMap,
    weights: PortfolioWeights,
    contribution_dates: pd.Index,
    contribution_flags: pd.Series,
    contribution_amount: float,
    constructor,
    **constructor_kwargs,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build a contribution strategy by summing scaled portfolio sleeves."""

    weights_series, opens, _, _, _, _ = _prepare_inputs(ohlcv_data, weights)
    full_index = opens.index
    slices: list[pd.DataFrame] = []

    for date in contribution_dates:
        slice_data = {
            ticker: ohlcv_data[ticker].loc[date:]
            for ticker in weights_series.index
        }

        portfolio_slice, slice_stats = constructor(slice_data, weights, **constructor_kwargs)
        portfolio_slice = portfolio_slice.reindex(full_index)
        slice_stats = slice_stats.reindex(full_index)
        portfolio_slice[['Open', 'High', 'Low', 'Close', 'Volume']] = (
            portfolio_slice[['Open', 'High', 'Low', 'Close', 'Volume']]
            * (contribution_amount / 100.0)
        )
        slice_stats['TotalInvested'] = slice_stats['TotalInvested'] * (contribution_amount / 100.0)
        slices.append(_combine_ohlcv_and_stats(portfolio_slice, slice_stats))

    if not slices:
        ohlcv = pd.DataFrame(
            0.0,
            index=full_index,
            columns=['Open', 'High', 'Low', 'Close', 'Volume'],
        )
        stats = pd.DataFrame(
            {'TotalInvested': 0.0, 'ReturnOnCost': pd.NA},
            index=full_index,
        )
        return ohlcv, stats

    combined = pd.concat(slices, axis=1, keys=range(len(slices)))
    result = pd.DataFrame({
        column: combined.xs(column, axis=1, level=1).fillna(0.0).sum(axis=1)
        for column in ['Open', 'High', 'Low', 'Close', 'Volume', 'TotalInvested']
    }, index=full_index)

    result['TotalInvested'] = contribution_flags.astype(float).cumsum() * contribution_amount
    result['ReturnOnCost'] = pd.NA

    invested_mask = result['TotalInvested'] > 0
    result.loc[invested_mask, 'ReturnOnCost'] = (
        (result.loc[invested_mask, 'Close'] - result.loc[invested_mask, 'TotalInvested'])
        / result.loc[invested_mask, 'TotalInvested']
    )

    return _split_ohlcv_and_stats(result)


def _split_ohlcv_and_stats(result: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a combined result into OHLCV data and accounting stats."""

    ohlcv = result[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    stats = result[['TotalInvested', 'ReturnOnCost']].copy()
    return ohlcv, stats


def _combine_ohlcv_and_stats(ohlcv: pd.DataFrame, stats: pd.DataFrame) -> pd.DataFrame:
    """Combine OHLCV data and stats into a single aligned DataFrame."""

    return pd.concat([ohlcv, stats], axis=1)


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


def _get_period_start_flags(index: pd.Index, freq: str) -> pd.Series:
    """Flag the first available row in each contribution period."""

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
        raise ValueError(f'Unsupported contribution frequency: {freq}')

    period_series = pd.Series(index, index=index)
    period_starts = period_series.groupby(periods).transform('min')

    return pd.Series(index == period_starts.to_numpy(), index=index)
