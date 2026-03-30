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

indices_ohlcv_window = load_data(paths.INDICES_DATA_PARQUET, '1d', start_date='01-01-2024')
snp = indices_ohlcv_window['SPX']
qqq = indices_ohlcv_window['QQQ']
iwm = indices_ohlcv_window['IWM']

btc = crypto_ohlc_window['BTC']
eth = crypto_ohlc_window['ETH']
xrp = crypto_ohlc_window['XRP']

indices_portfolio = {
    'SPY': snp,
    'QQQ': qqq,
    'IWM': iwm,
}

indices_weights = {
    'SPY': 1/3,
    'QQQ': 1/3,
    'IWM': 1/3,
}

crypto_portfolio = {
    'BTC': btc,
    'ETH': eth,
    'XRP': xrp,
}

crypto_weights = {
    'BTC': 1/3,
    'ETH': 1/3,
    'XRP': 1/3,
}

crypto_portfolio_ohlcv = portfolio.construct_ohlcv_rebalanced(crypto_portfolio, crypto_weights)
indices_portfolio_ohlcv = portfolio.construct_ohlcv_rebalanced(indices_portfolio, indices_weights)

if __name__ == '__main__':
    print(snp.tail())
    vis.plot_chart(snp)
    #vis.plot_chart(crypto_portfolio_ohlcv)
    #vis.plot_chart(indices_portfolio_ohlcv)
