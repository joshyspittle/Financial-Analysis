"""Simple return and volatility estimators for stochastic modelling.

The functions here are currently lightweight helpers for simulation work.
They assume daily data and annualise using either ``365.25`` for BTC or
``252`` for non-BTC assets. That convention is provisional and should be
revisited once trading-calendar handling is formalised.
"""

import numpy as np
import pandas as pd

import src.utils as utils


def expected_arithmetic_return(close_series: pd.Series) -> float:
    """Estimate arithmetic return as drift plus half the variance."""

    drift = calculate_drift(close_series)
    volatility = calculate_volatility(close_series)
    expected_return = drift + (volatility ** 2) / 2

    return float(expected_return)


def calculate_volatility(close_series: pd.Series) -> float:
    """Return annualised volatility from log returns."""

    asset_id = str(close_series.name)
    log_returns = utils.get_returns(close_series, return_type='log')
    volatility = np.std(log_returns, ddof=1)

    if asset_id == 'BTC':
        annual_volatility = volatility * np.sqrt(365.25)
    else:
        annual_volatility = volatility * np.sqrt(252)

    return float(annual_volatility)


def calculate_drift(close_series: pd.Series) -> float:
    """Return annualised drift from mean log returns."""

    asset_id = str(close_series.name)
    log_returns = utils.get_returns(close_series, return_type='log')
    drift = np.mean(log_returns)

    if asset_id == 'BTC':
        annual_drift = drift * 365.25
    else:
        annual_drift = drift * 252

    return float(annual_drift)
