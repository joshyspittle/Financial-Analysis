import pandas as pd

def simple_moving_average(close_data, identifier, window=21):
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

    sma = close_data[identifier].rolling(window).mean()

    return sma

def exponential_moving_average(close_data, identifier, span=21):
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
    
    ema = close_data[identifier].ewm(span=span, adjust=False).mean()

    return ema