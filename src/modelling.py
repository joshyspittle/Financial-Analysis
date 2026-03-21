import pandas as pd
import paths as paths
import numpy as np

def load_data(folder, identifier, time_period, start_date=None, end_date=None):

    df = pd.read_csv(folder, index_col=0, parse_dates=True).loc[start_date:end_date]

    return df

def get_returns(data, type='log'):
    """
    Calculate returns for a given time series.

    Parameters
    ----------
    data : pandas.Series or pandas.DataFrame
        Time series data to compute returns for.
    type : str, optional
        Type of return to calculate:
        - 'log'        : logarithmic returns
        - 'simple'     : percentage returns
        - 'arithmetic' : absolute differences
        Default is 'log'.

    Returns
    -------
    returns : pandas.Series or pandas.DataFrame
        Returns of the same shape as the input data.
        The first observation will contain NaN values due to differencing.

    Raises
    ------
    ValueError
        If an unsupported return type is specified.
    """

    if type == 'log':
        return np.log(data / data.shift(1))
    elif type == 'simple':
        return data.pct_change()
    elif type == 'arithmetic':
        return data.diff()
    else:
        raise ValueError(f"Unsupported return type: {type}")

def expected_arithmetic_return(data, identifier, time_period, start_date=None, end_date=None):
    """
    Estimate the expected return of an instrument using drift and volatility.

    The expected return is computed assuming lognormally distributed returns:
    E[R] = μ + (σ² / 2), where μ is the drift and σ is the volatility.

    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame containing the time series data.
    identifier : str
        Column name of the instrument.
    time_period : str
        Time frequency of the data (e.g. '1d').
    start_date : str, optional
        Start date for the calculation (inclusive).
    end_date : str, optional
        End date for the calculation (inclusive).

    Returns
    -------
    expected_return : float
        Annualised expected return of the instrument.
    """

    drift = calculate_drift(data, identifier, time_period, start_date, end_date)
    volatility = calculate_volatility(data, identifier, time_period, start_date, end_date)
    expected_return = drift + (volatility ** 2) / 2

    return expected_return

def calculate_volatility(data, identifier, time_period, start_date=None, end_date=None):
    """
    Calculate the annualised volatility of an instrument.

    Volatility is computed as the standard deviation of log returns,
    scaled to an annual value.

    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame containing the time series data.
    identifier : str
        Column name of the instrument.
    time_period : str
        Time frequency of the data (e.g. '1d').
    start_date : str, optional
        Start date for the calculation (inclusive).
    end_date : str, optional
        End date for the calculation (inclusive).

    Returns
    -------
    annual_volatility : float
        Annualised standard deviation of log returns.
    """

    log_returns = get_returns(data[identifier])

    volatility = np.std(log_returns, ddof=1)

    # NEED TO CHANGE THIS
    if identifier == 'BTC':
        annual_volatility = volatility * np.sqrt(365.25)
    else:
         annual_volatility = volatility * np.sqrt(252)

    return annual_volatility

def calculate_drift(data, identifier, time_period, start_date=None, end_date=None):
    """
    Calculate the annualised drift of an instrument.

    Drift is defined as the mean of log returns, scaled to an annual value.

    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame containing the time series data.
    identifier : str
        Column name of the instrument.
    time_period : str
        Time frequency of the data (e.g. '1d').
    start_date : str, optional
        Start date for the calculation (inclusive).
    end_date : str, optional
        End date for the calculation (inclusive).

    Returns
    -------
    annual_drift : float
        Annualised mean of log returns.
    """

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
print('expected_return:', expected_arithmetic_return(data, 'BTC', '1d', '2025-09-01'))