"""Development scratchpad for interactive testing.

This file is not part of the production pipeline. It is used to load local
data, try out analysis functions, and preview charts while iterating.
"""

import pandas as pd
import src.features as features
import src.paths as paths
import src.portfolio as portfolio
import src.utils as utils
import src.visualisation as vis
from src.data_getter import load_data

crypto_ohlcv = load_data(paths.CRYPTO_DATA_PARQUET, '1d')
crypto_close = crypto_ohlcv.xs('Close', axis=1, level=1)

crypto_ohlc_window = load_data(paths.CRYPTO_DATA_PARQUET, '1d', start_date='01-01-2024')
crypto_close_window = crypto_ohlc_window.xs('Close', axis=1, level=1)

btc = crypto_ohlc_window['BTC']
eth = crypto_ohlc_window['ETH']
xrp = crypto_ohlc_window['XRP']

myportfolio = {
    'BTC': btc,
    'ETH': eth,
    'XRP': xrp,
}

weights = {
    'BTC': 0.333,
    'ETH': 0.333,
    'XRP': 0.333,
}

portfolio_ohlcv = portfolio.construct_ohlcv_rebalanced(myportfolio, weights)

if __name__ == '__main__':
    vis.plot_chart(portfolio_ohlcv)
