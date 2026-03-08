import os
import time
import pandas as pd
import paths as paths
import numpy as np

def load_data(folder, identifier, time_period, start_date=None, end_date=None):

    df = pd.read_csv(folder, index_col=0, parse_dates=True).loc[start_date:end_date]

    return df

def get_returns(data, start_date=None, end_date=None, type='simple'):

    if type == 'simple':
        return data.pct_change()
    elif type == 'arithmetic':
        return data.diff()
    else:
        raise ValueError(f"Unsupported return type: {type}")
    
def mean_returns(data, identifier, time_period, start_date=None, end_date=None):

    returns = get_returns(data[identifier], type='simple')
    mean_returns = returns.mean() * 365.25

    return mean_returns

def rolling_average(parameter_func, window_size, data, identifier, time_period, start_date=None, end_date=None):

    results = []

    for i in range(window_size, len(data)+1):

        window_slice = data.iloc[i - window_size : i]
        current_date = window_slice.index[-1]

        val = parameter_func(window_slice, identifier, time_period)
        results.append({'Date:': current_date, 'Value': val})

    return pd.DataFrame(results).set_index('Date:')

def calculate_sharpe_ratio(data, identifier, time_period, start_date=None, end_date=None):

    df_macro = pd.read_csv(paths.MACRO_DATA_CSV, index_col=0, parse_dates=True).loc[start_date:end_date]
    returns = get_returns(data[identifier], type='simple')
    risk_free_return = (df_macro['US01Y'] / (100 * 365.25)).reindex(data.index).ffill()

    excess_returns = returns - risk_free_return
    volatility = np.std(excess_returns, ddof=1)

    sharpe_ratio = excess_returns.mean() / volatility * np.sqrt(365.25)

    return sharpe_ratio

def calculate_cagr(data, identifier, time_period, start_date=None, end_date=None):

    initial_price = data[identifier].iloc[0]
    final_price = data[identifier].iloc[-1]

    duration_days = (data.index[-1] - data.index[0]).days
    duration_years = duration_days / 365.25

    cagr = (final_price / initial_price) ** (1 / duration_years) - 1

    return cagr

def calculate_sortino_ratio(data, identifier, time_period, start_date=None, end_date=None):

    df = pd.read_csv(paths.MACRO_DATA_CSV, index_col=0, parse_dates=True).loc[start_date:end_date]
    risk_free_return = df['US01Y'].mean() / 100
    risk_free_daily_return = risk_free_return / 365.25

    returns = get_returns(data[identifier], type='simple')
    mean_return = returns.mean() * 365.25
    downside_returns = returns[returns < risk_free_daily_return]
    print('risk free daily', risk_free_daily_return)
    downside_volatility = downside_returns.std(ddof=1) * np.sqrt(365.25)

    sortino_ratio = (mean_return - risk_free_return) / downside_volatility

    return sortino_ratio

data = load_data(paths.CRYPTO_DATA_CSV, 'BTC', '1d', '2025-09-01', '2026-02-20')
print('cagr:', calculate_cagr(data, 'BTC', '1d', '2025-09-01'))
print('sharpe_ratio:', calculate_sharpe_ratio(data, 'BTC', '1d', '2025-09-01'))
print('30d volatility rolling average:', rolling_average(mean_returns, 30, data, 'BTC', '2025-09-01', '2026-02-20'))
print('sortino_ratio:', calculate_sortino_ratio(data, 'BTC', '1d', '2025-09-01'))