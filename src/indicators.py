import os
import time
import pandas as pd
import paths as paths
import numpy as np

def load_data(folder, identifier, time_period, start_date=None, end_date=None):

    df = pd.read_csv(folder, index_col=0, parse_dates=True).loc[start_date:end_date]

    return df

def simple_moving_average(data, identifier, window=21, start_date=None, end_date=None):

    sma = data[identifier].rolling(window).mean()

    return sma

def exponential_moving_average(data, identifier, span=21, start_date=None, end_date=None):

    ema = data[identifier].ewm(span=span, adjust=False).mean()

    return ema

data = load_data(paths.CRYPTO_DATA_CSV, 'BTC', '1d', '2025-09-01', '2026-02-20')

print(simple_moving_average(data, 'BTC', window=30, start_date='2025-10-01', end_date='2026-01-31'))
print(exponential_moving_average(data, 'BTC', span=30, start_date='2025-10-01', end_date='2026-01-31'))
