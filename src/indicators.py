import pandas as pd
import paths as paths

def load_data(folder, identifier, time_period, start_date=None, end_date=None):

    df = pd.read_csv(folder, index_col=0, parse_dates=True).loc[start_date:end_date]

    return df

def simple_moving_average(data, identifier, window=21):
    """
    Compute the simple moving average (SMA) of a time series.

    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame containing time series data.
    identifier : str
        Column name of the instrument to compute the SMA for.
    window : int, optional
        Rolling window size (number of periods). 
        Default is 21.

    Returns
    -------
    sma : pandas.Series
        Simple moving average of the specified column.
        The result is indexed identically to the input data and will
        contain NaN values for the initial periods where the window
        is not fully populated.
    """

    sma = data[identifier].rolling(window).mean()

    return sma

def exponential_moving_average(data, identifier, span=21):
    """
    Compute the exponential moving average (EMA) of a time series.

    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame containing time series data.
    identifier : str
        Column name of the instrument to compute the EMA for.
    span : int, optional
        Span parameter for the exponential weighting. Default is 21.

    Returns
    -------
    ema : pandas.Series
        Exponential moving average of the specified column.
        The result is indexed identically to the input data and
        applies exponentially decreasing weights to past observations.
    """
    
    ema = data[identifier].ewm(span=span, adjust=False).mean()

    return ema

data = load_data(paths.CRYPTO_DATA_CSV, 'BTC', '1d', '2025-09-01', '2026-02-20')

print(simple_moving_average(data, 'BTC', window=30, start_date='2025-10-01', end_date='2026-01-31'))
print(exponential_moving_average(data, 'BTC', span=30, start_date='2025-10-01', end_date='2026-01-31'))
