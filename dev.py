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
import src.metrics as metrics
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

max_dd, peak, trough = metrics.max_drawdown(btc, return_type='high-to-low')
#print(max_dd, peak, trough)

rsi = features.rsi(btc['Close'])
#print(rsi)
sma = features.sma(btc['Close'])
#print(sma)

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

dad_data = load_data(paths.CRYPTO_DATA_PARQUET, '1d', start_date='08-01-2025')
dad_eth = dad_data['ETH']
dad_xrp = dad_data['XRP']
dad_ltc = dad_data['LTC']

dad_portfolio = {
    'ETH': dad_eth,
    'XRP': dad_xrp,
    'LTC': dad_ltc,
}

dad_weights = {
    'ETH': 1/3,
    'XRP': 1/3,
    'LTC': 1/3,
}

dad_portfolio_ohlcv, stats = portfolio.construct_ohlcv_rebalanced(dad_portfolio, dad_weights, contribution_amount=75)
print(stats.iloc[-1])

crypto_portfolio_ohlcv = portfolio.construct_ohlcv_rebalanced(crypto_portfolio, crypto_weights)
indices_portfolio_ohlcv = portfolio.construct_ohlcv_rebalanced(indices_portfolio, indices_weights)

if __name__ == '__main__':
    vis.plot_chart(
    dad_portfolio_ohlcv,
    analyses=[
        {
            'fn': features.sma,
            'kwargs': {'window': 20},
            'style': {'color': '#f4d35e', 'width': 2},
        },
        {
            'fn': features.ema,
            'kwargs': {'window': 50},
            'style': {'color': '#90be6d', 'width': 2},
        },
        {
            'fn': features.rsi,
            'kwargs': {'window': 14},
            'name': 'RSI 14',
            'style': {'color': '#c77dff', 'width': 2, 'price_line': False, 'price_label': False},
             'guide_lines': [
                {'value': 70, 'color': '#ef5350aa', 'line_style': 'dashed', 'text': '70'},
                {'value': 50, 'color': '#9aa4b2aa', 'line_style': 'dotted', 'text': '50'},
                {'value': 30, 'color': '#26a69aaa', 'line_style': 'dashed', 'text': '30'},
             ],
        },
        {
            'fn': features.macd,
            'name': 'MACD',
            'series_styles': {
                'MACD': {'color': '#4fc3f7', 'width': 2},
                'Signal': {'color': '#ffca28', 'width': 2, 'line_style': 'dashed'},
                'Histogram': {
                    'positive_color': '#26a69acc',
                    'negative_color': '#ef5350cc',
                    'scale_margin_top': 0.15,
                    'scale_margin_bottom': 0.15,
                },
            },
        },
    ],
)
    #vis.plot_chart(btc, features.macd)
    #vis.plot_chart(crypto_portfolio_ohlcv)
    #vis.plot_chart(indices_portfolio_ohlcv)
