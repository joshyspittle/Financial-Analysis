import pandas as pd
import src.paths as paths
import numpy as np

def load_data(folder, identifier, time_period, start_date=None, end_date=None):

    df = pd.read_csv(folder, index_col=0, parse_dates=True).loc[start_date:end_date]

    return df

def get_returns(close_data, start_date=None, end_date=None, type='simple'):
    """
    Compute returns for a time series.

    Parameters
    ----------
    data : pandas.Series or pandas.DataFrame
        Time series data to compute returns for.
    start_date : str, optional
        Unused. Included for interface consistency.
    end_date : str, optional
        Unused. Included for interface consistency.
    type : str, optional
        Type of return to compute:
        - 'simple'     : percentage returns (default)
        - 'arithmetic' : absolute differences

    Returns
    -------
    returns : pandas.Series or pandas.DataFrame
        Returns of the same shape as the input data. The first observation
        will contain NaN values due to differencing.

    Raises
    ------
    ValueError
        If an unsupported return type is specified.
    """

    if type == 'simple':
        return close_data.pct_change()
    elif type == 'arithmetic':
        return close_data.diff()
    else:
        raise ValueError(f"Unsupported return type: {type}")
    
def mean_returns(close_data, identifier, time_period, start_date=None, end_date=None):
    """
    Calculate the annualised mean simple return of an instrument.

    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame containing time series data.
    identifier : str
        Column name of the instrument.
    time_period : str
        Time frequency of the data (e.g. '1d').
    start_date : str, optional
        Unused. Included for interface consistency.
    end_date : str, optional
        Unused. Included for interface consistency.

    Returns
    -------
    mean_returns : float
        Annualised mean of simple returns, scaled using 365.25 days.
    """

    returns = get_returns(close_data[identifier], type='simple')
    mean_returns = returns.mean() * 365.25

    return mean_returns

def rolling_average(parameter_func, window_size, close_data, identifier, time_period, start_date=None, end_date=None):
    """
    Compute a rolling metric over a specified window using a custom function.

    Applies a user-defined parameter function over rolling windows of the data
    and returns the resulting time series.

    Parameters
    ----------
    parameter_func : callable
        Function to apply to each rolling window. Must accept arguments:
        (data, identifier, time_period).
    window_size : int
        Number of observations in each rolling window.
    data : pandas.DataFrame
        DataFrame containing time series data.
    identifier : str
        Column name of the instrument.
    time_period : str
        Time frequency of the data (e.g. '1d').
    start_date : str, optional
        Unused. Included for interface consistency.
    end_date : str, optional
        Unused. Included for interface consistency.

    Returns
    -------
    rolling_df : pandas.DataFrame
        DataFrame indexed by window end date, containing computed values
        for each rolling window.
    """

    results = []

    for i in range(window_size, len(close_data)+1):

        window_slice = close_data.iloc[i - window_size : i]
        current_date = window_slice.index[-1]

        val = parameter_func(window_slice, identifier, time_period)
        results.append({'Date:': current_date, 'Value': val})

    return pd.DataFrame(results).set_index('Date:')

def calculate_cagr(close_data, identifier, time_period, start_date=None, end_date=None):
    """
    Calculate the Compound Annual Growth Rate (CAGR) of an instrument.

    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame containing time series data.
    identifier : str
        Column name of the instrument.
    time_period : str
        Time frequency of the data (e.g. '1d').
    start_date : str, optional
        Unused. Included for interface consistency.
    end_date : str, optional
        Unused. Included for interface consistency.

    Returns
    -------
    cagr : float
        Annualised growth rate of the instrument over the specified period.
    """

    initial_price = close_data[identifier].iloc[0]
    final_price = close_data[identifier].iloc[-1]

    duration_days = (close_data.index[-1] - close_data.index[0]).days
    duration_years = duration_days / 365.25

    cagr = (final_price / initial_price) ** (1 / duration_years) - 1

    return cagr

def calculate_sharpe_ratio(close_data, identifier, time_period, start_date=None, end_date=None):
    """
    Calculate the annualised Sharpe ratio of an instrument.

    The Sharpe ratio is computed using excess returns over a risk-free rate,
    with volatility defined as the standard deviation of excess returns.

    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame containing time series data.
    identifier : str
        Column name of the instrument.
    time_period : str
        Time frequency of the data (e.g. '1d').
    start_date : str, optional
        Start date for filtering both asset and macro data.
    end_date : str, optional
        End date for filtering both asset and macro data.

    Returns
    -------
    sharpe_ratio : float
        Annualised Sharpe ratio based on daily excess returns.

    Notes
    -----
    - Risk-free rate is sourced from 'US01Y' and converted to a daily rate.
    - Missing values are forward-filled to align with asset data.
    """

    df_macro = pd.read_csv(paths.MACRO_DATA_PARQUET, index_col=0, parse_dates=True).loc[start_date:end_date]
    returns = get_returns(close_data[identifier], type='simple')
    risk_free_return = (df_macro['US01Y'] / (100 * 365.25)).reindex(data.index).ffill()

    excess_returns = returns - risk_free_return
    volatility = np.std(excess_returns, ddof=1)

    sharpe_ratio = excess_returns.mean() / volatility * np.sqrt(365.25)

    return sharpe_ratio

def calculate_sortino_ratio(close_data, identifier, time_period, start_date=None, end_date=None):
    """
    Calculate the annualised Sortino ratio of an instrument.

    The Sortino ratio measures risk-adjusted return using downside
    volatility instead of total volatility.

    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame containing time series data.
    identifier : str
        Column name of the instrument.
    time_period : str
        Time frequency of the data (e.g. '1d').
    start_date : str, optional
        Start date for filtering both asset and macro data.
    end_date : str, optional
        End date for filtering both asset and macro data.

    Returns
    -------
    sortino_ratio : float
        Annualised Sortino ratio.

    Notes
    -----
    - Downside volatility is calculated using returns below the daily
    risk-free rate.
    - Risk-free rate is derived from 'US01Y' and annualised.
    """

    df = pd.read_csv(paths.MACRO_DATA_PARQUET, index_col=0, parse_dates=True).loc[start_date:end_date]
    risk_free_return = df['US01Y'].mean() / 100
    risk_free_daily_return = risk_free_return / 365.25

    returns = get_returns(close_data[identifier], type='simple')
    mean_return = returns.mean() * 365.25
    downside_returns = returns[returns < risk_free_daily_return]
    print('risk free daily', risk_free_daily_return)
    downside_volatility = downside_returns.std(ddof=1) * np.sqrt(365.25)

    sortino_ratio = (mean_return - risk_free_return) / downside_volatility

    return sortino_ratio

data = load_data(paths.CRYPTO_DATA_PARQUET, 'BTC', '1d', '2025-09-01', '2026-02-20')
print('cagr:', calculate_cagr(data, 'BTC', '1d', '2025-09-01'))
print('sharpe_ratio:', calculate_sharpe_ratio(data, 'BTC', '1d', '2025-09-01'))
print('30d volatility rolling average:', rolling_average(mean_returns, 30, data, 'BTC', '2025-09-01', '2026-02-20'))
print('sortino_ratio:', calculate_sortino_ratio(data, 'BTC', '1d', '2025-09-01'))