import os
import time
import pandas as pd
import paths as paths
import numpy as np

def load_data(folder, identifier, time_period, start_date=None, end_date=None):

    df = pd.read_csv(folder, index_col=0, parse_dates=True).loc[start_date:end_date]

    return df

def get_returns(data, start_date=None, end_date=None, type='log'):

    if type == 'log':
        return np.log(data / data.shift(1))
    elif type == 'simple':
        return data.pct_change()
    elif type == 'arithmetic':
        return data.diff()
    else:
        raise ValueError(f"Unsupported return type: {type}")

def expected_return(data, identifier, time_period, start_date=None, end_date=None):

    drift = calculate_drift(data, identifier, time_period, start_date, end_date)
    volatility = calculate_volatility(data, identifier, time_period, start_date, end_date)
    expected_return = drift + (volatility ** 2) / 2

    return expected_return

def calculate_volatility(data, identifier, time_period, start_date=None, end_date=None):

    log_returns = get_returns(data[identifier])

    volatility = np.std(log_returns, ddof=1)

    # NEED TO CHANGE THIS
    if identifier == 'BTC':
        annual_volatility = volatility * np.sqrt(365.25)
    else:
         annual_volatility = volatility * np.sqrt(252)

    return annual_volatility

def calculate_drift(data, identifier, time_period, start_date=None, end_date=None):

    #log_prices = np.log(df[identifier].values)
    #log_returns = np.diff(log_prices)

    log_returns = get_returns(data[identifier])

    drift = np.mean(log_returns)

    # NEED TO CHANGE THIS
    if identifier == 'BTC':
        annual_drift = drift * 365.25
    else:
            annual_drift = drift * 252

    return annual_drift

data = load_data(paths.CRYPTO_DATA_CSV, 'BTC', '1d', '2025-09-01', '2026-02-20')
print('volatility:', calculate_volatility(data, 'BTC', '1d', '2025-09-01'))
print('drift:', calculate_drift(data, 'BTC', '1d', '2025-09-01'))